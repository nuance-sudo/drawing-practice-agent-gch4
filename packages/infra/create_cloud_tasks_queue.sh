#!/bin/bash
set -e

# Cloud Tasksキュー作成スクリプト
# 審査処理用のCloud Tasksキューを作成します

# 設定
QUEUE_NAME="${QUEUE_NAME:-review-processing-queue}"
LOCATION="${LOCATION:-us-central1}"
PROJECT_ID=$(gcloud config get-value project)

echo "=================================================="
echo "Cloud Tasks Queue Setup"
echo "=================================================="
echo "Project ID: $PROJECT_ID"
echo "Queue Name: $QUEUE_NAME"
echo "Location: $LOCATION"
echo ""

# Cloud Tasks APIを有効化
echo "Enabling Cloud Tasks API..."
gcloud services enable cloudtasks.googleapis.com --project=$PROJECT_ID

# キューが既に存在するか確認
if gcloud tasks queues describe $QUEUE_NAME --location=$LOCATION --project=$PROJECT_ID > /dev/null 2>&1; then
    echo "Queue '$QUEUE_NAME' already exists. Updating configuration..."
    
    # 既存キューの設定を更新
    gcloud tasks queues update $QUEUE_NAME \
        --location=$LOCATION \
        --project=$PROJECT_ID \
        --max-attempts=3 \
        --max-retry-duration=1800s \
        --min-backoff=10s \
        --max-backoff=300s \
        --max-doublings=4 \
        --max-dispatches-per-second=10 \
        --max-concurrent-dispatches=5
else
    echo "Creating new queue '$QUEUE_NAME'..."
    
    # 新規キュー作成
    gcloud tasks queues create $QUEUE_NAME \
        --location=$LOCATION \
        --project=$PROJECT_ID \
        --max-attempts=3 \
        --max-retry-duration=1800s \
        --min-backoff=10s \
        --max-backoff=300s \
        --max-doublings=4 \
        --max-dispatches-per-second=10 \
        --max-concurrent-dispatches=5
fi

echo ""
echo "=================================================="
echo "Queue Configuration"
echo "=================================================="
echo "- Max Attempts: 3 (最大3回リトライ)"
echo "- Max Retry Duration: 1800s (30分)"
echo "- Min Backoff: 10s"
echo "- Max Backoff: 300s (5分)"
echo "- Max Doublings: 4 (指数バックオフ)"
echo "- Max Dispatches/sec: 10"
echo "- Max Concurrent Dispatches: 5"
echo ""

# キュー情報を表示
gcloud tasks queues describe $QUEUE_NAME --location=$LOCATION --project=$PROJECT_ID

echo ""
echo "=================================================="
echo "Cloud Tasks Queue Setup Complete!"
echo "=================================================="
echo ""
echo "Queue Name: $QUEUE_NAME"
echo "Location: $LOCATION"
echo ""
echo "次のステップ:"
echo "1. process-review Cloud Functionをデプロイ"
echo "2. Cloud RunサービスにCloud Tasks権限を付与"
