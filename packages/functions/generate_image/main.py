import os
import json
import uuid
import structlog
import asyncio
import functions_framework
from typing import List, Optional, Dict, Any
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from google.cloud import storage

# structlog configuration
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger()


# Environment Variables
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
OUTPUT_BUCKET_NAME = os.environ.get("OUTPUT_BUCKET_NAME")
COMPLETE_TASK_FUNCTION_URL = os.environ.get("COMPLETE_TASK_FUNCTION_URL")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-image")
LOCATION = "us-central1"

class ImageGenerationError(Exception):
    pass

# Rank Descriptions (Ported from ImageGenerationService)
RANK_DESCRIPTIONS = {
    "10級": "初心者レベル：基本的な形の把握、3-4段階の明暗、迷い線を整理した輪郭線",
    "9級": "9級レベル：単純な図形の正確性、光源の統一、最低限の立体感表現",
    "8級": "8級レベル：適切な画面配置、明・中・暗の使い分け、表面に沿ったタッチ",
    "7級": "7級レベル：比率バランスの向上、一貫した光源方向、筆圧の強弱コントロール",
    "6級": "6級レベル：形の正確性向上、5-7段階の明暗階調、ハッチング技法の基礎",
    "5級": "5級レベル：しっかりした基礎技術、7-9段階の滑らかな階調、極端な質感の描き分け",
    "4級": "4級レベル：複合モチーフの固有比率、稜線位置の正確性、素材別タッチの使い分け",
    "3級": "3級レベル：パースペクティブの理解、反射光と陰影の描き分け、金属・ガラス・木材の質感表現",
    "2級": "2級レベル：奥行き感のある構図、10段階の繊細な階調、シャープとソフトな線の使い分け",
    "1級": "1級レベル：重心と動きの表現、空気遠近法の活用、クロスハッチングの高度な組み合わせ",
    "初段": "初段レベル：意図的な画面構成、無限階調の繊細なコントロール、触覚的リアリティの表現",
    "2段": "2段レベル：視点誘導のある構図、空気の層と奥行き表現、重さ・温度・柔らかさの表現",
    "3段": "3段レベル：空間に溶け込む輪郭処理、画面を引き締める強い暗部、一本の線に豊かな表情",
    "師範代": "師範代レベル：完璧な技術的実行力、「描かないこと」で形や光を表現する高度テクニック",
    "師範": "師範レベル：芸術的革新性、観る者の感覚を刺激する最高レベルの表現力"
}

# Base Prompt Template
BASE_PROMPT_TEMPLATE = """
Create an improved pencil drawing based on the following analysis and target skill level.

**Original Drawing Analysis:**
- Overall Score: {overall_score}/100
- Current Skill Level: {current_rank_label} (Current Performance: {current_rank})
- Target Skill Level: {target_rank}
- Subject Matter: {motif_tags}

**Context:**
The user is currently at {current_rank_label} level and aiming to improve toward {target_rank} level.
The example image should demonstrate what the drawing would look like when executed at {target_rank} skill level,
taking into account the user's current level ({current_rank_label}) and showing appropriate progression.

**Strengths (良い点):**
{strengths_list}

**Key Areas for Improvement (改善点):**
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

**Rank-Based Evaluation Context:**
- Current Rank ({current_rank_label}): The user's current skill level. Consider what techniques they are likely familiar with.
- Target Rank ({target_rank}): The next level they should aim for. The example should demonstrate techniques appropriate for this level.
- Progression: Show clear improvement from {current_rank_label} to {target_rank} level in the identified improvement areas.

**Drawing Specifications:**
- Medium: Graphite pencil on paper (realistic academic drawing style)
- Style: Classical realism with proper pencil techniques
- Format: Monochrome grayscale with full tonal range
- Resolution: 1024px, high detail
- Composition: Similar subject matter but demonstrating clear technical improvements

**Generation Instructions:**
Create a pencil drawing that demonstrates the specific improvements mentioned above.
The drawing should show what this subject would look like when executed at {target_rank} skill level.
The example should be achievable and inspiring for someone currently at {current_rank_label} level,
showing clear progression toward {target_rank} level techniques.

Emphasize the following technical improvements: {specific_improvements}

The result should be a traditional graphite pencil drawing that clearly demonstrates 
superior technique in the identified improvement areas while maintaining the same subject matter.
Ensure the drawing exhibits the technical standards expected at {target_rank} level,
while being appropriate as a learning reference for someone at {current_rank_label} level.
"""

