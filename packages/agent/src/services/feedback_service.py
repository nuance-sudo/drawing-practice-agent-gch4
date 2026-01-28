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
        summary = self._create_summary(analysis, rank)

        # 2. Markdown詳細フィードバックの生成 (ランクに応じたトーン＆アドバイス)
        detailed_feedback = self._generate_markdown(analysis, rank)

        return FeedbackResponse(
            analysis=analysis,  # 元の分析データも含める
            summary=summary,
            detailed_feedback=detailed_feedback,
        )

    def _create_summary(self, analysis: DessinAnalysis, rank: Rank | None = None) -> str:
        """分析結果から簡潔な要約を作成（ランク対応）"""
        score = analysis.overall_score
        # 主要な強みと改善点を1つずつピックアップ
        strength = analysis.strengths[0] if analysis.strengths else "全体的なバランス"
        improvement = analysis.improvements[0] if analysis.improvements else "特になし"
        
        return f"総合スコア: {score:.1f}/100 | 良い点: {strength} | 改善点: {improvement}"

    def _generate_markdown(self, analysis: DessinAnalysis, rank: Rank) -> str:
        """ランクに応じたMarkdownフィードバックを生成"""
        
        intro_message = self._get_rank_intro_message(rank, analysis.overall_score)

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
            advice_prefix = self._get_rank_advice_prefix(rank)
            for improvement in analysis.improvements:
                md.append(f"- {advice_prefix}{improvement}")
        
        # ランク別の次のステップアドバイス
        next_step = self._get_rank_next_step(rank, analysis.overall_score)
        if next_step:
            md.append("")
            md.append("## 🎯 次のステップ")
            md.append(next_step)
        
        return "\n".join(md)

    def _get_rank_intro_message(self, rank: Rank, score: float) -> str:
        """ランクに応じたイントロメッセージを生成"""
        rank_value = rank.value
        
        # 10級-6級（初級）
        if rank_value <= Rank.KYU_6.value:
            if score >= 80:
                return "素晴らしいデッサンです！基礎がしっかりと身についてきていますね。この調子で練習を続けましょう。"
            elif score >= 60:
                return "デッサン練習お疲れ様です！良い部分もたくさんあります。一つずつ改善していきましょう。"
            else:
                return "デッサン練習お疲れ様です！最初は難しく感じるかもしれませんが、継続することで必ず上達します。一緒に頑張りましょう！"
        
        # 5級-1級（中級）
        elif rank_value <= Rank.KYU_1.value:
            if score >= 80:
                return "技術的な完成度が高まってきていますね。中級者としての基礎がしっかりと固まってきました。"
            elif score >= 60:
                return "デッサン練習お疲れ様です。中級者として、より技術的な精度を意識していきましょう。"
            else:
                return "デッサン練習お疲れ様です。中級者として、基礎技術の見直しと応用技術の習得をバランスよく進めていきましょう。"
        
        # 初段-3段（上級）
        elif rank_value <= Rank.DAN_3.value:
            if score >= 80:
                return "上級者としての技術が確実に身についてきています。細部への意識と全体のバランスをさらに追求していきましょう。"
            elif score >= 60:
                return "デッサン練習お疲れ様です。上級者として、より高度な技術と表現力を目指していきましょう。"
            else:
                return "デッサン練習お疲れ様です。上級者として、技術の再確認と新たな表現方法の探求を続けていきましょう。"
        
        # 師範代-師範（達人）
        else:
            if score >= 80:
                return "達人レベルの技術と表現力が光る作品です。さらなる芸術的探求と革新を目指していきましょう。"
            elif score >= 60:
                return "デッサン練習お疲れ様です。達人として、技術の完成度と表現の独創性をさらに高めていきましょう。"
            else:
                return "デッサン練習お疲れ様です。達人として、基本に立ち返りつつ、新たな表現の可能性を探求していきましょう。"

    def _get_rank_advice_prefix(self, rank: Rank) -> str:
        """ランクに応じたアドバイスの接頭辞を取得"""
        rank_value = rank.value
        
        # 10級-6級（初級）
        if rank_value <= Rank.KYU_6.value:
            return "次回は、"
        # 5級-1級（中級）
        elif rank_value <= Rank.KYU_1.value:
            return "改善のポイントとして、"
        # 初段-3段（上級）
        elif rank_value <= Rank.DAN_3.value:
            return "より高度な表現のために、"
        # 師範代-師範（達人）
        else:
            return "表現の深化のために、"

    def _get_rank_next_step(self, rank: Rank, score: float) -> str:
        """ランクに応じた次のステップアドバイスを生成"""
        rank_value = rank.value
        
        # 10級-6級（初級）
        if rank_value <= Rank.KYU_6.value:
            if score >= 80:
                return "基礎がしっかりしてきました。次は**複数のモチーフ**に挑戦して、配置や前後関係を意識したデッサンに取り組んでみましょう。"
            else:
                return "まずは**単純な形（球、立方体など）**を正確に描く練習を続けましょう。形の正確さと基本的な明暗の使い分けを意識することが大切です。"
        
        # 5級-1級（中級）
        elif rank_value <= Rank.KYU_1.value:
            if score >= 80:
                return "中級者としての技術が身についてきました。次は**複合モチーフ**や**パースペクティブ**を意識した構図に挑戦してみましょう。"
            else:
                return "中級者として、**比率の正確性**と**明暗の階調（5-7段階）**を意識した練習を続けましょう。ハッチング技法も積極的に取り入れてみてください。"
        
        # 初段-3段（上級）
        elif rank_value <= Rank.DAN_3.value:
            if score >= 80:
                return "上級者としての技術が確立されてきました。次は**意図的な画面構成**や**空気遠近法**を活用した、より表現力豊かなデッサンに挑戦してみましょう。"
            else:
                return "上級者として、**細部の表現**と**全体のバランス**を両立させる練習を続けましょう。反射光や陰影の描き分け、素材感の表現をさらに追求してください。"
        
        # 師範代-師範（達人）
        else:
            if score >= 80:
                return "達人レベルの技術が確立されています。次は**芸術的革新性**や**観る者の感覚を刺激する表現**を追求し、独自のスタイルを確立していきましょう。"
            else:
                return "達人として、**基本に立ち返りつつ**、新たな表現の可能性を探求していきましょう。「描かないこと」で形や光を表現する高度なテクニックにも挑戦してみてください。"

    def _format_criterion(self,
                          title: str,
                          metric: ProportionAnalysis | ToneAnalysis | TextureAnalysis | LineQualityAnalysis,
                          rank: Rank) -> str:
        """評価項目のMarkdownフォーマット（ランクに応じた説明を追加）"""
        
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
        
        # ランクに応じた評価の説明を追加
        rank_context = self._get_rank_criterion_context(title, rank)
        if rank_context:
            section.append(f"*{rank_context}*")
            section.append("")
        
        # 各フィールドの内容を表示
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

    def _get_rank_criterion_context(self, criterion_title: str, rank: Rank) -> str:
        """ランクに応じた評価項目の説明を取得"""
        rank_value = rank.value
        
        # 10級-6級（初級）の説明
        if rank_value <= Rank.KYU_6.value:
            if criterion_title == "プロポーション":
                return "初級者として、基本的な形の正確さを意識しましょう"
            elif criterion_title == "明暗・陰影":
                return "初級者として、明・中・暗の3-4段階の使い分けを意識しましょう"
            elif criterion_title == "質感・タッチ":
                return "初級者として、極端な質感の違い（ツヤとザラザラ）を表現しましょう"
            elif criterion_title == "線の質":
                return "初級者として、筆圧の強弱と基本的なハッチングを意識しましょう"
        
        # 5級-1級（中級）の説明
        elif rank_value <= Rank.KYU_1.value:
            if criterion_title == "プロポーション":
                return "中級者として、複合モチーフの固有比率とパースペクティブを意識しましょう"
            elif criterion_title == "明暗・陰影":
                return "中級者として、7-9段階の滑らかな階調と反射光を意識しましょう"
            elif criterion_title == "質感・タッチ":
                return "中級者として、金属・ガラス・木材などの素材の描き分けを意識しましょう"
            elif criterion_title == "線の質":
                return "中級者として、シャープとソフトな線の使い分けとクロスハッチングを意識しましょう"
        
        # 初段-3段（上級）の説明
        elif rank_value <= Rank.DAN_3.value:
            if criterion_title == "プロポーション":
                return "上級者として、重心・動きの表現と意図的な画面構成を意識しましょう"
            elif criterion_title == "明暗・陰影":
                return "上級者として、無限階調の繊細なコントロールと空気遠近法を意識しましょう"
            elif criterion_title == "質感・タッチ":
                return "上級者として、重さ・温度・柔らかさまで感じさせる表現を意識しましょう"
            elif criterion_title == "線の質":
                return "上級者として、一本の線に豊かな表情と「描かないこと」の表現を意識しましょう"
        
        # 師範代-師範（達人）の説明
        else:
            if criterion_title == "プロポーション":
                return "達人として、芸術的革新性と観る者の感覚を刺激する表現を追求しましょう"
            elif criterion_title == "明暗・陰影":
                return "達人として、完璧な技術的実行力と「描かないこと」で光を表現する高度テクニックを追求しましょう"
            elif criterion_title == "質感・タッチ":
                return "達人として、触覚的リアリティと観る者の感覚を刺激する表現を追求しましょう"
            elif criterion_title == "線の質":
                return "達人として、一本の線に豊かな表情と「描かないこと」で形を表現する高度テクニックを追求しましょう"
        
        return ""


# シングルトンインスタンス
_feedback_service: FeedbackService | None = None


def get_feedback_service() -> FeedbackService:
    """FeedbackServiceのシングルトンインスタンスを取得"""
    global _feedback_service
    if _feedback_service is None:
        _feedback_service = FeedbackService()
    return _feedback_service
