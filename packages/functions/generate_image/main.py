import os
import json
import uuid
import structlog
import asyncio
import functions_framework
from typing import List, Optional, Dict, Any
from io import BytesIO
from urllib.parse import urlparse
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
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-pro-image-preview")
# gemini-2.5-flash-imageはグローバルエンドポイントで利用可能
LOCATION = "global"

class ImageGenerationError(Exception):
    pass

class InvalidImageURLError(Exception):
    """URL検証エラー"""
    pass

# Base Prompt Template - Improvement focused, no rank information
BASE_PROMPT_TEMPLATE = """
Create an improved pencil drawing that demonstrates how to fix the specific improvement points identified in the analysis.

**Original Drawing Analysis:**
- Overall Score: {overall_score}/100
- Subject Matter: {motif_tags}

**Strengths to Preserve (良い点):**
{strengths_list}

**Key Areas for Improvement (改善点) - FOCUS ON CORRECTING THESE:**
{improvements_list}

**Detailed Technical Feedback:**
- **Proportion (形の正確さ)**: {proportion_feedback}
- **Tone/Shading (陰影)**: {tone_feedback}
- **Line Quality (線の質)**: {line_feedback}
- **Texture (質感表現)**: {texture_feedback}

**Primary Focus Areas:**
Focus especially on correcting: {primary_improvement_areas}

**Drawing Specifications:**
- Medium: Graphite pencil on paper (realistic academic drawing style)
- Style: Classical realism with proper pencil techniques
- Format: Monochrome grayscale with full tonal range
- Resolution: 1024px, high detail
- Composition: Same subject matter with the improvement points corrected

**Generation Instructions:**
Create a pencil drawing that demonstrates how to CORRECT the specific improvement points mentioned above.
The drawing should:
1. Preserve the strengths already present in the original drawing
2. Show clear corrections for each improvement point listed
3. Demonstrate what the drawing would look like once the identified issues are fixed

Specific corrections needed: {specific_improvements}

The result should be a traditional graphite pencil drawing that clearly shows
how the identified improvement areas should be corrected, while maintaining
the subject matter and good elements from the original.
"""

# Annotated Image Instruction - Added when annotated image is provided
ANNOTATED_IMAGE_INSTRUCTION = """
**IMPORTANT - Annotated Reference Image:**
A second image is provided showing the original drawing with colored bounding boxes and numbered circles.
These annotations highlight specific areas that need improvement:
- Each numbered circle corresponds to an improvement point listed above
- Focus especially on correcting the issues in the areas marked by bounding boxes
- Use the annotations as a visual guide to understand which parts of the drawing need the most attention

The generated example should show clear improvements in all annotated areas.
"""

def _validate_image_url(url: str) -> None:
    """
    URLを検証して、セキュリティリスクを防ぐ
    
    Raises:
        InvalidImageURLError: URLが無効な場合
    """
    try:
        parsed = urlparse(url)
        
        # HTTPSスキームのみ許可
        if parsed.scheme != 'https':
            raise InvalidImageURLError(f"Only HTTPS URLs are allowed, got: {parsed.scheme}")
        
        # ホスト名の検証
        hostname = parsed.hostname
        if not hostname:
            raise InvalidImageURLError("Missing hostname in URL")
        
        # 内部GCPエンドポイントやプライベートIPをブロック
        blocked_hosts = [
            'metadata.google.internal',
            'metadata',
            '169.254.169.254',  # GCPメタデータサーバーのIP
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
        ]
        
        hostname_lower = hostname.lower()
        for blocked in blocked_hosts:
            if blocked in hostname_lower:
                raise InvalidImageURLError(f"Blocked hostname: {hostname}")
        
        # プライベートIPレンジのチェック（簡易版）
        if hostname.startswith('10.') or hostname.startswith('172.16.') or hostname.startswith('192.168.'):
            raise InvalidImageURLError(f"Private IP range not allowed: {hostname}")
            
    except Exception as e:
        if isinstance(e, InvalidImageURLError):
            raise
        raise InvalidImageURLError(f"Invalid URL format: {str(e)}")

