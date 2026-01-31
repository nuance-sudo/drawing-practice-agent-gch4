"""お手本画像生成サービス

ユーザーのデッサン分析結果に基づいて、Cloud Run Functionを呼び出し
お手本画像の生成を依頼する。
"""

import asyncio
import json
from typing import List, Optional

import structlog
import google.auth.transport.requests
import google.oauth2.id_token
import aiohttp

from src.config import settings
from src.models.feedback import DessinAnalysis
from src.models.rank import UserRank

logger = structlog.get_logger()


class ImageGenerationError(Exception):
    """画像生成エラー"""
    pass


class ImageGenerationService:
    """お手本画像生成サービス（Cloud Function クライアント）"""

    def __init__(self) -> None:
        """初期化"""
        self.function_url = settings.image_generation_function_url

    async def generate_example_image(
        self,
        task_id: str,
        original_image_url: str,
        analysis: DessinAnalysis,
        user_rank: UserRank,
        motif_tags: List[str]
    ) -> None:
        """お手本画像生成リクエストを送信する（非同期）

        Cloud Functionにお手本画像生成を依頼し、即座にリターンする。
        実際の画像生成と完了通知はFunction側で行われる。

        Args:
            task_id: タスクID
            original_image_url: 元画像のURL
            analysis: デッサン分析結果
            user_rank: ユーザーランク情報
            motif_tags: モチーフタグ

        Raises:
            ImageGenerationError: リクエスト送信に失敗した場合
        """
        if not self.function_url:
            logger.warning("image_generation_disabled_no_url")
            return

        try:
            logger.info(
                "image_generation_request_started",
                task_id=task_id,
                user_id=user_rank.user_id,
                function_url=self.function_url
            )

            # リクエストペイロード作成
            payload = {
                "task_id": task_id,
                "user_id": user_rank.user_id,
                "original_image_url": original_image_url,
                "analysis": analysis.model_dump(),
                "current_rank_label": user_rank.current_rank.label,
                "target_rank_label": self._get_target_rank_label(user_rank.current_rank.label),
                "motif_tags": motif_tags
            }

            # IDトークン取得
            # Cloud Functions Gen2の場合、.run.appのURLをtarget_audienceとして使用
            target_audience = self._convert_to_run_app_url(self.function_url)
            auth_req = google.auth.transport.requests.Request()
            
            # 同期処理なのでExecutorで実行
            id_token = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: google.oauth2.id_token.fetch_id_token(auth_req, target_audience)
            )

            # Cloud Function呼び出し
            headers = {
                "Authorization": f"Bearer {id_token}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.function_url,
                    json=payload,
                    headers=headers,
                    timeout=10  # リクエスト自体はすぐ終わるはず
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ImageGenerationError(
                            f"Cloud Function request failed: {response.status} - {error_text}"
                        )
                    
                    logger.info(
                        "image_generation_request_sent",
                        task_id=task_id,
                        status=response.status
                    )

        except Exception as e:
            logger.error(
                "image_generation_request_failed",
                task_id=task_id,
                error=str(e),
                error_type=type(e).__name__
            )
            # リトライはFunction側や呼び出し元の方針によるが、ここではエラーを送出せずログのみとする場合も考慮
            # しかし呼び出し元でステータス管理するなら例外を投げた方がよいか？
            # reviews.pyでは例外キャッチしているので投げてOK
            raise ImageGenerationError(f"Failed to request generation: {e}")

    def _convert_to_run_app_url(self, url: str) -> str:
        """Cloud Functions Gen2のURLを.run.app形式に変換（IDトークンのtarget_audience用）
        
        Cloud Functions Gen2の場合、IDトークンのtarget_audienceは.run.appのURLである必要があります。
        .cloudfunctions.netのURLが渡された場合、.run.app形式に変換します。
        
        Args:
            url: .cloudfunctions.netまたは.run.appのURL
            
        Returns:
            .run.app形式のURL（既に.run.appの場合はそのまま）
        """
        if ".cloudfunctions.net" in url:
            # https://REGION-PROJECT.cloudfunctions.net/FUNCTION_NAME
            # → https://FUNCTION_NAME-XXXXX-REGION.a.run.app
            # 正確な変換には実際のデプロイ後のURLが必要だが、簡易的に変換を試みる
            # 実際には環境変数に.run.appのURLを設定することを推奨
            logger.warning(
                "converting_cloudfunctions_url_to_run_app",
                original_url=url,
                note="Consider using .run.app URL directly in environment variable"
            )
            # 簡易変換（正確ではない可能性がある）
            return url.replace(".cloudfunctions.net", ".a.run.app")
        return url

    def _get_target_rank_label(self, current_rank_label: str) -> str:
        """現在のランクからターゲットランクのラベルを算出
        
        Args:
            current_rank_label: 現在のランクのラベル（例: "10級", "1段", "師範代"）
            
        Returns:
            次のランクのラベル。最高ランクの場合は現在のラベルをそのまま返す。
        """
        from src.models.rank import Rank
        
        # ラベルから現在のRankを逆引き
        current_rank: Rank | None = None
        for rank in Rank:
            if rank.label == current_rank_label:
                current_rank = rank
                break
        
        if current_rank is None:
            # 不明なラベルの場合は入力をそのまま返す
            logger.warning("unknown_rank_label", label=current_rank_label)
            return current_rank_label
        
        # 次のランクを取得（最高ランクの場合は現在のランクを返す）
        if current_rank.value >= Rank.SHIHAN.value:
            return current_rank.label
        
        try:
            next_rank = Rank(current_rank.value + 1)
            return next_rank.label
        except ValueError:
            # Invalid rank value, return current rank as fallback
            logger.warning("invalid_next_rank_value", current_value=current_rank.value)
            return current_rank.label


# シングルトンインスタンス
_image_generation_service: Optional[ImageGenerationService] = None


def get_image_generation_service() -> ImageGenerationService:
    """ImageGenerationServiceのシングルトンインスタンスを取得"""
    global _image_generation_service
    if _image_generation_service is None:
        _image_generation_service = ImageGenerationService()
    return _image_generation_service