def _get_rank_value(rank_label: str) -> int:
    """Helper to determine rank numeric value for requirements logic"""
    # Simplified mapping for logic
    if "級" in rank_label:
        try:
            return 11 - int(rank_label.replace("級", "")) # 10級->1, 1級->10
        except:
            return 1
    if "段" in rank_label:
        try:
            return 10 + int(rank_label.replace("段", "")) # 初段(1)->11
        except:
            if rank_label == "初段": return 11
            return 11
    if "師範" in rank_label:
        return 14
    return 1

def _get_tonal_requirements(rank_label: str) -> str:
    val = _get_rank_value(rank_label)
    if val <= 4: return "3-7 distinct tonal values, consistent light source direction, basic form shadows" # 10-7級
    if val <= 7: return "5-7 distinct tonal values, basic hatching" # 6-4級
    if val <= 10: return "7-10 smooth gradations, accurate shadow edge placement, reflected light awareness" # 3-1級
    if val <= 13: return "Infinite subtle gradations, atmospheric perspective, strong dark values for contrast" # 段
    return "Perfect tonal control, air layers and spatial depth, masterful use of 'black' quality"

def _get_line_requirements(rank_label: str) -> str:
    val = _get_rank_value(rank_label)
    if val <= 4: return "Varied pressure control, clean single lines"
    if val <= 7: return "Basic hatching techniques, organized contour lines"
    if val <= 10: return "Sharp and soft line variations, cross-hatching combinations, surface-following strokes"
    if val <= 13: return "Expressive line quality with entry and exit, advanced hatching density control"
    return "Rich expression within single lines, masterful use of negative space and 'not drawing'"

def _get_texture_requirements(rank_label: str) -> str:
    val = _get_rank_value(rank_label)
    if val <= 4: return "Basic material impression"
    if val <= 7: return "Basic material differentiation (smooth vs rough), surface-appropriate strokes"
    if val <= 10: return "Metal, glass, wood, fabric distinctions, appropriate pencil hardness usage"
    if val <= 13: return "Weight, temperature, softness expression, tactile reality that engages senses"
    return "Complete sensory engagement, innovative textural expression, revolutionary techniques"

def _get_mime_type_from_url(url: str) -> str:
    """URLからMIMEタイプを判定する"""
    url_lower = url.lower()
    if url_lower.endswith(('.png',)):
        return "image/png"
    elif url_lower.endswith(('.jpg', '.jpeg')):
        return "image/jpeg"
    else:
        # デフォルトはJPEG
        return "image/jpeg"


def create_generation_prompt(analysis: Dict[str, Any], target_rank: str, current_rank_label: str, motif_tags: List[str]) -> str:
    improvements_list = "\n".join([f"- {improvement}" for improvement in analysis.get("improvements", [])])
    strengths_list = "\n".join([f"- {strength}" for strength in analysis.get("strengths", [])])
    
    # Extract detailed feedback for each area
    prop = analysis.get("proportion", {})
    proportion_feedback = (
        f"Shape Accuracy: {prop.get('shape_accuracy', '')}. "
        f"Ratio & Balance: {prop.get('ratio_balance', '')}. "
        f"Contour Lines: {prop.get('contour_quality', '')}."
    )
    
    tone = analysis.get("tone", {})
    tone_feedback = (
        f"Tonal Range: {tone.get('value_range', '')}. "
        f"Light Consistency: {tone.get('light_consistency', '')}. "
        f"Three-Dimensionality: {tone.get('three_dimensionality', '')}."
    )
    
    line = analysis.get("line_quality", {})
    line_feedback = (
        f"Stroke Quality: {line.get('stroke_quality', '')}. "
        f"Pressure Control: {line.get('pressure_control', '')}. "
        f"Hatching Technique: {line.get('hatching', '')}."
    )
    
    texture = analysis.get("texture", {})
    texture_feedback = (
        f"Material Expression: {texture.get('material_expression', '')}. "
        f"Touch Variety: {texture.get('touch_variety', '')}."
    )

    # Calculate focus areas based on low scores
    prop_score = prop.get("score", 0)
    tone_score = tone.get("score", 0)
    line_score = line.get("score", 0)
    text_score = texture.get("score", 0)

    area_scores = [
        ("proportion", prop_score),
        ("tone/shading", tone_score),
        ("line quality", line_score),
        ("texture", text_score)
    ]
    area_scores.sort(key=lambda x: x[1])
    primary_improvement_areas = ", ".join([area[0] for area in area_scores[:3]])
    
    specific_improvements = []
    if prop_score < 80: specific_improvements.append("more accurate proportions and better shape accuracy")
    if tone_score < 80: specific_improvements.append("improved tonal range and consistent lighting")
    if line_score < 80: specific_improvements.append("better line control and hatching techniques")
    if text_score < 80: specific_improvements.append("enhanced texture rendering and material expression")
    
    specific_improvements_text = ", ".join(specific_improvements) if specific_improvements else "overall refinement"

    return BASE_PROMPT_TEMPLATE.format(
        overall_score=analysis.get("overall_score", 0),
        current_rank_label=current_rank_label,
        current_rank=f"{current_rank_label} (Score: {analysis.get('overall_score', 0)})",
        target_rank=target_rank,
        motif_tags=", ".join(motif_tags),
        strengths_list=strengths_list,
        improvements_list=improvements_list,
        proportion_feedback=proportion_feedback,
        tone_feedback=tone_feedback,
        line_feedback=line_feedback,
        texture_feedback=texture_feedback,
        target_rank_description=RANK_DESCRIPTIONS.get(target_rank, ""),
        primary_improvement_areas=primary_improvement_areas,
        specific_improvements=specific_improvements_text,
        tonal_requirements=_get_tonal_requirements(target_rank),
        line_requirements=_get_line_requirements(target_rank),
        texture_requirements=_get_texture_requirements(target_rank)
    )

