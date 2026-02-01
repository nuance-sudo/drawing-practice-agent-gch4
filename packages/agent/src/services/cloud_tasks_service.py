"""Cloud Tasksサービス

Cloud Tasksへのタスク投入を行うサービス。
"""

from datetime import datetime
from functools import lru_cache

import structlog
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2
from pydantic import BaseModel

from src.config import get_settings

logger = structlog.get_logger()


class ReviewTaskPayload(BaseModel):
    """審査タスクのペイロード"""
    task_id: str
    user_id: str
    image_url: str


class CloudTasksService:
    """Cloud Tasksサービス

    審査処理タスクをCloud Tasksキューに投入する。
    """

    def __init__(self) -> None:
        """Cloud Tasksサービスを初期化"""
        self._client: tasks_v2.CloudTasksClient | None = None
        settings = get_settings()
        self._project_id = settings.gcp_project_id
        self._location = settings.cloud_tasks_location
        self._queue_name = settings.cloud_tasks_queue_name
        self._process_review_function_url = settings.process_review_function_url

    def _get_client(self) -> tasks_v2.CloudTasksClient:
        """Cloud Tasksクライアントを取得（遅延初期化）"""
        if self._client is None:
            self._client = tasks_v2.CloudTasksClient()
        return self._client

    def _get_queue_path(self) -> str:
        """キューのフルパスを取得"""
        return self._get_client().queue_path(
            self._project_id,
            self._location,
            self._queue_name,
        )

    def create_review_task(
        self,
        task_id: str,
        user_id: str,
        image_url: str,
        schedule_time: datetime | None = None,
    ) -> str:
        """審査タスクをCloud Tasksに投入

        Args:
            task_id: タスクID
            user_id: ユーザーID
            image_url: 分析対象の画像URL
            schedule_time: スケジュール実行時間（Noneの場合は即時実行）

        Returns:
            str: 作成されたCloud TaskのID

        Raises:
            Exception: タスク作成に失敗した場合
        """
        client = self._get_client()
        queue_path = self._get_queue_path()

        # ペイロード作成
        payload = ReviewTaskPayload(
            task_id=task_id,
            user_id=user_id,
            image_url=image_url,
        )
        payload_bytes = payload.model_dump_json().encode("utf-8")

        # タスク作成
        task_request: dict[str, object] = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": self._process_review_function_url,
                "headers": {
                    "Content-Type": "application/json",
                },
                "body": payload_bytes,
                # OIDCトークンを使用（Cloud Run/Cloud Functions向け）
                "oidc_token": {
                    "service_account_email": f"{self._project_id}@appspot.gserviceaccount.com",
                    "audience": self._process_review_function_url,
                },
            },
            # タスク名を指定（重複防止）
            "name": f"{queue_path}/tasks/review-{task_id}",
        }

        # スケジュール時間が指定されている場合
        if schedule_time:
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(schedule_time)
            task_request["schedule_time"] = timestamp

        # タスク作成リクエスト
        request = tasks_v2.CreateTaskRequest(
            parent=queue_path,
            task=task_request,
        )

        try:
            response = client.create_task(request=request)

            # Cloud TaskのIDを抽出（パスから）
            cloud_task_id = response.name.split("/")[-1] if response.name else ""

            logger.info(
                "cloud_task_created",
                task_id=task_id,
                cloud_task_id=cloud_task_id,
                queue=self._queue_name,
            )

            return cloud_task_id

        except Exception as e:
            logger.error(
                "cloud_task_creation_failed",
                task_id=task_id,
                error=str(e),
            )
            raise

    def delete_review_task(self, task_id: str) -> bool:
        """審査タスクを削除（キャンセル）

        Args:
            task_id: タスクID

        Returns:
            bool: 削除に成功した場合True
        """
        client = self._get_client()
        queue_path = self._get_queue_path()
        task_path = f"{queue_path}/tasks/review-{task_id}"

        try:
            client.delete_task(name=task_path)
            logger.info("cloud_task_deleted", task_id=task_id)
            return True
        except Exception as e:
            logger.warning(
                "cloud_task_deletion_failed",
                task_id=task_id,
                error=str(e),
            )
            return False


@lru_cache
def get_cloud_tasks_service() -> CloudTasksService:
    """CloudTasksServiceのシングルトンインスタンスを取得"""
    return CloudTasksService()
