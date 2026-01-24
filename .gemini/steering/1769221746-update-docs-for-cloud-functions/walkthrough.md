# ワークスルー：アーキテクチャ変更に伴うドキュメントの最新化

お手本画像生成機能が Cloud Run Functions へ移行されたことに伴い、プロジェクト全体の永続的ドキュメントを現状の設計と一致するように更新しました。

## 実施した変更

### 1. [README.md](file:///home/ec2-user/src/drawing-practice-agent-gch4/README.md)
- アーキテクチャ図を更新し、Agent API から Cloud Functions への連携（HTTP Request）を追加しました。
- 技術スタック表に `Cloud Run Functions` を追加し、ホスティング先を `Firebase Hosting` に修正しました。

### 2. [docs/architecture.md](file:///home/ec2-user/src/drawing-practice-agent-gch4/docs/architecture.md)
- インフラ構成に Cloud Run Functions を追加しました。
- ADK ランタイム構成図を、Eventarc 駆動から HTTP リクエストベースの非同期フローに更新しました。

### 3. [docs/functional-design.md](file:///home/ec2-user/src/drawing-practice-agent-gch4/docs/functional-design.md)
- システム構成図とシーケンス図を現在の実装（非同期 Cloud Functions 連携）に合わせて更新しました。
- Firestore のコレクション名を、実際のコードに合わせ `tasks` から `review_tasks` へ統一しました。

### 4. [docs/repository-structure.md](file:///home/ec2-user/src/drawing-practice-agent-gch4/docs/repository-structure.md)
- `packages/functions/` ディレクトリ（`generate_image`, `complete_task`）の構造定義を追加しました。

### 5. 全ドキュメントからの旧アーキテクチャ記述の削除
- プロダクト要求定義書、技術仕様書、機能設計書から、旧アーキテクチャの残骸である **Eventarc** の記述を完全に削除し、最新の HTTP 連携フローに統一しました。

## 検証結果
- 各ドキュメントの Mermaid ダイアグラムが正しい構文で記述されていることを確認しました。
- 用語（コレクション名、サービス名）が最新の実装と一致していることを確認しました。

## 完了したタスク
- [x] `README.md` の更新
- [x] `docs/architecture.md` の更新
- [x] `docs/functional-design.md` の更新
- [x] `docs/repository-structure.md` の更新
- [x] ステアリングドキュメントの完了
