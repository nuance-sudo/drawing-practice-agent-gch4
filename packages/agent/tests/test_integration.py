"""統合テスト

Firestore + Gemini APIを使用した統合テスト。
実際のGCPリソースにアクセスするため、CI環境では環境変数とサービスアカウントが必要。
"""

import os
from datetime import datetime

import pytest
import structlog

from src.config import settings
from src.models.task import ReviewTask, TaskStatus
from src.services.task_service import TaskService
from src.tools.analysis import analyze_dessin_image

logger = structlog.get_logger()

# テスト用の画像URL（公開GCSバケット）
TEST_IMAGE_URL = (
    f"https://storage.googleapis.com/{settings.gcs_bucket_name}/"
    "PXL_20260115_155656989.jpg"
)


def is_gcp_configured() -> bool:
    """GCP環境が設定されているか確認"""
    return bool(settings.gcp_project_id)


@pytest.mark.skipif(
    not is_gcp_configured(),
    reason="GCP_PROJECT_ID が設定されていないためスキップ",
)
class TestDessinAnalysisIntegration:
    """デッサン分析の統合テスト"""

    def test_analyze_dessin_image_success(self) -> None:
        """デッサン画像分析が正常に動作すること"""
        result = analyze_dessin_image(TEST_IMAGE_URL)

        assert result["status"] == "success"
        assert "analysis" in result
        assert "summary" in result

        analysis = result["analysis"]
        assert "overall_score" in analysis
        assert 0 <= analysis["overall_score"] <= 100
        assert "proportion" in analysis
        assert "tone" in analysis
        assert "texture" in analysis
        assert "line_quality" in analysis
        assert "tags" in analysis
        assert "strengths" in analysis
        assert "improvements" in analysis

    def test_analyze_dessin_image_returns_tags(self) -> None:
        """分析結果にタグが含まれること"""
        result = analyze_dessin_image(TEST_IMAGE_URL)

        assert result["status"] == "success"
        tags = result["analysis"]["tags"]
        assert isinstance(tags, list)
        assert len(tags) > 0


@pytest.mark.skipif(
    not is_gcp_configured(),
    reason="GCP_PROJECT_ID が設定されていないためスキップ",
)
class TestTaskServiceIntegration:
    """タスクサービスの統合テスト（Firestore使用）"""

    @pytest.fixture
    def service(self) -> TaskService:
        """TaskServiceインスタンスを作成"""
        return TaskService()

    @pytest.fixture
    def cleanup_task_ids(self) -> list[str]:
        """テスト後に削除するタスクIDのリスト"""
        task_ids: list[str] = []
        yield task_ids
        # クリーンアップ
        service = TaskService()
        for task_id in task_ids:
            try:
                service.delete_task(task_id)
                logger.info("test_cleanup_task_deleted", task_id=task_id)
            except Exception as e:
                logger.warning("test_cleanup_failed", task_id=task_id, error=str(e))

    def test_create_and_get_task(
        self, service: TaskService, cleanup_task_ids: list[str]
    ) -> None:
        """タスク作成と取得が正常に動作すること"""
        # タスク作成
        task = service.create_task(
            user_id="integration-test-user",
            image_url=TEST_IMAGE_URL,
        )
        cleanup_task_ids.append(task.task_id)

        assert task.task_id is not None
        assert task.user_id == "integration-test-user"
        assert task.status == TaskStatus.PENDING
        assert task.image_url == TEST_IMAGE_URL

        # タスク取得
        fetched = service.get_task(task.task_id)
        assert fetched is not None
        assert fetched.task_id == task.task_id
        assert fetched.user_id == task.user_id

    def test_update_task_with_analysis_result(
        self, service: TaskService, cleanup_task_ids: list[str]
    ) -> None:
        """タスクに分析結果を保存できること"""
        # タスク作成
        task = service.create_task(
            user_id="integration-test-user",
            image_url=TEST_IMAGE_URL,
        )
        cleanup_task_ids.append(task.task_id)

        # デッサン分析を実行
        result = analyze_dessin_image(task.image_url)
        assert result["status"] == "success"

        # タスクを更新
        updated_task = service.update_task_status(
            task_id=task.task_id,
            status=TaskStatus.COMPLETED,
            feedback=result["analysis"],
            score=result["analysis"]["overall_score"],
            tags=result["analysis"]["tags"],
        )

        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.score is not None
        assert 0 <= updated_task.score <= 100
        assert updated_task.tags is not None
        assert len(updated_task.tags) > 0
        assert updated_task.feedback is not None

    def test_list_tasks_by_user(
        self, service: TaskService, cleanup_task_ids: list[str]
    ) -> None:
        """ユーザーのタスク一覧が取得できること"""
        test_user_id = f"integration-test-user-{datetime.now().timestamp()}"

        # 複数タスク作成
        for i in range(3):
            task = service.create_task(
                user_id=test_user_id,
                image_url=TEST_IMAGE_URL,
            )
            cleanup_task_ids.append(task.task_id)

        # 一覧取得
        tasks = service.list_tasks(user_id=test_user_id, limit=10)
        assert len(tasks) == 3

    def test_delete_task(
        self, service: TaskService, cleanup_task_ids: list[str]
    ) -> None:
        """タスク削除が正常に動作すること"""
        # タスク作成
        task = service.create_task(
            user_id="integration-test-user",
            image_url=TEST_IMAGE_URL,
        )

        # 削除
        deleted = service.delete_task(task.task_id)
        assert deleted is True

        # 削除確認
        fetched = service.get_task(task.task_id)
        assert fetched is None
