import os
import structlog
import asyncio
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlparse

import aiohttp
import functions_framework
from google import genai
from google.genai import types
from google.cloud import firestore
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

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
OUTPUT_BUCKET_NAME = os.environ.get("OUTPUT_BUCKET_NAME")
# Gemini 3モデルはグローバルエンドポイントで利用可能
LOCATION = "global"
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")


class AnnotationGenerationError(Exception):
    pass


class InvalidImageURLError(Exception):
    """URL検証エラー"""


def _validate_image_url(url: str) -> None:
    try:
        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise InvalidImageURLError(f"Only HTTPS URLs are allowed, got: {parsed.scheme}")

        hostname = parsed.hostname
        if not hostname:
            raise InvalidImageURLError("Missing hostname in URL")

        blocked_hosts = [
            "metadata.google.internal",
            "metadata",
            "169.254.169.254",
            "localhost",
            "127.0.0.1",
            "0.0.0.0",
        ]

        hostname_lower = hostname.lower()
        for blocked in blocked_hosts:
            if blocked in hostname_lower:
                raise InvalidImageURLError(f"Blocked hostname: {hostname}")

        if hostname.startswith("10.") or hostname.startswith("172.16.") or hostname.startswith("192.168."):
            raise InvalidImageURLError(f"Private IP range not allowed: {hostname}")
    except Exception as e:
        if isinstance(e, InvalidImageURLError):
            raise
        raise InvalidImageURLError(f"Invalid URL format: {str(e)}")


def _get_mime_type_from_url(url: str) -> str:
    url_lower = url.lower()
    if url_lower.endswith(".png"):
        return "image/png"
    if url_lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    return "image/jpeg"


def _build_annotation_prompt(
    analysis: Dict[str, Any],
    current_rank_label: str,
    motif_tags: List[str],
) -> str:
    improvements = analysis.get("improvements", [])
    # 番号付きリストに変更（フロントエンドの表示と一致させる）
    improvements_list = "\n".join([f"{i + 1}. {item}" for i, item in enumerate(improvements[:5])])

    prop = analysis.get("proportion", {})
    tone = analysis.get("tone", {})
    line = analysis.get("line_quality", {})
    texture = analysis.get("texture", {})

    return f"""
You are an art instructor. Annotate the drawing to highlight improvement points.
Use code execution with Python PIL/Pillow to draw annotations directly on the image.

CRITICAL REQUIREMENTS:
1. Draw a BOUNDING BOX (rectangle outline) around each area that needs improvement
2. Place a NUMBERED CIRCLE next to each bounding box
3. The circle must contain the NUMBER (1, 2, 3...) in WHITE text
4. USE A DIFFERENT COLOR FOR EACH NUMBER to make them visually distinct

COLOR PALETTE (use these colors for each number):
- Number 1: Orange (RGB: 245, 158, 11)
- Number 2: Blue (RGB: 59, 130, 246)
- Number 3: Green (RGB: 34, 197, 94)
- Number 4: Purple (RGB: 168, 85, 247)
- Number 5: Red (RGB: 239, 68, 68)

EXACT SPECIFICATIONS:
- Bounding box: Colored outline matching the number color, line width 3-4px
- Number circle: Filled circle with the same color, radius ~30px
- Number text: WHITE color, bold, font size 32-40px, centered in the circle
- Place the numbered circle at the top-left corner of each bounding box

Context:
- Current rank: {current_rank_label}
- Motif: {", ".join(motif_tags)}

Improvements (draw these numbers with their assigned colors):
{improvements_list}

Category notes:
- Proportion: {prop.get("shape_accuracy", "")}, {prop.get("ratio_balance", "")}
- Tone: {tone.get("value_range", "")}, {tone.get("light_consistency", "")}
- Line: {line.get("stroke_quality", "")}, {line.get("pressure_control", "")}
- Texture: {texture.get("material_expression", "")}, {texture.get("touch_variety", "")}

EXAMPLE CODE STRUCTURE (you must adapt coordinates based on actual image analysis):
```python
from PIL import Image, ImageDraw, ImageFont
import io

# Load image
img = Image.open(io.BytesIO(image_bytes))
draw = ImageDraw.Draw(img)

# Color palette for each number
colors = [
    (245, 158, 11),   # 1: Orange
    (59, 130, 246),   # 2: Blue
    (34, 197, 94),    # 3: Green
    (168, 85, 247),   # 4: Purple
    (239, 68, 68),    # 5: Red
]
white = (255, 255, 255)

# For each improvement area (example for number 1):
num = 1
color = colors[num - 1]

# 1. Draw bounding box around the area
draw.rectangle([x1, y1, x2, y2], outline=color, width=4)

# 2. Draw numbered circle at top-left of box
circle_x, circle_y = x1 - 20, y1 - 20
draw.ellipse([circle_x - 28, circle_y - 28, circle_x + 28, circle_y + 28], fill=color)

# 3. Draw the number in white
font = ImageFont.load_default(size=36)
draw.text((circle_x, circle_y), str(num), fill=white, font=font, anchor="mm")
```

OUTPUT: The final annotated image with colored bounding boxes and numbered circles.
""".strip()



