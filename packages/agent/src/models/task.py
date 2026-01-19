"""タスクモデル定義"""

from datetime import datetime
from enum import Enum
from urllib.parse import unquote, urlparse

from pydantic import BaseModel, Field, field_validator

# 許可するホスト名（完全一致）
_ALLOWED_HOSTNAMES = [
    "storage.googleapis.com",
    "storage.cloud.google.com",
]


class TaskStatus(str, Enum):
    """タスクステータス"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewTask(BaseModel):
    """審査タスク

    デッサン画像の審査タスクを表すモデル。
    """

    task_id: str = Field(..., description="タスクID", min_length=1, max_length=100)
    user_id: str = Field(..., description="ユーザーID", min_length=1, max_length=100)
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="タスクステータス")
    image_url: str = Field(..., description="元画像のURL（Cloud Storage/CDNのみ）")
    example_image_url: str | None = Field(
        default=None, description="お手本画像のURL（Cloud Storage/CDNのみ）"
    )
    feedback: dict[str, object] | None = Field(default=None, description="フィードバックデータ")
    score: float | None = Field(default=None, ge=0, le=100, description="総合スコア (0-100)")
    tags: list[str] | None = Field(default=None, description="モチーフタグ")
    error_message: str | None = Field(
        default=None, description="エラー時のメッセージ", max_length=1000
    )
    created_at: datetime = Field(default_factory=datetime.now, description="作成日時")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新日時")

    @field_validator("image_url", "example_image_url", mode="before")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """URLのホスト名が許可リストに含まれるか検証（完全一致）"""
        if v is None:
            return None

        # URLデコードして正規化
        normalized = unquote(v)
        parsed = urlparse(normalized)

        # gs:// スキームはバケット名を検証
        if parsed.scheme == "gs":
            # DetailedバリデーションはvalidationモジュールでI行うため、ここでは基本チェックのみ
            bucket_name = parsed.netloc
            if not bucket_name:
                raise ValueError("GCSバケット名が指定されていません")
            return normalized

        # httpsのみ許可
        if parsed.scheme != "https":
            raise ValueError(f"HTTPSのみ許可されています: {parsed.scheme}")

        # ホスト名の完全一致を確認
        hostname = parsed.hostname
        if hostname not in _ALLOWED_HOSTNAMES:
            raise ValueError(
                f"許可されていないホストです: {hostname}。"
                "Cloud StorageまたはCDN URLのみ使用可能です"
            )

        return normalized

    class Config:
        use_enum_values = True


class CreateReviewRequest(BaseModel):
    """審査リクエスト作成用モデル

    user_idは認証から取得するためリクエストには含めない。
    """

    image_url: str = Field(..., description="元画像のURL（Cloud Storage/CDNのみ）")
    example_image_url: str | None = Field(
        default=None, description="お手本画像のURL（Cloud Storage/CDNのみ）"
    )

    @field_validator("image_url", "example_image_url", mode="before")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        """URLのホスト名が許可リストに含まれるか検証（完全一致）"""
        if v is None:
            return None

        # URLデコードして正規化
        normalized = unquote(v)
        parsed = urlparse(normalized)

        # gs:// スキームはバケット名を検証
        if parsed.scheme == "gs":
            bucket_name = parsed.netloc
            if not bucket_name:
                raise ValueError("GCSバケット名が指定されていません")
            return normalized

        # httpsのみ許可
        if parsed.scheme != "https":
            raise ValueError(f"HTTPSのみ許可されています: {parsed.scheme}")

        # ホスト名の完全一致を確認
        hostname = parsed.hostname
        if hostname not in _ALLOWED_HOSTNAMES:
            raise ValueError(
                f"許可されていないホストです: {hostname}。"
                "Cloud StorageまたはCDN URLのみ使用可能です"
            )

        return normalized


class ReviewTaskResponse(BaseModel):
    """審査タスクレスポンス用モデル

    APIレスポンス用にdatetimeをISO文字列に変換。
    """

    task_id: str = Field(..., description="タスクID")
    user_id: str = Field(..., description="ユーザーID")
    status: str = Field(..., description="タスクステータス")
    image_url: str = Field(..., description="元画像のURL")
    example_image_url: str | None = Field(default=None, description="お手本画像のURL")
    feedback: dict[str, object] | None = Field(default=None, description="フィードバックデータ")
    score: float | None = Field(default=None, description="総合スコア")
    tags: list[str] | None = Field(default=None, description="モチーフタグ")
    error_message: str | None = Field(default=None, description="エラー時のメッセージ")
    created_at: str = Field(..., description="作成日時（ISO 8601形式）")
    updated_at: str = Field(..., description="更新日時（ISO 8601形式）")

    @classmethod
    def from_task(cls, task: "ReviewTask") -> "ReviewTaskResponse":
        """ReviewTaskからレスポンスモデルを生成"""
        status_value = task.status.value if isinstance(task.status, TaskStatus) else task.status
        return cls(
            task_id=task.task_id,
            user_id=task.user_id,
            status=str(status_value),
            image_url=task.image_url,
            example_image_url=task.example_image_url,
            feedback=task.feedback,
            score=task.score,
            tags=task.tags,
            error_message=task.error_message,
            created_at=task.created_at.isoformat(),
            updated_at=task.updated_at.isoformat(),
        )


class ReviewListResponse(BaseModel):
    """審査タスク一覧レスポンス用モデル"""

    tasks: list[ReviewTaskResponse] = Field(..., description="タスク一覧")
    total_count: int = Field(..., description="総件数")
