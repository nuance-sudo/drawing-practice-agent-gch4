# Walkthrough: Cloud Tasks移行による審査処理の非同期化

## 概要

審査処理をCloud Tasksに移行し、同期処理から非同期処理に変更。APIレスポンス時間を改善し、Cloud Tasksによるリトライ機能で信頼性を向上させた。

## 変更サマリー

| ファイル | 変更内容 |
|---------|----------|
| [reviews.py](file:///home/ec2-user/src/drawing-practice-agent-gch4/packages/agent/src/api/reviews.py) | Cloud Tasks投入に変更 |
| [cloud_tasks_service.py](file:///home/ec2-user/src/drawing-practice-agent-gch4/packages/agent/src/services/cloud_tasks_service.py) | 新規作成 - Cloud Tasksクライアントサービス |
| [config.py](file:///home/ec2-user/src/drawing-practice-agent-gch4/packages/agent/src/config.py) | Cloud Tasks設定を追加 |
| [process_review/main.py](file:///home/ec2-user/src/drawing-practice-agent-gch4/packages/functions/process_review/main.py) | 新規作成 - 審査処理Cloud Function |
| [deploy_functions.sh](file:///home/ec2-user/src/drawing-practice-agent-gch4/packages/functions/deploy_functions.sh) | process-review関数のデプロイを追加 |

## 主要な変更点

### アーキテクチャ変更

**Before:**
```
[Web App] → [Cloud Run API (同期処理)] → [Agent Engine]
```

**After:**
```
[Web App] → [Cloud Run API] → [Cloud Tasks] → [Cloud Function] → [Agent Engine]
                 ↓ (即座にレスポンス)
```

### Cloud Tasksサービス実装

`CloudTasksService`クラスを新規作成：
- `create_review_task()`: 審査タスクをCloud Tasksに投入
- `delete_review_task()`: タスクのキャンセル機能
- OIDCトークンによる認証済みHTTPリクエスト

### Cloud Function: process-review

Cloud Tasksから呼び出される審査処理関数を実装：
- Agent Engineへのデッサン分析リクエスト
- Firestoreステータス更新
- アノテーション画像生成の呼び出し
- お手本画像生成の呼び出し

## テスト・検証

- [x] リント・型チェック（pre-deploy-check）
- [x] Cloud Functions デプロイ
- [ ] E2Eテスト

## 関連Issue

- [#62](https://github.com/nuance-sudo/drawing-practice-agent-gch4/issues/62)

## 次のステップ

1. Cloud Tasksキューの作成（gcloud CLI）
2. Cloud Run APIの再デプロイ
3. 統合テストの実施