def _get_mime_type_from_url(url: str) -> str:
    """URLからMIMEタイプを判定する"""
    url_lower = url.lower()
    if url_lower.endswith('.png'):
        return "image/png"
    elif url_lower.endswith(('.jpg', '.jpeg')):
        return "image/jpeg"
    else:
        # デフォルトはJPEG
        return "image/jpeg"


def create_generation_prompt(analysis: Dict[str, Any], motif_tags: List[str], has_annotated_image: bool = False) -> str:
    """改善点にフォーカスした画像生成プロンプトを作成"""
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

    prompt = BASE_PROMPT_TEMPLATE.format(
        overall_score=analysis.get("overall_score", 0),
        motif_tags=", ".join(motif_tags),
        strengths_list=strengths_list,
        improvements_list=improvements_list,
        proportion_feedback=proportion_feedback,
        tone_feedback=tone_feedback,
        line_feedback=line_feedback,
        texture_feedback=texture_feedback,
        primary_improvement_areas=primary_improvement_areas,
        specific_improvements=specific_improvements_text,
    )
    
    # Add annotated image instruction if annotated image is provided
    if has_annotated_image:
        prompt += "\n\n" + ANNOTATED_IMAGE_INSTRUCTION
    
    return prompt


async def generate_image(prompt: str, original_image_data: bytes, annotated_image_data: Optional[bytes] = None, mime_type: str = "image/jpeg", max_retries: int = 3) -> bytes:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
    )
    
    # 公式ドキュメントの例に合わせて、bytesからPIL Imageに変換
    # Pythonの例: contents=[prompt, image] の形式で、imageはPIL Imageオブジェクト
    # mime_typeは現在の実装では使用されないが、将来の拡張のために保持
    with Image.open(BytesIO(original_image_data)) as original_image:
        # Build contents list
        contents: list = [prompt, original_image]
        
        # Add annotated image if provided
        annotated_image = None
        if annotated_image_data:
            try:
                annotated_image = Image.open(BytesIO(annotated_image_data))
                contents.append(annotated_image)
                logger.info("annotated_image_included_in_generation")
            except Exception as e:
                logger.warning("failed_to_open_annotated_image", error=str(e))
        
        try:
            for attempt in range(max_retries):
                try:
                    # Use generate_content for Gemini 2.5 Flash Image with native image output
                    # 公式ドキュメントの例に合わせて、シンプルな形式でcontentsを渡す
                    # contents=[prompt, original_image] or [prompt, original_image, annotated_image]
                    response = client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=contents,
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
        finally:
            # Close annotated image if it was opened
            if annotated_image:
                annotated_image.close()
                    
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
        annotated_image_url = request_json.get("annotated_image_url")  # Optional
        analysis = request_json.get("analysis")
        motif_tags = request_json.get("motif_tags", [])

        if not all([task_id, user_id, original_image_url, analysis]):
            return {"error": "Missing required fields"}, 400

        logger.info("function_started", task_id=task_id, user_id=user_id, has_annotated_image=bool(annotated_image_url))

        # Generate Prompt (improvement-focused, no rank information)
        has_annotated_image = bool(annotated_image_url)
        prompt = create_generation_prompt(analysis, motif_tags, has_annotated_image)
        
        # Initialize storage client for saving generated image
        storage_client = storage.Client()

        # We will use a helper async function to handle the flow
        async def process():
            # 0. Validate URL (security check)
            _validate_image_url(original_image_url)
            
            # 1. Fetch Image with timeout and size limits
            import aiohttp
            # タイムアウト設定: 10秒
            timeout = aiohttp.ClientTimeout(total=10)
            # サイズ制限: 10MB
            max_size = 10 * 1024 * 1024  # 10MB
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Fetch original image
                async with session.get(original_image_url) as resp:
                    if resp.status != 200:
                        raise ImageGenerationError(f"Failed to fetch original image: {resp.status}")
                    
                    # サイズ制限チェック
                    content_length = resp.headers.get('Content-Length')
                    if content_length and int(content_length) > max_size:
                        raise ImageGenerationError(f"Image size exceeds limit: {content_length} bytes")
                    
                    # チャンクごとに読み込んでサイズをチェック
                    original_image_data = b''
                    async for chunk in resp.content.iter_chunked(8192):
                        original_image_data += chunk
                        if len(original_image_data) > max_size:
                            raise ImageGenerationError(f"Image size exceeds limit: {len(original_image_data)} bytes")
                
                # Fetch annotated image if provided
                annotated_image_data: bytes | None = None
                if annotated_image_url:
                    try:
                        _validate_image_url(annotated_image_url)
                        async with session.get(annotated_image_url) as annot_resp:
                            if annot_resp.status == 200:
                                annotated_image_data = b''
                                async for chunk in annot_resp.content.iter_chunked(8192):
                                    annotated_image_data += chunk
                                    if len(annotated_image_data) > max_size:
                                        logger.warning("annotated_image_too_large", task_id=task_id)
                                        annotated_image_data = None
                                        break
                                if annotated_image_data:
                                    logger.info("annotated_image_fetched", task_id=task_id, size=len(annotated_image_data))
                            else:
                                logger.warning("failed_to_fetch_annotated_image", task_id=task_id, status=annot_resp.status)
                    except Exception as e:
                        logger.warning("annotated_image_fetch_error", task_id=task_id, error=str(e))

            # 2. Determine MIME type from URL
            mime_type = _get_mime_type_from_url(original_image_url)

            # 3. Generate (with annotated image if available)
            generated_bytes = await generate_image(prompt, original_image_data, annotated_image_data, mime_type)
            
            # 生成された画像のサイズを取得してログに記録
            try:
                with Image.open(BytesIO(generated_bytes)) as generated_image:
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
                import google.auth.transport.requests
                import google.oauth2.id_token
                
                # IDトークンを取得してサービス間認証を行う
                try:
                    auth_req = google.auth.transport.requests.Request()
                    target_audience = COMPLETE_TASK_FUNCTION_URL
                    
                    # 同期処理なのでExecutorで実行
                    id_token = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: google.oauth2.id_token.fetch_id_token(auth_req, target_audience)
                    )
                    
                    headers = {
                        "Authorization": f"Bearer {id_token}",
                        "Content-Type": "application/json"
                    }
                except Exception as e:
                    logger.error("failed_to_get_id_token",
                                error=str(e),
                                task_id=task_id,
                                complete_task_url=COMPLETE_TASK_FUNCTION_URL)
                    # 認証トークンの取得に失敗した場合でも続行（後方互換性のため）
                    # ただし、エラーを記録して警告
                    headers = {"Content-Type": "application/json"}
                
                async with aiohttp.ClientSession() as session:
                    payload = {
                        "task_id": task_id,
                        "example_image_url": example_image_url,
                    }
                    async with session.post(COMPLETE_TASK_FUNCTION_URL, json=payload, headers=headers) as resp:
                        if resp.status >= 400:
                            response_text = await resp.text()
                            logger.error("failed_to_call_complete_task", 
                                        status=resp.status, 
                                        body=response_text,
                                        task_id=task_id,
                                        example_image_url=example_image_url)
                            # タスク完了の呼び出しに失敗した場合は、関数全体を失敗させる
                            # これにより、状態の一貫性が保たれる
                            raise ImageGenerationError(f"Failed to call complete_task: {resp.status} - {response_text}")
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

    except InvalidImageURLError as e:
        # URL検証エラーは400 Bad Requestとして返す
        error_message = str(e)
        logger.error("invalid_image_url", 
                    error=error_message,
                    original_image_url=request_json.get("original_image_url") if request_json else None)
        return {"error": f"Invalid image URL: {error_message}", "error_type": "InvalidImageURLError"}, 400
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
