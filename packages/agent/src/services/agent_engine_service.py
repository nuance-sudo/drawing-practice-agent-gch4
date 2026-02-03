"""Agent Engine呼び出しサービス

Vertex AI Agent Engineにデプロイされたエージェントを呼び出すサービス。
エージェント側でPreloadMemoryToolを使用してMemory Bankから過去メモリを自動取得。
"""

import json
from collections.abc import AsyncIterable

import structlog
import vertexai
from pydantic import ValidationError

from src.config import settings
from src.models.feedback import DessinAnalysis

logger = structlog.get_logger()


class AgentEngineService:
    """Vertex AI Agent Engine呼び出しサービス

    Agent Engineにデプロイされたコーチングエージェントを呼び出し、
    デッサン分析結果を取得します。

    新しいVertex AI SDK（vertexai.Client）パターンを使用。
    参考: https://docs.cloud.google.com/agent-builder/agent-engine/use/adk?hl=ja
    """

    def __init__(self) -> None:
        """サービスを初期化"""
        self._client: vertexai.Client | None = None
        self._adk_app: object | None = None  # AdkAppの型は実行時に解決
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """Vertex AI Clientを初期化"""
        if not self._initialized:
            # 必須設定のバリデーション
            if not settings.agent_engine_id:
                raise RuntimeError("AGENT_ENGINE_ID is required but not configured")
            if not settings.gcp_project_id:
                raise RuntimeError("GCP_PROJECT_ID is required but not configured")

            self._client = vertexai.Client(
                project=settings.gcp_project_id,
                location=settings.agent_engine_location,
            )
            self._initialized = True

    def _get_adk_app(self) -> object:
        """AdkAppを取得（遅延初期化）"""
        if self._adk_app is None:
            self._ensure_initialized()
            resource_name = (
                f"projects/{settings.gcp_project_id}/"
                f"locations/{settings.agent_engine_location}/"
                f"reasoningEngines/{settings.agent_engine_id}"
            )
            if self._client is None:
                raise RuntimeError("Client not initialized")
            self._adk_app = self._client.agent_engines.get(name=resource_name)
            logger.info(
                "adk_app_initialized",
                resource_name=resource_name,
            )
        return self._adk_app

    def _parse_agent_response(self, event: dict[str, object]) -> dict[str, object] | None:
        """Agent Engineからのレスポンスをパース

        レスポンス形式:
        - {"content": {"parts": [{"text": "..."}], "role": "model"}} - Geminiモデルレスポンス
        - {"content": {...}} - 辞書形式のコンテンツ
        - {"content": "..."} - 文字列形式のコンテンツ
        - {"parts": [{"text": "..."}]} - parts形式（markdown code block含む可能性）
        """
        # content形式
        if "content" in event and event["content"]:
            content = event["content"]
            if isinstance(content, dict):
                # content が {"parts": [...], "role": "..."} 形式の場合
                if "parts" in content and isinstance(content["parts"], list):
                    parts = content["parts"]
                    if len(parts) > 0:
                        first_part = parts[0]
                        if isinstance(first_part, dict):
                            if "text" in first_part and isinstance(first_part["text"], str):
                                text = first_part["text"]
                                return self._extract_json_from_text(text)
                            elif "function_response" in first_part:
                                func_resp = first_part["function_response"]
                                if isinstance(func_resp, dict) and "response" in func_resp:
                                    response = func_resp["response"]
                                    if isinstance(response, dict):
                                        return response
                else:
                    return content
            elif isinstance(content, str):
                return self._extract_json_from_text(content)

        # parts形式（イベント直下）
        if "parts" in event:
            parts = event["parts"]
            if isinstance(parts, list) and len(parts) > 0:
                first_part = parts[0]
                if isinstance(first_part, dict) and "text" in first_part:
                    text = first_part["text"]
                    if isinstance(text, str):
                        return self._extract_json_from_text(text)

        return None

    def _extract_json_from_text(self, text: str) -> dict[str, object] | None:
        """テキストからJSONを抽出

        markdown code blockで囲まれている場合も処理
        """
        import re

        # markdown code blockを除去（複数パターン対応）
        # パターン1: ```json ... ```
        # パターン2: ``` ... ```
        code_block_patterns = [
            r"```json\s*\n([\s\S]*?)\n```",
            r"```\s*\n([\s\S]*?)\n```",
            r"```json\s*([\s\S]*?)```",
            r"```([\s\S]*?)```",
        ]

        for pattern in code_block_patterns:
            match = re.search(pattern, text)
            if match:
                text = match.group(1).strip()
                break

        # JSONとしてパース
        try:
            result = json.loads(text)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        return None

    async def run_coaching_agent(
        self,
        image_url: str,
        rank_label: str,
        user_id: str,
    ) -> dict[str, object]:
        """Agent Engineのコーチングエージェントを実行

        エージェント側でPreloadMemoryToolを使用して過去メモリを自動取得するため、
        APIサーバー側でのメモリ処理は不要。

        Args:
            image_url: 分析対象の画像URL
            rank_label: ユーザーの現在のランク（例: "10級", "初段"）
            user_id: ユーザーID

        Returns:
            分析結果を含む辞書:
            - status: "success" または "error"
            - analysis: 分析結果（DessinAnalysis形式）
            - summary: フィードバックの要約
            - error_message: エラー時のメッセージ（エラー時のみ）
        """
        # セキュリティ: URLからクエリパラメータを除去してログ出力
        # （アクセストークンなどの機密情報を含む可能性があるため）
        safe_url = image_url.split("?")[0] if "?" in image_url else image_url
        logger.info(
            "agent_engine_query_started",
            image_url=safe_url[:100],
            rank_label=rank_label,
            user_id=user_id,
        )

        try:
            adk_app = self._get_adk_app()

            # エージェントへのメッセージを構築
            # Note: Agent Engine内のエージェントはanalyze_dessin_imageツールを持っており、
            # 画像URLを渡すことでデッサン分析を実行します
            # PreloadMemoryToolにより過去メモリは自動的にプリロードされます
            # user_idはメモリ保存のためにメッセージに含める
            message = (
                f"画像URL: {image_url}\n"
                f"ユーザーランク: {rank_label}\n"
                f"ユーザーID: {user_id}\n"
                f"この画像を分析してください。"
            )

            # Agent Engineにクエリを送信（非同期ストリーミング）
            final_response: dict[str, object] | None = None
            # Note: async_stream_query はAdkAppのメソッド
            events: AsyncIterable[dict[str, object]] = adk_app.async_stream_query(  # type: ignore[attr-defined]
                message=message,
                user_id=user_id,
            )

            async for event in events:
                # 最終レスポンスを取得
                if isinstance(event, dict):
                    # Agent Engineからのレスポンス形式の処理
                    parsed = self._parse_agent_response(event)
                    if parsed:
                        final_response = parsed
                    else:
                        # partsがあるのにパースできなかった場合のフォールバック
                        if "parts" in event:
                            parts = event.get("parts", [])
                            if parts and isinstance(parts[0], dict) and "text" in parts[0]:
                                text = parts[0]["text"]
                                extracted = self._extract_json_from_text(text)
                                if extracted:
                                    final_response = extracted

            if final_response is None:
                logger.error("agent_engine_no_response")
                return {
                    "status": "error",
                    "error_message": "Agent Engineからのレスポンスがありませんでした",
                }

            # レスポンスを検証
            # DessinAnalysisの形式で直接返ってきた場合
            if "overall_score" in final_response:
                analysis = DessinAnalysis.model_validate(final_response)
                logger.info(
                    "agent_engine_query_completed",
                    overall_score=analysis.overall_score,
                )
                return {
                    "status": "success",
                    "analysis": analysis.model_dump(),
                    "summary": "",
                }

            # ツール呼び出し結果が status + analysis 形式の場合
            if "analysis" in final_response:
                analysis_data = final_response["analysis"]
                if isinstance(analysis_data, dict):
                    analysis = DessinAnalysis.model_validate(analysis_data)
                    logger.info(
                        "agent_engine_query_completed",
                        overall_score=analysis.overall_score,
                    )
                    return {
                        "status": "success",
                        "analysis": analysis.model_dump(),
                        "summary": str(final_response.get("summary", "")),
                    }

            # status: success が直接返ってきた場合
            if "status" in final_response and final_response["status"] == "success":
                return dict(final_response)

            logger.warning(
                "agent_engine_unexpected_response",
                response=str(final_response),
                response_keys=list(final_response.keys()) if isinstance(final_response, dict) else [],
                response_type=type(final_response).__name__,
            )
            return {
                "status": "error",
                "error_message": "予期しないレスポンス形式です",
            }

        except ValidationError as e:
            logger.error("agent_engine_validation_error", error=str(e))
            return {
                "status": "error",
                "error_message": "分析結果の検証に失敗しました",
            }
        except Exception as e:
            logger.error("agent_engine_query_failed", error=str(e))
            return {
                "status": "error",
                "error_message": f"Agent Engineへのクエリに失敗しました: {e!s}",
            }


# シングルトンインスタンス
_agent_engine_service: AgentEngineService | None = None


def get_agent_engine_service() -> AgentEngineService:
    """AgentEngineServiceのシングルトンインスタンスを取得"""
    global _agent_engine_service
    if _agent_engine_service is None:
        _agent_engine_service = AgentEngineService()
    return _agent_engine_service
