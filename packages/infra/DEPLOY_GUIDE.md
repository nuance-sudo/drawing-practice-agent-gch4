# GCPリソース デプロイガイド

本ドキュメントは、デプロイ済みのGCPリソースの概要と、デプロイ手順をまとめたものです。

---

## デプロイ済みリソース一覧

| サービス | リソース名 | リージョン | 備考 |
|----------|-----------|----------|------|
| Agent Engine | `1367965088278904832` | us-central1 | デッサンコーチングエージェント |
| Cloud Run | `dessin-coaching-agent` | us-central1 | エージェントAPI（従来方式） |
| Artifact Registry | `drawing-practice-agent` | us-central1 | Dockerイメージ |
| Cloud Storage | `drawing-practice-agent-gch4` | - | 画像ストレージ |
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
| `AGENT_ENGINE_ID` | `1367965088278904832` | Agent Engine リソースID |
| `AGENT_ENGINE_LOCATION` | `us-central1` | Agent Engine リージョン |
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

# ADK CLI でデプロイ
uv run adk deploy agent_engine \
  --project=drawing-practice-agent \
  --region=us-central1 \
  --staging_bucket=gs://drawing-practice-agent-staging \
  --display_name="Dessin Coaching Agent" \
  --requirements_file=dessin_coaching_agent/requirements.txt \
  dessin_coaching_agent
```

**デプロイ成功後の出力例:**
```
✅ Created agent engine: projects/333660601649/locations/us-central1/reasoningEngines/{AGENT_ENGINE_ID}
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
  --staging_bucket={STAGING_BUCKET} \
  --agent_engine_id={AGENT_ENGINE_ID} \
  --requirements_file=dessin_coaching_agent/requirements.txt \
  dessin_coaching_agent
```

> **Note**: Agent Engine の料金については [Vertex AI Agent Engine 料金ページ](https://cloud.google.com/vertex-ai/pricing#vertex-ai-agent-engine) を参照してください。

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

### 4. Firestoreセキュリティルールのデプロイ

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