# 要件確認質問

Cloud Tasks移行による審査処理の非同期化について、以下の質問にお答えください。

## Question 1
タスク処理用のコンピュートリソースとして何を使用しますか？

A) Cloud Functions（Gen 2）
B) Cloud Run（既存のAPI Serverとは別のサービス）
C) 既存のCloud Run API Server内で処理（別エンドポイント）
D) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 2
タスクの進捗状況をフロントエンドにどのように通知しますか？

A) ポーリング方式（現在のFirestoreリアルタイム監視を継続）
B) Firebase Cloud Messaging（プッシュ通知）
C) Server-Sent Events (SSE)
D) WebSocket
E) Other (please describe after [Answer]: tag below)

[Answer]: A

## Question 3
Cloud Tasksのタイムアウト設定はどの程度を想定していますか？

A) 5分（Agent Engine処理が完了する最短時間）
B) 10分（余裕を持った設定）
C) 30分（画像生成を含む全処理が完了するまで）
D) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 4
リトライ戦略についてはどのようにしますか？

A) リトライなし（1回で失敗したらエラー通知）
B) 最大3回のリトライ（指数バックオフ付き）
C) 最大5回のリトライ（長時間処理のため）
D) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 5
インフラ定義の管理方法はどうしますか？

A) Terraform（packages/infra配下）
B) gcloud CLIスクリプト（既存の方式）
C) 手動構築（コンソールから設定）
D) Other (please describe after [Answer]: tag below)

[Answer]: B

## Question 6
エラー発生時のユーザーへの通知方法は？

A) Firestoreのタスクステータスを`failed`に更新（現在の方式と同様）
B) メール通知
C) プッシュ通知（Firebase Cloud Messaging）
D) Other (please describe after [Answer]: tag below)

[Answer]: A
