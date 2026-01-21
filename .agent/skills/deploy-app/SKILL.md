---
name: deploy-app
description: アプリケーション（Web/Agent）をデプロイする
---

# Deploy App Skill

このスキルは、アプリケーションのフロントエンド（Firebase Hosting）とバックエンド（Cloud Run）をデプロイするために使用します。

## 使い方

ユーザーからデプロイを依頼された場合、対象（frontend, backend, all）を確認し、以下の手順に従ってコマンドを実行してください。
特に指定がない場合は、ユーザーに対象を確認してください。

スラッシュコマンド: `/deploy-app [target]`
- target: `frontend`, `backend`, `all`

## 前提条件

- `gcloud` コマンドが認証済みであること
- `firebase` コマンドが認証済みであること
- プロジェクトID: `drawing-practice-agent`
- リージョン: `asia-northeast1`

## 手順

> [!IMPORTANT]
> コマンド実行時は必ず指定された作業ディレクトリ（Cwd）で実行すること。
> ビルドには時間がかかる場合があるため、タイムアウトを長めに設定すること。

### 1. Backend (Cloud Run) のデプロイ

対象が `backend` または `all` の場合：

1. **ディレクトリ移動 & ビルド & Push**
   - Cwd: `packages/agent`
   - Command:
     ```bash
     gcloud builds submit --region=asia-northeast1 --tag asia-northeast1-docker.pkg.dev/drawing-practice-agent/drawing-practice-agent/agent:latest --project=drawing-practice-agent .
     ```

2. **Cloud Run へデプロイ**
   - Cwd: `packages/agent`
   - Command:
     ```bash
     gcloud run deploy dessin-coaching-agent --image asia-northeast1-docker.pkg.dev/drawing-practice-agent/drawing-practice-agent/agent:latest --platform managed --region asia-northeast1 --project=drawing-practice-agent --allow-unauthenticated
     ```

### 2. Frontend (Firebase Hosting) のデプロイ

対象が `frontend` または `all` の場合：

1. **ビルド**
   - Cwd: `packages/web`
   - Command:
     ```bash
     npm run build
     ```
   - 注意: ビルドエラーが発生した場合はデプロイを中止し、エラーを報告すること。

2. **Firebase Hosting へデプロイ**
   - Cwd: プロジェクトルート (`/home/ec2-user/src/drawing-practice-agent-gch4`)
   - Command:
     ```bash
     firebase deploy --only hosting --project drawing-practice-agent
     ```

## 完了確認

デプロイ完了後、以下の情報をユーザーに報告してください。

- デプロイした対象（API / Web）
- サービスのURL（Cloud Runの場合はコマンド出力に含まれるURL、Firebaseの場合はHosting URL）
