"""Memory Bankサービス

Vertex AI Agent Engine Memory Bankとの連携を担当するサービス。
ADK MemoryService APIを使用してメモリの検索・追加を行う。
"""

import structlog
from google.adk.memory import VertexAiMemoryBankService
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import settings
from src.models.memory import MemoryContext, SkillProgression

logger = structlog.get_logger()

# アプリケーション名（Memory Bank検索時に使用）
APP_NAME = "dessin-coaching-agent"


class MemoryService:
    """Memory Bankサービス

    Vertex AI Agent Engine Memory Bankを使用して、
    ユーザーの成長履歴を管理する。

    ADK API:
    - search_memory(app_name, user_id, query): メモリ検索
    - add_session_to_memory(session): セッションをメモリに追加
    """

    def __init__(self, agent_engine_id: str | None = None) -> None:
        """初期化

        Args:
            agent_engine_id: Agent Engine ID（未指定時は設定から取得）
        """
        self._agent_engine_id = agent_engine_id or settings.agent_engine_id
        self._memory_service: VertexAiMemoryBankService | None = None

    def _get_memory_service(self) -> VertexAiMemoryBankService:
        """Memory Bankサービスインスタンスを取得（遅延初期化）"""
        if self._memory_service is None:
            self._memory_service = VertexAiMemoryBankService(
                project=settings.gcp_project_id,
                location=settings.agent_engine_location,
                agent_engine_id=self._agent_engine_id,
            )
        return self._memory_service

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def search_user_memories(self, user_id: str) -> MemoryContext:
        """ユーザーの過去メモリを検索

        Args:
            user_id: ユーザーID

        Returns:
            メモリコンテキスト（過去のメモリ情報）
        """
        try:
            memory_service = self._get_memory_service()

            # デッサン分析に関連するメモリを検索
            search_response = await memory_service.search_memory(
                app_name=APP_NAME,
                user_id=user_id,
                query="デッサン分析結果 スコア 評価",
            )

            memories = search_response.memories if search_response else []

            if not memories or len(memories) == 0:
                logger.info(
                    "memory_search_empty",
                    user_id=user_id,
                )
                return MemoryContext(
                    has_previous_submissions=False,
                    submission_count=0,
                )

            # メモリからスキル進捗を抽出
            skill_progressions = self._extract_skill_progressions(memories)
            recent_summary = self._extract_recent_summary(memories)

            logger.info(
                "memory_search_success",
                user_id=user_id,
                memory_count=len(memories),
            )

            return MemoryContext(
                has_previous_submissions=True,
                submission_count=len(memories),
                skill_progressions=skill_progressions,
                recent_feedback_summary=recent_summary,
            )

        except Exception as e:
            logger.error(
                "memory_search_error",
                user_id=user_id,
                error=str(e),
            )
            # エラー時は空のコンテキストを返す（フォールバック）
            return MemoryContext(
                has_previous_submissions=False,
                submission_count=0,
            )

    def _extract_skill_progressions(
        self, memories: list[object]
    ) -> list[SkillProgression]:
        """メモリからスキル進捗を抽出

        Args:
            memories: 取得したメモリのリスト

        Returns:
            スキル進捗のリスト
        """
        # メモリからスコア履歴を集計
        category_scores: dict[str, list[float]] = {
            "proportion": [],
            "tone": [],
            "texture": [],
            "line_quality": [],
        }

        for memory in memories:
            # MemoryEntryからコンテンツを取得
            content = getattr(memory, "content", None)
            if content and isinstance(content, dict):
                for category in category_scores:
                    if category in content:
                        category_data = content[category]
                        if isinstance(category_data, dict) and "score" in category_data:
                            score = category_data["score"]
                            if isinstance(score, (int, float)):
                                category_scores[category].append(float(score))

        # スキル進捗を生成
        progressions: list[SkillProgression] = []
        for category, scores in category_scores.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                latest_score = scores[-1]
                trend = self._calculate_trend(scores)

                progressions.append(
                    SkillProgression(
                        category=category,
                        average_score=avg_score,
                        latest_score=latest_score,
                        trend=trend,
                        submission_count=len(scores),
                    )
                )

        return progressions

    def _calculate_trend(self, scores: list[float]) -> str:
        """スコアトレンドを計算

        Args:
            scores: スコアのリスト

        Returns:
            トレンド（improving, stable, declining）
        """
        if len(scores) < 2:
            return "stable"

        # 直近3回の平均と全体平均を比較
        recent_count = min(3, len(scores))
        recent_avg = sum(scores[-recent_count:]) / recent_count
        overall_avg = sum(scores) / len(scores)

        diff = recent_avg - overall_avg
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"

    def _extract_recent_summary(self, memories: list[object]) -> str:
        """直近のフィードバック要約を抽出

        Args:
            memories: 取得したメモリのリスト

        Returns:
            フィードバック要約
        """
        if not memories:
            return ""

        # 直近のメモリを取得
        recent_memory = memories[-1] if memories else None
        if recent_memory is None:
            return ""

        content = getattr(recent_memory, "content", None)

        if content and isinstance(content, dict):
            strengths = content.get("strengths", [])
            improvements = content.get("improvements", [])

            summary_parts: list[str] = []
            if strengths and isinstance(strengths, list):
                summary_parts.append(f"前回の強み: {', '.join(strengths[:2])}")
            if improvements and isinstance(improvements, list):
                summary_parts.append(f"前回の改善点: {', '.join(improvements[:2])}")

            return "。".join(summary_parts)

        return ""
