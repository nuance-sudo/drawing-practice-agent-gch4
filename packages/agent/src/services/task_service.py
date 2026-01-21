"""タスク管理サービス

Firestoreを使ったタスクのCRUD操作を提供する。
"""

import uuid
from collections.abc import Sequence
from datetime import datetime

import structlog
from google.cloud import firestore

from src.config import settings
from src.exceptions import TaskNotFoundError
from src.models.task import ReviewTask, TaskStatus

logger = structlog.get_logger()


class TaskService:
    """タスク管理サービス

    Firestoreを使用してReviewTaskのCRUD操作を行う。
    """

    COLLECTION_NAME = "review_tasks"

    def __init__(self, db: firestore.Client | None = None) -> None:
        """初期化

        Args:
            db: Firestoreクライアント（テスト用にDI可能）
        """
        if db is None:
            self._db = firestore.Client(
                project=settings.gcp_project_id,
                database=settings.firestore_database,
            )
        else:
            self._db = db
        self._collection = self._db.collection(self.COLLECTION_NAME)

    def create_task(
        self,
        user_id: str,
        image_url: str,
        example_image_url: str | None = None,
    ) -> ReviewTask:
        """新規タスクを作成

        Args:
            user_id: ユーザーID
            image_url: 元画像のURL
            example_image_url: お手本画像のURL（オプション）

        Returns:
            作成されたReviewTask
        """
        task_id = str(uuid.uuid4())
        now = datetime.now()

        task = ReviewTask(
            task_id=task_id,
            user_id=user_id,
            status=TaskStatus.PENDING,
            image_url=image_url,
            example_image_url=example_image_url,
            created_at=now,
            updated_at=now,
        )

        # Firestoreに保存
        doc_ref = self._collection.document(task_id)
        doc_ref.set(self._task_to_dict(task))

        logger.info(
            "task_created",
            task_id=task_id,
            user_id=user_id,
        )

        return task

    def get_task(self, task_id: str) -> ReviewTask | None:
        """タスクを取得

        Args:
            task_id: タスクID

        Returns:
            ReviewTask または None
        """
        doc_ref = self._collection.document(task_id)
        doc = doc_ref.get()

        if not doc.exists:
            return None

        return self._dict_to_task(doc.to_dict())

    def list_tasks(
        self,
        user_id: str,
        limit: int = 20,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        status: str | None = None,
        tag: str | None = None,
    ) -> list[ReviewTask]:
        """ユーザーのタスク一覧を取得

        Args:
            user_id: ユーザーID
            limit: 取得件数の上限
            start_date: 検索開始日時
            end_date: 検索終了日時
            status: ステータスフィルタ
            tag: タグフィルタ

        Returns:
            ReviewTaskのリスト
        """
        query = self._collection.where("user_id", "==", user_id)

        if status:
            query = query.where("status", "==", status)
        
        if tag:
            query = query.where("tags", "array_contains", tag)
            
        if start_date:
            query = query.where("created_at", ">=", start_date)
            
        if end_date:
            query = query.where("created_at", "<=", end_date)

        query = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)

        docs: Sequence[firestore.DocumentSnapshot] = query.stream()
        tasks: list[ReviewTask] = []

        for doc in docs:
            doc_dict = doc.to_dict()
            if doc_dict is not None:
                tasks.append(self._dict_to_task(doc_dict))

        return tasks

    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        feedback: dict[str, object] | None = None,
        score: float | None = None,
        tags: list[str] | None = None,
        error_message: str | None = None,
    ) -> ReviewTask:
        """タスクステータスを更新

        Args:
            task_id: タスクID
            status: 新しいステータス
            feedback: フィードバックデータ
            score: 総合スコア
            tags: モチーフタグ
            error_message: エラーメッセージ

        Returns:
            更新されたReviewTask

        Raises:
            TaskNotFoundError: タスクが見つからない場合
        """
        doc_ref = self._collection.document(task_id)
        doc = doc_ref.get()

        if not doc.exists:
            raise TaskNotFoundError(f"Task not found: {task_id}")

        now = datetime.now()
        update_data: dict[str, object] = {
            "status": status.value,
            "updated_at": now,
        }

        if feedback is not None:
            update_data["feedback"] = feedback
        if score is not None:
            update_data["score"] = score
        if tags is not None:
            update_data["tags"] = tags
        if error_message is not None:
            update_data["error_message"] = error_message

        doc_ref.update(update_data)

        logger.info(
            "task_updated",
            task_id=task_id,
            status=status.value,
        )

        # 更新後のタスクを取得して返す
        updated_doc = doc_ref.get()
        updated_dict = updated_doc.to_dict()
        if updated_dict is None:
            raise TaskNotFoundError(f"Task not found after update: {task_id}")

        return self._dict_to_task(updated_dict)

    def delete_task(self, task_id: str) -> bool:
        """タスクを削除

        Args:
            task_id: タスクID

        Returns:
            削除成功した場合True
        """
        doc_ref = self._collection.document(task_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        doc_ref.delete()

        logger.info(
            "task_deleted",
            task_id=task_id,
        )

        return True

    def _task_to_dict(self, task: ReviewTask) -> dict[str, object]:
        """ReviewTaskをFirestore用のdictに変換"""
        return {
            "task_id": task.task_id,
            "user_id": task.user_id,
            "status": task.status.value if isinstance(task.status, TaskStatus) else task.status,
            "image_url": task.image_url,
            "example_image_url": task.example_image_url,
            "feedback": task.feedback,
            "score": task.score,
            "tags": task.tags,
            "error_message": task.error_message,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }

    def _dict_to_task(self, data: dict[str, object]) -> ReviewTask:
        """Firestoreのdictからt ReviewTaskに変換"""
        # Firestoreのタイムスタンプをdatetimeに変換
        created_at = data.get("created_at")
        updated_at = data.get("updated_at")

        if hasattr(created_at, "timestamp"):
            created_at = datetime.fromtimestamp(created_at.timestamp())
        if hasattr(updated_at, "timestamp"):
            updated_at = datetime.fromtimestamp(updated_at.timestamp())

        # status の型を処理
        status_value = data.get("status", TaskStatus.PENDING.value)
        if isinstance(status_value, TaskStatus):
            status = status_value
        else:
            status = TaskStatus(str(status_value))

        # tags と feedback の型を処理
        tags_value = data.get("tags")
        tags: list[str] | None = None
        if tags_value is not None and isinstance(tags_value, list):
            tags = [str(t) for t in tags_value]

        feedback_value = data.get("feedback")
        feedback: dict[str, object] | None = None
        if isinstance(feedback_value, dict):
            feedback = feedback_value

        # example_image_urlの型処理
        example_url_value = data.get("example_image_url")
        example_image_url: str | None = None
        if example_url_value is not None:
            example_image_url = str(example_url_value)

        # scoreの型処理
        score_value = data.get("score")
        score: float | None = None
        if score_value is not None:
            score = float(str(score_value))

        # error_messageの型処理
        error_message_value = data.get("error_message")
        error_message: str | None = None
        if error_message_value is not None:
            error_message = str(error_message_value)

        return ReviewTask(
            task_id=str(data.get("task_id", "")),
            user_id=str(data.get("user_id", "")),
            status=status,
            image_url=str(data.get("image_url", "")),
            example_image_url=example_image_url,
            feedback=feedback,
            score=score,
            tags=tags,
            error_message=error_message,
            created_at=created_at if isinstance(created_at, datetime) else datetime.now(),
            updated_at=updated_at if isinstance(updated_at, datetime) else datetime.now(),
        )


    def generate_upload_url(self, content_type: str) -> dict[str, str]:
        """GCSへのアップロード用署名付きURLを生成

        Args:
            content_type: アップロードするファイルのContent-Type (image/jpeg or image/png)

        Returns:
            dict: {
                "upload_url": 署名付きURL,
                "public_url": アップロード後の公開URL
            }
        """
        import datetime
        from google.cloud import storage
        import google.auth
        from google.auth.transport import requests
        from google.auth import compute_engine

        # Content-Typeに基づいた拡張子の決定
        ext = ".jpg" if content_type == "image/jpeg" else ".png"
        filename = f"{uuid.uuid4()}{ext}"
        blob_name = f"uploads/{filename}"

        # GCSクライアントの初期化
        storage_client = storage.Client(project=settings.gcp_project_id)
        bucket = storage_client.bucket(settings.gcs_bucket_name)
        blob = bucket.blob(blob_name)

        # Cloud Run環境用: IAM Credentials APIを使用した署名
        # デフォルトのサービスアカウント認証情報を取得
        credentials, project = google.auth.default()
        
        # 認証情報がコンピュート認証の場合、署名用認証情報に変換
        if isinstance(credentials, compute_engine.Credentials):
            # サービスアカウントのメールアドレスを取得
            auth_request = requests.Request()
            credentials.refresh(auth_request)
            service_account_email = credentials.service_account_email
            
            # 署名用認証情報を作成
            signing_credentials = compute_engine.IDTokenCredentials(
                auth_request,
                target_audience="",
                service_account_email=service_account_email,
            )
            # 署名付きURLの生成（IAMを使用）
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=15),
                method="PUT",
                content_type=content_type,
                service_account_email=service_account_email,
                access_token=credentials.token,
            )
        else:
            # ローカル環境など：直接署名
            url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=15),
                method="PUT",
                content_type=content_type,
            )

        # 公開URLの生成 (CDN経由を想定するか、直接GCS参照か)
        # CDN Base URLが設定されていればそれを使用、なければGCSの公開URL
        if settings.cdn_base_url:
            public_url = f"{settings.cdn_base_url}/{blob_name}"
        else:
            public_url = f"https://storage.googleapis.com/{settings.gcs_bucket_name}/{blob_name}"

        return {
            "upload_url": url,
            "public_url": public_url,
        }


# シングルトンインスタンス
_task_service: TaskService | None = None


def get_task_service() -> TaskService:
    """TaskServiceのシングルトンインスタンスを取得"""
    global _task_service
    if _task_service is None:
        _task_service = TaskService()
    return _task_service
