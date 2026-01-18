---
name: code-quality
description: コード品質チェック、コーディング規約、命名規則、スタイリングの確認。PRレビュー、コードレビュー、品質チェックを依頼されたときに使用。
---

# コード品質チェック

## 目標
プロジェクトのコーディング規約に従っているか確認し、改善点を指摘する。

## 参照ドキュメント

各パッケージの詳細なコーディング規約は以下を参照：

- **packages/agent**: [CODING_RULES.md](packages/agent/CODING_RULES.md) - Python/ADK
- **packages/web**: [CODING_RULES.md](packages/web/CODING_RULES.md) - React/TypeScript
- **packages/infra**: [CODING_RULES.md](packages/infra/CODING_RULES.md) - Terraform/gcloud

## チェック項目

### 1. Python（packages/agent）

#### 必須チェック
- [ ] **型定義**: すべての関数に引数・戻り値の型が指定されているか
- [ ] **Any禁止**: `Any`型が使用されていないか
- [ ] **命名規則**: snake_case（関数/変数）、PascalCase（クラス）
- [ ] **Pydanticモデル**: 構造化データはPydanticで定義されているか
- [ ] **エラーハンドリング**: try-exceptで適切に処理されているか
- [ ] **ログ出力**: print文ではなくstructlogを使用しているか
- [ ] **機密情報**: ハードコードされていないか

#### ADK固有
- [ ] **root_agent定義**: agent.pyにroot_agent変数があるか
- [ ] **Toolデコレータ**: ツール関数に@Toolが付いているか
- [ ] **docstring**: ツール関数にdocstringがあるか

### 2. TypeScript/React（packages/web）

#### 必須チェック
- [ ] **型定義**: すべての変数・関数に型が指定されているか
- [ ] **any禁止**: `any`型が使用されていないか
- [ ] **コンポーネント命名**: PascalCase.tsxになっているか
- [ ] **フック命名**: use + PascalCase.tsになっているか
- [ ] **Props型定義**: コンポーネントのPropsが型定義されているか

#### Zustand
- [ ] **ストア分離**: StateとActionsが分離されているか
- [ ] **persist使用**: 必要に応じてpersistミドルウェアを使用しているか

#### SWR
- [ ] **エラーハンドリング**: errorを適切に処理しているか
- [ ] **ローディング状態**: isLoadingを使用しているか

#### パフォーマンス
- [ ] **useCallback**: イベントハンドラをメモ化しているか
- [ ] **useMemo**: 重い計算をメモ化しているか
- [ ] **React.memo**: 頻繁に再レンダリングされるコンポーネントに適用しているか

### 3. 共通ルール

#### セキュリティ
- [ ] XSS対策（ユーザー入力のエスケープ）
- [ ] 入力バリデーション
- [ ] 機密情報のハードコード禁止

#### Tailwind CSS
- [ ] ユーティリティクラスを適切に使用
- [ ] tailwind-mergeで動的クラスを結合

## チェックコマンド

```bash
# Python
cd packages/agent
uv run ruff check .
uv run ruff format --check .
uv run mypy .

# TypeScript
cd packages/web
pnpm lint
pnpm run typecheck
```

## 出力フォーマット

チェック結果は以下の形式で報告：

```markdown
## コード品質レビュー

### 概要
- 対象ファイル: [ファイル一覧]
- 重大な問題: X件
- 改善提案: Y件

### 重大な問題（必須修正）
1. **[ファイル名:行番号]** 問題の説明
   - 現状: `問題のあるコード`
   - 修正案: `修正後のコード`

### 改善提案（推奨）
1. **[ファイル名:行番号]** 提案内容

### 良い点
- 良い実装のポイント
```

## 制約
- `any`型を見つけたら必ず「重大な問題」として指摘
- 命名規則違反は具体的な修正案を提示
- セキュリティに関わる問題は最優先で報告
