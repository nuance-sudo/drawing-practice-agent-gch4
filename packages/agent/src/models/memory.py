"""メモリ関連モデル定義

Memory Bankに保存するスキル進捗と成長フィードバックのデータモデル。
"""

from pydantic import BaseModel, Field


class SkillProgression(BaseModel):
    """スキル進捗トラッキング

    各スキルカテゴリの進捗状況を追跡する。
    """

    category: str = Field(..., description="スキルカテゴリ（proportion, tone, texture, line_quality）")
    average_score: float = Field(..., ge=0, le=100, description="平均スコア")
    latest_score: float = Field(..., ge=0, le=100, description="最新スコア")
    trend: str = Field(..., description="傾向（improving, stable, declining）")
    submission_count: int = Field(..., ge=0, description="提出回数")


class GrowthFeedback(BaseModel):
    """成長フィードバック

    過去の提出と比較した成長レポート。
    """

    improvements: list[str] = Field(default_factory=list, description="改善された点")
    maintained_strengths: list[str] = Field(default_factory=list, description="維持している強み")
    ongoing_challenges: list[str] = Field(default_factory=list, description="継続的な課題")
    skill_progressions: list[SkillProgression] = Field(
        default_factory=list, description="スキル進捗リスト"
    )
    comparison_summary: str = Field(default="", description="比較サマリー")


class MemoryContext(BaseModel):
    """メモリコンテキスト

    エージェントに渡す過去のメモリ情報。
    """

    has_previous_submissions: bool = Field(
        default=False, description="過去の提出があるか"
    )
    submission_count: int = Field(default=0, description="過去の提出回数")
    skill_progressions: list[SkillProgression] = Field(
        default_factory=list, description="スキル進捗リスト"
    )
    recent_feedback_summary: str = Field(default="", description="直近のフィードバック要約")
