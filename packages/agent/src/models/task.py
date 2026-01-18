"""タスクモデル定義"""

import re
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# 許可するCloud Storageバケットパターン
_ALLOWED_URL_PATTERNS = [
    r"^https://storage\.googleapis\.com/.+$",
    r"^https://storage\.cloud\.google\.com/.+$",
    r"^gs://.+$",
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
        """URLがCloud Storage/CDNパターンに一致するか検証"""
        if v is None:
            return None

        # 許可されたパターンかチェック
        for pattern in _ALLOWED_URL_PATTERNS:
            if re.match(pattern, v):
                return v

        raise ValueError("許可されていないURLです。Cloud StorageまたはCDN URLのみ使用可能です")

    class Config:
        use_enum_values = True
