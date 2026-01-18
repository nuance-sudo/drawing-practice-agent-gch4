---
name: pre-deploy-check
description: デプロイ前のテスト・構文チェック・リント・型チェックを実行する。deploy、デプロイ、本番反映、リリース前のチェックを依頼されたときに使用。
---

# デプロイ前チェック

## 目標
デプロイ前に構文エラー・型エラー・テスト失敗がないことを確認する。

## 参照ドキュメント

- **コーディング規約**: 各パッケージのCODING_RULES.mdを参照
- **リポジトリ構造**: [docs/repository-structure.md](docs/repository-structure.md)

## 手順

### 1. バックエンド（packages/agent）のチェック

```bash
cd packages/agent

# 1. 依存関係の確認
uv sync

# 2. フォーマットチェック
uv run ruff format --check .

# 3. リント（構文・スタイルチェック）
uv run ruff check .

# 4. 型チェック
uv run mypy .

# 5. テスト実行
uv run pytest tests/ -v
```

**エラー時の対処:**
- `ruff format`: `uv run ruff format .` で自動修正
- `ruff check`: `uv run ruff check --fix .` で自動修正可能な問題を修正
- `mypy`: 型エラーは手動修正が必要（CODING_RULES.md参照）

### 2. フロントエンド（packages/web）のチェック

```bash
cd packages/web

# 1. 依存関係の確認
pnpm install

# 2. 型チェック
pnpm tsc --noEmit

# 3. リント
pnpm lint

# 4. ビルド（本番ビルドが通るか確認）
pnpm build

# 5. テスト実行（テストがある場合）
pnpm test
```

**エラー時の対処:**
- `lint`: `pnpm lint --fix` で自動修正
- `tsc`: 型エラーは手動修正が必要（CODING_RULES.md参照）
- `build`: エラーログを確認して修正

### 3. インフラ（packages/infra）のチェック

```bash
cd packages/infra

# シェルスクリプト構文チェック
shellcheck scripts/*.sh

# Terraform（使用している場合）
terraform fmt -check
terraform validate
```

### 4. 全体チェック（Makefile経由）

```bash
# ルートディレクトリから一括実行
make lint
make test
```

## 出力フォーマット

チェック結果を以下の形式で報告：

```markdown
## デプロイ前チェック結果

### バックエンド（packages/agent）
| チェック項目 | 結果 | 備考 |
|-------------|------|------|
| フォーマット | ✅ / ❌ | |
| リント | ✅ / ❌ | |
| 型チェック | ✅ / ❌ | |
| テスト | ✅ / ❌ | X件成功、Y件失敗 |

### フロントエンド（packages/web）
| チェック項目 | 結果 | 備考 |
|-------------|------|------|
| 型チェック | ✅ / ❌ | |
| リント | ✅ / ❌ | |
| ビルド | ✅ / ❌ | |
| テスト | ✅ / ❌ | |

### 総合判定
- **デプロイ可能**: ✅ / ❌
- **要修正項目**: [該当があれば列挙]
- **修正コマンド**: [自動修正可能な場合は提示]
```

## 判定基準

| 問題レベル | デプロイ可否 | 対応 |
|-----------|-------------|------|
| 型エラー | ❌ ブロック | 必須修正 |
| テスト失敗 | ❌ ブロック | 必須修正 |
| ビルド失敗 | ❌ ブロック | 必須修正 |
| リントエラー | ❌ ブロック | 必須修正 |
| リント警告 | ⚠️ 警告 | 推奨修正 |
| フォーマット | ⚠️ 警告 | 自動修正可能 |

## 制約

- テストが1つでも失敗したら「デプロイ不可」と判定
- 型エラーがあれば必ず報告し「デプロイ不可」
- 警告は報告するが、デプロイ可否判定には影響しない
- 自動修正可能な問題は修正コマンドを提示
