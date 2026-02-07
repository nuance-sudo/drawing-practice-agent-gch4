"""Cloud Function: process-review

Cloud Tasksから呼び出され、審査処理を実行するCloud Function。
"""

import json
import os
from typing import TypedDict

import aiohttp
import asyncio
import functions_framework
import structlog
from flask import Request, Response
from google.cloud import firestore
from google.auth import default as google_auth_default
from google.auth.transport.requests import Request as AuthRequest

# 環境変数
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
LOCATION = os.environ.get("GCP_REGION", "us-central1")
AGENT_ENGINE_ID = os.environ.get("AGENT_ENGINE_ID", "")
AGENT_ENGINE_LOCATION = os.environ.get("AGENT_ENGINE_LOCATION", "us-central1")
ANNOTATION_FUNCTION_URL = os.environ.get("ANNOTATION_FUNCTION_URL", "")
IMAGE_GENERATION_FUNCTION_URL = os.environ.get("IMAGE_GENERATION_FUNCTION_URL", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")

# ログ設定
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger()


class TaskPayload(TypedDict):
    """Cloud Tasksからのペイロード型定義"""
    task_id: str
    user_id: str
    image_url: str


class TaskStatus:
    """タスクステータス定数"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


def get_firestore_client() -> firestore.Client:
    """Firestoreクライアントを取得"""
    return firestore.Client(project=PROJECT_ID)


def update_task_status(
    task_id: str,
    status: str,
    feedback: dict | None = None,
    score: int | None = None,
    tags: list[str] | None = None,
    rank_changed: bool | None = None,
    error_message: str | None = None,
    annotated_image_url: str | None = None,
) -> None:
    """Firestoreのタスクステータスを更新"""
    db = get_firestore_client()
    task_ref = db.collection("review_tasks").document(task_id)
    
    update_data: dict[str, object] = {
        "status": status,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }
    
    if feedback is not None:
        update_data["feedback"] = feedback
    if score is not None:
        update_data["score"] = score
    if tags is not None:
        update_data["tags"] = tags
    if rank_changed is not None:
        update_data["rank_changed"] = rank_changed
    if error_message is not None:
        update_data["error_message"] = error_message
    if annotated_image_url is not None:
        update_data["annotated_image_url"] = annotated_image_url
    
    task_ref.update(update_data)
    logger.info("task_status_updated", task_id=task_id, status=status)


def get_user_rank(user_id: str) -> str:
    """ユーザーの現在のランクを取得"""
    db = get_firestore_client()
    rank_ref = db.collection("user_ranks").document(user_id)
    rank_doc = rank_ref.get()
    
    if rank_doc.exists:
        rank_data = rank_doc.to_dict()
        if rank_data:
            return rank_data.get("current_rank", "10級")
    return "10級"


async def get_id_token(target_url: str) -> str:
    """認証済みCloud Function呼び出し用のIDトークンを取得"""
    credentials, _ = google_auth_default()
    auth_request = AuthRequest()
    
    # IDトークンを取得
    from google.auth import compute_engine
    from google.oauth2 import id_token
    
    id_token_value = id_token.fetch_id_token(auth_request, target_url)
    return id_token_value


async def call_agent_engine(
    image_url: str,
    rank_label: str,
    user_id: str,
    session_id: str = "",
) -> dict[str, object]:
    """Agent Engineを呼び出してデッサン分析を実行"""
    logger.info(
        "call_agent_engine_started",
        user_id=user_id,
        session_id=session_id,
        image_url=image_url,
        rank_label=rank_label,
    )
    
    try:
        # Vertex AI SDKを使用してAgent Engineを呼び出す
        import vertexai
        
        # Clientパターンで初期化
        client = vertexai.Client(
            project=PROJECT_ID,
            location=AGENT_ENGINE_LOCATION,
        )
        
        # Agent Engineアプリケーションを取得
        resource_name = f"projects/{PROJECT_ID}/locations/{AGENT_ENGINE_LOCATION}/reasoningEngines/{AGENT_ENGINE_ID}"
        adk_app = client.agent_engines.get(name=resource_name)
        
        # メッセージ構築（user_idとsession_idを含める）
        message = (
            f"画像URL: {image_url}\n"
            f"ユーザーランク: {rank_label}\n"
            f"ユーザーID: {user_id}\n"
            f"セッションID: {session_id}\n"
            "この画像を分析してください。"
        )
        
        # Agent Engine呼び出し（ストリーミング）
        final_response: dict[str, object] | None = None
        async for event in adk_app.async_stream_query(
            user_id=user_id,
            message=message,
        ):
            if isinstance(event, dict):
                # レスポンス解析
                parsed = _parse_agent_response(event)
                if parsed:
                    final_response = parsed
        
        if final_response is None:
            logger.error("agent_engine_no_response")
            return {"status": "error", "error_message": "Agent Engineからのレスポンスがありませんでした"}
        
        # 結果を返す
        if "overall_score" in final_response:
            return {"status": "success", "analysis": final_response}
        if "analysis" in final_response:
            return {"status": "success", "analysis": final_response.get("analysis")}
        if "status" in final_response and final_response["status"] == "success":
            return dict(final_response)
            
        logger.warning("agent_engine_unexpected_response", response=str(final_response))
        return {"status": "error", "error_message": "予期しないレスポンス形式です"}
        
    except Exception as e:
        logger.error("call_agent_engine_error", error=str(e))
        return {"status": "error", "error_message": str(e)}


def _parse_agent_response(event: dict[str, object]) -> dict[str, object] | None:
    """Agent Engineからのレスポンスをパース"""
    import re
    
    # content形式
    if "content" in event and event["content"]:
        content = event["content"]
        if isinstance(content, dict):
            if "parts" in content and isinstance(content["parts"], list):
                parts = content["parts"]
                if len(parts) > 0:
                    first_part = parts[0]
                    if isinstance(first_part, dict) and "text" in first_part:
                        text = first_part["text"]
                        if isinstance(text, str):
                            return _extract_json_from_text(text)
        elif isinstance(content, str):
            return _extract_json_from_text(content)
    
    # parts形式（イベント直下）
    if "parts" in event:
        parts = event["parts"]
        if isinstance(parts, list) and len(parts) > 0:
            first_part = parts[0]
            if isinstance(first_part, dict) and "text" in first_part:
                text = first_part["text"]
                if isinstance(text, str):
                    return _extract_json_from_text(text)
    
    return None


def _extract_json_from_text(text: str) -> dict[str, object] | None:
    """テキストからJSONを抽出"""
    import re
    
    # markdown code blockを除去
    patterns = [
        r"```json\s*\n([\s\S]*?)\n```",
        r"```\s*\n([\s\S]*?)\n```",
        r"```json\s*([\s\S]*?)```",
        r"```([\s\S]*?)```",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            text = match.group(1).strip()
            break
    
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    
    return None


async def call_cloud_function(url: str, payload: dict[str, object]) -> dict[str, object] | None:
    """認証済みCloud Functionを呼び出す"""
    try:
        id_token = await get_id_token(url)
        headers = {
            "Authorization": f"Bearer {id_token}",
            "Content-Type": "application/json",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=300) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    logger.error("cloud_function_error", status=response.status, response=text)
                    return None
    except Exception as e:
        logger.error("cloud_function_call_error", error=str(e))
        return None


def update_user_rank(user_id: str, score: int, task_id: str) -> tuple[str, bool]:
    """ユーザーランクを更新"""
    db = get_firestore_client()
    rank_ref = db.collection("user_ranks").document(user_id)
    rank_doc = rank_ref.get()
    
    current_rank = "10級"
    rank_changed = False
    
    if rank_doc.exists:
        rank_data = rank_doc.to_dict()
        if rank_data:
            current_rank = rank_data.get("current_rank", "10級")
    
    # スコアに基づくランク判定のシンプルな実装
    # 実際のロジックはrank_serviceから移植が必要
    new_rank = current_rank
    
    rank_ref.set({
        "user_id": user_id,
        "current_rank": new_rank,
        "current_score": score,
        "updated_at": firestore.SERVER_TIMESTAMP,
    }, merge=True)
    
    return new_rank, rank_changed


def generate_feedback_markdown(analysis: dict[str, object], rank: str) -> tuple[str, str]:
    """フィードバックのMarkdownを生成"""
    # シンプルなフィードバック生成
    summary = f"スコア: {analysis.get('overall_score', 0)}点"
    
    detailed_feedback = f"""
## 審査結果

**現在のランク**: {rank}

### スコア
{analysis.get('overall_score', 0)}点

### 評価ポイント
{analysis.get('strength_points', ['評価ポイントなし'])}

### 改善ポイント
{analysis.get('improvement_points', ['改善ポイントなし'])}
"""
    return summary, detailed_feedback


async def process_review(payload: TaskPayload) -> None:
    """審査処理のメインロジック"""
    task_id = payload["task_id"]
    user_id = payload["user_id"]
    image_url = payload["image_url"]
    
    logger.info("process_review_started", task_id=task_id, user_id=user_id)
    
    try:
        # ステータスをprocessingに更新
        update_task_status(task_id, TaskStatus.PROCESSING)
        
        # 現在のランクを取得
        current_rank = get_user_rank(user_id)
        
        # Agent Engine呼び出し（task_idをsession_idとして渡す）
        result = await call_agent_engine(
            image_url=image_url,
            rank_label=current_rank,
            user_id=user_id,
            session_id=task_id,
        )
        
        if result.get("status") != "success":
            error_message = str(result.get("error_message", "分析に失敗しました"))
            update_task_status(task_id, TaskStatus.FAILED, error_message=error_message)
            logger.error("process_review_failed", task_id=task_id, error=error_message)
            return
        
        analysis = result.get("analysis", {})
        if not isinstance(analysis, dict):
            analysis = {}
        score = int(analysis.get("overall_score", 0))
        tags = [str(tag) for tag in analysis.get("tags", [])]
        
        # 中間結果を保存
        update_task_status(
            task_id,
            TaskStatus.PROCESSING,
            feedback=analysis,
            score=score,
            tags=tags,
        )
        
        # ランク更新
        new_rank, rank_changed = update_user_rank(user_id, score, task_id)
        
        # フィードバック生成
        summary, detailed_feedback = generate_feedback_markdown(analysis, new_rank)
        
        feedback_data = dict(analysis)
        feedback_data["summary"] = summary
        feedback_data["detailed_feedback"] = detailed_feedback
        
        # 中間結果を保存（フィードバックまで完了）
        update_task_status(
            task_id,
            TaskStatus.PROCESSING,
            feedback=feedback_data,
            score=score,
            tags=tags,
            rank_changed=rank_changed,
        )
        
        # アノテーション画像生成
        annotated_image_url: str | None = None
        if ANNOTATION_FUNCTION_URL:
            logger.info("annotation_generation_started", task_id=task_id)
            annotation_result = await call_cloud_function(
                ANNOTATION_FUNCTION_URL,
                {
                    "task_id": task_id,
                    "user_id": user_id,
                    "original_image_url": image_url,
                    "analysis": analysis,
                    "current_rank_label": new_rank,
                    "motif_tags": tags,
                }
            )
            if annotation_result:
                url = annotation_result.get("annotated_image_url")
                if isinstance(url, str):
                    annotated_image_url = url
                logger.info("annotation_generation_completed", task_id=task_id)
        
        # お手本画像生成（Cloud Function呼び出し）
        if IMAGE_GENERATION_FUNCTION_URL:
            logger.info("example_image_generation_started", task_id=task_id)
            await call_cloud_function(
                IMAGE_GENERATION_FUNCTION_URL,
                {
                    "task_id": task_id,
                    "user_id": user_id,
                    "original_image_url": image_url,
                    "analysis": analysis,
                    "motif_tags": tags,
                    "annotated_image_url": annotated_image_url,
                }
            )
            logger.info("example_image_generation_request_sent", task_id=task_id)
            # Cloud Functionからの完了通知待ちのため、ここでは完了にしない
        else:
            # 画像生成Cloud FunctionがないのでここでCOMPLETED
            update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                feedback=feedback_data,
                score=score,
                tags=tags,
                rank_changed=rank_changed,
                annotated_image_url=annotated_image_url,
            )
        
        logger.info("process_review_completed", task_id=task_id)
        
    except Exception as e:
        logger.error("process_review_error", task_id=task_id, error=str(e))
        try:
            update_task_status(task_id, TaskStatus.FAILED, error_message=str(e))
        except Exception as update_error:
            logger.error("status_update_error", task_id=task_id, error=str(update_error))


@functions_framework.http
def process_review_handler(request: Request) -> Response:
    """Cloud Tasksからのリクエストを処理するエントリーポイント"""
    logger.info("process_review_handler_invoked", method=request.method)
    
    # Cloud Tasksからのリクエスト検証
    # Cloud Tasks は X-CloudTasks-* ヘッダーを自動付与
    task_name = request.headers.get("X-CloudTasks-TaskName")
    queue_name = request.headers.get("X-CloudTasks-QueueName")
    
    if not task_name or not queue_name:
        logger.warning("missing_cloud_tasks_headers")
        # ローカルテストやデバッグ用に許可
    
    try:
        # リクエストボディを取得
        request_json = request.get_json(silent=True)
        
        if not request_json:
            logger.error("empty_request_body")
            return Response("Bad Request: Empty body", status=400)
        
        # ペイロード検証
        task_id = request_json.get("task_id")
        user_id = request_json.get("user_id")
        image_url = request_json.get("image_url")
        
        if not all([task_id, user_id, image_url]):
            logger.error("missing_required_fields", payload=request_json)
            return Response("Bad Request: Missing required fields", status=400)
        
        payload: TaskPayload = {
            "task_id": task_id,
            "user_id": user_id,
            "image_url": image_url,
        }
        
        # 非同期処理を実行
        asyncio.run(process_review(payload))
        
        return Response("OK", status=200)
        
    except Exception as e:
        logger.error("process_review_handler_error", error=str(e))
        return Response(f"Internal Server Error: {str(e)}", status=500)