async def _generate_annotated_image(prompt: str, image_data: bytes, mime_type: str) -> bytes:
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION,
    )

    image_part = types.Part.from_bytes(data=image_data, mime_type=mime_type)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[image_part, types.Part.from_text(text=prompt)],
        config=types.GenerateContentConfig(
            tools=[types.Tool(code_execution=types.ToolCodeExecution)],
        ),
    )

    if response.candidates:
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.inline_data and part.inline_data.data:
                        return part.inline_data.data

    logger.error(
        "annotation_generation_response_invalid",
        response_candidates=len(response.candidates) if response.candidates else 0,
        detail="No inline_data found in candidates",
    )
    raise AnnotationGenerationError("No annotated image data found in response")


@functions_framework.http
def annotate_image(request):
    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            return {"error": "Invalid JSON"}, 400

        task_id = request_json.get("task_id")
        user_id = request_json.get("user_id")
        original_image_url = request_json.get("original_image_url")
        analysis = request_json.get("analysis")
        current_rank_label = request_json.get("current_rank_label", "10級")
        motif_tags = request_json.get("motif_tags", [])

        if not all([task_id, user_id, original_image_url, analysis]):
            return {"error": "Missing required fields"}, 400

        logger.info("annotate_function_started", task_id=task_id, user_id=user_id)

        storage_client = storage.Client()
        firestore_client = firestore.Client()

        async def process():
            _validate_image_url(original_image_url)

            timeout = aiohttp.ClientTimeout(total=10)
            max_size = 10 * 1024 * 1024
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(original_image_url) as resp:
                    if resp.status != 200:
                        raise AnnotationGenerationError(
                            f"Failed to fetch original image: {resp.status}"
                        )

                    content_length = resp.headers.get("Content-Length")
                    if content_length and int(content_length) > max_size:
                        raise AnnotationGenerationError(
                            f"Image size exceeds limit: {content_length} bytes"
                        )

                    original_image_data = b""
                    async for chunk in resp.content.iter_chunked(8192):
                        original_image_data += chunk
                        if len(original_image_data) > max_size:
                            raise AnnotationGenerationError(
                                f"Image size exceeds limit: {len(original_image_data)} bytes"
                            )

            mime_type = _get_mime_type_from_url(original_image_url)
            prompt = _build_annotation_prompt(analysis, current_rank_label, motif_tags)
            annotated_bytes = await _generate_annotated_image(prompt, original_image_data, mime_type)

            bucket = storage_client.bucket(OUTPUT_BUCKET_NAME)
            blob_path = f"annotated/{task_id}.png"
            blob = bucket.blob(blob_path)

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: blob.upload_from_string(annotated_bytes, content_type="image/png"),
            )

            blob.metadata = {
                "user_id": user_id,
                "task_id": task_id,
                "ai_generated": "true",
                "model": GEMINI_MODEL,
            }
            await asyncio.get_event_loop().run_in_executor(None, blob.patch)

            annotated_image_url = f"https://storage.googleapis.com/{OUTPUT_BUCKET_NAME}/{blob_path}"
            doc_ref = firestore_client.collection("review_tasks").document(task_id)
            doc_ref.update(
                {
                    "annotated_image_url": annotated_image_url,
                    "updated_at": datetime.now(),
                }
            )

            logger.info("annotation_saved", task_id=task_id, blob_path=blob_path)
            return blob_path, annotated_image_url

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        blob_path, annotated_image_url = loop.run_until_complete(process())
        loop.close()

        return {"status": "success", "path": blob_path, "annotated_image_url": annotated_image_url}, 200
    except InvalidImageURLError as e:
        error_message = str(e)
        logger.error("invalid_image_url", error=error_message)
        return {"error": f"Invalid image URL: {error_message}"}, 400
    except Exception as e:
        logger.error("annotation_function_failed", error=str(e))
        return {"error": str(e)}, 500
