"""アノテーション画像生成サービス

レビュー改善点を対象に、Cloud Functionでアノテーション画像を生成する。
"""

import asyncio
from typing import List

import aiohttp
import google.auth.transport.requests
import google.oauth2.id_token
import structlog

from src.config import settings
from src.models.feedback import DessinAnalysis
from src.models.rank import UserRank

logger = structlog.get_logger()


class AnnotationGenerationError(Exception):
    """アノテーション生成エラー"""


class AnnotationService:
    """アノテーション画像生成サービス（Cloud Function クライアント）"""

    def __init__(self) -> None:
        self.function_url = settings.annotation_function_url

    async def generate_annotated_image(
        self,
        task_id: str,
        original_image_url: str,
        analysis: DessinAnalysis,
        user_rank: UserRank,
        motif_tags: List[str],
    ) -> str | None:
        """アノテーション画像生成リクエストを送信し、結果を待って返す

        Args:
            task_id: タスクID
            original_image_url: 元画像のURL
            analysis: デッサン分析結果
            user_rank: ユーザーランク情報
            motif_tags: モチーフタグ
            
        Returns:
            アノテーション画像のURL（生成失敗時はNone）
        """
        if not self.function_url:
            logger.warning("annotation_generation_disabled_no_url")
            return None

        try:
            payload = {
                "task_id": task_id,
                "user_id": user_rank.user_id,
                "original_image_url": original_image_url,
                "analysis": analysis.model_dump(),
                "current_rank_label": user_rank.current_rank.label,
                "motif_tags": motif_tags,
            }

            # Cloud Functions Gen2の場合、.run.appのURLをtarget_audienceとして使用
            target_audience = self._convert_to_run_app_url(self.function_url)
            auth_req = google.auth.transport.requests.Request()
            id_token = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: google.oauth2.id_token.fetch_id_token(auth_req, target_audience),
            )

            headers = {
                "Authorization": f"Bearer {id_token}",
                "Content-Type": "application/json",
            }

            # タイムアウトを300秒（5分）に延長（アノテーション生成には時間がかかる場合がある）
            timeout = aiohttp.ClientTimeout(total=300)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    self.function_url,
                    json=payload,
                    headers=headers,
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            "annotation_generation_failed",
                            task_id=task_id,
                            status=response.status,
                            error=error_text,
                        )
                        return None
                    
                    # レスポンスからannotated_image_urlを取得
                    result = await response.json()
                    annotated_image_url = result.get("annotated_image_url")
                    
                    if annotated_image_url:
                        logger.info(
                            "annotation_generation_completed",
                            task_id=task_id,
                            annotated_image_url=annotated_image_url,
                        )
                        return annotated_image_url
                    else:
                        logger.warning(
                            "annotation_generation_no_url_in_response",
                            task_id=task_id,
                            response=result,
                        )
                        return None

        except Exception as e:
            logger.error(
                "annotation_generation_request_failed",
                task_id=task_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            # エラーが発生しても処理を続行できるようにNoneを返す
            return None

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
            logger.warning(
                "converting_cloudfunctions_url_to_run_app",
                original_url=url,
                note="Consider using .run.app URL directly in environment variable"
            )
            # 簡易変換（正確ではない可能性がある）
            return url.replace(".cloudfunctions.net", ".a.run.app")
        return url


_annotation_service: AnnotationService | None = None


def get_annotation_service() -> AnnotationService:
    """AnnotationServiceのシングルトンインスタンスを取得"""
    global _annotation_service
    if _annotation_service is None:
        _annotation_service = AnnotationService()
    return _annotation_service