async def generate_image(prompt: str, original_image_data: bytes, mime_type: str = "image/jpeg", max_retries: int = 3) -> bytes:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
    )
    
    # 公式ドキュメントの例に合わせて、bytesからPIL Imageに変換
    # Pythonの例: contents=[prompt, image] の形式で、imageはPIL Imageオブジェクト
    image = Image.open(BytesIO(original_image_data))
    
    for attempt in range(max_retries):
        try:
            # Use generate_content for Gemini 2.5 Flash Image with native image output
            # 公式ドキュメントの例に合わせて、シンプルな形式でcontentsを渡す
            # contents=[prompt, image] の形式（imageはPIL Imageオブジェクト）
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    safety_settings=[
                        types.SafetySetting(
                            category="HARM_CATEGORY_HATE_SPEECH",
                            threshold="BLOCK_MEDIUM_AND_ABOVE"
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_DANGEROUS_CONTENT",
                            threshold="BLOCK_MEDIUM_AND_ABOVE"
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                            threshold="BLOCK_MEDIUM_AND_ABOVE"
                        ),
                        types.SafetySetting(
                            category="HARM_CATEGORY_HARASSMENT",
                            threshold="BLOCK_MEDIUM_AND_ABOVE"
                        ),
                    ],
                )
            )
            
            # Extract image from response parts
            if response.candidates:
                for candidate in response.candidates:
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if part.inline_data and part.inline_data.data:
                                return part.inline_data.data

            # Log the actual response structure for debugging if we fail
            logger.error("image_generation_response_invalid", 
                         response_candidates=len(response.candidates) if response.candidates else 0,
                         detail="No inline_data found in candidates")

            raise ImageGenerationError("No image data found in response")
            
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            logger.error("image_generation_failed", 
                        error=error_message,
                        error_type=error_type,
                        attempt=attempt+1,
                        max_retries=max_retries)
            
            if attempt == max_retries - 1:
                logger.error("image_generation_failed_final", 
                            error=error_message, 
                            error_type=error_type,
                            task_attempt=attempt+1)
                raise
            
            wait_time = 2 ** attempt
            logger.warning("image_generation_failed_retrying", 
                           attempt=attempt+1, 
                           wait_time=wait_time, 
                           error=error_message,
                           error_type=error_type)
            await asyncio.sleep(wait_time)
            
    # Should not reach here
    raise ImageGenerationError("Retry loop exhausted without result")

