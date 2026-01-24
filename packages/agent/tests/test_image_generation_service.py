"""ImageGenerationServiceのテスト"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.models.feedback import DessinAnalysis, ProportionAnalysis, ToneAnalysis, TextureAnalysis, LineQualityAnalysis
from src.models.rank import Rank, UserRank
from src.services.image_generation_service import ImageGenerationService, ImageGenerationError


class TestImageGenerationService:
    """ImageGenerationServiceのテストクラス"""

    def setup_method(self):
        """各テストメソッドの前に実行される初期化処理"""
        # GeminiServiceとCloud Storageをモック化してImageGenerationServiceを初期化
        with patch('src.services.image_generation_service.get_gemini_service') as mock_get_gemini, \
             patch('src.services.image_generation_service.storage.Client') as mock_storage_client:
            
            # GeminiServiceのモック
            mock_gemini_service = Mock()
            mock_get_gemini.return_value = mock_gemini_service
            
            # Cloud Storageのモック
            mock_bucket = Mock()
            mock_storage_client.return_value.bucket.return_value = mock_bucket
            
            # ImageGenerationServiceを初期化
            self.service = ImageGenerationService()
            
            # テスト用にモックオブジェクトを保存
            self.mock_gemini_service = mock_gemini_service
            self.mock_bucket = mock_bucket
        
        # テスト用の分析データ
        self.test_analysis = DessinAnalysis(
            proportion=ProportionAnalysis(
                shape_accuracy="形の正確性は良好です",
                ratio_balance="比率のバランスが取れています",
                contour_quality="輪郭線が丁寧に描かれています",
                score=75.0
            ),
            tone=ToneAnalysis(
                value_range="明暗の階調が適切です",
                light_consistency="光源が一貫しています",
                three_dimensionality="立体感が表現されています",
                score=70.0
            ),
            texture=TextureAnalysis(
                material_expression="素材感の表現が良いです",
                touch_variety="タッチの使い分けができています",
                score=65.0
            ),
            line_quality=LineQualityAnalysis(
                stroke_quality="運筆が安定しています",
                pressure_control="筆圧のコントロールが良いです",
                hatching="ハッチング技法が適切です",
                score=80.0
            ),
            overall_score=72.5,
            strengths=["陰影表現が良い", "構図が安定している"],
            improvements=["プロポーションの精度向上", "質感表現の強化"],
            tags=["りんご", "静物"]
        )
        
        # テスト用のユーザーランク
        self.test_user_rank = UserRank(
            user_id="test_user_123",
            current_rank=Rank.KYU_7,
            current_score=72.5,
            total_submissions=5,
            high_scores=[75.0, 80.0, 72.5],
            updated_at=datetime.now()
        )

    def test_get_target_rank_normal_progression(self):
        """通常のランク進行のテスト"""
        # 7級 → 6級
        target = self.service.get_target_rank(Rank.KYU_7)
        assert target == Rank.KYU_6
        
        # 1級 → 初段
        target = self.service.get_target_rank(Rank.KYU_1)
        assert target == Rank.DAN_1
        
        # 2段 → 3段
        target = self.service.get_target_rank(Rank.DAN_2)
        assert target == Rank.DAN_3

    def test_get_target_rank_max_rank(self):
        """最上位ランクのテスト"""
        # 師範は師範のまま
        target = self.service.get_target_rank(Rank.SHIHAN)
        assert target == Rank.SHIHAN

    def test_create_generation_prompt_basic(self):
        """基本的なプロンプト生成のテスト"""
        prompt = self.service.create_generation_prompt(
            analysis=self.test_analysis,
            target_rank=Rank.KYU_6,
            motif_tags=["りんご", "静物"]
        )
        
        # プロンプトに必要な要素が含まれているかチェック
        assert "72.5/100" in prompt  # 総合スコア
        assert "6級" in prompt  # ターゲットランク
        assert "りんご, 静物" in prompt  # モチーフタグ
        assert "プロポーションの精度向上" in prompt  # 改善点
        assert "graphite pencil" in prompt.lower()  # スタイル要件
        assert "1024px" in prompt  # 解像度
        assert "5-7段階の明暗階調" in prompt  # ランク別明暗要件

    def test_create_generation_prompt_improvement_areas(self):
        """改善領域の特定テスト"""
        # 質感スコアが最も低い（65.0）ので、textureが主要改善領域に含まれるはず
        prompt = self.service.create_generation_prompt(
            analysis=self.test_analysis,
            target_rank=Rank.KYU_6,
            motif_tags=["りんご"]
        )
        
        assert "texture" in prompt.lower()

    @pytest.mark.asyncio
    async def test_fetch_original_image_success(self):
        """画像取得成功のテスト"""
        mock_image_data = b"fake_image_data"
        
        # _fetch_original_imageメソッド全体をモック化
        with patch.object(self.service, '_fetch_original_image', return_value=mock_image_data) as mock_fetch:
            result = await self.service._fetch_original_image("https://example.com/image.jpg")
            
            assert result == mock_image_data
            mock_fetch.assert_called_once_with("https://example.com/image.jpg")

    @pytest.mark.asyncio
    async def test_fetch_original_image_http_error(self):
        """画像取得HTTPエラーのテスト"""
        # _fetch_original_imageメソッドをエラーを発生させるようにモック化
        with patch.object(self.service, '_fetch_original_image', side_effect=ImageGenerationError("Failed to fetch image: HTTP 404")):
            with pytest.raises(ImageGenerationError, match="Failed to fetch image: HTTP 404"):
                await self.service._fetch_original_image("https://example.com/image.jpg")

    @pytest.mark.asyncio
    async def test_fetch_original_image_empty_data(self):
        """空の画像データのテスト"""
        # _fetch_original_imageメソッドをエラーを発生させるようにモック化
        with patch.object(self.service, '_fetch_original_image', side_effect=ImageGenerationError("Empty image data received")):
            with pytest.raises(ImageGenerationError, match="Empty image data received"):
                await self.service._fetch_original_image("https://example.com/image.jpg")

    @pytest.mark.asyncio
    async def test_generate_with_retry_success_first_attempt(self):
        """リトライ機能：1回目で成功のテスト"""
        mock_image_data = b"generated_image_data"
        
        # モックされたGeminiServiceを使用
        self.mock_gemini_service.generate_image = AsyncMock(return_value=mock_image_data)
        
        result = await self.service._generate_with_retry(
            prompt="test prompt",
            original_image_data=b"original",
            max_retries=3
        )
        
        assert result == mock_image_data
        assert self.mock_gemini_service.generate_image.call_count == 1

    @pytest.mark.asyncio
    async def test_generate_with_retry_success_after_retry(self):
        """リトライ機能：2回目で成功のテスト"""
        mock_image_data = b"generated_image_data"
        
        # モックされたGeminiServiceを使用
        # 1回目は失敗、2回目は成功
        self.mock_gemini_service.generate_image = AsyncMock(
            side_effect=[Exception("API Error"), mock_image_data]
        )
        
        with patch('asyncio.sleep', new_callable=AsyncMock):  # sleepをモック化
            result = await self.service._generate_with_retry(
                prompt="test prompt",
                original_image_data=b"original",
                max_retries=3
            )
        
        assert result == mock_image_data
        assert self.mock_gemini_service.generate_image.call_count == 2

    @pytest.mark.asyncio
    async def test_generate_with_retry_all_attempts_fail(self):
        """リトライ機能：全て失敗のテスト"""
        # モックされたGeminiServiceを使用
        self.mock_gemini_service.generate_image = AsyncMock(side_effect=Exception("API Error"))
        
        with patch('asyncio.sleep', new_callable=AsyncMock):  # sleepをモック化
            with pytest.raises(ImageGenerationError, match="Failed after 3 attempts"):
                await self.service._generate_with_retry(
                    prompt="test prompt",
                    original_image_data=b"original",
                    max_retries=3
                )
        
        assert self.mock_gemini_service.generate_image.call_count == 3

    @pytest.mark.asyncio
    async def test_save_generated_image_success(self):
        """画像保存成功のテスト"""
        mock_image_data = b"generated_image_data"
        
        # モックされたCloud Storageを使用
        mock_blob = Mock()
        self.mock_bucket.blob.return_value = mock_blob
        
        with patch('src.services.image_generation_service.settings') as mock_settings:
            mock_settings.cdn_base_url = "https://cdn.example.com"
            
            result = await self.service._save_generated_image(
                image_data=mock_image_data,
                user_id="test_user_123"
            )
            
            # CDN URLが正しく生成されているかチェック
            assert result.startswith("https://cdn.example.com/generated/test_user_123/")
            assert result.endswith("/example.png")
            
            # Cloud Storageへの保存が呼ばれているかチェック
            mock_blob.upload_from_string.assert_called_once_with(
                mock_image_data,
                content_type="image/png"
            )

    @pytest.mark.asyncio
    async def test_generate_example_image_full_flow_success(self):
        """お手本画像生成の全体フロー成功テスト"""
        mock_original_image = b"original_image_data"
        mock_generated_image = b"generated_image_data"
        expected_url = "https://cdn.example.com/generated/test_user_123/uuid/example.png"
        
        with patch.object(self.service, '_fetch_original_image', return_value=mock_original_image) as mock_fetch, \
             patch.object(self.service, '_generate_with_retry', return_value=mock_generated_image) as mock_generate, \
             patch.object(self.service, '_save_generated_image', return_value=expected_url) as mock_save:
            
            result = await self.service.generate_example_image(
                original_image_url="https://example.com/original.jpg",
                analysis=self.test_analysis,
                user_rank=self.test_user_rank,
                motif_tags=["りんご", "静物"]
            )
            
            assert result == expected_url
            
            # 各ステップが正しく呼ばれているかチェック
            mock_fetch.assert_called_once_with("https://example.com/original.jpg")
            mock_generate.assert_called_once()
            mock_save.assert_called_once_with(image_data=mock_generated_image, user_id="test_user_123")

    @pytest.mark.asyncio
    async def test_generate_example_image_fetch_failure(self):
        """お手本画像生成：画像取得失敗のテスト"""
        with patch.object(self.service, '_fetch_original_image', side_effect=ImageGenerationError("Fetch failed")):
            
            result = await self.service.generate_example_image(
                original_image_url="https://example.com/original.jpg",
                analysis=self.test_analysis,
                user_rank=self.test_user_rank,
                motif_tags=["りんご", "静物"]
            )
            
            assert result is None

    @pytest.mark.asyncio
    async def test_generate_example_image_generation_failure(self):
        """お手本画像生成：画像生成失敗のテスト"""
        mock_original_image = b"original_image_data"
        
        with patch.object(self.service, '_fetch_original_image', return_value=mock_original_image), \
             patch.object(self.service, '_generate_with_retry', side_effect=ImageGenerationError("Generation failed")):
            
            result = await self.service.generate_example_image(
                original_image_url="https://example.com/original.jpg",
                analysis=self.test_analysis,
                user_rank=self.test_user_rank,
                motif_tags=["りんご", "静物"]
            )
            
            assert result is None

    def test_rank_descriptions_completeness(self):
        """ランク説明の完全性テスト"""
        # 全てのランクに説明が定義されているかチェック
        for rank in Rank:
            assert rank in ImageGenerationService.RANK_DESCRIPTIONS
            assert len(ImageGenerationService.RANK_DESCRIPTIONS[rank]) > 0

    def test_prompt_template_variables(self):
        """プロンプトテンプレートの変数チェック"""
        # テンプレートに必要な変数が含まれているかチェック
        template = ImageGenerationService.BASE_PROMPT_TEMPLATE
        
        required_vars = [
            "{overall_score}",
            "{current_rank}",
            "{target_rank}",
            "{motif_tags}",
            "{improvements_list}",
            "{proportion_feedback}",
            "{tone_feedback}",
            "{line_feedback}",
            "{texture_feedback}",
            "{target_rank_description}",
            "{primary_improvement_areas}",
            "{specific_improvements}",
            "{tonal_requirements}",
            "{line_requirements}",
            "{texture_requirements}"
        ]
        
        for var in required_vars:
            assert var in template, f"Required variable {var} not found in template"

    def test_get_tonal_requirements(self):
        """明暗要件取得のテスト"""
        # 初級レベル
        req = self.service._get_tonal_requirements(Rank.KYU_7)
        assert "3-7 distinct tonal values" in req
        
        # 中級レベル
        req = self.service._get_tonal_requirements(Rank.KYU_3)
        assert "7-10 smooth gradations" in req
        
        # 上級レベル
        req = self.service._get_tonal_requirements(Rank.DAN_2)
        assert "Infinite subtle gradations" in req
        
        # 師範レベル
        req = self.service._get_tonal_requirements(Rank.SHIHAN)
        assert "Perfect tonal control" in req

    def test_get_line_requirements(self):
        """線質要件取得のテスト"""
        # 初級レベル
        req = self.service._get_line_requirements(Rank.KYU_6)
        assert "Varied pressure control" in req
        
        # 中級レベル
        req = self.service._get_line_requirements(Rank.KYU_2)
        assert "Sharp and soft line variations" in req
        
        # 上級レベル
        req = self.service._get_line_requirements(Rank.DAN_1)
        assert "Expressive line quality" in req
        
        # 師範レベル
        req = self.service._get_line_requirements(Rank.SHIHAN_DAI)
        assert "Rich expression within single lines" in req

    def test_create_generation_prompt_detailed_output(self):
        """詳細なプロンプト生成の出力確認テスト"""
        # より詳細な分析データでテスト
        detailed_analysis = DessinAnalysis(
            proportion=ProportionAnalysis(
                shape_accuracy="形の正確性は良好ですが、右側の輪郭がやや歪んでいます",
                ratio_balance="比率のバランスが取れていますが、縦横比がわずかに不正確です",
                contour_quality="輪郭線が丁寧に描かれていますが、迷い線が少し見られます",
                score=75.0
            ),
            tone=ToneAnalysis(
                value_range="明暗の階調は4段階程度で、もう少し細かい階調が必要です",
                light_consistency="光源は一貫していますが、反射光の表現が不足しています",
                three_dimensionality="立体感は表現されていますが、稜線の位置が不正確です",
                score=70.0
            ),
            texture=TextureAnalysis(
                material_expression="素材感の表現は基本的ですが、表面の質感がもう少し欲しいです",
                touch_variety="タッチの使い分けはできていますが、より繊細な表現が必要です",
                score=65.0
            ),
            line_quality=LineQualityAnalysis(
                stroke_quality="運筆は安定していますが、線に強弱をもっとつけましょう",
                pressure_control="筆圧のコントロールは良いですが、より意図的な使い分けを",
                hatching="ハッチング技法は適切ですが、密度のコントロールを向上させましょう",
                score=80.0
            ),
            overall_score=72.5,
            strengths=["陰影表現の基礎ができている", "構図が安定している"],
            improvements=["プロポーションの精度向上", "明暗階調の細分化", "質感表現の強化"],
            tags=["りんご", "静物"]
        )
        
        prompt = self.service.create_generation_prompt(
            analysis=detailed_analysis,
            target_rank=Rank.KYU_6,
            motif_tags=["りんご", "静物"]
        )
        
        # 生成されたプロンプトの内容を確認
        print("\n=== Generated Prompt ===")
        print(prompt)
        print("=== End of Prompt ===\n")
        
        # 新しい要素が含まれているかチェック
        assert "6級レベル：形の正確性向上、5-7段階の明暗階調" in prompt
        assert "3-7 distinct tonal values" in prompt  # 明暗要件
        assert "Varied pressure control" in prompt  # 線質要件
        assert "Basic material differentiation" in prompt  # 質感要件
        assert "texture" in prompt.lower()  # 主要改善領域
        
        # プロンプトが適切な長さであることを確認
        assert len(prompt) > 1000  # 詳細なプロンプトなので十分な長さがあるはず