"""カスタムメモリ検索ツール

ADKエージェントが使用するModチーフフィルタ付きメモリ検索ツール。
Vertex AI Client APIを使用してメタデータフィルタリングを実装。
"""

import logging

from vertexai import Client

from .config import settings

logger = logging.getLogger(__name__)

# メモリエントリの型定義
MemoryEntry = dict[str, str | dict[str, str | float | bool]]


def search_memory_by_motif(
    motif: str,
    user_id: str,
) -> list[MemoryEntry]:
    """モチーフでフィルタしたメモリを取得

    指定されたモチーフに関連する過去のデッサン分析結果を
    Memory Bankから取得します。成長フィードバック生成に使用。

    Args:
        motif: モチーフ名（例: "りんご", "静物", "人物"）
        user_id: ユーザーID（メモリのスコープキー）

    Returns:
        過去のメモリリスト。各メモリには以下を含む:
        - fact: 分析結果のテキスト
        - metadata: スコアなどのメタデータ

    Example:
        >>> memories = search_memory_by_motif("りんご", "abc123")
        >>> for m in memories:
        ...     print(m["metadata"]["overall_score"])
    """
    if not settings.agent_engine_id:
        logger.warning("AGENT_ENGINE_ID未設定のためメモリ検索をスキップ")
        return []

    try:
        client = Client()

        engine_name = (
            f"projects/{settings.gcp_project_id}"
            f"/locations/{settings.agent_engine_region}"
            f"/reasoningEngines/{settings.agent_engine_id}"
        )

        results = client.agent_engines.memories.retrieve(
            name=engine_name,
            scope={"user_id": user_id},
            config={
                "filter_groups": [
                    {
                        "filters": [
                            {"key": "motif", "value": {"string_value": motif}}
                        ]
                    }
                ]
            },
        )

        memories: list[MemoryEntry] = []
        for retrieved in results:
            memory = retrieved.memory
            memories.append({
                "fact": memory.fact,
                "metadata": _extract_metadata(memory.metadata) if memory.metadata else {},
            })

        logger.info(
            "メモリ検索完了: user=%s, motif=%s, count=%d",
            user_id,
            motif,
            len(memories),
        )
        return memories

    except Exception as e:
        logger.exception("メモリ検索エラー: %s", e)
        return []


def search_recent_memories(
    github_username: str,
    limit: int = 5,
) -> list[MemoryEntry]:
    """直近のメモリを取得

    ユーザーの直近のデッサン分析結果を取得します。

    Args:
        github_username: ユーザーのGitHubユーザー名
        limit: 取得する最大件数

    Returns:
        直近のメモリリスト（新しい順）
    """
    if not settings.agent_engine_id:
        logger.warning("AGENT_ENGINE_ID未設定のためメモリ検索をスキップ")
        return []

    try:
        client = Client()

        engine_name = (
            f"projects/{settings.gcp_project_id}"
            f"/locations/{settings.agent_engine_region}"
            f"/reasoningEngines/{settings.agent_engine_id}"
        )

        # スコープベースで全メモリを取得
        results = client.agent_engines.memories.retrieve(
            name=engine_name,
            scope={"user_id": github_username},
        )

        memories: list[MemoryEntry] = []
        for retrieved in results:
            if len(memories) >= limit:
                break
            memory = retrieved.memory
            memories.append({
                "fact": memory.fact,
                "metadata": _extract_metadata(memory.metadata) if memory.metadata else {},
            })

        logger.info(
            "直近メモリ取得完了: user=%s, count=%d",
            github_username,
            len(memories),
        )
        return memories

    except Exception as e:
        logger.exception("直近メモリ取得エラー: %s", e)
        return []


def _extract_metadata(
    metadata: dict[str, object],
) -> dict[str, str | float | bool]:
    """メタデータを辞書形式に変換"""
    extracted: dict[str, str | float | bool] = {}
    for key, value in metadata.items():
        if hasattr(value, "string_value"):
            str_val = getattr(value, "string_value", None)
            if str_val:
                extracted[key] = str_val
        elif hasattr(value, "double_value"):
            double_val = getattr(value, "double_value", None)
            if double_val is not None:
                extracted[key] = double_val
        elif hasattr(value, "bool_value"):
            bool_val = getattr(value, "bool_value", None)
            if bool_val is not None:
                extracted[key] = bool_val
        elif hasattr(value, "timestamp_value"):
            ts_val = getattr(value, "timestamp_value", None)
            if ts_val:
                extracted[key] = str(ts_val)
    return extracted
