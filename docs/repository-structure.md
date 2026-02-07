# 鉛筆デッサンコーチングエージェント リポジトリ構造定義書

## 概要

本ドキュメントは、Google Cloud Hackathon対応版のプロジェクトにおけるリポジトリ構造とファイル配置ルールを定義します。
モノレポ構成を採用し、packages/配下でエージェント・ウェブアプリ・インフラを統合管理します。

> **参考**: [aws-samples/generative-ai-use-cases](https://github.com/aws-samples/generative-ai-use-cases)

---

## ルートディレクトリ構造

```
drawing-practice-agent-gch4/
├── .agent/                     # エージェントスキル・支援ドキュメント
├── .gemini/                    # ステアリングファイル（作業単位のドキュメント）
├── .github/                    # GitHub Actions ワークフロー
├── packages/                   # モノレポパッケージ
│   ├── agent/                  # エージェント・API実装（Python/ADK）
│   ├── web/                    # ウェブアプリ実装（Next.js）
│   ├── functions/              # Cloud Run Functions実装（Python）
│   └── infra/                  # インフラ定義（gcloud/補助スクリプト）
├── docs/                       # 永続的ドキュメント
├── GEMINI.md                   # プロジェクトメモリ
├── README.md                   # プロジェクト概要
└── .gitignore                  # Git除外設定
```

---

## 統合管理

ルートディレクトリから全パッケージを統合管理できます。

### 統合コマンド

現時点ではルートの統合Makefileはありません。各パッケージ配下のスクリプトを使用します。

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
    └── verify-gcp-auth.yml    # GCP認証確認
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
├── dessin_coaching_agent/     # ADKエージェント（Vertex AI Agent Engineデプロイ用）
│   ├── __init__.py
│   ├── agent.py              # root_agent定義
│   ├── tools.py              # analyze_dessin_imageツール
│   ├── models.py             # DessinAnalysis, GrowthAnalysis等
│   ├── prompts.py            # コーチング用プロンプト
│   ├── callbacks.py          # Memory Bank保存コールバック
│   ├── memory_tools.py       # メモリ検索ツール
│   └── config.py             # エージェント設定
│
├── src/                       # APIサーバーソースコード
│   ├── __init__.py
│   ├── main.py               # FastAPIエントリーポイント
│   ├── config.py             # 設定管理
│   ├── auth.py               # 認証処理
│   ├── exceptions.py         # カスタム例外
│   │
│   ├── api/                  # REST APIエンドポイント
│   │   ├── __init__.py
│   │   └── reviews.py        # 審査API
│   │
│   ├── models/               # Pydanticモデル
│   │   ├── __init__.py
│   │   ├── task.py           # タスクモデル
│   │   ├── feedback.py       # フィードバックモデル
│   │   └── rank.py           # ランクモデル
│   │
│   └── services/             # 外部サービス連携
│       ├── __init__.py
│       ├── agent_engine_service.py  # Agent Engine呼び出し
│       ├── cloud_tasks_service.py   # Cloud Tasks連携
│       ├── gemini_service.py        # Vertex AI Gemini連携
│       ├── task_service.py          # タスク管理（Firestore）
│       ├── rank_service.py          # ランク管理（Firestore）
│       ├── feedback_service.py      # フィードバック生成
│       ├── annotation_service.py    # アノテーション生成
│       ├── image_generation_service.py  # 画像生成
│       └── memory_service.py        # Memory Bank連携
│
├── tests/                     # テストコード
│   ├── __init__.py
│   ├── conftest.py           # pytest fixtures
│   └── ...
│
└── scripts/                   # スクリプト
    ├── deploy.sh             # デプロイスクリプト
    └── deploy_agent.sh       # Agent Engineデプロイ
```

### `packages/web/` - ウェブアプリ実装

Next.js + App Router + Tailwind CSSのウェブアプリ。

```
packages/web/
├── package.json               # Node.js依存関係
├── package-lock.json         # 依存関係ロック
├── next.config.ts            # Next.js設定
├── tailwind.config.ts        # Tailwind CSS設定
├── eslint.config.mjs         # ESLint設定
├── postcss.config.mjs        # PostCSS設定
├── tsconfig.json             # TypeScript設定
├── .env.example              # 環境変数テンプレート
├── README.md                 # ウェブアプリ説明
│
├── src/
│   ├── app/                  # App Router
│   │   ├── globals.css       # グローバルスタイル
│   │   ├── layout.tsx        # ルートレイアウト
│   │   ├── page.tsx          # ホーム（ログイン）
│   │   └── (authenticated)/  # 認証必須ページ
│   │       ├── layout.tsx
│   │       ├── review/
│   │       │   └── page.tsx
│   │
│   ├── components/           # UIコンポーネント
│   │   ├── auth-provider.tsx
│   │   ├── login-button.tsx
│   │   ├── common/           # 共通コンポーネント
│   │   └── features/         # 機能別コンポーネント
│   │
│   ├── stores/               # Zustandストア
│   │   └── ...
│   │
│   ├── hooks/                # カスタムフック
│   │   └── ...
│   │
│   ├── lib/                  # ユーティリティ
│   │   ├── firebase.ts       # Firebase初期化
│   │   └── api.ts            # API呼び出し
│   │
│   └── types/                # 型定義
│       └── ...
│
├── public/                   # 静的ファイル
│   ├── favicon.ico
│   └── sw.js                 # Service Worker
│
└── tests/                    # テストコード
    └── ...

### `packages/functions/` - Cloud Run Functions実装

画像生成、アノテーション生成、タスク完了処理、レビュー処理を行う軽量なHTTP関数。

```
packages/functions/
├── deploy_functions.sh         # デプロイスクリプト
├── .env.example                # 環境変数テンプレート
├── annotate_image/             # アノテーション画像生成関数
│   ├── main.py
│   └── requirements.txt
├── generate_image/             # お手本画像生成関数
│   ├── main.py
│   └── requirements.txt
├── complete_task/              # タスク完了処理関数
│   ├── main.py
│   └── requirements.txt
└── process_review/             # レビュー処理関数（Cloud Tasksから呼び出し）
    ├── main.py
    └── requirements.txt
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
| `packages/agent/dessin_coaching_agent/agent.py` | ADK Agent定義（`root_agent`） |
| `packages/web/src/app/layout.tsx` | Next.js ルートレイアウト |

### 設定ファイル

| ファイル | 用途 |
|----------|------|
| `packages/agent/pyproject.toml` | Python依存関係・プロジェクト設定 |
| `packages/agent/Dockerfile` | コンテナイメージ定義 |
| `packages/web/package.json` | Node.js依存関係 |
| `packages/web/next.config.ts` | Next.js設定 |
| `packages/web/tailwind.config.ts` | Tailwind CSS設定 |

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
# packages/agent/dessin_coaching_agent/agent.py
from google.adk.agents import Agent

root_agent = Agent(
    name="dessin_coaching_agent",
    model=gemini_model,
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
| `packages/web/` | ウェブアプリが任意のホスティングにデプロイ可能 |
| `Makefile` | 統合管理コマンドが動作する |
| ライセンス | ライセンスファイルがある（必要に応じて） |
