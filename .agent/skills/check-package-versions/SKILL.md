---
name: check-package-versions
description: Pythonパッケージの最新バージョンを確認し、pyproject.tomlを更新する
---

# パッケージバージョン確認スキル

Pythonパッケージの最新バージョンを確認し、必要に応じて`pyproject.toml`を更新します。

## いつ使うか

- 新規プロジェクト作成時
- 定期的なバージョン更新時
- セキュリティアップデート確認時

## 手順

### 1. 現在のバージョン確認

`packages/agent/pyproject.toml`の依存関係を確認します。

### 2. 最新バージョンの取得

以下のコマンドで各パッケージの最新バージョンを確認します：

```bash
# 主要パッケージのバージョン確認
pip index versions google-adk 2>&1 | head -2
pip index versions google-cloud-aiplatform 2>&1 | head -2
pip index versions google-cloud-firestore 2>&1 | head -2
pip index versions google-cloud-storage 2>&1 | head -2
pip index versions fastapi 2>&1 | head -2
pip index versions uvicorn 2>&1 | head -2
pip index versions pydantic 2>&1 | head -2
pip index versions structlog 2>&1 | head -2
```

### 3. pyproject.tomlの更新

最新バージョンを確認後、`packages/agent/pyproject.toml`の依存関係を更新します。

```toml
dependencies = [
    "google-adk>=X.Y.Z",
    "google-cloud-aiplatform>=X.Y.Z",
    "google-cloud-firestore>=X.Y.Z",
    "google-cloud-storage>=X.Y.Z",
    "fastapi>=X.Y.Z",
    "uvicorn[standard]>=X.Y.Z",
    "pydantic>=X.Y.Z",
    "structlog>=X.Y.Z",
    # ...
]
```

### 4. 依存関係の再インストール

```bash
cd packages/agent
rm -rf .venv uv.lock
uv sync
```

### 5. 動作確認

```bash
uv run uvicorn src.main:app --port 8000 &
sleep 3
curl http://localhost:8000/health
pkill -f "uvicorn"
```

### 6. ドキュメント更新

`docs/architecture.md`のバージョン情報を更新します。

## 確認対象パッケージ一覧

| パッケージ | 用途 | PyPI |
|-----------|------|------|
| google-adk | ADKエージェント構築 | [PyPI](https://pypi.org/project/google-adk/) |
| google-cloud-aiplatform | Vertex AI連携 | [PyPI](https://pypi.org/project/google-cloud-aiplatform/) |
| google-cloud-firestore | Firestore連携 | [PyPI](https://pypi.org/project/google-cloud-firestore/) |
| google-cloud-storage | Cloud Storage連携 | [PyPI](https://pypi.org/project/google-cloud-storage/) |
| fastapi | REST API | [PyPI](https://pypi.org/project/fastapi/) |
| uvicorn | ASGIサーバー | [PyPI](https://pypi.org/project/uvicorn/) |
| pydantic | データバリデーション | [PyPI](https://pypi.org/project/pydantic/) |
| structlog | 構造化ログ | [PyPI](https://pypi.org/project/structlog/) |
| tenacity | リトライ処理 | [PyPI](https://pypi.org/project/tenacity/) |
| pillow | 画像処理 | [PyPI](https://pypi.org/project/pillow/) |

## 注意事項

- メジャーバージョンアップ時は破壊的変更がないか確認
- ADKは頻繁にアップデートされるため、リリースノートを確認
- セキュリティアップデートは優先的に適用
