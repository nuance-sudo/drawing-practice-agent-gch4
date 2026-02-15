# Walkthrough: 画像生成リトライ機能追加

## 概要

Cloud Function呼び出し（アノテーション画像・お手本画像の生成）に最大3回の指数バックオフリトライを追加し、それでも失敗した場合はフロントエンドからリトライボタンで再実行できるようにした。

## 変更サマリー

| ファイル | 変更内容 |
|---------|---------|
| `packages/agent/src/services/annotation_service.py` | Cloud Function呼び出しに最大3回リトライ（指数バックオフ）追加 |
| `packages/agent/src/services/image_generation_service.py` | Cloud Function呼び出しに最大3回リトライ（指数バックオフ）追加 |
| `packages/agent/src/api/reviews.py` | `POST /reviews/{task_id}/retry-images` エンドポイント新設 |
| `packages/web/src/lib/api.ts` | `retryImages()` APIメソッド追加 |
| `packages/web/src/components/features/review/ExampleImageDisplay.tsx` | エラー表示にリトライボタン＋再生成中スピナー追加 |
| `packages/web/src/components/features/review/FeedbackDisplay.tsx` | リトライハンドラ実装（Firestore onSnapshotでUI自動更新） |

## 主要な変更点

### バックエンド: リトライロジック

`annotation_service.py` と `image_generation_service.py` のCloud Function呼び出し部分を内部メソッド（`_call_annotation_function`, `_call_generation_function`）に分離し、最大3回の指数バックオフリトライ（2秒→4秒→8秒）を実装。429 Resource Exhaustedエラーに対応。

### バックエンド: リトライAPIエンドポイント

`POST /reviews/{task_id}/retry-images` エンドポイントを新設。completedステータスかつ画像未生成のタスクに対して、保存済みfeedbackデータからDessinAnalysisを復元し、アノテーション＆お手本画像生成を再実行する。所有権チェック・ステータスチェック付き。

### フロントエンド: リトライUI

`ExampleImageDisplay.tsx` のアノテーション失敗・お手本画像失敗のエラー表示に「再試行する」ボタンを追加。リトライ中は「再生成中...」スピナーを表示。`FeedbackDisplay.tsx` がAPIコールを行い、Firestore onSnapshotリスナーがリアルタイムでUIを自動更新する設計。

## テスト・検証

- [x] pytest（exit code 0）
- [x] Next.js build（Compiled successfully）
- [x] Cloud Runデプロイ（gcloud builds submit + gcloud run deploy + env.yaml）
- [x] 本番環境でリトライボタン動作確認

## デプロイ時の注意事項

Cloud Run MCP（`deploy_local_folder`）経由のデプロイでは環境変数（`CORS_ORIGINS`等）が設定されない。本番デプロイは `gcloud builds submit` + `gcloud run deploy --env-vars-file=env.yaml` を使用すること。

## 次のステップ

- `/git-commit` でコミット・PR作成を行う
