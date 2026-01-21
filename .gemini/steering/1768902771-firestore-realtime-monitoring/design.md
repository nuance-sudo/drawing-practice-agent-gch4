# Firestore Realtime Monitoring Design

## アーキテクチャ変更
- **Frontend**: SWR (`useSWR`) を廃止し、`useSyncExternalStore` と `onSnapshot` を組み合わせたカスタムフック (`useTasks`) を導入。
- **Firestore**: コレクション名を `tasks` から `review_tasks` に統一（バックエンドの実装に合わせる）。
- **Agent**: タスク作成時に同期的に処理を開始するトリガー（FastAPI `BackgroundTasks`）を追加。

## コンポーネント設計

### `useTasks` (Hooks)
- `useTasks(userId)`: ユーザーのタスク一覧をリアルタイム監視。
- `useTask(taskId)`: 単一タスクをリアルタイム監視。
- 内部でデータ変換を行い、Firestoreの Snake Case データを Frontend の Camel Case モデルにマッピング。

### `TaskList` (UI)
- `useTasks` フックを使用するように変更。
- 画像表示部分でGCS公開URLを使用。

## データモデル調整
- Firestore上の `feedback` オブジェクトの構造（フラットな構造）を、Frontendが期待するネストされた `CategoryFeedback` 構造にマッピング。
    - `tone` -> `shading`
    - `line_quality` -> `lineQuality`

## セキュリティ設計
- `firestore.rules`:
    - `review_tasks`: `auth.uid == resource.data.user_id` で読み取り許可。書き込みはサーバーサイドのみ。
- **GCS**:
    - バケットを公開設定 (`allUsers` -> `objectViewer`) に変更し、フロントエンドからの画像表示を許可。
    - Vertex AIからのアクセスエラーもこれにより解消（`gs://` URIへの変換も合わせて実施）。
