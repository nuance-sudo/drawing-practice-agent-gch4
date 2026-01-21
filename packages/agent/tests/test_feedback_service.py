import unittest

from src.models.feedback import DessinAnalysis, ProportionAnalysis, ToneAnalysis, TextureAnalysis, LineQualityAnalysis
from src.models.rank import Rank
from src.services.feedback_service import FeedbackService


class TestFeedbackService(unittest.TestCase):
    def setUp(self):
        self.service = FeedbackService()
        
        # ダミーの分析データ
        self.mock_analysis = DessinAnalysis(
            proportion=ProportionAnalysis(
                shape_accuracy="Good accuracy",
                ratio_balance="Balanced",
                contour_quality="Smooth",
                score=80.0
            ),
            tone=ToneAnalysis(
                value_range="Wide range",
                light_consistency="Consistent",
                three_dimensionality="Good depth",
                score=70.0
            ),
            texture=TextureAnalysis(
                material_expression="Realistic",
                touch_variety="Varied",
                score=60.0
            ),
            line_quality=LineQualityAnalysis(
                stroke_quality="Confident",
                pressure_control="Controlled",
                hatching="Clean",
                score=50.0
            ),
            overall_score=65.0,
            strengths=["Good proportion", "Nice tone"],
            improvements=["Texture needs work", "Lines are shaky"],
            tags=["apple", "still_life"]
        )

    def test_generate_feedback_structure(self):
        """フィードバックの構造が正しいかテスト"""
        rank = Rank.KYU_1
        response = self.service.generate_feedback(self.mock_analysis, rank)

        self.assertEqual(response.analysis, self.mock_analysis)
        self.assertIn("総合スコア: 65.0/100", response.summary)
        self.assertIn("良い点: Good proportion", response.summary)
        self.assertLess(len(response.summary), 200) # 要約は短くあるべき

        # Markdownのチェック
        self.assertIn("# デッサン分析レポート", response.detailed_feedback)
        self.assertIn(f"**現在のランク**: {rank.label}", response.detailed_feedback)
        
        # 評価項目が含まれているか
        self.assertIn("## 📊 評価項目別分析", response.detailed_feedback)
        self.assertIn("プロポーション", response.detailed_feedback)
        self.assertIn("明暗・陰影", response.detailed_feedback)
        
        # アドバイスが含まれているか
        self.assertIn("## 💡 総合アドバイス", response.detailed_feedback)
        self.assertIn("- Good proportion", response.detailed_feedback)
        self.assertIn("- Texture needs work", response.detailed_feedback)
        self.assertIn("- Lines are shaky", response.detailed_feedback)

    def test_markdown_tone_by_rank(self):
        """ランクによって表示ラベルが変わることのテスト"""
        # Kyu 10
        res_kyu10 = self.service.generate_feedback(self.mock_analysis, Rank.KYU_10)
        self.assertIn("10級", res_kyu10.detailed_feedback)
        
        # Shihan
        res_shihan = self.service.generate_feedback(self.mock_analysis, Rank.SHIHAN)
        self.assertIn("師範", res_shihan.detailed_feedback)

    def test_score_icons(self):
        """スコアに応じたアイコンのテスト"""
        # High score -> 🌟
        self.mock_analysis.proportion.score = 90.0
        res = self.service.generate_feedback(self.mock_analysis, Rank.KYU_1)
        self.assertIn("🌟", res.detailed_feedback)

        # Low score -> 🔴
        self.mock_analysis.proportion.score = 20.0
        res_low = self.service.generate_feedback(self.mock_analysis, Rank.KYU_1)
        self.assertIn("🔴", res_low.detailed_feedback)
