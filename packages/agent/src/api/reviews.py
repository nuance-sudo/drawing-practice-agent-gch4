"""審査API エンドポイント

審査リクエストの作成・取得・一覧取得を行うREST API。
"""

import structlog
from fastapi import APIRouter, HTTPException, Query

from src.models.task import (
    CreateReviewRequest,
    ReviewListResponse,
    ReviewTaskResponse,
)
from src.services.task_service import get_task_service

logger = structlog.get_logger()

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewTaskResponse, status_code=201)
async def create_review(request: CreateReviewRequest) -> ReviewTaskResponse:
    """審査リクエストを作成

    画像URLを受け取り、新規タスクを作成してpending状態で返す。
    """
    service = get_task_service()

    task = service.create_task(
        user_id=request.user_id,
        image_url=request.image_url,
        example_image_url=request.example_image_url,
    )

    logger.info(
        "review_created",
        task_id=task.task_id,
        user_id=task.user_id,
    )

    return ReviewTaskResponse.from_task(task)


@router.get("/{task_id}", response_model=ReviewTaskResponse)
async def get_review(task_id: str) -> ReviewTaskResponse:
    """審査タスク詳細を取得

    Args:
        task_id: タスクID

    Returns:
        審査タスクの詳細

    Raises:
        HTTPException 404: タスクが見つからない場合
    """
    service = get_task_service()

    task = service.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    return ReviewTaskResponse.from_task(task)


@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    user_id: str = Query(..., description="ユーザーID"),
    limit: int = Query(default=20, ge=1, le=100, description="取得件数の上限"),
) -> ReviewListResponse:
    """審査タスク一覧を取得

    Args:
        user_id: ユーザーID
        limit: 取得件数の上限（1-100）

    Returns:
        審査タスクの一覧
    """
    service = get_task_service()

    tasks = service.list_tasks(user_id=user_id, limit=limit)

    return ReviewListResponse(
        tasks=[ReviewTaskResponse.from_task(task) for task in tasks],
        total_count=len(tasks),
    )


@router.delete("/{task_id}", status_code=204)
async def delete_review(task_id: str) -> None:
    """審査タスクを削除

    Args:
        task_id: タスクID

    Raises:
        HTTPException 404: タスクが見つからない場合
    """
    service = get_task_service()

    deleted = service.delete_task(task_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")

    logger.info(
        "review_deleted",
        task_id=task_id,
    )
