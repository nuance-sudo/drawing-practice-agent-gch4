# GCPリソース デプロイガイド

本ドキュメントは、デプロイ済みのGCPリソースの概要と、デプロイ手順をまとめたものです。

---

## デプロイ済みリソース一覧

| サービス | リソース名 | リージョン | 備考 |
|----------|-----------|----------|------|
| Agent Engine | `<AGENT_ENGINE_ID>` | us-central1 | デッサンコーチングエージェント |
| Cloud Run | `dessin-coaching-agent` | us-central1 | エージェントAPI（従来方式） |
| Cloud Functions | `process-review` | us-central1 | 審査処理メイン |
| Cloud Functions | `annotate-image` | us-central1 | 画像アノテーション生成 |
| Cloud Functions | `generate-image` | us-central1 | お手本画像生成 |
| Cloud Functions | `complete-task` | us-central1 | タスク完了処理 |
| Artifact Registry | `drawing-practice-agent` | us-central1 | Dockerイメージ |
| Cloud Storage | `drawing-practice-agent-images` | us-central1 | 生成画像ストレージ |
| Cloud Storage | `drawing-practice-agent-staging` | us-central1 | Agent Engineステージング用 |
| Firestore | `(default)` | asia-northeast1 | タスク・データ管理 |

---

## 環境変数

Cloud Runサービスに設定されている環境変数：

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `GCP_PROJECT_ID` | `<YOUR_PROJECT_ID>` | GCPプロジェクトID |
| `GCP_REGION` | `global` | Gemini API用リージョン ※ |
| `FIRESTORE_DATABASE` | `(default)` | Firestoreデータベース名 |
| `STORAGE_BUCKET` | `<YOUR_BUCKET_NAME>` | Cloud Storageバケット名 |
| `AGENT_ENGINE_ID` | `<AGENT_ENGINE_ID>` | Agent Engine リソースID |
| `AGENT_ENGINE_LOCATION` | `us-central1` | Agent Engine リージョン |
| `CORS_ORIGINS` | `https://<PROJECT>.web.app,https://<PROJECT>.firebaseapp.com` | CORS許可オリジン（カンマ区切り） |
| `DEBUG` | `false` | デバッグモード |
| `LOG_LEVEL` | `INFO` | ログレベル |

---

## デプロイ手順
 
 ### 1. Web アプリ (FrontEnd)
 Firebase Hosting にデプロイします。
 
 ```bash
 # 1. ビルド
 cd packages/web
 npm run build
 
 # 2. ルートに戻ってデプロイ
 cd ../..
 firebase deploy --only hosting --project drawing-practice-agent
 ```
 
### 2. Agent (BackEnd)

#### Option A: Vertex AI Agent Engine へデプロイ（推奨）

ADK CLI を使用して Vertex AI Agent Engine にエージェントをデプロイします。
エージェントはマネージドサービスとして実行され、スケーリングやインフラ管理が不要です。

```bash
cd packages/agent

# 1. 環境変数ファイルを作成（初回のみ）
cat > dessin_coaching_agent/.env << EOF
AGENT_ENGINE_ID=<YOUR_AGENT_ENGINE_ID>
AGENT_ENGINE_REGION=us-central1
GEMINI_LOCATION=global

# テレメトリー有効化（Cloud Trace連携）
GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true

# プロンプト入力とレスポンス出力のロギング有効化
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true
EOF

# 2. ADK CLI でデプロイ
uv run adk deploy agent_engine \
  --project=drawing-practice-agent \
  --region=us-central1 \
  --display_name="Dessin Coaching Agent" \
  --requirements_file=dessin_coaching_agent/requirements.txt \
  --env_file=dessin_coaching_agent/.env \
  --trace_to_cloud \
  --otel_to_cloud \
  dessin_coaching_agent
```

**出力された Resource ID を `.env` に設定:**
```bash
AGENT_ENGINE_ID={AGENT_ENGINE_ID}
```

**既存のAgent Engineを更新する場合:**
```bash
uv run adk deploy agent_engine \
  --project=drawing-practice-agent \
  --region=us-central1 \
  --agent_engine_id={AGENT_ENGINE_ID} \
  --requirements_file=dessin_coaching_agent/requirements.txt \
  --env_file=dessin_coaching_agent/.env \
  --trace_to_cloud \
  --otel_to_cloud \
  dessin_coaching_agent
```
#### Option B: Cloud Run へデプロイ（従来方式）

