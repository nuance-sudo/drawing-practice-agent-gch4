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

        # gs:// スキームは許可
        if parsed.scheme == "gs":
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
