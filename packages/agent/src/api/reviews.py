"""審査API エンドポイント

審査リクエストの作成・取得・一覧取得を行うREST API。
認証済みユーザーのみアクセス可能。
"""

import contextlib

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from src.auth import AuthenticatedUser, get_current_user
from src.models.task import (
    CreateReviewRequest,
    ReviewListResponse,
    ReviewTaskResponse,
    TaskStatus,
)
from src.services.task_service import get_task_service
from src.tools.analysis import analyze_dessin_image

logger = structlog.get_logger()

router = APIRouter(prefix="/reviews", tags=["reviews"])


def process_review_task(task_id: str, image_url: str) -> None:
    """バックグラウンドでレビュータスクを処理

    Args:
        task_id: タスクID
        image_url: 分析対象の画像URL
    """
    logger.info("process_review_task_started", task_id=task_id)
    service = get_task_service()

    try:
        # ステータスをprocessingに更新
        service.update_task_status(task_id, TaskStatus.PROCESSING)

        # デッサン分析を実行
        result = analyze_dessin_image(image_url)

        if result.get("status") == "success":
            analysis = result.get("analysis", {})
            # 成功時：結果をFirestoreに保存
            service.update_task_status(
                task_id,
                TaskStatus.COMPLETED,
                feedback=analysis,
                score=analysis.get("overall_score"),
                tags=analysis.get("tags"),
            )
            logger.info(
                "process_review_task_completed",
                task_id=task_id,
                score=analysis.get("overall_score"),
            )
        else:
            # 失敗時：エラーステータスに更新
            error_message = result.get("error_message", "分析に失敗しました")
            service.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error_message=error_message,
            )
            logger.error(
                "process_review_task_failed",
                task_id=task_id,
                error=error_message,
            )
    except Exception as e:
        logger.error("process_review_task_error", task_id=task_id, error=str(e))
        with contextlib.suppress(Exception):
            service.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error_message=str(e),
            )


@router.get("/upload-url")
async def get_upload_url(
    content_type: str = Query(..., regex="^image/(jpeg|png)$"),
    _current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, str]:
    """アップロード用署名付きURLを取得

    Args:
        content_type: アップロードするファイルのMIMEタイプ (image/jpeg or image/png)

    Returns:
        dict: {
            "upload_url": 署名付きURL (PUT用),
            "public_url": 公開URL
        }
    """
    service = get_task_service()
    return service.generate_upload_url(content_type)


@router.post("", response_model=ReviewTaskResponse, status_code=201)
async def create_review(
    request: CreateReviewRequest,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ReviewTaskResponse:
    """審査リクエストを作成

    画像URLを受け取り、新規タスクを作成してpending状態で返す。
    バックグラウンドでエージェントによる分析を開始する。
    user_idは認証済みユーザーから取得する。
    """
    service = get_task_service()

    task = service.create_task(
        user_id=current_user.user_id,  # 認証済みユーザーから取得
        image_url=request.image_url,
        example_image_url=request.example_image_url,
    )

    # バックグラウンドでエージェント分析を開始
    background_tasks.add_task(process_review_task, task.task_id, task.image_url)

    logger.info(
        "review_created",
        task_id=task.task_id,
        user_id=task.user_id,
    )

    return ReviewTaskResponse.from_task(task)




@router.get("/{task_id}", response_model=ReviewTaskResponse)
async def get_review(
    task_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ReviewTaskResponse:
    """審査タスク詳細を取得

    Args:
        task_id: タスクID

    Returns:
        審査タスクの詳細

    Raises:
        HTTPException 404: タスクが見つからない場合
        HTTPException 403: 他ユーザーのタスクにアクセスした場合
    """
    service = get_task_service()

    task = service.get_task(task_id)

    if task is None:
        # 情報漏洩を防ぐため汎用的なメッセージを返す
        raise HTTPException(status_code=404, detail="Not found")

    # 所有権チェック
    if task.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return ReviewTaskResponse.from_task(task)


@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    current_user: AuthenticatedUser = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100, description="取得件数の上限"),
) -> ReviewListResponse:
    """審査タスク一覧を取得

    認証済みユーザーのタスクのみ取得する。

    Args:
        limit: 取得件数の上限（1-100）

    Returns:
        審査タスクの一覧
    """
    service = get_task_service()

    # 認証済みユーザーのタスクのみ取得
    tasks = service.list_tasks(user_id=current_user.user_id, limit=limit)

    return ReviewListResponse(
        tasks=[ReviewTaskResponse.from_task(task) for task in tasks],
        total_count=len(tasks),
    )


@router.delete("/{task_id}", status_code=204)
async def delete_review(
    task_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> None:
    """審査タスクを削除

    Args:
        task_id: タスクID

    Raises:
        HTTPException 404: タスクが見つからない場合
        HTTPException 403: 他ユーザーのタスクを削除しようとした場合
    """
    service = get_task_service()

    # まずタスクを取得して所有権チェック
    task = service.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Not found")

    # 所有権チェック
    if task.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    deleted = service.delete_task(task_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Not found")

    logger.info(
        "review_deleted",
        task_id=task_id,
        user_id=current_user.user_id,
    )