Container Registry (Artifact Registry) にビルドして Cloud Run にデプロイします。
※ `packages/agent` ディレクトリで実行してください。

```bash
cd packages/agent

# 0. Artifact Registryリポジトリを作成（初回のみ）
gcloud artifacts repositories create drawing-practice-agent \
  --repository-format=docker \
  --location=us-central1 \
  --project=drawing-practice-agent \
  || echo "Repository may already exist"

# 1. ビルド & Push
gcloud builds submit --region=us-central1 --tag us-central1-docker.pkg.dev/drawing-practice-agent/drawing-practice-agent/agent:latest --project=drawing-practice-agent .
 
# 2. デプロイ（env.yamlで環境変数を管理）
gcloud run deploy dessin-coaching-agent \
  --image us-central1-docker.pkg.dev/drawing-practice-agent/drawing-practice-agent/agent:latest \
  --platform managed \
  --region us-central1 \
  --project=drawing-practice-agent \
  --env-vars-file=env.yaml
 ```

 ### 3. アクセス権限の設定（初回のみ / CORSエラー対策）
 Cloud Runサービスを公開設定にし、ブラウザからのプリフライトリクエスト(OPTIONS)を許可します。
 ※ アプリケーションレベルで認証（Firebase Auth）を行っているため、サービス自体は公開設定とします。
 
 ```bash
 gcloud run services add-iam-policy-binding dessin-coaching-agent \
   --region=us-central1 \
   --project=drawing-practice-agent \
   --member="allUsers" \
   --role="roles/run.invoker"
 ```

### 4. Cloud Functions（審査処理API）のデプロイ

Cloud Functions (2nd gen) として審査処理関連のAPIをデプロイします。

| 関数名 | 説明 |
|--------|------|
| `process-review` | 審査処理メイン（Agent Engine呼び出し） |
| `annotate-image` | 画像アノテーション生成 |
| `generate-image` | お手本画像生成 |
| `complete-task` | タスク完了処理 |

#### 一括デプロイ

デプロイスクリプトを使用して全関数を一括デプロイします。

```bash
# 1. 環境変数ファイルを作成
cat > packages/functions/.env << EOF
REGION=us-central1
GCS_BUCKET_NAME=drawing-practice-agent-images
AGENT_ENGINE_ID=<AGENT_ENGINE_ID>
AGENT_ENGINE_LOCATION=us-central1
EOF

# 2. リポジトリルートからデプロイスクリプトを実行
cd /path/to/drawing-practice-agent-gch4
./packages/functions/deploy_functions.sh
```

### 5. Firestoreセキュリティルールのデプロイ

Firestoreのセキュリティルールを更新した場合は、以下のコマンドでデプロイします。

```bash
firebase deploy --only firestore:rules --project drawing-practice-agent
```

**必要なコレクションとルール:**

| コレクション | 用途 | 読み取り権限 |
|-------------|------|-------------|
| `review_tasks` | 審査タスク | 自分のタスクのみ |
| `users` | ユーザーランク情報 | 自分のドキュメントのみ |
| `push_subscriptions` | プッシュ通知設定 | 自分の設定のみ（読み書き可） |
 
 ---
 
 ## トラブルシューティング
 
 ### `exec format error` が発生する
 
 ARM64マシンでビルドしたイメージをCloud Runにデプロイした際に発生します。
 上記の `gcloud builds submit` コマンドを使用することで、Cloud Build上で適切なプラットフォーム向けのビルドが行われるため、この問題を回避できます。
 
 ### コンテナがポート8080でリッスンしない
 
 Cloud Runのログを確認してください：
 ```bash
 gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=dessin-coaching-agent" --limit=30
 ```

### Geminiモデルが見つからない（404エラー）

**症状**:
```
404 NOT_FOUND. Publisher Model `projects/.../models/gemini-3-flash-preview` was not found
```

**原因**: Gemini 3 Flash Preview など一部のモデルは、特定のリージョン（`us-central1` など）では利用できません。

**解決策**: `env.yaml` の `GCP_REGION` を `global` に設定してください：
```yaml
GCP_REGION: global
```

> **Note**: Gemini 3モデルはグローバルエンドポイント経由でのみアクセス可能です。
> 詳細: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations`