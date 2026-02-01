# コード生成計画: Cloud Tasks移行

## ユニット概要

| 項目 | 内容 |
|------|------|
| **ユニット名** | cloud-tasks-migration |
| **目的** | 審査処理をCloud Tasksを使った非同期処理に移行 |
| **依存関係** | Cloud Tasks API, Agent Engine, Firestore |
| **関連ファイル** | `reviews.py`, 新規Cloud Function, 新規Cloud Tasksサービス |

## 実装ステップ

### Phase 1: インフラ準備

#### [x] Step 1: Cloud Tasksキュー作成スクリプト

**ファイル**: `packages/infra/create_cloud_tasks_queue.sh`（新規作成）

**内容**:
- Cloud Tasksキュー `review-processing-queue` の作成
- リージョン: `asia-northeast1`
- タイムアウト: 10分（600秒）
- リトライ: 最大3回（指数バックオフ）

---

### Phase 2: Cloud Function実装

#### [x] Step 2: Cloud Function `process-review` 作成

**ディレクトリ**: `packages/functions/process_review/`（新規作成）

**ファイル**:
- `main.py` - Cloud Function本体
- `requirements.txt` - 依存関係

**処理内容**:
1. Cloud Tasksからのリクエストを受信
2. リクエストからtask_id, user_id, image_urlを取得
3. Agent Engineを呼び出してデッサン分析を実行
4. 結果をFirestoreに保存
5. ランク更新処理
6. フィードバック生成
7. アノテーション画像生成Cloud Functionを呼び出し
8. 最終ステータス更新

**認証**:
- Cloud Tasksサービスアカウントからのみ呼び出し可能
- OIDCトークン検証

---

### Phase 3: API Server変更

#### [x] Step 3: Cloud Tasksクライアントサービス作成

**ファイル**: `packages/agent/src/services/cloud_tasks_service.py`（新規作成）

**内容**:
- Cloud Tasksクライアントの初期化
- タスク作成メソッド `create_review_task()`
- タスクペイロードの構築（task_id, user_id, image_url）
- OIDCトークンの設定

#### [x] Step 4: reviews.py の変更

**ファイル**: `packages/agent/src/api/reviews.py`（既存修正）

**変更内容**:
- `create_review()` から `await process_review_task()` を削除
- Cloud Tasksサービスを使ってタスクをキューに投入
- 即座に `pending` ステータスでレスポンスを返す

---

### Phase 4: デプロイスクリプト更新

#### [x] Step 5: Cloud Function デプロイスクリプト更新

**ファイル**: `packages/functions/deploy_functions.sh`（既存修正）

**内容**:
- `process-review` Cloud Functionのデプロイを追加
- 必要な環境変数の設定
- サービスアカウント権限の設定

---

### Phase 5: 設定ファイル更新

#### [x] Step 6: 環境変数・設定ファイル更新

**ファイル**:
- `packages/agent/.env.example`（既存修正）- Cloud Tasksキュー名、Cloud Function URL追加
- `packages/agent/src/config.py`（既存修正）- 新しい設定項目追加

---

## ファイル一覧

### 新規作成ファイル

| ファイル | 説明 |
|----------|------|
| `packages/infra/create_cloud_tasks_queue.sh` | Cloud Tasksキュー作成スクリプト |
| `packages/functions/process_review/main.py` | Cloud Function本体 |
| `packages/functions/process_review/requirements.txt` | 依存関係 |
| `packages/agent/src/services/cloud_tasks_service.py` | Cloud Tasksクライアントサービス |

### 既存修正ファイル

| ファイル | 変更内容 |
|----------|----------|
| `packages/agent/src/api/reviews.py` | Cloud Tasks投入に変更 |
| `packages/functions/deploy_functions.sh` | process-reviewデプロイ追加 |
| `packages/agent/.env` | 環境変数追加 |
| `packages/agent/src/config.py` | 設定項目追加 |

---

## 依存関係

```
Step 1 (インフラ)
    ↓
Step 2 (Cloud Function)
    ↓
Step 3 (Cloud Tasksサービス) → Step 4 (reviews.py修正)
    ↓
Step 5 (デプロイスクリプト) → Step 6 (設定ファイル)
```

---

## 成功基準

- [ ] Cloud Tasksキューが作成される
- [ ] Cloud Function `process-review` がデプロイできる
- [ ] `/reviews` POST APIが即座にレスポンスを返す
- [ ] Cloud Tasksにタスクが投入される
- [ ] Cloud Functionが審査処理を完了する
- [ ] Firestoreのステータスが正しく更新される
