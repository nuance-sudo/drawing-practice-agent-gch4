# コーディング規約

## Python / ADK (Agent Development Kit)

### 1. ファイル・ディレクトリ構成

**概要**: 機能別にディレクトリを分けて、コードの可読性と保守性を向上させる

#### 基本構成

```
packages/agent/src/
├── main.py           # FastAPIエントリーポイント
├── agent.py          # ADK Agent定義（root_agent）
├── config.py         # 設定管理
├── exceptions.py     # カスタム例外
├── api/              # REST APIエンドポイント
├── models/           # Pydanticモデル
├── prompts/          # プロンプト定義
├── services/         # 外部サービス連携
├── tools/            # ADK Tools
└── utils/            # ユーティリティ
```

#### ルール

- 機能ごとにディレクトリを分ける
- 1ファイル1責務の原則を守る
- 循環インポートを避ける

### 2. 命名規則

**概要**: 一貫性のある命名でコードの可読性を向上させる

| 種別 | 規則 | 例 |
|------|------|-----|
| モジュール | snake_case | `task_service.py`, `storage_tool.py` |
| クラス | PascalCase | `ReviewTask`, `DessinCoachingAgent` |
| 関数/メソッド | snake_case | `analyze_dessin()`, `get_task_by_id()` |
| 変数 | snake_case | `task_id`, `user_rank` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `STORAGE_BUCKET` |
| プライベート | _接頭辞 | `_internal_method`, `_cache` |

```python
# ✅ 良い例
class ReviewTaskService:
    MAX_RETRY_COUNT = 3
    
    def __init__(self, task_id: str):
        self._task_id = task_id
    
    def get_task_status(self) -> str:
        return self._fetch_status()
    
    def _fetch_status(self) -> str:
        ...

# ❌ 悪い例
class reviewTaskService:  # PascalCaseでない
    maxRetryCount = 3     # UPPER_SNAKE_CASEでない
    
    def GetTaskStatus(self):  # snake_caseでない
        ...
```

### 3. 型定義

**概要**: 型ヒントを必須とし、`any`型は使用禁止

#### 基本ルール

- すべての関数に引数と戻り値の型を指定
- `Any`型は使用禁止
- Pydanticモデルで構造化データを定義
- `Optional`を適切に使用

```python
from typing import Optional
from pydantic import BaseModel

# ✅ 良い例 - Pydanticモデル定義
class ReviewTask(BaseModel):
    task_id: str
    user_id: str
    status: str
    score: Optional[float] = None

# ✅ 良い例 - 関数の型定義
def get_task(task_id: str) -> Optional[ReviewTask]:
    ...

def update_task(task_id: str, status: str, score: float) -> bool:
    ...

# ❌ 悪い例
def process_data(data):  # 型定義なし
    return data

def get_result() -> Any:  # Any型使用
    ...
```

### 4. インポート順序

**概要**: PEP 8に従った順序でインポートを整理

```python
# 1. 標準ライブラリ
import os
import json
from datetime import datetime
from typing import Optional, List

# 2. サードパーティ
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google.adk import Agent, Tool

# 3. ローカルモジュール
from src.config import settings
from src.models.task import ReviewTask
from src.services.gemini_service import GeminiService
```

### 5. エラーハンドリング

**概要**: 具体的な例外を使用し、適切にログを出力

```python
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger()

# ✅ 良い例 - カスタム例外
class TaskNotFoundError(Exception):
    """タスクが見つからない場合の例外"""
    pass

class AnalysisFailedError(Exception):
    """分析失敗時の例外"""
    pass

# ✅ 良い例 - 適切なエラーハンドリング
async def get_task(task_id: str) -> ReviewTask:
    try:
        task = await db.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"Task not found: {task_id}")
        return task
    except DatabaseError as e:
        logger.error("database_error", task_id=task_id, error=str(e))
        raise

# ✅ 良い例 - リトライ処理
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
)
async def call_vertex_ai(prompt: str) -> str:
    ...
```

### 6. ADK Agent定義

**概要**: ADKのベストプラクティスに従ってエージェントを定義

```python
from google.adk import Agent, Tool

# ✅ 良い例 - エージェント定義
root_agent = Agent(
    name="dessin-coaching-agent",
    model="gemini-3-flash-preview",
    description="鉛筆デッサンを分析し、改善フィードバックを提供するエージェント",
    instruction="""
    あなたは鉛筆デッサンのコーチです。
    以下の手順でフィードバックを提供してください：
    1. 画像を分析
    2. 評価項目ごとにスコアリング
    3. 改善点を提案
    """,
    tools=[
        analyze_dessin,
        generate_feedback,
        update_task,
    ],
)

# ✅ 良い例 - Tool定義
@Tool
def analyze_dessin(image_url: str) -> dict:
    """
    デッサン画像を分析します。
    
    Args:
        image_url: 分析対象の画像URL
        
    Returns:
        分析結果を含む辞書
    """
    ...
```

### 7. ログ出力

**概要**: 構造化ログを使用し、適切な情報を記録

```python
import structlog

logger = structlog.get_logger()

# ✅ 良い例 - 構造化ログ
logger.info(
    "task_created",
    task_id=task.task_id,
    user_id=task.user_id,
    image_size=len(image_data),
)

logger.error(
    "analysis_failed",
    task_id=task.task_id,
    error=str(e),
    retry_count=retry_count,
)

# ❌ 悪い例 - print文
print(f"Task created: {task_id}")
```

### 8. テスト

**概要**: pytestを使用し、モックを適切に活用

```python
import pytest
from unittest.mock import AsyncMock, patch

# ✅ 良い例 - テスト構成
class TestReviewTaskService:
    @pytest.fixture
    def service(self):
        return ReviewTaskService()
    
    async def test_get_task_success(self, service):
        # Arrange
        task_id = "test-task-id"
        
        # Act
        result = await service.get_task(task_id)
        
        # Assert
        assert result.task_id == task_id
    
    async def test_get_task_not_found(self, service):
        with pytest.raises(TaskNotFoundError):
            await service.get_task("invalid-id")
```

### 9. セキュリティ

**概要**: 機密情報の取り扱いに注意

```python
# ✅ 良い例 - Secret Managerから取得
from src.services.secrets import get_secret

api_key = get_secret("VAPID_PRIVATE_KEY")

# ❌ 悪い例 - ハードコード
api_key = "sk-1234567890abcdef"

# ❌ 悪い例 - ログに機密情報
logger.info("API call", api_key=api_key)  # 絶対にNG
```
