"""ランクモデル定義"""

from datetime import datetime
from enum import IntEnum

from pydantic import BaseModel, Field


class Rank(IntEnum):
    """デッサンスキルランク (1-15)"""
    KYU_10 = 1
    KYU_9 = 2
    KYU_8 = 3
    KYU_7 = 4
    KYU_6 = 5
    KYU_5 = 6
    KYU_4 = 7
    KYU_3 = 8
    KYU_2 = 9
    KYU_1 = 10
    DAN_1 = 11
    DAN_2 = 12
    DAN_3 = 13
    SHIHAN_DAI = 14
    SHIHAN = 15

    @property
    def label(self) -> str:
        """表示用ラベル"""
        if self.value <= 10:
            return f"{11 - self.value}級"
        elif self.value <= 13:
            return f"{self.value - 10}段" # Rank.DAN_1 is 11, so 11-10=1段
        elif self.value == 14:
            return "師範代"
        else:
            return "師範"




class UserRank(BaseModel):
    """ユーザーの現在のランク情報"""
    user_id: str = Field(..., description="ユーザーID")
    current_rank: Rank = Field(..., description="現在のランク")
    current_score: float = Field(..., description="現在のスコア（最新のデッサン総合スコア）")
    total_submissions: int = Field(0, description="総提出回数")
    high_scores: list[float] = Field(default_factory=list, description="80点以上のスコア履歴")
    rank_changed: bool = Field(False, description="今回ランクが変動したか（昇格した場合True）")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新日時")


class RankHistory(BaseModel):
    """ランク変動履歴"""
    user_id: str = Field(..., description="ユーザーID")
    old_rank: Rank | None = Field(None, description="変更前のランク")
    new_rank: Rank = Field(..., description="変更後のランク")
    score: float = Field(..., description="ランク変更時のスコア")
    changed_at: datetime = Field(default_factory=datetime.now, description="変更日時")
    task_id: str | None = Field(None, description="トリガーとなったタスクID")
