# 鉛筆デッサンコーチングエージェント 開発ガイドライン

## 概要

本ドキュメントは、プロジェクトにおけるコーディング規約、命名規則、テスト規約、Git規約を定義します。

---

## コーディング規約

### Python バージョン

- **Python 3.12+** を使用
- 型ヒントを積極的に使用（`any`型は禁止）

### フォーマッター / リンター

| ツール | 用途 | 設定 |
|--------|------|------|
| **ruff** | フォーマット・リント | `pyproject.toml` で設定 |
| **mypy** | 型チェック | strict モード |

```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true
```

### コードスタイル

#### インポート順序

```python
# 1. 標準ライブラリ
import os
from datetime import datetime

# 2. サードパーティ
from google.adk import Agent
from pydantic import BaseModel

# 3. ローカルモジュール
from src.models.feedback import DessinFeedback
from src.services.gemini_service import GeminiService
```

#### 型ヒント

```python
# ✅ 良い例: 明示的な型定義
def analyze_dessin(image_data: bytes, user_rank: int) -> DessinAnalysis:
    ...

# ❌ 悪い例: any型の使用（禁止）
def analyze_dessin(image_data, user_rank) -> Any:
    ...
```

#### 非同期関数

```python
# ✅ 良い例: async/await の使用
async def call_gemini_api(prompt: str, image: bytes) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(...)
    return response.text
```

#### エラーハンドリング

```python
# ✅ 良い例: 具体的な例外をキャッチ
try:
    result = await gemini_service.analyze(image)
except GeminiAPIError as e:
    logger.error("Gemini API error", error=str(e))
    raise
except httpx.TimeoutException:
    logger.warning("API timeout, retrying...")
    raise

# ❌ 悪い例: 広すぎる例外キャッチ
try:
    result = await gemini_service.analyze(image)
except Exception:
    pass
```

---

## 命名規則

### ファイル・ディレクトリ

| 種別 | 規則 | 例 |
|------|------|-----|
| Pythonモジュール | snake_case | `github_tool.py` |
| テストファイル | `test_` prefix | `test_github_tool.py` |
| ディレクトリ | snake_case (複数形) | `models/`, `services/` |

### クラス・関数・変数

| 種別 | 規則 | 例 |
|------|------|-----|
| クラス | PascalCase | `DessinCoachingAgent` |
| 関数 | snake_case（動詞から開始） | `analyze_dessin()`, `get_user_rank()` |
| 変数 | snake_case | `user_rank`, `image_data` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| プライベート | `_` prefix | `_internal_method()` |

### Pydantic モデル

```python
# モデル名: PascalCase + 用途を示すサフィックス
class CoachingRequest(BaseModel):     # リクエスト
    ...

class DessinAnalysis(BaseModel):       # 分析結果
    ...

class UserRank(BaseModel):             # エンティティ
    ...
```

### ADK 関連

| 種別 | 規則 | 例 |
|------|------|-----|
| Agent | PascalCase + `Agent` サフィックス | `DessinCoachingAgent` |
| Tool関数 | snake_case（動詞から開始） | `analyze_dessin`, `post_comment` |
| root_agent | snake_case（ADK規約） | `root_agent` |

---

## ドキュメンテーション

### Docstring

Google スタイルを採用：

```python
def analyze_dessin(image_data: bytes, user_rank: int) -> DessinAnalysis:
    """デッサン画像を分析してフィードバックを生成する。

    Args:
        image_data: 分析対象の画像データ（JPEG/PNG）
        user_rank: ユーザーの現在のランクレベル（1-15）

    Returns:
        分析結果を含むDessinAnalysisオブジェクト

    Raises:
        GeminiAPIError: Gemini API呼び出しに失敗した場合
        InvalidImageError: 画像形式が不正な場合
    """
    ...
```

### コメント

```python
# ✅ 良い例: なぜそうするかを説明
# リトライ間隔を指数的に増加させることで、API負荷を軽減
wait_time = 2 ** attempt

# ❌ 悪い例: 何をしているかだけ
# wait_timeに2のattitude乗を代入
wait_time = 2 ** attempt
```

