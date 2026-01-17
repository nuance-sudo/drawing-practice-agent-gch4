# 鉛筆デッサンコーチングエージェント リポジトリ構造定義書

## 概要

本ドキュメントは、Google Cloud Hackathon対応版のプロジェクトにおけるリポジトリ構造とファイル配置ルールを定義します。

---

## ルートディレクトリ構造

```
drawing-practice-agent-gch4/
├── .gemini/                    # ステアリングファイル（作業単位のドキュメント）
├── .github/                    # GitHub Actions ワークフロー
├── agent/                      # エージェント実装（Python/ADK）
├── docs/                       # 永続的ドキュメント
├── infra/                      # インフラ定義（Terraform/gcloud）
├── GEMINI.md                   # プロジェクトメモリ
├── Makefile                    # 開発タスク定義
├── README.md                   # プロジェクト概要
└── .gitignore                  # Git除外設定
```

---

## ディレクトリ詳細

### `.gemini/` - ステアリングファイル

作業単位のドキュメントを管理。作業完了後も履歴として保持。

```
.gemini/
└── steering/
    └── {unixtime}-{開発タイトル}/
        ├── requirements.md     # 今回の作業要求
        ├── design.md          # 変更設計
        ├── task.md            # タスクリスト
        └── walkthrough.md     # 作業完了サマリー
```

### `.github/` - GitHub Actions

```
.github/
└── workflows/
    ├── dessin-coaching.yml    # メインワークフロー（PRトリガー）
    ├── ci.yml                 # CI（Lint/Test）
    └── deploy.yml             # デプロイ（Cloud Run）
```

### `agent/` - エージェント実装

ADKを使用したエージェント実装。Cloud Runにデプロイ。

```
agent/
├── Dockerfile                  # コンテナイメージ定義
├── pyproject.toml             # Pythonプロジェクト設定
├── uv.lock                    # 依存関係ロック
├── .env.example               # 環境変数テンプレート
├── README.md                  # エージェント説明
│
├── src/                       # ソースコード
│   ├── __init__.py
│   ├── main.py               # FastAPIエントリーポイント
│   ├── agent.py              # ADK Agent定義（root_agent）
│   ├── config.py             # 設定管理
│   ├── exceptions.py         # カスタム例外
│   │
│   ├── models/               # Pydanticモデル
│   │   ├── __init__.py
│   │   ├── request.py        # リクエストモデル
│   │   ├── feedback.py       # フィードバックモデル
│   │   ├── analysis.py       # 分析結果モデル
│   │   └── rank.py           # ランクモデル
│   │
│   ├── prompts/              # プロンプト定義
│   │   ├── __init__.py
│   │   └── coaching.py       # コーチングプロンプト
│   │
│   ├── services/             # 外部サービス連携
│   │   ├── __init__.py
│   │   ├── gemini_service.py # Vertex AI Gemini連携
│   │   ├── rank_service.py   # ランク管理（Firestore）
│   │   ├── memory_service.py # メモリ管理（Memory Bank）
│   │   └── secrets.py        # Secret Manager連携
│   │
│   ├── tools/                # ADK Tools
│   │   ├── __init__.py
│   │   ├── github_tool.py    # GitHub API操作
│   │   └── image_tool.py     # 画像処理
│   │
│   └── utils/                # ユーティリティ
│       ├── __init__.py
│       ├── logging.py        # ログ設定
│       └── helpers.py        # 汎用ヘルパー
│
├── tests/                     # テストコード
│   ├── __init__.py
│   ├── conftest.py           # pytest fixtures
│   ├── test_agent.py         # エージェントテスト
│   └── test_services/        # サービステスト
│       └── ...
│
└── scripts/                   # スクリプト
    └── local_dev.sh          # ローカル開発用
```

### `docs/` - 永続的ドキュメント

プロジェクト全体の設計を定義する恒久的なドキュメント。

