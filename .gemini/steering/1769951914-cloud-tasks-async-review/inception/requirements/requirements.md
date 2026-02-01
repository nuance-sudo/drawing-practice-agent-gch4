# 要件定義書: Cloud Tasks移行による審査処理の非同期化

## 意図分析サマリー

| 項目 | 内容 |
|------|------|
| **ユーザーリクエスト** | 審査処理をCloud Tasksに移行してバックグラウンド処理を安定化 |
| **リクエストタイプ** | Enhancement（バックグラウンド処理の改善） |
| **スコープ** | Multiple Components（API、Cloud Functions、インフラ） |
| **複雑度** | Moderate（GCPサービス統合） |
| **GitHub Issue** | [#62](https://github.com/nuance-sudo/drawing-practice-agent-gch4/issues/62) |

---

## 背景と問題

### 現状の問題

1. **同期処理によるUX悪化**
   - 現在の`/reviews` POST APIは`await process_review_task()`で同期的に処理完了を待機
   - ユーザーはレスポンス待ち（数分）になりUXが悪化

2. **以前の問題（解決済み）**
   - `asyncio.create_task()`を使ったバックグラウンドタスクは、Cloud RunインスタンスがHTTPレスポンス後にシャットダウンされると実行されない問題があった
   - 暫定対応として同期処理に変更

### 目標

- **即時レスポンス**: `/reviews` POST APIは即座にレスポンスを返す
- **信頼性**: Cloud Tasksによりタスク実行が保証される
- **リトライ機能**: 失敗時の自動リトライ

---

## 提案アーキテクチャ

```
[Web App] → [Cloud Run API] → [Cloud Tasks Queue] → [Cloud Function] → [Agent Engine]
                 ↓                                         ↓
            [Firestore]  ←─────────────────────────────────┘
                 ↑
[Web App] ← [Firestore Realtime Listener]
```

### フロー

1. ユーザーが画像をアップロードし、審査リクエストを送信
2. Cloud Run APIがタスクをCloud Tasksキューに投入
3. APIは即座に`pending`ステータスでレスポンスを返す
4. Cloud TasksがCloud Functionを呼び出し
5. Cloud FunctionがAgent Engineを呼び出して審査処理を実行
6. 結果をFirestoreに保存
7. フロントエンドがFirestoreリアルタイム監視で更新を検知

---

## 機能要件

### FR-1: Cloud Tasksキューの作成

| 項目 | 内容 |
|------|------|
| **キュー名** | `review-processing-queue` |
| **リージョン** | `asia-northeast1`（既存インフラと同じ） |
| **タイムアウト** | 10分 |
| **リトライ** | 最大3回（指数バックオフ） |

### FR-2: タスク投入APIの変更

| 項目 | 内容 |
|------|------|
| **エンドポイント** | `POST /reviews`（既存） |
| **変更内容** | `process_review_task()`の同期呼び出しをCloud Tasksへの投入に変更 |
| **レスポンス** | 即座に`pending`ステータスのタスク情報を返す |

### FR-3: Cloud Function実装

| 項目 | 内容 |
|------|------|
| **関数名** | `process-review` |
| **トリガー** | HTTP（Cloud Tasksから呼び出し） |
| **処理内容** | 既存の`process_review_task()`ロジックを移植 |
| **認証** | サービスアカウント（Cloud Tasks → Cloud Function） |

### FR-4: Firestoreステータス更新

| 項目 | 内容 |
|------|------|
| **ステータス遷移** | `pending` → `processing` → `completed` / `failed` |
| **エラー時** | `status: failed`、`error_message`フィールドに詳細を保存 |
| **フロントエンド通知** | 既存のFirestoreリアルタイム監視を継続（変更なし） |

---

## 非機能要件

### NFR-1: パフォーマンス

| 項目 | 目標値 |
|------|--------|
| APIレスポンス時間 | 500ms以内（タスク投入まで） |
| タスク処理時間 | 10分以内（タイムアウト設定） |

### NFR-2: 信頼性

| 項目 | 内容 |
|------|------|
| リトライ | 最大3回（指数バックオフ） |
| デッドレターキュー | 3回失敗後はエラーログ出力 |

### NFR-3: セキュリティ

| 項目 | 内容 |
|------|------|
| Cloud Function認証 | Cloud Tasksサービスアカウントからのみ呼び出し可能 |
| タスクペイロード | task_id, user_id, image_url（最小限の情報） |

---

## 技術選択サマリー

| 項目 | 選択 |
|------|------|
| タスク処理リソース | **Cloud Functions（Gen 2）** |
| 進捗通知方式 | **Firestoreリアルタイム監視（現状維持）** |
| タイムアウト | **10分** |
| リトライ戦略 | **最大3回（指数バックオフ）** |
| インフラ管理 | **gcloud CLIスクリプト** |
| エラー通知 | **Firestoreステータス更新** |

---

## 実装スコープ

### In Scope

- [x] Cloud Tasksキュー作成（gcloud CLI）
- [x] Cloud Function `process-review` 実装
- [x] `/reviews` API変更（Cloud Tasks投入）
- [x] Firestoreステータス更新ロジック
- [x] サービスアカウント権限設定

### Out of Scope

- [ ] フロントエンド変更（現状のFirestore監視を継続）
- [ ] プッシュ通知実装
- [ ] デッドレターキュー（将来の拡張）

---

## 影響範囲

### 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `packages/agent/src/api/reviews.py` | `create_review()`をCloud Tasks投入に変更 |
| `packages/agent/src/services/` | Cloud Tasksクライアントサービス追加 |
| `packages/infra/scripts/` | Cloud Tasksキュー作成スクリプト追加 |
| **新規作成** | Cloud Function `process-review` |

### 変更なし

- `packages/web/` - フロントエンド（Firestore監視継続）
- `packages/agent/src/services/agent_engine_service.py` - Agent Engine呼び出し（ロジック移植）

---

## 受入条件

1. `/reviews` POST APIが500ms以内にレスポンスを返す
2. Cloud Tasksにタスクが正常に投入される
3. Cloud Functionが呼び出され、審査処理が完了する
4. Firestoreのタスクステータスが正しく更新される
5. フロントエンドで審査結果が表示される
6. 失敗時にリトライが実行される
7. 3回失敗後にタスクが`failed`ステータスになる