---

## テスト規約

### テストフレームワーク

- **pytest** を使用
- **pytest-asyncio** で非同期テスト対応

### ファイル構成

```
tests/
├── conftest.py              # 共通fixture
├── test_agent.py            # エージェントテスト
├── test_services/
│   ├── test_gemini_service.py
│   └── test_rank_service.py
└── test_tools/
    └── test_github_tool.py
```

### テスト命名

```python
# パターン: test_{対象}_{条件}_{期待結果}
def test_analyze_dessin_with_valid_image_returns_analysis():
    ...

def test_analyze_dessin_with_invalid_format_raises_error():
    ...

# 非同期テスト
async def test_call_gemini_api_with_timeout_retries():
    ...
```

### Fixture

```python
# conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_gemini_service() -> AsyncMock:
    """Gemini Serviceのモック"""
    mock = AsyncMock()
    mock.analyze.return_value = DessinAnalysis(...)
    return mock

@pytest.fixture
def sample_image_data() -> bytes:
    """テスト用サンプル画像"""
    return Path("tests/fixtures/sample.jpg").read_bytes()
```

### テストカバレッジ

- 目標: **80%以上**
- 重要なビジネスロジックは**100%**カバー

---

## Git規約

### ブランチ戦略

```
main                          # 本番環境
├── develop                   # 開発統合ブランチ
│   ├── feature/xxx          # 機能開発
│   ├── fix/xxx              # バグ修正
│   └── docs/xxx             # ドキュメント
```

### ブランチ命名

| 種別 | 形式 | 例 |
|------|------|-----|
| 機能 | `feature/{概要}` | `feature/add-memory-bank` |
| 修正 | `fix/{概要}` | `fix/github-auth-error` |
| ドキュメント | `docs/{概要}` | `docs/update-architecture` |
| リファクタ | `refactor/{概要}` | `refactor/extract-service` |

### コミットメッセージ

Conventional Commits 形式を採用：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Type:**

| Type | 用途 |
|------|------|
| `feat` | 新機能 |
| `fix` | バグ修正 |
| `docs` | ドキュメントのみ |
| `style` | フォーマット変更 |
| `refactor` | リファクタリング |
| `test` | テスト追加・修正 |
| `chore` | ビルド・設定変更 |

**例:**

```
feat(agent): add memory bank integration

- Integrate Vertex AI Memory Bank for long-term memory
- Add memory search tool for feedback history
- Update runner configuration

Closes #123
```

### Pull Request

- タイトル: Conventional Commits 形式
- 本文: テンプレートに従う
- レビュー: 1名以上の承認必須（チームの場合）

---

## 開発コマンド

### Makefile

```makefile
.PHONY: install lint test format typecheck all

install:
	cd agent && uv sync

lint:
	cd agent && uv run ruff check .

format:
	cd agent && uv run ruff format .

typecheck:
	cd agent && uv run mypy src/

test:
	cd agent && uv run pytest tests/ -v

all: format lint typecheck test
```

### 日常的な開発フロー

```bash
# 1. 依存関係インストール
make install

# 2. コード変更後
make format    # フォーマット
make lint      # リント
make typecheck # 型チェック
make test      # テスト

# 3. 全チェック
make all
```

---

## ローカル開発

### 環境変数

```bash
# agent/.env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=asia-northeast1
GOOGLE_GENAI_USE_VERTEXAI=true
GITHUB_APP_ID=123456
GITHUB_APP_INSTALLATION_ID=789012
```

### ADK開発サーバー

```bash
# Web UI起動
cd agent
uv run adk web

# API Server起動
uv run adk api_server

# 直接実行
uv run adk run
```

---

## セキュリティガイドライン

### 禁止事項

- ❌ 秘密情報のハードコーディング
- ❌ `.env` ファイルのコミット
- ❌ 本番データのローカル保存
- ❌ 未検証の外部入力の直接使用

### 推奨事項

- ✅ Secret Managerからの秘密情報取得
- ✅ 環境変数による設定
- ✅ 入力バリデーション（Pydantic）
- ✅ 適切なログレベル設定（本番ではDEBUG無効）