```
docs/
├── product-requirements.md    # プロダクト要求定義書
├── functional-design.md       # 機能設計書
├── architecture.md            # 技術仕様書
├── repository-structure.md    # リポジトリ構造定義書（本ファイル）
├── development-guidelines.md  # 開発ガイドライン
├── glossary.md                # ユビキタス言語定義
└── images/                    # 画像リソース（必要に応じて）
    └── ...
```

### `infra/` - インフラ定義

GCPリソースの定義とデプロイスクリプト。

```
infra/
├── README.md                  # インフラ説明
├── terraform/                 # Terraform定義（オプション）
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
│
├── scripts/                   # gcloudスクリプト
│   ├── setup-project.sh      # プロジェクト初期設定
│   ├── deploy.sh             # デプロイスクリプト
│   └── setup-workload-identity.sh  # Workload Identity設定
│
└── cloudbuild/               # Cloud Build設定（オプション）
    └── cloudbuild.yaml
```

---

## ファイル命名規則

### Python ファイル

| 種別 | 命名規則 | 例 |
|------|----------|-----|
| モジュール | snake_case | `github_tool.py`, `rank_service.py` |
| クラス | PascalCase | `DessinCoachingAgent`, `UserRank` |
| 関数/変数 | snake_case | `analyze_dessin()`, `user_rank` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |

### ディレクトリ

| 種別 | 命名規則 | 例 |
|------|----------|-----|
| 機能別 | 単数形 snake_case | `model/`, `service/`, `tool/` |
| 複数形OK | 複数形 snake_case | `models/`, `services/`, `tools/` |

### ドキュメント

| 種別 | 命名規則 | 例 |
|------|----------|-----|
| 永続的ドキュメント | kebab-case | `product-requirements.md` |
| ステアリング | `{unixtime}-{title}/` | `1768640110-migration-google-cloud-hackathon/` |

---

## 重要なファイル

### エントリーポイント

| ファイル | 用途 |
|----------|------|
| `agent/src/main.py` | FastAPI アプリケーション（Cloud Run用） |
| `agent/src/agent.py` | ADK Agent定義（`root_agent`） |

### 設定ファイル

| ファイル | 用途 |
|----------|------|
| `agent/pyproject.toml` | Python依存関係・プロジェクト設定 |
| `agent/Dockerfile` | コンテナイメージ定義 |
| `agent/.env.example` | 環境変数テンプレート |
| `Makefile` | 開発タスクショートカット |

---

## Git管理ルール

### `.gitignore` に含めるべきファイル

```gitignore
# Python
__pycache__/
*.pyc
.venv/
*.egg-info/

# 環境変数
.env
.env.local

# IDE
.vscode/
.idea/

# ローカルDB
*.db

# ログ
*.log

# ビルド成果物
dist/
build/

# Terraform
.terraform/
*.tfstate*
```

### コミット対象外

- 秘密情報（APIキー、秘密鍵）
- ローカル設定ファイル（`.env`）
- ビルド成果物
- 一時ファイル

---

## ADK固有の配置ルール

ADK (Agents Development Kit) を使用する場合の必須構成：

### 必須ファイル

| ファイル | 必須 | 用途 |
|----------|------|------|
| `agent.py` | ✅ | エージェント定義（`root_agent` 変数必須） |
| `__init__.py` | ✅ | `from . import agent` を含む |
| `requirements.txt`または`pyproject.toml` | ✅ | 依存関係 |

### root_agent の定義

```python
# agent/src/agent.py
from google.adk import Agent

root_agent = Agent(
    name="dessin-coaching-agent",
    model="gemini-3-flash-preview",
    description="鉛筆デッサンコーチングエージェント",
    tools=[...],
)
```

---

## ハッカソン提出時の構成確認

| 項目 | 確認内容 |
|------|----------|
| `README.md` | プロジェクト概要、セットアップ手順が記載されている |
| `docs/` | 設計ドキュメントが揃っている |
| `.github/workflows/` | CI/CDワークフローが動作する |
| `agent/` | エージェントコードがCloud Runにデプロイ可能 |
| ライセンス | ライセンスファイルがある（必要に応じて） |
