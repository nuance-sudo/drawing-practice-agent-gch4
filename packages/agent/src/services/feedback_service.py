"""フィードバック生成サービス

分析結果とユーザーランクに基づいて、構造化されたフィードバック（Markdown）を生成する。
"""

import structlog
from typing import List

from src.models.feedback import DessinAnalysis, FeedbackResponse, ProportionAnalysis, ToneAnalysis, TextureAnalysis, LineQualityAnalysis
from src.models.rank import Rank

logger = structlog.get_logger()


class FeedbackService:
    """フィードバック生成サービス"""

    def generate_feedback(self, analysis: DessinAnalysis, rank: Rank) -> FeedbackResponse:
        """分析結果とランクからフィードバックを生成する

        Args:
            analysis: デッサン分析結果
            rank: ユーザーの現在のランク

        Returns:
            構造化されたフィードバックレスポンス
        """
        # 1. 要約の生成 (既存ロジックの再利用または強化)
        summary = self._create_summary(analysis)

        # 2. Markdown詳細フィードバックの生成 (ランクに応じたトーン＆アドバイス)
        detailed_feedback = self._generate_markdown(analysis, rank)

        return FeedbackResponse(
            analysis=analysis,  # 元の分析データも含める
            summary=summary,
            detailed_feedback=detailed_feedback,
        )

    def _create_summary(self, analysis: DessinAnalysis) -> str:
        """分析結果から簡潔な要約を作成"""
        score = analysis.overall_score
        # 主要な強みと改善点を1つずつピックアップ
        strength = analysis.strengths[0] if analysis.strengths else "全体的なバランス"
        improvement = analysis.improvements[0] if analysis.improvements else "特になし"
        
        return f"総合スコア: {score:.1f}/100 | 良い点: {strength} | 改善点: {improvement}"

    def _generate_markdown(self, analysis: DessinAnalysis, rank: Rank) -> str:
        """ランクに応じたMarkdownフィードバックを生成"""
        
        # ランクごとのメッセージテンプレート
        # ランクが高いほど専門的で厳しい視点、低いほど励ましと基礎重視
        # 10級-6級: 初級
        # 5級-1級: 中級
        # 初段-3段: 上級
        # 師範: 達人
        
        
        intro_message = "デッサン練習お疲れ様です！"

        md = []
        md.append(f"# デッサン分析レポート")
        md.append(f"**現在のランク**: {rank.label} | **総合スコア**: {analysis.overall_score:.1f}")
        md.append("")
        md.append(intro_message)
        md.append("")

        # 各評価項目
        md.append("## 📊 評価項目別分析")
        md.append(self._format_criterion("プロポーション", analysis.proportion, rank))
        md.append(self._format_criterion("明暗・陰影", analysis.tone, rank))
        md.append(self._format_criterion("質感・タッチ", analysis.texture, rank))
        md.append(self._format_criterion("線の質", analysis.line_quality, rank))
        
        # 総合アドバイス（強みと改善点）
        md.append("## 💡 総合アドバイス")
        
        if analysis.strengths:
            md.append("### 良い点")
            for strength in analysis.strengths:
                md.append(f"- {strength}")
        
        if analysis.improvements:
            md.append("### 改善ポイント")
            for improvement in analysis.improvements:
                md.append(f"- {improvement}")
        
        return "\n".join(md)

    def _format_criterion(self,
                          title: str,
                          metric: ProportionAnalysis | ToneAnalysis | TextureAnalysis | LineQualityAnalysis,
                          rank: Rank) -> str:
        """評価項目のMarkdownフォーマット"""
        
        # スコアに応じたアイコン
        score_icon = "🟢"
        if metric.score >= 80:
            score_icon = "🌟" # Excellent
        elif metric.score >= 60:
            score_icon = "🟢" # Good
        elif metric.score >= 40:
            score_icon = "🟡" # Average
        else:
            score_icon = "🔴" # Needs Improvement

        section = []
        section.append(f"### {title} {score_icon} ({metric.score:.1f}/100)")
        
        # 各フィールドの内容を表示（フィールド名はモデルによって異なるため動的に取得は難しいが、
        # ここでは既知のモデル構造を使って展開する）
        
        details = []
        if isinstance(metric, ProportionAnalysis):
            details.append(f"- **形の正確さ**: {metric.shape_accuracy}")
            details.append(f"- **比率・バランス**: {metric.ratio_balance}")
            details.append(f"- **輪郭線**: {metric.contour_quality}")
        elif isinstance(metric, ToneAnalysis):
            details.append(f"- **明暗の階調**: {metric.value_range}")
            details.append(f"- **光源の一貫性**: {metric.light_consistency}")
            details.append(f"- **立体感**: {metric.three_dimensionality}")
        elif isinstance(metric, TextureAnalysis):
            details.append(f"- **素材感**: {metric.material_expression}")
            details.append(f"- **タッチ**: {metric.touch_variety}")
        elif isinstance(metric, LineQualityAnalysis):
            details.append(f"- **運筆**: {metric.stroke_quality}")
            details.append(f"- **筆圧**: {metric.pressure_control}")
            details.append(f"- **ハッチング**: {metric.hatching}")

        section.extend(details)
        section.append("")
        return "\n".join(section)


# シングルトンインスタンス
_feedback_service: FeedbackService | None = None


def get_feedback_service() -> FeedbackService:
    """FeedbackServiceのシングルトンインスタンスを取得"""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
