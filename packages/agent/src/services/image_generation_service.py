"""お手本画像生成サービス

ユーザーのデッサン分析結果に基づいて、Cloud Run Functionを呼び出し
お手本画像の生成を依頼する。
"""

import asyncio

import aiohttp
import google.auth.transport.requests
import google.oauth2.id_token
import structlog

from src.config import settings
from src.models.feedback import DessinAnalysis

logger = structlog.get_logger()


class ImageGenerationError(Exception):
    """画像生成エラー"""
    pass


class ImageGenerationService:
    """お手本画像生成サービス（Cloud Function クライアント）"""

    # リトライ設定
    MAX_RETRIES = 3

    def __init__(self) -> None:
        """初期化"""
        self.function_url = settings.image_generation_function_url

    async def generate_example_image(
        self,
        task_id: str,
        user_id: str,
        original_image_url: str,
        analysis: DessinAnalysis,
        motif_tags: list[str],
        annotated_image_url: str | None = None,
    ) -> None:
        """お手本画像生成リクエストを送信する（非同期）

        最大3回リトライ（指数バックオフ: 2秒, 4秒, 8秒）を行い、
        全て失敗した場合はImageGenerationErrorを送出する。

        Args:
            task_id: タスクID
            user_id: ユーザーID
            original_image_url: 元画像のURL
            analysis: デッサン分析結果
            motif_tags: モチーフタグ
            annotated_image_url: アノテーション画像のURL（オプション）

        Raises:
            ImageGenerationError: 全リトライ失敗時
        """
        if not self.function_url:
            logger.warning("image_generation_disabled_no_url")
            return

        # リクエストペイロード作成
        payload: dict[str, object] = {
            "task_id": task_id,
            "user_id": user_id,
            "original_image_url": original_image_url,
            "analysis": analysis.model_dump(),
            "motif_tags": motif_tags,
        }

        # アノテーション画像URLがあれば追加
        if annotated_image_url:
            payload["annotated_image_url"] = annotated_image_url

        last_error: ImageGenerationError | None = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                await self._call_generation_function(task_id, user_id, payload)
                return  # 成功
            except ImageGenerationError as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    wait_time = 2 ** attempt
                    logger.warning(
                        "image_generation_retry",
                        task_id=task_id,
                        attempt=attempt,
                        max_retries=self.MAX_RETRIES,
                        wait_seconds=wait_time,
                        error=str(e),
                    )
                    await asyncio.sleep(wait_time)

        logger.error(
            "image_generation_all_retries_failed",
            task_id=task_id,
            max_retries=self.MAX_RETRIES,
        )
        raise last_error or ImageGenerationError(
            f"Failed after {self.MAX_RETRIES} attempts"
        )

    async def _call_generation_function(
        self,
        task_id: str,
        user_id: str,
        payload: dict[str, object],
    ) -> None:
        """Cloud Functionを呼び出してお手本画像生成を依頼（1回の試行）

        Args:
            task_id: タスクID
            user_id: ユーザーID
            payload: リクエストペイロード

        Raises:
            ImageGenerationError: リクエスト送信に失敗した場合
        """
        try:
            logger.info(
                "image_generation_request_started",
                task_id=task_id,
                user_id=user_id,
                function_url=self.function_url,
            )

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

            async with aiohttp.ClientSession() as session, session.post(
                self.function_url,
                json=payload,
                headers=headers,
                timeout=300  # Cloud Functionの処理に時間がかかる場合がある（5分）
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

        except ImageGenerationError:
            raise
        except Exception as e:
            logger.error(
                "image_generation_request_failed",
                task_id=task_id,
                error=str(e),
                error_type=type(e).__name__
            )
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


# シングルトンインスタンス
_image_generation_service: ImageGenerationService | None = None


def get_image_generation_service() -> ImageGenerationService:
    """ImageGenerationServiceのシングルトンインスタンスを取得"""
    global _image_generation_service
    if _image_generation_service is None:
        _image_generation_service = ImageGenerationService()
    return _image_generation_service
