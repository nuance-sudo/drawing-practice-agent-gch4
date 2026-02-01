"""フィードバック・ランクモデル定義"""

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
            return f"{self.value - 10}段"
        elif self.value == 14:
            return "師範代"
        else:
            return "師範"


class ProportionAnalysis(BaseModel):
    """プロポーション分析"""
    shape_accuracy: str = Field(..., description="形の正確さの評価")
    ratio_balance: str = Field(..., description="比率・バランスの評価")
    contour_quality: str = Field(..., description="輪郭線の質の評価")
    score: float = Field(..., ge=0, le=100, description="スコア (0-100)")


class ToneAnalysis(BaseModel):
    """陰影（トーン）分析"""
    value_range: str = Field(..., description="明暗の階調の評価")
    light_consistency: str = Field(..., description="光源の一貫性の評価")
    three_dimensionality: str = Field(..., description="立体感の評価")
    score: float = Field(..., ge=0, le=100, description="スコア (0-100)")


class TextureAnalysis(BaseModel):
    """質感表現分析"""
    material_expression: str = Field(..., description="素材感の評価")
    touch_variety: str = Field(..., description="タッチの使い分けの評価")
    score: float = Field(..., ge=0, le=100, description="スコア (0-100)")


class LineQualityAnalysis(BaseModel):
    """線の質分析"""
    stroke_quality: str = Field(..., description="運筆の評価")
    pressure_control: str = Field(..., description="筆圧コントロールの評価")
    hatching: str = Field(..., description="ハッチング技法の評価")
    score: float = Field(..., ge=0, le=100, description="スコア (0-100)")


class DessinAnalysis(BaseModel):
    """デッサン総合分析"""
    proportion: ProportionAnalysis = Field(..., description="プロポーション分析")
    tone: ToneAnalysis = Field(..., description="陰影分析")
    texture: TextureAnalysis = Field(..., description="質感分析")
    line_quality: LineQualityAnalysis = Field(..., description="線の質分析")
    overall_score: float = Field(..., ge=0, le=100, description="総合スコア (0-100)")
    strengths: list[str] = Field(..., description="強み・良い点")
    improvements: list[str] = Field(..., description="改善点")
    tags: list[str] = Field(..., description="モチーフタグ（例: りんご、球体、静物）")