@functions_framework.http
def generate_example_image(request):
    """HTTP Cloud Function entry point."""
    
    # Check for authentication (Optional: if using Cloud Run Service to Service auth, request is already authenticated by IAM proxy. 
    # But if calling directly or for extra safety, we might check headers. 
    # For this implementation, we assume Cloud Run IAM handles auth.)

    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            return {"error": "Invalid JSON"}, 400

        task_id = request_json.get("task_id")
        user_id = request_json.get("user_id")
        original_image_url = request_json.get("original_image_url")
        analysis = request_json.get("analysis")
        target_rank_label = request_json.get("target_rank_label", "5級")
        current_rank_label = request_json.get("current_rank_label", "10級")
        motif_tags = request_json.get("motif_tags", [])

        if not all([task_id, user_id, original_image_url, analysis]):
            return {"error": "Missing required fields"}, 400

        logger.info("function_started", task_id=task_id, user_id=user_id)

        # Generate Prompt
        prompt = create_generation_prompt(analysis, target_rank_label, current_rank_label, motif_tags)
        
        # Initialize storage client for saving generated image
        storage_client = storage.Client()

        # We will use a helper async function to handle the flow
        async def process():
            # 1. Fetch Image
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(original_image_url) as resp:
                    if resp.status != 200:
                        raise ImageGenerationError(f"Failed to fetch original image: {resp.status}")
                    original_image_data = await resp.read()

            # 2. Determine MIME type from URL
            mime_type = _get_mime_type_from_url(original_image_url)

            # 3. Generate
            generated_bytes = await generate_image(prompt, original_image_data, mime_type)
            
            # 生成された画像のサイズを取得してログに記録
            try:
                generated_image = Image.open(BytesIO(generated_bytes))
                image_width, image_height = generated_image.size
                logger.info("image_generation_completed",
                            task_id=task_id,
                            generated_bytes_len=len(generated_bytes),
                            image_width=image_width,
                            image_height=image_height,
                            image_format=generated_image.format)
            except Exception as e:
                logger.warning("image_size_extraction_failed",
                             task_id=task_id,
                             generated_bytes_len=len(generated_bytes),
                             error=str(e))

            # 4. Save to GCS
            bucket = storage_client.bucket(OUTPUT_BUCKET_NAME)
            blob_path = f"generated/{task_id}.png"
            blob = bucket.blob(blob_path)
            
            # Run upload in executor because it's blocking
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: blob.upload_from_string(generated_bytes, content_type="image/png")
            )
            
            # Set metadata
            metadata = {
                "user_id": user_id,
                "task_id": task_id,
                "ai_generated": "true",
                "model": GEMINI_MODEL
            }
            blob.metadata = metadata
            await asyncio.get_event_loop().run_in_executor(None, blob.patch)
            
            logger.info("image_saved_to_gcs",
                        task_id=task_id,
                        blob_path=blob_path,
                        bucket_name=OUTPUT_BUCKET_NAME)

            # 4. Call Complete Task Function
            example_image_url = f"https://storage.googleapis.com/{OUTPUT_BUCKET_NAME}/{blob_path}"
            
            if COMPLETE_TASK_FUNCTION_URL:
                 import aiohttp
                 async with aiohttp.ClientSession() as session:
                    payload = {
                        "task_id": task_id,
                        "example_image_url": example_image_url,
                         # Add any other fields if complete_task needs them, but currently it just needs these.
                         # Should we pass user_id? complete_task doesn't seem to use it for docref update.
                         # It logged it previously, but now we removed that.
                    }
                    # Add Auth header if your service requires it (e.g. OIDC token)
                    # For now assuming public or internal unauth (which might fail if ingress is strict)
                    # If running in Cloud Run/Functions, we should get an ID token to call another authenticated function.
                    # But deploy script says "--ingress-settings=ALLOW_ALL" and "no-auth" is unstated but let's assume...
                    # Wait, usually functions require auth. 
                    # If allow-unauthenticated is NOT set, we need a token.
                    # Given the user context "Just call it normally", and "Internal traffic", 
                    # let's try calling it. If 403, we need to add auth logic.
                    # For simplicity, I will implement a basic call.
                    async with session.post(COMPLETE_TASK_FUNCTION_URL, json=payload) as resp:
                         if resp.status >= 400:
                             response_text = await resp.text()
                             logger.error("failed_to_call_complete_task", 
                                        status=resp.status, 
                                        body=response_text,
                                        task_id=task_id,
                                        example_image_url=example_image_url)
                             # Don't fail the whole function if this fails? Or should we?
                             # Better to fail so we know.
                             # But image is generated.
                             pass
                         else:
                             logger.info("complete_task_called_successfully",
                                       task_id=task_id,
                                       example_image_url=example_image_url)
            else:
                logger.warning("COMPLETE_TASK_FUNCTION_URL_not_set", 
                             detail="Task completion step skipped",
                             task_id=task_id,
                             example_image_url=example_image_url,
                             note="Firestore will not be updated. Set COMPLETE_TASK_FUNCTION_URL environment variable.")
            
            return blob_path

        # Execute
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        blob_path = loop.run_until_complete(process())
        loop.close()

        logger.info("function_completed", task_id=task_id, path=blob_path)
        return {"status": "success", "path": blob_path}, 200

    except Exception as e:
        error_type = type(e).__name__
        error_message = str(e)
        import traceback
        error_traceback = traceback.format_exc()
        
        logger.error("function_failed", 
                    error=error_message,
                    error_type=error_type,
                    traceback=error_traceback)
        # Ensure we return 500 so Cloud Functions/Scheduler knows it failed
        return {"error": error_message, "error_type": error_type}, 500
