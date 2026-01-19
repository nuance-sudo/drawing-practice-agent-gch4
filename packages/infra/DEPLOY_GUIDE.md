# GCPリソース デプロイガイド

本ドキュメントは、デプロイ済みのGCPリソースの概要と、デプロイ手順をまとめたものです。

---

## デプロイ済みリソース一覧

| サービス | リソース名 | リージョン | 備考 |
|----------|-----------|----------|------|
| Cloud Run | `dessin-coaching-agent` | asia-northeast1 | エージェントAPI |
| Artifact Registry | `drawing-practice-agent` | asia-northeast1 | Dockerイメージ |
| Cloud Storage | `drawing-practice-agent-gch4` | - | 画像ストレージ |
| Firestore | `(default)` | asia-northeast1 | タスク・データ管理 |

---

## 環境変数

Cloud Runサービスに設定されている環境変数：

| 変数名 | 値 | 説明 |
|--------|-----|------|
| `GCP_PROJECT_ID` | `<YOUR_PROJECT_ID>` | GCPプロジェクトID |
| `GCP_REGION` | `asia-northeast1` | リージョン |
| `FIRESTORE_DATABASE` | `(default)` | Firestoreデータベース名 |
| `STORAGE_BUCKET` | `<YOUR_BUCKET_NAME>` | Cloud Storageバケット名 |
| `DEBUG` | `false` | デバッグモード |
| `LOG_LEVEL` | `INFO` | ログレベル |

---

## デプロイ手順

### 1. gcloud CLI の認証

```bash
gcloud auth login
gcloud config set project <YOUR_PROJECT_ID>
gcloud config set run/region asia-northeast1
```

### 2. Artifact Registry へのDocker認証

```bash
gcloud auth configure-docker asia-northeast1-docker.pkg.dev
```

### 3. Dockerイメージのビルド・プッシュ

> [!CAUTION]
> **ARMアーキテクチャでのビルド時の注意**
>
> ARM64マシン（Apple Silicon Mac、AWS Graviton等）でビルドしたイメージは、
> Cloud Run（AMD64）では動作しません（`exec format error`）。
>
> **解決策**: Cloud Build を使用してビルドすることで、AMD64イメージが生成されます。

```bash
cd packages/agent

# Cloud Build を使用（推奨）
gcloud builds submit \
  --tag asia-northeast1-docker.pkg.dev/<YOUR_PROJECT_ID>/drawing-practice-agent/agent:latest .

# または、AMD64でビルドできる環境がある場合
# docker buildx build --platform linux/amd64 \
#   -t asia-northeast1-docker.pkg.dev/<YOUR_PROJECT_ID>/drawing-practice-agent/agent:latest . \
#   --push
```

### 4. Cloud Run へのデプロイ

```bash
gcloud run deploy dessin-coaching-agent \
  --image asia-northeast1-docker.pkg.dev/<YOUR_PROJECT_ID>/drawing-practice-agent/agent:latest \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --timeout 300 \
  --set-env-vars "GCP_PROJECT_ID=<YOUR_PROJECT_ID>,GCP_REGION=asia-northeast1,FIRESTORE_DATABASE=(default),STORAGE_BUCKET=<YOUR_BUCKET_NAME>,DEBUG=false,LOG_LEVEL=INFO"
```

### 5. デプロイ確認

```bash
# サービスURL取得
gcloud run services describe dessin-coaching-agent --format='value(status.url)'

# ヘルスチェック
curl <SERVICE_URL>/health
# 期待されるレスポンス: {"status":"healthy"}
```

---

## 初回セットアップ（リソースが存在しない場合）

### Artifact Registry リポジトリ作成

```bash
gcloud artifacts repositories create drawing-practice-agent \
  --repository-format=docker \
  --location=asia-northeast1 \
  --description="Drawing Practice Agent Docker images"
```

### Cloud Storage バケット作成

```bash
gcloud storage buckets create gs://<YOUR_BUCKET_NAME> \
  --location=asia-northeast1 \
  --uniform-bucket-level-access
```

### Firestore データベース作成

```bash
gcloud firestore databases create \
  --location=asia-northeast1 \
  --type=firestore-native
```

---

## トラブルシューティング

### `exec format error` が発生する

ARM64マシンでビルドしたイメージをCloud Runにデプロイした際に発生します。
**Cloud Build** を使用してビルドしてください（上記「Dockerイメージのビルド・プッシュ」参照）。

### コンテナがポート8080でリッスンしない

Cloud Runのログを確認してください：
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=dessin-coaching-agent" --limit=30
```

---

## 次のステップ

- [ ] Terraform化
- [ ] 認証機能の実装（Issue #34）
- [ ] ウェブアプリのデプロイ
