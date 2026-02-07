"""デッサン分析ツール

ADKエージェントが使用するツール関数を定義。
"""

import logging
import re

from google import genai
from google.adk.tools import ToolContext
from google.genai import types
from pydantic import ValidationError

from .callbacks import save_analysis_to_memory
from .config import settings
from .models import DessinAnalysis, Rank
from .prompts import (
    DESSIN_ANALYSIS_USER_PROMPT,
    get_dessin_analysis_system_prompt,
)

logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    """画像処理エラー"""
    pass


def _convert_to_gcs_uri(url: str) -> str:
    """HTTPS URLをGCS URI形式に変換

    https://storage.googleapis.com/bucket-name/path/to/file
    → gs://bucket-name/path/to/file
    """
    if url.startswith("gs://"):
        return url

    if url.startswith("https://storage.googleapis.com/"):
        path = url.replace("https://storage.googleapis.com/", "")
        return f"gs://{path}"

    if url.startswith("https://storage.cloud.google.com/"):
        path = url.replace("https://storage.cloud.google.com/", "")
        return f"gs://{path}"

    return url


def _validate_image_url(url: str) -> str:
    """画像URLを検証"""
    if not url:
        raise ImageProcessingError("画像URLが空です")

    # 基本的なスキームチェック
    if not (url.startswith("https://") or url.startswith("gs://")):
        raise ImageProcessingError(f"許可されていないスキームです: {url[:10]}")

    return url


def _sanitize_for_storage(text: str, max_length: int = 10000) -> str:
    """テキストをサニタイズ"""
    if not text:
        return ""
    sanitized = text[:max_length]
    sanitized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", sanitized)
    return sanitized


def analyze_dessin_image(
    image_url: str,
    rank_label: str = "初学者",
    user_id: str = "",
    session_id: str = "",
    tool_context: "ToolContext | None" = None,
) -> dict[str, object]:
    """デッサン画像を分析し、フィードバックを返す

    鉛筆デッサン画像を分析し、プロポーション、陰影、質感、線の質の観点から
    評価とフィードバックを生成します。分析結果はMemory Bankに保存されます。

    Args:
        image_url: 分析対象の画像URL（Cloud StorageまたはCloud CDN経由）
        rank_label: ユーザーの現在のランク（例: "10級", "初段"）
        user_id: ユーザーID（メモリ保存用）
        session_id: セッションID（レビューID、メモリ保存用）
        tool_context: ADKツールコンテキスト（自動注入）

    Returns:
        分析結果を含む辞書。以下のキーを含む:
        - status: "success" または "error"
        - analysis: 分析結果（DessinAnalysis形式）
        - summary: フィードバックの要約
        - error_message: エラー時のメッセージ（エラー時のみ）

    Example:
        >>> result = analyze_dessin_image(
        ...     "https://storage.googleapis.com/.../drawing.jpg",
        ...     "5級",
        ...     "user123",
        ...     "review123"
        ... )
        >>> print(result["status"])
        "success"
        >>> print(result["analysis"]["overall_score"])
        75.5
    """
    # ランクのホワイトリスト検証
    valid_ranks = {r.label for r in Rank}
    if rank_label not in valid_ranks:
        rank_label = Rank.KYU_10.label

    # デバッグログ: ツール呼び出し時に受け取った引数を記録（Issue #74 調査用）
    logger.info(
        "analyze_dessin_image_called - DEBUG: 受け取った引数",
        image_url_preview=image_url[:100] if image_url else "",
        rank_label=rank_label,
        user_id=user_id,
        session_id=session_id,
        user_id_length=len(user_id),
        session_id_length=len(session_id),
        has_tool_context=tool_context is not None,
    )

    try:
        # URL検証
        validated_url = _validate_image_url(image_url)

        # GCS URIに変換
        gcs_uri = _convert_to_gcs_uri(validated_url)

        # Gemini クライアント初期化
        client = genai.Client(
            vertexai=True,
            project=settings.gcp_project_id,
            location=settings.gemini_location,
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

        # プロンプト生成
        system_prompt = get_dessin_analysis_system_prompt(rank_label)
        user_prompt = DESSIN_ANALYSIS_USER_PROMPT

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
                system_instruction=system_prompt,
                max_output_tokens=settings.gemini_max_output_tokens,
                temperature=settings.gemini_temperature,
                response_mime_type="application/json",
                response_schema=DessinAnalysis,
            ),
        )

        # レスポンスをパース
        analysis = DessinAnalysis.model_validate_json(response.text)

        # スコア範囲の検証
        analysis = _validate_and_sanitize_analysis(analysis)

        # 要約を作成
        summary = _create_summary(analysis)

        # Memory Bankに保存（引数のuser_idを優先、フォールバックでtool_contextから取得）
        effective_user_id = user_id
        if not effective_user_id and tool_context and hasattr(tool_context, "user_id"):
            effective_user_id = tool_context.user_id or ""

        if effective_user_id:
            saved = save_analysis_to_memory(analysis, effective_user_id, session_id)
            if saved:
                logger.info(
                    "分析結果をMemory Bankに保存: user=%s, session=%s",
                    effective_user_id,
                    session_id,
                )

        return {
            "status": "success",
            "analysis": analysis.model_dump(),
            "summary": summary,
        }

    except ValidationError:
        return {
            "status": "error",
            "error_message": "分析結果の検証に失敗しました",
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"デッサン分析に失敗しました: {e!s}",
        }


def _validate_and_sanitize_analysis(analysis: DessinAnalysis) -> DessinAnalysis:
    """分析結果を検証しサニタイズ"""
    # スコアを0-100の範囲にクランプ
    analysis.overall_score = max(0.0, min(100.0, analysis.overall_score))
    analysis.proportion.score = max(0.0, min(100.0, analysis.proportion.score))
    analysis.tone.score = max(0.0, min(100.0, analysis.tone.score))
    analysis.texture.score = max(0.0, min(100.0, analysis.texture.score))
    analysis.line_quality.score = max(0.0, min(100.0, analysis.line_quality.score))

    # テキストフィールドをサニタイズ
    analysis.strengths = [_sanitize_for_storage(s, 500) for s in analysis.strengths[:10]]
    analysis.improvements = [_sanitize_for_storage(i, 500) for i in analysis.improvements[:10]]
    analysis.tags = [_sanitize_for_storage(t, 50) for t in analysis.tags[:20]]

    return analysis


def _create_summary(analysis: DessinAnalysis) -> str:
    """分析結果から要約を作成"""
    score = analysis.overall_score
    strengths = analysis.strengths[:2] if analysis.strengths else []
    improvements = analysis.improvements[:1] if analysis.improvements else []

    summary_parts = [f"総合スコア: {score}/100点"]

    if strengths:
        summary_parts.append(f"良い点: {', '.join(strengths)}")

    if improvements:
        summary_parts.append(f"改善ポイント: {improvements[0]}")

    return " | ".join(summary_parts)
