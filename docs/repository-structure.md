# 鉛筆デッサンコーチングエージェント リポジトリ構造定義書

## 概要

本ドキュメントは、Google Cloud Hackathon対応版のプロジェクトにおけるリポジトリ構造とファイル配置ルールを定義します。
モノレポ構成を採用し、packages/配下でエージェント・ウェブアプリ・インフラを統合管理します。

> **参考**: [aws-samples/generative-ai-use-cases](https://github.com/aws-samples/generative-ai-use-cases)

---

## ルートディレクトリ構造

```
drawing-practice-agent-gch4/
├── .gemini/                    # ステアリングファイル（作業単位のドキュメント）
├── .github/                    # GitHub Actions ワークフロー
├── packages/                   # モノレポパッケージ
│   ├── agent/                  # エージェント・API実装（Python/ADK）
│   ├── web/                    # ウェブアプリ実装（React/Vite）
│   ├── functions/              # Cloud Run Functions実装（Python）
│   └── infra/                  # インフラ定義（Terraform/gcloud）
├── docs/                       # 永続的ドキュメント
├── scripts/                    # ルートスクリプト（統合デプロイ等）
├── GEMINI.md                   # プロジェクトメモリ
├── Makefile                    # 開発タスク定義（統合管理）
├── README.md                   # プロジェクト概要
└── .gitignore                  # Git除外設定
```

---

## 統合管理

ルートディレクトリから全パッケージを統合管理できます。

### Makefile コマンド

```makefile
# Makefile

# 全体デプロイ
deploy-all:
	@echo "Deploying all packages..."
	$(MAKE) deploy-agent
	$(MAKE) deploy-web

# エージェントのみデプロイ
deploy-agent:
	cd packages/agent && ./scripts/deploy.sh

# ウェブアプリのみデプロイ
deploy-web:
	cd packages/web && firebase deploy --only hosting

# ローカル開発（全体起動）
dev:
	@echo "Starting all services..."
	$(MAKE) -j2 dev-agent dev-web

dev-agent:
	cd packages/agent && uv run uvicorn src.main:app --reload

dev-web:
	cd packages/web && pnpm dev

# テスト（全体）
test:
	$(MAKE) test-agent
	$(MAKE) test-web

test-agent:
	cd packages/agent && uv run pytest tests/ -v

test-web:
	cd packages/web && pnpm test

# リント（全体）
lint:
	$(MAKE) lint-agent
	$(MAKE) lint-web

lint-agent:
	cd packages/agent && uv run ruff check . && uv run mypy .

lint-web:
	cd packages/web && pnpm lint
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
    ├── dessin-coaching.yml    # PRトリガー（オプション）
    ├── ci.yml                 # CI（Lint/Test）
    └── deploy.yml             # デプロイ（Cloud Run）
```

### `packages/agent/` - エージェント・API実装

ADKを使用したエージェントとFastAPI APIサーバー。Cloud Runにデプロイ。

```
packages/agent/
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
│   ├── api/                  # REST APIエンドポイント
│   │   ├── __init__.py
│   │   ├── reviews.py        # 審査API
│   │   ├── tasks.py          # タスクAPI
│   │   └── users.py          # ユーザーAPI
│   │
│   ├── models/               # Pydanticモデル
│   │   ├── __init__.py
│   │   ├── task.py           # タスクモデル
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
│   │   ├── storage_service.py # Cloud Storage連携
│   │   ├── task_service.py   # タスク管理（Firestore）
│   │   ├── rank_service.py   # ランク管理（Firestore）
│   │   ├── push_service.py   # Web Push通知
│   │   └── secrets.py        # Secret Manager連携
│   │
│   ├── tools/                # ADK Tools
│   │   ├── __init__.py
│   │   ├── storage_tool.py   # Cloud Storage操作
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
    ├── deploy.sh             # デプロイスクリプト
    └── local_dev.sh          # ローカル開発用
```

### `packages/web/` - ウェブアプリ実装

React + Vite + Tailwind CSSのウェブアプリ。Firebase Hostingにデプロイ。

```
packages/web/
├── package.json               # Node.js依存関係
├── pnpm-lock.yaml            # 依存関係ロック
├── vite.config.ts            # Vite設定
├── tailwind.config.js        # Tailwind CSS設定
├── tsconfig.json             # TypeScript設定
├── index.html                # HTMLエントリーポイント
├── .env.example              # 環境変数テンプレート
├── README.md                 # ウェブアプリ説明
│
├── public/                   # 静的ファイル
│   ├── favicon.ico
│   ├── manifest.json         # PWAマニフェスト
│   └── sw.js                 # Service Worker
│
├── src/                      # ソースコード
│   ├── main.tsx              # エントリーポイント
│   ├── App.tsx               # ルートコンポーネント
│   ├── index.css             # グローバルスタイル
│   ├── vite-env.d.ts         # Vite型定義
│   │
│   ├── components/           # UIコンポーネント
│   │   ├── common/           # 共通コンポーネント
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   └── Loading.tsx
│   │   ├── ImageUpload.tsx   # 画像アップロード
│   │   ├── FeedbackDisplay.tsx # フィードバック表示
│   │   ├── TaskList.tsx      # タスク一覧
│   │   └── RankBadge.tsx     # ランクバッジ
│   │
│   ├── pages/                # ページコンポーネント
│   │   ├── Home.tsx          # ホーム（アップロード）
│   │   ├── Review.tsx        # 審査結果表示
│   │   └── History.tsx       # 審査履歴
│   │
│   ├── stores/               # Zustandストア
│   │   ├── index.ts
│   │   ├── authStore.ts      # 認証状態
│   │   └── taskStore.ts      # タスク状態
│   │
│   ├── hooks/                # カスタムフック
│   │   ├── useReview.ts      # 審査API
│   │   ├── useTasks.ts       # タスク管理
│   │   └── usePushNotification.ts # プッシュ通知
│   │
│   ├── api/                  # API呼び出し
│   │   ├── client.ts         # HTTPクライアント
│   │   └── reviewApi.ts      # 審査API
│   │
│   ├── types/                # 型定義
│   │   ├── task.ts
│   │   ├── feedback.ts
│   │   └── rank.ts
│   │
│   └── utils/                # ユーティリティ
│       ├── pushNotification.ts
│       └── imageUtils.ts
│
└── tests/                    # テストコード
    └── ...

### `packages/functions/` - Cloud Run Functions実装

画像生成とタスク完了処理を行う軽量なHTTP関数。

```
packages/functions/
├── deploy_functions.sh         # デプロイスクリプト
├── generate_image/             # お手本画像生成関数
│   ├── main.py
│   └── requirements.txt
└── complete_task/               # タスク完了処理関数
    ├── main.py
    └── requirements.txt
```
```

### `packages/infra/` - インフラ定義

GCPリソースの定義とデプロイスクリプト。

```
packages/infra/
├── README.md                  # インフラ説明
├── terraform/                 # Terraform定義（オプション）
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
│
└── scripts/                   # gcloudスクリプト
    ├── setup-project.sh      # プロジェクト初期設定
    ├── setup-storage.sh      # Cloud Storage設定
    ├── setup-eventarc.sh     # Eventarc設定
    └── setup-workload-identity.sh  # Workload Identity設定
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

### `scripts/` - ルートスクリプト

プロジェクト全体に関わるスクリプト。

```
scripts/
├── setup.sh                   # 初期セットアップ
└── deploy-all.sh              # 全体デプロイ
```

---

## ファイル命名規則

### Python ファイル

| 種別 | 命名規則 | 例 |
|------|----------|-----|
| モジュール | snake_case | `storage_tool.py`, `task_service.py` |
| クラス | PascalCase | `DessinCoachingAgent`, `ReviewTask` |
| 関数/変数 | snake_case | `analyze_dessin()`, `task_id` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `STORAGE_BUCKET` |

### TypeScript/React ファイル

| 種別 | 命名規則 | 例 |
|------|----------|-----|
| コンポーネント | PascalCase.tsx | `ImageUpload.tsx`, `TaskList.tsx` |
| フック | camelCase.ts | `useReview.ts`, `useTasks.ts` |
| ストア | camelCase.ts | `taskStore.ts`, `authStore.ts` |
| 型定義 | camelCase.ts | `task.ts`, `feedback.ts` |
| ユーティリティ | camelCase.ts | `imageUtils.ts` |

### ディレクトリ

| 種別 | 命名規則 | 例 |
|------|----------|-----|
| 機能別 | 複数形 camelCase | `components/`, `pages/`, `hooks/` |
| パッケージ | 単数形 | `agent/`, `web/`, `infra/` |

### ドキュメント

| 種別 | 命名規則 | 例 |
|------|----------|-----|
| 永続的ドキュメント | kebab-case | `product-requirements.md` |
| ステアリング | `{unixtime}-{title}/` | `1768700311-webapp-scope-change/` |

---

## 重要なファイル

### エントリーポイント

| ファイル | 用途 |
|----------|------|
| `packages/agent/src/main.py` | FastAPI アプリケーション（Cloud Run用） |
| `packages/agent/src/agent.py` | ADK Agent定義（`root_agent`） |
| `packages/web/src/main.tsx` | React アプリケーション |

### 設定ファイル

| ファイル | 用途 |
|----------|------|
| `packages/agent/pyproject.toml` | Python依存関係・プロジェクト設定 |
| `packages/agent/Dockerfile` | コンテナイメージ定義 |
| `packages/web/package.json` | Node.js依存関係 |
| `packages/web/vite.config.ts` | Vite設定 |
| `packages/web/tailwind.config.js` | Tailwind CSS設定 |
| `Makefile` | 統合タスク管理 |

---

## Git管理ルール

### `.gitignore` に含めるべきファイル

```gitignore
# Python
__pycache__/
*.pyc
.venv/
*.egg-info/

# Node.js
node_modules/
dist/

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
build/

# Terraform
.terraform/
*.tfstate*

# Vite
*.local

# Firebase
.firebase/
firebase-debug.log
```

### コミット対象外

- 秘密情報（APIキー、秘密鍵）
- ローカル設定ファイル（`.env`）
- ビルド成果物（`dist/`, `node_modules/`）
- 一時ファイル

---

## ADK固有の配置ルール

ADK (Agents Development Kit) を使用する場合の必須構成：

### 必須ファイル

| ファイル | 必須 | 用途 |
|----------|------|------|
| `agent.py` | ✅ | エージェント定義（`root_agent` 変数必須） |
| `__init__.py` | ✅ | `from . import agent` を含む |
| `pyproject.toml` | ✅ | 依存関係 |

### root_agent の定義

```python
# packages/agent/src/agent.py
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
| `packages/agent/` | エージェントコードがCloud Runにデプロイ可能 |
| `packages/web/` | ウェブアプリがFirebase Hostingにデプロイ可能 |
| `Makefile` | 統合管理コマンドが動作する |
| ライセンス | ライセンスファイルがある（必要に応じて） |
