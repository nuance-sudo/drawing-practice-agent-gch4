# ドキュメント更新設計：アーキテクチャ変更の反映

## 修正アプローチ

### 1. 共通のアーキテクチャ変更
- 画像生成ロジックを `packages/agent` から `packages/functions/generate_image` へ分離。
- タスク完了処理を `packages/functions/complete_task` へ集約。
- Agent API から Cloud Functions への HTTP 連携フローを主要な通信経路として記述。

### 2. ファイルごとの主な修正点

#### README.md
- アーキテクチャ図（Mermaid）に Cloud Functions を追加。
- 技術スタックの表に Cloud Run Functions を追加。

#### docs/architecture.md
- AI/ML サービスの用途を Cloud Functions 経由であることに修正。
- ADK ランタイム構成図を修正。

#### docs/functional-design.md
- システム構成図を修正（Agent -> Cloud Functions の流れ）。
- シーケンス図を全面的に修正（Eventarc 駆動から HTTP 連携、および順序の変更）。
- Firestore コレクション名を `tasks` から `review_tasks` へ統一。

#### docs/repository-structure.md
- `packages/functions/` ディレクトリとその配下の構造を追加。
