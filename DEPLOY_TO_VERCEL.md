# Vercel Deployment Guide

このWebアプリケーション（`packages/web`）をVercelにデプロイする手順です。

## 1. プロジェクトのインポート

1. Vercelダッシュボードにアクセスし、"Add New..." > "Project" をクリックします。
2. GitHubリポジトリ `drawing-practice-agent-gch4` をインポートします。

## 2. ビルド設定（Framework Preset & Root Directory）

モノレポ構成のため、以下の設定を変更してください：

- **Framework Preset**: `Next.js` (自動検出されるはずです)
- **Root Directory**: `packages/web` を指定します。
  - "Edit"をクリックし、`packages/web`を選択します。

## 3. 環境変数の設定 (Environment Variables)

"Environment Variables" セクションで、以下の変数を設定してください。
これらの値は `.env.local` からコピーできますが、本番環境用のURLを使用してください。

| キー | 値の例 | 説明 |
|------|--------|------|
| `NEXT_PUBLIC_API_URL` | `https://dessin-coaching-agent-112562671215.asia-northeast1.run.app` | Cloud RunのバックエンドURL |
| `NEXT_PUBLIC_AUTH_SECRET` | `hackathon-secret-123` | JWT生成用のシークレット（バックエンドと同一の値） |

## 4. デプロイ

"Deploy" ボタンをクリックします。
ビルドが完了すると、自動的にURLが発行され、Webアプリが公開されます。

## 5. 動作確認

デプロイされたURLにアクセスし、以下の機能を確認してください：

1. トップページが表示されること
2. 画像アップロードが成功すること（GCSへの直接アップロード）
3. アップロード後、タスク審査結果が表示されること

> **Note**: バックエンドのCORS設定は現在 `*`（全許可）になっているため、Vercelのドメインからも問題なくアクセスできます。
