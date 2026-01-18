"""フィードバックモデル定義"""

from pydantic import BaseModel, Field


class ProportionAnalysis(BaseModel):
    """プロポーション分析

    形の正確さ、比率・バランス、輪郭線の質を評価。
    """

    shape_accuracy: str = Field(..., description="形の正確さの評価")
    ratio_balance: str = Field(..., description="比率・バランスの評価")
    contour_quality: str = Field(..., description="輪郭線の質の評価")
    score: float = Field(..., ge=0, le=100, description="スコア (0-100)")


class ToneAnalysis(BaseModel):
    """陰影（トーン）分析

    明暗の階調、光源の一貫性、立体感を評価。
    """

    value_range: str = Field(..., description="明暗の階調の評価")
    light_consistency: str = Field(..., description="光源の一貫性の評価")
    three_dimensionality: str = Field(..., description="立体感の評価")
    score: float = Field(..., ge=0, le=100, description="スコア (0-100)")


class TextureAnalysis(BaseModel):
    """質感表現分析

    素材感、タッチの使い分けを評価。
    """

    material_expression: str = Field(..., description="素材感の評価")
    touch_variety: str = Field(..., description="タッチの使い分けの評価")
    score: float = Field(..., ge=0, le=100, description="スコア (0-100)")


class LineQualityAnalysis(BaseModel):
    """線の質分析

    運筆、筆圧コントロール、ハッチング技法を評価。
    """

    stroke_quality: str = Field(..., description="運筆の評価")
    pressure_control: str = Field(..., description="筆圧コントロールの評価")
    hatching: str = Field(..., description="ハッチング技法の評価")
    score: float = Field(..., ge=0, le=100, description="スコア (0-100)")


class DessinAnalysis(BaseModel):
    """デッサン総合分析

    プロポーション、陰影、質感、線の質の総合評価。
    """

    proportion: ProportionAnalysis = Field(..., description="プロポーション分析")
    tone: ToneAnalysis = Field(..., description="陰影分析")
    texture: TextureAnalysis = Field(..., description="質感分析")
    line_quality: LineQualityAnalysis = Field(..., description="線の質分析")
    overall_score: float = Field(..., ge=0, le=100, description="総合スコア (0-100)")
    strengths: list[str] = Field(..., description="強み・良い点")
    improvements: list[str] = Field(..., description="改善点")
    tags: list[str] = Field(..., description="モチーフタグ（例: りんご、球体、静物）")


class FeedbackResponse(BaseModel):
    """フィードバックレスポンス

    ユーザーに返すフィードバックの構造化データ。
    """

    analysis: DessinAnalysis = Field(..., description="デッサン分析結果")
    summary: str = Field(..., description="フィードバックの要約文")
    detailed_feedback: str = Field(..., description="詳細なフィードバック（Markdown形式）")
