"""タスクモデル定義"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


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

    task_id: str = Field(..., description="タスクID")
    user_id: str = Field(..., description="ユーザーID")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="タスクステータス")
    image_url: str = Field(..., description="元画像のURL")
    example_image_url: str | None = Field(default=None, description="お手本画像のURL")
    feedback: dict[str, object] | None = Field(default=None, description="フィードバックデータ")
    score: float | None = Field(default=None, ge=0, le=100, description="総合スコア (0-100)")
    tags: list[str] | None = Field(default=None, description="モチーフタグ")
    error_message: str | None = Field(default=None, description="エラー時のメッセージ")
    created_at: datetime = Field(default_factory=datetime.now, description="作成日時")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新日時")

    class Config:
        use_enum_values = True
