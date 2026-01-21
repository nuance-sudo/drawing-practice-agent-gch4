"""ランクモデル定義"""

from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field


class Rank(str, Enum):
    """デッサンスキルランク"""
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"
    DIAMOND = "Diamond"


class RankRange(BaseModel):
    """ランクごとのスコア範囲定義"""
    rank: Rank
    min_score: int
    max_score: int


# ランク定義
# Bronze: 0-30
# Silver: 31-50
# Gold: 51-70
# Platinum: 71-85
# Diamond: 86-100
RANK_RANGES = [
    RankRange(rank=Rank.BRONZE, min_score=0, max_score=30),
    RankRange(rank=Rank.SILVER, min_score=31, max_score=50),
    RankRange(rank=Rank.GOLD, min_score=51, max_score=70),
    RankRange(rank=Rank.PLATINUM, min_score=71, max_score=85),
    RankRange(rank=Rank.DIAMOND, min_score=86, max_score=100),
]


class UserRank(BaseModel):
    """ユーザーの現在のランク情報"""
    user_id: str = Field(..., description="ユーザーID")
    current_rank: Rank = Field(..., description="現在のランク")
    current_score: float = Field(..., description="現在のスコア（最新のデッサン総合スコア）")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新日時")


class RankHistory(BaseModel):
    """ランク変動履歴"""
    user_id: str = Field(..., description="ユーザーID")
    old_rank: Rank | None = Field(None, description="変更前のランク")
    new_rank: Rank = Field(..., description="変更後のランク")
    score: float = Field(..., description="ランク変更時のスコア")
    changed_at: datetime = Field(default_factory=datetime.now, description="変更日時")
    task_id: str | None = Field(None, description="トリガーとなったタスクID")
