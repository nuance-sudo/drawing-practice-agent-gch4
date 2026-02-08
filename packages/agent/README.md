# Art coachIng Agent

> 鉛筆デッサンコーチングエージェント

デッサン画像を分析し、フィードバックを提供するAIエージェント。

## 概要

Google Cloud ADK（Agents Development Kit）を使用して、鉛筆デッサンを分析し、
プロポーション、陰影、線の質などの観点から具体的なフィードバックを提供します。

## セットアップ

### 必要条件

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)
- Google Cloud アカウント

### インストール

```bash
# 依存関係のインストール
uv sync

# 開発依存関係を含める場合
uv sync --all-extras
```

### 環境変数

`.env.example` をコピーして `.env` を作成し、必要な値を設定してください。

```bash
cp .env.example .env
```

## 起動

```bash
# ローカル開発サーバー
uv run uvicorn src.main:app --reload --port 8000
```

## API

### ヘルスチェック

```bash
curl http://localhost:8000/health
```

## 開発

### リント・フォーマット

```bash
uv run ruff check .
uv run ruff format .
```

### 型チェック

```bash
uv run mypy .
```

### テスト

```bash
uv run pytest tests/ -v
```
