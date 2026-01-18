"""TaskServiceのユニットテスト

モックを使用してFirestore連携をテストする。
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from src.models.task import ReviewTask, TaskStatus
from src.services.task_service import TaskService


class MockDocumentSnapshot:
    """Firestore DocumentSnapshotのモック"""

    def __init__(self, data: dict[str, object] | None, exists: bool = True) -> None:
        self._data = data
        self.exists = exists

    def to_dict(self) -> dict[str, object] | None:
        return self._data


class MockDocumentReference:
    """Firestore DocumentReferenceのモック"""

    def __init__(self, data: dict[str, object] | None = None) -> None:
        self._data = data

    def get(self) -> MockDocumentSnapshot:
        return MockDocumentSnapshot(self._data, exists=self._data is not None)

    def set(self, data: dict[str, object]) -> None:
        self._data = data

    def update(self, data: dict[str, object]) -> None:
        if self._data:
            self._data.update(data)

    def delete(self) -> None:
        self._data = None


class MockQuery:
    """Firestore Queryのモック"""

    def __init__(self, docs: list[dict[str, object]]) -> None:
        self._docs = docs

    def order_by(self, field: str, direction: object = None) -> "MockQuery":
        return self

    def limit(self, count: int) -> "MockQuery":
        return self

    def stream(self) -> list[MockDocumentSnapshot]:
        return [MockDocumentSnapshot(doc) for doc in self._docs]


class MockCollection:
    """Firestore Collectionのモック"""

    def __init__(self) -> None:
        self._documents: dict[str, dict[str, object]] = {}

    def document(self, doc_id: str) -> MockDocumentReference:
        return MockDocumentReference(self._documents.get(doc_id))

    def where(self, field: str, op: str, value: object) -> MockQuery:
        matching = [
            doc for doc in self._documents.values() if doc.get(field) == value
        ]
        return MockQuery(matching)


class MockFirestoreClient:
    """Firestore Clientのモック"""

    def __init__(self) -> None:
        self._collections: dict[str, MockCollection] = {}

    def collection(self, name: str) -> MockCollection:
        if name not in self._collections:
            self._collections[name] = MockCollection()
        return self._collections[name]


class TestTaskService:
    """TaskServiceのテスト"""

    @pytest.fixture
    def mock_db(self) -> MockFirestoreClient:
        """モックFirestoreクライアントを作成"""
        return MockFirestoreClient()

    @pytest.fixture
    def service(self, mock_db: MockFirestoreClient) -> TaskService:
        """TaskServiceインスタンスを作成"""
        return TaskService(db=mock_db)  # type: ignore[arg-type]

    def test_create_task(self, service: TaskService) -> None:
        """タスク作成テスト"""
        task = service.create_task(
            user_id="test-user",
            image_url="https://storage.googleapis.com/bucket/test.jpg",
        )

        assert task.user_id == "test-user"
        assert task.image_url == "https://storage.googleapis.com/bucket/test.jpg"
        assert task.status == TaskStatus.PENDING
        assert task.task_id is not None
        assert len(task.task_id) == 36  # UUID形式

    def test_create_task_with_example(self, service: TaskService) -> None:
        """お手本画像付きタスク作成テスト"""
        task = service.create_task(
            user_id="test-user",
            image_url="https://storage.googleapis.com/bucket/test.jpg",
            example_image_url="https://storage.googleapis.com/bucket/example.jpg",
        )

        assert task.example_image_url == "https://storage.googleapis.com/bucket/example.jpg"

    def test_get_task_not_found(self, service: TaskService) -> None:
        """存在しないタスク取得テスト"""
        result = service.get_task("non-existent-id")
        assert result is None


class TestReviewTaskModel:
    """ReviewTaskモデルのテスト"""

    def test_valid_task(self) -> None:
        """有効なタスク作成テスト"""
        task = ReviewTask(
            task_id="test-id",
            user_id="user-123",
            image_url="https://storage.googleapis.com/bucket/image.jpg",
        )

        assert task.task_id == "test-id"
        assert task.status == TaskStatus.PENDING

    def test_invalid_url_rejected(self) -> None:
        """無効なURL拒否テスト"""
        with pytest.raises(ValueError, match="許可されていないホスト"):
            ReviewTask(
                task_id="test-id",
                user_id="user-123",
                image_url="https://evil.com/malicious.jpg",
            )

    def test_http_rejected(self) -> None:
        """HTTP URL拒否テスト"""
        with pytest.raises(ValueError, match="HTTPSのみ"):
            ReviewTask(
                task_id="test-id",
                user_id="user-123",
                image_url="http://storage.googleapis.com/bucket/image.jpg",
            )

    def test_gs_url_accepted(self) -> None:
        """gs:// URL許可テスト"""
        task = ReviewTask(
            task_id="test-id",
            user_id="user-123",
            image_url="gs://my-bucket/image.jpg",
        )

        assert task.image_url == "gs://my-bucket/image.jpg"
