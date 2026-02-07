"""Memory Bank コールバック

Vertex AI Agent Engine Memory Bankへのメモリ保存を担当。
分析結果をメタデータ付きで保存し、成長トラッキングに使用。
"""

import datetime
import logging

from vertexai import Client, types

from .config import settings
from .models import DessinAnalysis

logger = logging.getLogger(__name__)


def save_analysis_to_memory(
    analysis: DessinAnalysis,
    user_id: str,
    session_id: str = "",
) -> bool:
    """分析結果をメタデータ付きでMemory Bankに保存

    Args:
        analysis: デッサン分析結果
        user_id: ユーザーID（スコープキー）
        session_id: セッションID（レビューID、スコープキー）

    Returns:
        保存成功時True、失敗時False
    """
    if not settings.agent_engine_id:
        logger.warning("AGENT_ENGINE_ID未設定のためメモリ保存をスキップ")
        return False

    # デバッグログ: メモリ保存に使われるIDを記録（Issue #74 調査用）
    logger.info(
        "save_analysis_to_memory_called - DEBUG: 保存に使用するID",
        user_id=user_id,
        session_id=session_id,
        user_id_length=len(user_id),
        session_id_length=len(session_id),
        overall_score=analysis.overall_score,
    )

    try:
        client = Client()

        # メタデータを構築
        metadata = _build_memory_metadata(analysis)

        # factを構築
        fact = _build_memory_fact(analysis)

        # Agent Engine名を構築
        engine_name = (
            f"projects/{settings.gcp_project_id}"
            f"/locations/{settings.agent_engine_region}"
            f"/reasoningEngines/{settings.agent_engine_id}"
        )

        # スコープを構築（user_id + session_idで分離）
        scope: dict[str, str] = {"user_id": user_id}
        if session_id:
            scope["session_id"] = session_id

        logger.info(
            "メモリ保存開始: engine=%s, user=%s, session=%s, fact_length=%d",
            engine_name,
            user_id,
            session_id,
            len(fact),
        )

        # Memory Bankに保存（direct_memories_sourceを使用）
        # https://cloud.google.com/agent-builder/agent-engine/memory-bank/generate-memories
        result = client.agent_engines.memories.generate(
            name=engine_name,
            direct_memories_source={"direct_memories": [{"fact": fact}]},
            scope=scope,
            config=types.GenerateAgentEngineMemoriesConfig(
                metadata=metadata,
            ),
        )

        logger.info(
            "メモリ保存完了: user=%s, motif=%s, score=%.1f, result=%s",
            user_id,
            analysis.tags[0] if analysis.tags else "不明",
            analysis.overall_score,
            result,
        )
        return True

    except Exception as e:
        logger.exception("メモリ保存エラー: %s", e)
        return False


def _build_memory_metadata(analysis: DessinAnalysis) -> dict[str, types.MemoryMetadataValue]:
    """分析結果からメタデータを構築"""
    return {
        "motif": types.MemoryMetadataValue(
            string_value=analysis.tags[0] if analysis.tags else "不明"
        ),
        "overall_score": types.MemoryMetadataValue(
            double_value=analysis.overall_score
        ),
        "proportion_score": types.MemoryMetadataValue(
            double_value=analysis.proportion.score
        ),
        "tone_score": types.MemoryMetadataValue(
            double_value=analysis.tone.score
        ),
        "texture_score": types.MemoryMetadataValue(
            double_value=analysis.texture.score
        ),
        "line_quality_score": types.MemoryMetadataValue(
            double_value=analysis.line_quality.score
        ),
        "submitted_at": types.MemoryMetadataValue(
            timestamp_value=datetime.datetime.now(datetime.UTC)
        ),
    }


def _build_memory_fact(analysis: DessinAnalysis) -> str:
    """分析結果からfactテキストを構築"""
    strengths_text = ", ".join(analysis.strengths[:3]) if analysis.strengths else "なし"
    improvements_text = ", ".join(analysis.improvements[:3]) if analysis.improvements else "なし"
    tags_text = ", ".join(analysis.tags) if analysis.tags else "なし"

    return f"""デッサン分析結果:
- 総合スコア: {analysis.overall_score}/100
- プロポーション: {analysis.proportion.score}/100
- 陰影: {analysis.tone.score}/100
- 質感: {analysis.texture.score}/100
- 線の質: {analysis.line_quality.score}/100
- 強み: {strengths_text}
- 改善点: {improvements_text}
- タグ: {tags_text}
"""
