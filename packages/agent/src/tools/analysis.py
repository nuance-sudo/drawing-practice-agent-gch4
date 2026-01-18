"""デッサン分析ツール

ADKエージェントが使用するツール関数を定義。
"""

import structlog
from google import genai
from google.genai import types

from src.config import settings
from src.models.feedback import DessinAnalysis
from src.prompts.coaching import (
    DESSIN_ANALYSIS_SYSTEM_PROMPT,
    DESSIN_ANALYSIS_USER_PROMPT,
)

logger = structlog.get_logger()


def analyze_dessin_image(image_url: str) -> dict[str, object]:
    """デッサン画像を分析し、フィードバックを返す

    鉛筆デッサン画像を分析し、プロポーション、陰影、質感、線の質の観点から
    評価とフィードバックを生成します。

    Args:
        image_url: 分析対象の画像URL（Cloud StorageまたはCloud CDN経由）

    Returns:
        分析結果を含む辞書。以下のキーを含む:
        - status: "success" または "error"
        - analysis: 分析結果（DessinAnalysis形式）
        - summary: フィードバックの要約
        - error_message: エラー時のメッセージ（エラー時のみ）

    Example:
        >>> result = analyze_dessin_image("https://storage.googleapis.com/.../drawing.jpg")
        >>> print(result["status"])
        "success"
        >>> print(result["analysis"]["overall_score"])
        75.5
    """
    logger.info("analyze_dessin_image_started", image_url=image_url)

    try:
        # Gemini クライアント初期化
        client = genai.Client(
            vertexai=True,
            project=settings.gcp_project_id,
            location=settings.gcp_region,
        )

        # 画像をURLから取得してPart作成
        image_part = types.Part.from_uri(
            file_uri=image_url,
            mime_type="image/jpeg",
        )

        # 分析リクエスト
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=DESSIN_ANALYSIS_USER_PROMPT),
                        image_part,
                    ],
                ),
            ],
            config=types.GenerateContentConfig(
                system_instruction=DESSIN_ANALYSIS_SYSTEM_PROMPT,
                max_output_tokens=settings.gemini_max_output_tokens,
                temperature=settings.gemini_temperature,
                response_mime_type="application/json",
                response_schema=DessinAnalysis,
            ),
        )

        # レスポンスをパース
        analysis = DessinAnalysis.model_validate_json(response.text)

        # 要約を作成
        summary = _create_summary(analysis)

        logger.info(
            "analyze_dessin_image_completed",
            overall_score=analysis.overall_score,
            tags=analysis.tags,
        )

        return {
            "status": "success",
            "analysis": analysis.model_dump(),
            "summary": summary,
        }

    except Exception as e:
        logger.error("analyze_dessin_image_failed", error=str(e), image_url=image_url)
        return {
            "status": "error",
            "error_message": f"デッサン分析に失敗しました: {e}",
        }


def _create_summary(analysis: DessinAnalysis) -> str:
    """分析結果から要約を作成

    Args:
        analysis: デッサン分析結果

    Returns:
        要約文字列
    """
    score = analysis.overall_score
    strengths = analysis.strengths[:2] if analysis.strengths else []
    improvements = analysis.improvements[:1] if analysis.improvements else []

    summary_parts = [f"総合スコア: {score}/100点"]

    if strengths:
        summary_parts.append(f"良い点: {', '.join(strengths)}")

    if improvements:
        summary_parts.append(f"改善ポイント: {improvements[0]}")

    return " | ".join(summary_parts)
