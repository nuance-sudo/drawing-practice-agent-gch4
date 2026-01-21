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
 Container Registry (Artifact Registry) にビルドして Cloud Run にデプロイします。
 ※ `packages/agent` ディレクトリで実行してください。
 
 ```bash
 cd packages/agent
 
 # 1. ビルド & Push
 gcloud builds submit --region=asia-northeast1 --tag asia-northeast1-docker.pkg.dev/drawing-practice-agent/drawing-practice-agent/agent:latest --project=drawing-practice-agent .
 
 # 2. デプロイ
 gcloud run deploy dessin-coaching-agent --image asia-northeast1-docker.pkg.dev/drawing-practice-agent/drawing-practice-agent/agent:latest --platform managed --region asia-northeast1 --project=drawing-practice-agent
 ```
 
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