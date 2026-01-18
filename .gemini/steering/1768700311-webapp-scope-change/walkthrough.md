# Walkthrough: ウェブアプリスコープ変更とドキュメント更新

## 概要

PRベースからウェブアプリベースへのスコープ変更に伴い、4つのドキュメントを全面更新。
Agent Skills、CODING_RULES、GEMINI.mdを整備。

## 変更サマリー

| カテゴリ | ファイル | 変更内容 |
|---------|---------|---------|
| ドキュメント | `docs/product-requirements.md` | ウェブアプリ機能・ユーザーストーリー刷新 |
| ドキュメント | `docs/functional-design.md` | システム構成図・処理フロー全面更新 |
| ドキュメント | `docs/architecture.md` | フロントエンド技術スタック追加 |
| ドキュメント | `docs/repository-structure.md` | packages/モノレポ構成に変更 |
| コーディング規約 | `packages/agent/CODING_RULES.md` | Python/ADK規約 |
| コーディング規約 | `packages/web/CODING_RULES.md` | React/TypeScript規約 |
| コーディング規約 | `packages/infra/CODING_RULES.md` | Terraform/gcloud規約 |
| Agent Skills | `.agent/skills/pre-deploy-check/` | デプロイ前チェック |
| Agent Skills | `.agent/skills/code-quality/` | コード品質チェック |
| Agent Skills | `.agent/skills/git-commit/` | Gitコミット手順 |
| 設定 | `GEMINI.md` | モノレポ構成追加、Skills参照追加 |

## 決定事項

- **フロントエンド**: React 19 + Vite 7 + Tailwind 4 + Zustand 5 + SWR
- **ホスティング**: Vercel（ウェブ）、Cloud Run（エージェント）
- **トリガー**: Eventarc即時実行
- **通知**: Web Push API
- **ランク制度**: 80点以上で昇格、レベル別評価基準

## 次のステップ

- MVPラベル付きIssueの実装開始
