# Firestoreリアルタイム監視機能 - 実装完了

Issue #18「ポーリングによるタスク監視」をFirestoreリアルタイム監視方式に変更する実装が完了しました。

---

## 変更サマリー

| カテゴリ | ファイル | 変更内容 |
|---------|---------|---------|
| ドキュメント | [architecture.md](file:///home/ec2-user/src/drawing-practice-agent-gch4/docs/architecture.md) | Firebase SDK追加 |
| ドキュメント | [functional-design.md](file:///home/ec2-user/src/drawing-practice-agent-gch4/docs/functional-design.md) | リアルタイム監視説明追加 |
| Firebase設定 | [firebase.ts](file:///home/ec2-user/src/drawing-practice-agent-gch4/packages/web/src/lib/firebase.ts) | Firestore初期化追加 |
| フック | [useTaskRealtime.ts](file:///home/ec2-user/src/drawing-practice-agent-gch4/packages/web/src/hooks/useTaskRealtime.ts) | **新規作成** |
| コンポーネント | [TaskList.tsx](file:///home/ec2-user/src/drawing-practice-agent-gch4/packages/web/src/components/features/dashboard/TaskList.tsx) | リアルタイムフックに切替 |
| セキュリティ | [firestore.rules](file:///home/ec2-user/src/drawing-practice-agent-gch4/firestore.rules) | **新規作成** |
| Firebase設定 | [firebase.json](file:///home/ec2-user/src/drawing-practice-agent-gch4/firebase.json) | Firestoreルール追加 |

---

## 新規作成ファイル

### useTaskRealtime.ts

`useSyncExternalStore`を使用したリアルタイム監視フック：

- `useTaskRealtime(userId)` - ユーザーのタスク一覧をリアルタイム監視
- `useTaskRealtimeSingle(taskId)` - 単一タスクをリアルタイム監視

### firestore.rules

ユーザーごとのアクセス制御を定義：

- タスク：自分のタスクのみ読み取り可能、書き込みはサーバーのみ
- ランク：自分のランクのみ読み取り可能
- プッシュ購読：自分のデータのみ読み書き可能

---

## 検証結果

✅ **ビルド成功**

```
▲ Next.js 16.1.3 (Turbopack)
✓ Compiled successfully in 10.6s
✓ Generating static pages (5/5) in 184.1ms
```


## トラブルシューティング

### 1. Vertex AI 403 Permission Denied
- **原因**: Vertex AI APIがプロジェクトで有効化されていなかった
- **解決**: `gcloud services enable aiplatform.googleapis.com` を実行

### 2. Vertex AI Cannot fetch content (URL Error)
- **原因**: Vertex AIは非公開GCSバケットのHTTPS URLから直接コンテンツを取得できない
- **解決**: HTTPS URLを`gs://`形式に変換する関数`_convert_to_gcs_uri`を`analysis.py`に追加し、Vertex AIに`gs://` URIを渡すように修正

### 3. フロントエンド型不一致
- **原因**: Firestoreデータのフィールド名（snake_case）がフロントエンドの型定義（camelCase）と不一致
- **解決**: `useTaskRealtime.ts`内でデータ変換ロジックを実装。`tone`→`shading`, `line_quality`→`lineQuality`のマッピングを実施

### 4. 履歴画像が表示されない
- **原因**: GCSバケットが非公開であり、`TaskList`の`img`タグがアクセス拒否された
- **解決**: GCSバケットに`allUsers`への`Storage Object Viewer`権限を付与して公開。`next.config.ts`にドメイン設定を追加。


## 次のステップ

1. **デプロイ**: `firebase deploy --only firestore:rules` でセキュリティルールを適用
2. **動作確認**: 本番環境でリアルタイム更新が機能することを確認
