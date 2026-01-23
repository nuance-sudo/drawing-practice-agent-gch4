"""お手本画像生成サービス

ユーザーのデッサン分析結果に基づいて、Gemini 2.5 Flash Imageを使用して
ワンランク上のレベルのお手本画像を生成する。
"""

import asyncio
import uuid
from typing import List, Optional

import structlog
from google.cloud import storage

from src.config import settings
from src.models.feedback import DessinAnalysis
from src.models.rank import Rank, UserRank
from src.services.gemini_service import get_gemini_service

logger = structlog.get_logger()


class ImageGenerationError(Exception):
    """画像生成エラー"""
    pass


class ImageGenerationService:
    """お手本画像生成サービス"""

    # ランク別の技術レベル説明（分析プロンプトベース）
    RANK_DESCRIPTIONS = {
        Rank.KYU_10: "初心者レベル：基本的な形の把握、3-4段階の明暗、迷い線を整理した輪郭線",
        Rank.KYU_9: "9級レベル：単純な図形の正確性、光源の統一、最低限の立体感表現",
        Rank.KYU_8: "8級レベル：適切な画面配置、明・中・暗の使い分け、表面に沿ったタッチ",
        Rank.KYU_7: "7級レベル：比率バランスの向上、一貫した光源方向、筆圧の強弱コントロール",
        Rank.KYU_6: "6級レベル：形の正確性向上、5-7段階の明暗階調、ハッチング技法の基礎",
        Rank.KYU_5: "5級レベル：しっかりした基礎技術、7-9段階の滑らかな階調、極端な質感の描き分け",
        Rank.KYU_4: "4級レベル：複合モチーフの固有比率、稜線位置の正確性、素材別タッチの使い分け",
        Rank.KYU_3: "3級レベル：パースペクティブの理解、反射光と陰影の描き分け、金属・ガラス・木材の質感表現",
        Rank.KYU_2: "2級レベル：奥行き感のある構図、10段階の繊細な階調、シャープとソフトな線の使い分け",
        Rank.KYU_1: "1級レベル：重心と動きの表現、空気遠近法の活用、クロスハッチングの高度な組み合わせ",
        Rank.DAN_1: "初段レベル：意図的な画面構成、無限階調の繊細なコントロール、触覚的リアリティの表現",
        Rank.DAN_2: "2段レベル：視点誘導のある構図、空気の層と奥行き表現、重さ・温度・柔らかさの表現",
        Rank.DAN_3: "3段レベル：空間に溶け込む輪郭処理、画面を引き締める強い暗部、一本の線に豊かな表情",
        Rank.SHIHAN_DAI: "師範代レベル：完璧な技術的実行力、「描かないこと」で形や光を表現する高度テクニック",
        Rank.SHIHAN: "師範レベル：芸術的革新性、観る者の感覚を刺激する最高レベルの表現力"
    }

    # ベースプロンプトテンプレート（分析プロンプトベース）
    BASE_PROMPT_TEMPLATE = """
Create an improved pencil drawing based on the following analysis and target skill level.

**Original Drawing Analysis:**
- Overall Score: {overall_score}/100
- Current Performance: {current_rank}
- Target Skill Level: {target_rank}
- Subject Matter: {motif_tags}

**Key Areas for Improvement:**
{improvements_list}

**Detailed Technical Feedback:**
- **Proportion (形の正確さ)**: {proportion_feedback}
- **Tone/Shading (陰影)**: {tone_feedback}
- **Line Quality (線の質)**: {line_feedback}
- **Texture (質感表現)**: {texture_feedback}

**Target Technical Standards ({target_rank}):**
{target_rank_description}

**Primary Focus Areas for Improvement:**
Focus especially on: {primary_improvement_areas}

**Technical Requirements for {target_rank}:**
- **Proportion**: Accurate shape representation, proper ratios and balance, clean contour lines
- **Tonal Range**: {tonal_requirements}
- **Line Quality**: {line_requirements}
- **Texture Expression**: {texture_requirements}

**Drawing Specifications:**
- Medium: Graphite pencil on paper (realistic academic drawing style)
- Style: Classical realism with proper pencil techniques
- Format: Monochrome grayscale with full tonal range
- Resolution: 1024px, high detail
- Composition: Similar subject matter but demonstrating clear technical improvements

**Generation Instructions:**
Create a pencil drawing that demonstrates the specific improvements mentioned above.
The drawing should show what this subject would look like when executed at {target_rank} skill level.
Emphasize the following technical improvements: {specific_improvements}

The result should be a traditional graphite pencil drawing that clearly demonstrates 
superior technique in the identified improvement areas while maintaining the same subject matter.
Ensure the drawing exhibits the technical standards expected at {target_rank} level.
"""

    def __init__(self) -> None:
        """初期化"""
        self._gemini_service = get_gemini_service()
        self._storage_client = storage.Client(project=settings.gcp_project_id)
        self._bucket = self._storage_client.bucket(settings.gcs_bucket_name)

    def get_target_rank(self, current_rank: Rank) -> Rank:
        """現在のランクからワンランク上のターゲットランクを取得

        Args:
            current_rank: 現在のランク

        Returns:
            ワンランク上のランク（最上位の場合は同じランク）
        """
        if current_rank == Rank.SHIHAN:
            # 師範が最上位なので、同じランクを返す
            return Rank.SHIHAN
        
        # IntEnumなので、値を1増やすことで次のランクを取得
        try:
            return Rank(current_rank.value + 1)
        except ValueError:
            # 念のため、無効な値の場合は現在のランクを返す
            logger.warning("invalid_rank_increment", current_rank=current_rank.value)
            return current_rank

    def create_generation_prompt(
        self,
        analysis: DessinAnalysis,
        target_rank: Rank,
        motif_tags: List[str]
    ) -> str:
        """ランクと改善点に基づいてプロンプトを生成

        Args:
            analysis: デッサン分析結果
            target_rank: ターゲットランク
            motif_tags: モチーフタグ

        Returns:
            画像生成用プロンプト
        """
        # 改善点を文字列として整理
        improvements_list = "\n".join([f"- {improvement}" for improvement in analysis.improvements])
        
        # 主要な改善領域を特定（スコアが低い順に3つ）
        area_scores = [
            ("proportion", analysis.proportion.score),
            ("tone/shading", analysis.tone.score),
            ("line quality", analysis.line_quality.score),
            ("texture", analysis.texture.score)
        ]
        area_scores.sort(key=lambda x: x[1])  # スコア昇順でソート
        primary_improvement_areas = ", ".join([area[0] for area in area_scores[:3]])
        
        # 具体的な改善点を整理
        specific_improvements = []
        if analysis.proportion.score < 80:
            specific_improvements.append("more accurate proportions and better shape accuracy")
        if analysis.tone.score < 80:
            specific_improvements.append("improved tonal range and consistent lighting")
        if analysis.line_quality.score < 80:
            specific_improvements.append("better line control and hatching techniques")
        if analysis.texture.score < 80:
            specific_improvements.append("enhanced texture rendering and material expression")
        
        specific_improvements_text = ", ".join(specific_improvements) if specific_improvements else "overall refinement"

        # ランク別技術要件を生成
        tonal_requirements = self._get_tonal_requirements(target_rank)
        line_requirements = self._get_line_requirements(target_rank)
        texture_requirements = self._get_texture_requirements(target_rank)

        # プロンプトを生成
        prompt = self.BASE_PROMPT_TEMPLATE.format(
            overall_score=analysis.overall_score,
            current_rank=f"Current performance level (Score: {analysis.overall_score})",
            target_rank=target_rank.label,
            motif_tags=", ".join(motif_tags),
            improvements_list=improvements_list,
            proportion_feedback=analysis.proportion.shape_accuracy,
            tone_feedback=analysis.tone.value_range,
            line_feedback=analysis.line_quality.stroke_quality,
            texture_feedback=analysis.texture.material_expression,
            target_rank_description=self.RANK_DESCRIPTIONS[target_rank],
            primary_improvement_areas=primary_improvement_areas,
            specific_improvements=specific_improvements_text,
            tonal_requirements=tonal_requirements,
            line_requirements=line_requirements,
            texture_requirements=texture_requirements
        )
        
        return prompt.strip()

    def _get_tonal_requirements(self, rank: Rank) -> str:
        """ランク別の明暗要件を取得"""
        if rank.value <= 7:  # 10級-4級
            return "3-7 distinct tonal values, consistent light source direction, basic form shadows"
        elif rank.value <= 10:  # 3級-1級
            return "7-10 smooth gradations, accurate shadow edge placement, reflected light awareness"
        elif rank.value <= 13:  # 初段-3段
            return "Infinite subtle gradations, atmospheric perspective, strong dark values for contrast"
        else:  # 師範代-師範
            return "Perfect tonal control, air layers and spatial depth, masterful use of 'black' quality"

    def _get_line_requirements(self, rank: Rank) -> str:
        """ランク別の線質要件を取得"""
        if rank.value <= 7:  # 10級-4級
            return "Varied pressure control, basic hatching techniques, organized contour lines"
        elif rank.value <= 10:  # 3級-1級
            return "Sharp and soft line variations, cross-hatching combinations, surface-following strokes"
        elif rank.value <= 13:  # 初段-3段
            return "Expressive line quality with entry and exit, advanced hatching density control"
        else:  # 師範代-師範
            return "Rich expression within single lines, masterful use of negative space and 'not drawing'"

    def _get_texture_requirements(self, rank: Rank) -> str:
        """ランク別の質感要件を取得"""
        if rank.value <= 7:  # 10級-4級
            return "Basic material differentiation (smooth vs rough), surface-appropriate strokes"
        elif rank.value <= 10:  # 3級-1級
            return "Metal, glass, wood, fabric distinctions, appropriate pencil hardness usage"
        elif rank.value <= 13:  # 初段-3段
            return "Weight, temperature, softness expression, tactile reality that engages senses"
        else:  # 師範代-師範
            return "Complete sensory engagement, innovative textural expression, revolutionary techniques"

    async def generate_example_image(
        self,
        original_image_url: str,
        analysis: DessinAnalysis,
        user_rank: UserRank,
        motif_tags: List[str]
    ) -> Optional[str]:
        """お手本画像を生成し、URLを返す

        Args:
            original_image_url: 元画像のURL
            analysis: デッサン分析結果
            user_rank: ユーザーランク情報
            motif_tags: モチーフタグ

        Returns:
            生成画像のCDN URL（失敗時はNone）
        """
        try:
            # 1. ターゲットランクを決定
            target_rank = self.get_target_rank(user_rank.current_rank)
            
            logger.info(
                "image_generation_started",
                user_id=user_rank.user_id,
                current_rank=user_rank.current_rank.label,
                target_rank=target_rank.label,
                motif_tags=motif_tags,
                overall_score=analysis.overall_score
            )
            
            # 2. 元画像を取得
            original_image_data = await self._fetch_original_image(original_image_url)
            
            # 3. 生成プロンプトを作成
            prompt = self.create_generation_prompt(analysis, target_rank, motif_tags)
            
            logger.debug("generation_prompt_created", prompt_length=len(prompt))
            
            # 4. 画像生成を実行（リトライ付き）
            generated_image_data = await self._generate_with_retry(
                prompt=prompt,
                original_image_data=original_image_data,
                max_retries=3
            )
            
            # 5. 生成画像を保存
            example_image_url = await self._save_generated_image(
                image_data=generated_image_data,
                user_id=user_rank.user_id
            )
            
            logger.info(
                "image_generation_completed",
                user_id=user_rank.user_id,
                target_rank=target_rank.label,
                image_size_bytes=len(generated_image_data),
                example_image_url=example_image_url
            )
            
            return example_image_url
            
        except Exception as e:
            logger.error(
                "image_generation_failed",
                user_id=user_rank.user_id,
                error=str(e),
                error_type=type(e).__name__
            )
            return None

    async def _fetch_original_image(self, image_url: str) -> bytes:
        """元画像をCDNから取得

        Args:
            image_url: 画像のCDN URL

        Returns:
            画像データ（bytes）

        Raises:
            ImageGenerationError: 画像取得に失敗した場合
        """
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        raise ImageGenerationError(f"Failed to fetch image: HTTP {response.status}")
                    
                    image_data = await response.read()
                    
                    if len(image_data) == 0:
                        raise ImageGenerationError("Empty image data received")
                    
                    return image_data
                    
        except Exception as e:
            raise ImageGenerationError(f"Failed to fetch original image: {e}")

    async def _generate_with_retry(
        self,
        prompt: str,
        original_image_data: bytes,
        max_retries: int = 3
    ) -> bytes:
        """リトライ機能付き画像生成

        Args:
            prompt: 生成プロンプト
            original_image_data: 元画像データ
            max_retries: 最大リトライ回数

        Returns:
            生成画像データ（bytes）

        Raises:
            ImageGenerationError: 最大リトライ回数に達した場合
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug("image_generation_attempt", attempt=attempt + 1, max_retries=max_retries)
                
                generated_image_data = await self._gemini_service.generate_image(
                    prompt=prompt,
                    original_image_data=original_image_data
                )
                
                if generated_image_data and len(generated_image_data) > 0:
                    return generated_image_data
                else:
                    raise ImageGenerationError("Empty image data generated")
                    
            except Exception as e:
                last_error = e
                logger.warning(
                    "image_generation_attempt_failed",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e)
                )
                
                if attempt < max_retries - 1:
                    # 指数バックオフでリトライ
                    wait_time = 2 ** attempt
                    logger.debug("retrying_after_delay", wait_seconds=wait_time)
                    await asyncio.sleep(wait_time)
        
        # 全てのリトライが失敗
        raise ImageGenerationError(f"Failed after {max_retries} attempts: {last_error}")

    async def _save_generated_image(
        self,
        image_data: bytes,
        user_id: str
    ) -> str:
        """生成画像をCloud Storageに保存し、CDN URLを返す

        Args:
            image_data: 生成画像データ
            user_id: ユーザーID

        Returns:
            CDN URL

        Raises:
            ImageGenerationError: 保存に失敗した場合
        """
        try:
            # ファイル名を生成（UUID + タイムスタンプ）
            image_id = str(uuid.uuid4())
            file_path = f"generated/{user_id}/{image_id}/example.png"
            
            # Cloud Storageに保存
            blob = self._bucket.blob(file_path)
            blob.upload_from_string(
                image_data,
                content_type="image/png"
            )
            
            # メタデータを設定
            blob.metadata = {
                "user_id": user_id,
                "generated_at": str(asyncio.get_event_loop().time()),
                "ai_generated": "true",
                "model": "gemini-2.5-flash-image"
            }
            blob.patch()
            
            base_url = f"https://storage.googleapis.com/{settings.gcs_bucket_name}"
            
            cdn_url = f"{base_url}/{file_path}"
            
            logger.debug(
                "image_saved_to_storage",
                file_path=file_path,
                cdn_url=cdn_url,
                image_size_bytes=len(image_data)
            )
            
            return cdn_url
            
        except Exception as e:
            raise ImageGenerationError(f"Failed to save generated image: {e}")


# シングルトンインスタンス
_image_generation_service: Optional[ImageGenerationService] = None


def get_image_generation_service() -> ImageGenerationService:
    """ImageGenerationServiceのシングルトンインスタンスを取得"""
    global _image_generation_service
    if _image_generation_service is None:
        _image_generation_service = ImageGenerationService()
    return _image_generation_service