"""デッサン分析ツール

ADKエージェントが使用するツール関数を定義。
"""

import structlog
from google import genai
from google.genai import types
from pydantic import ValidationError

from src.config import settings
from src.models.feedback import DessinAnalysis
from src.prompts.coaching import (
    DESSIN_ANALYSIS_SYSTEM_PROMPT,
    DESSIN_ANALYSIS_USER_PROMPT,
)
from src.utils.validation import sanitize_for_storage, validate_image_url

logger = structlog.get_logger()


def _convert_to_gcs_uri(url: str) -> str:
    """HTTPS URLをGCS URI形式に変換

    https://storage.googleapis.com/bucket-name/path/to/file
    → gs://bucket-name/path/to/file

    Args:
        url: 検証済みのURL

    Returns:
        gs://形式のURI（変換不可の場合は元のURLをそのまま返す）
    """
    if url.startswith("gs://"):
        return url

    # storage.googleapis.com 形式の場合
    if url.startswith("https://storage.googleapis.com/"):
        # https://storage.googleapis.com/bucket/path → gs://bucket/path
        path = url.replace("https://storage.googleapis.com/", "")
        return f"gs://{path}"

    # storage.cloud.google.com 形式の場合
    if url.startswith("https://storage.cloud.google.com/"):
        path = url.replace("https://storage.cloud.google.com/", "")
        return f"gs://{path}"

    # 変換できない場合は元のURLを返す
    return url

def analyze_dessin_image(image_url: str, rank_label: str = "初学者") -> dict[str, object]:
    """デッサン画像を分析し、フィードバックを返す

    鉛筆デッサン画像を分析し、プロポーション、陰影、質感、線の質の観点から
    評価とフィードバックを生成します。

    Args:
        image_url: 分析対象の画像URL（Cloud StorageまたはCloud CDN経由）
        rank_label: ユーザーの現在のランク（例: "10級", "初段"）。プロンプトに含めることで、ランクに応じた評価を促す。
                    不正な値の場合はデフォルト（10級）にフォールバックします。

    Returns:
        分析結果を含む辞書。以下のキーを含む:
        - status: "success" または "error"
        - analysis: 分析結果（DessinAnalysis形式）
        - summary: フィードバックの要約
        - error_message: エラー時のメッセージ（エラー時のみ）

    Example:
        >>> result = analyze_dessin_image("https://storage.googleapis.com/.../drawing.jpg", "5級")
        >>> print(result["status"])
        "success"
        >>> print(result["analysis"]["overall_score"])
        75.5
    """
    logger.info("analyze_dessin_image_started", image_url=image_url[:100], rank=rank_label)

    # ランクのホワイトリスト検証（Prompt Injection対策）
    from src.models.rank import Rank
    valid_ranks = {r.label for r in Rank}
    if rank_label not in valid_ranks:
        logger.warning(
            "invalid_rank_label_fallback",
            original_label=rank_label,
            fallback=Rank.KYU_10.label
        )
        rank_label = Rank.KYU_10.label

    try:
        # URL検証（SSRF対策）
        validated_url = validate_image_url(image_url)

        # https:// URLをgs:// URIに変換（Vertex AIがGCSに直接アクセスできるように）
        gcs_uri = _convert_to_gcs_uri(validated_url)

        # Gemini クライアント初期化
        client = genai.Client(
            vertexai=True,
            project=settings.gcp_project_id,
            location=settings.gcp_region,
        )

        # MIMEタイプを判定
        mime_type = "image/jpeg"
        if gcs_uri.lower().endswith(".png"):
            mime_type = "image/png"

        # 画像をGCS URIから取得してPart作成
        image_part = types.Part.from_uri(
            file_uri=gcs_uri,
            mime_type=mime_type,
        )

        # プロンプトにランク情報を注入
        user_prompt = f"ユーザーの現在のランク: {rank_label}\n\n{DESSIN_ANALYSIS_USER_PROMPT}"

        # 分析リクエスト
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=user_prompt),
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

        # レスポンスをパース（Pydanticで構造検証）
        analysis = DessinAnalysis.model_validate_json(response.text)

        # スコア範囲の追加検証
        analysis = _validate_and_sanitize_analysis(analysis)

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

    except ValidationError as e:
        logger.error("analysis_validation_failed", error=str(e))
        return {
            "status": "error",
            "error_message": "分析結果の検証に失敗しました",
        }
    except Exception as e:
        logger.error("analyze_dessin_image_failed", error=str(e))
        return {
            "status": "error",
            "error_message": "デッサン分析に失敗しました",
        }


def _validate_and_sanitize_analysis(analysis: DessinAnalysis) -> DessinAnalysis:
    """分析結果を検証しサニタイズ

    Args:
        analysis: 分析結果

    Returns:
        検証・サニタイズ済みの分析結果
    """
    # スコアを0-100の範囲にクランプ
    analysis.overall_score = max(0.0, min(100.0, analysis.overall_score))
    analysis.proportion.score = max(0.0, min(100.0, analysis.proportion.score))
    analysis.tone.score = max(0.0, min(100.0, analysis.tone.score))
    analysis.texture.score = max(0.0, min(100.0, analysis.texture.score))
    analysis.line_quality.score = max(0.0, min(100.0, analysis.line_quality.score))

    # テキストフィールドをサニタイズ
    analysis.strengths = [sanitize_for_storage(s, 500) for s in analysis.strengths[:10]]
    analysis.improvements = [sanitize_for_storage(i, 500) for i in analysis.improvements[:10]]
    analysis.tags = [sanitize_for_storage(t, 50) for t in analysis.tags[:20]]

    return analysis


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
