#!/bin/bash
set -e



# 設定（環境に合わせて変更してください）
REGION="${REGION:-asia-northeast1}"
# バケット設定
GCS_BUCKET_NAME="${GCS_BUCKET_NAME:-drawing-practice-agent-images}"

PROJECT_ID=$(gcloud config get-value project)
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Bucket Name: $GCS_BUCKET_NAME"


echo "=================================================="
echo "Deploying 'complete_task' function..."
echo "=================================================="

# デプロイ順序を変更：complete-taskを先にデプロイしてURLを取得する

gcloud functions deploy complete-task \
    --gen2 \
    --runtime=python312 \
    --region=$REGION \
    --source=packages/functions/complete_task \
    --entry-point=complete_task \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars=GCP_PROJECT_ID=$PROJECT_ID

COMPLETE_TASK_URL=$(gcloud functions describe complete-task --gen2 --region=$REGION --format="value(serviceConfig.uri)")
echo "Complete Task URL: $COMPLETE_TASK_URL"

echo "=================================================="
echo "Deploying 'generate-image' function..."
echo "=================================================="

gcloud functions deploy generate-image \
    --gen2 \
    --runtime=python312 \
    --region=$REGION \
    --source=packages/functions/generate_image \
    --entry-point=generate_example_image \
    --trigger-http \
    --allow-unauthenticated \
    --set-env-vars=GCP_PROJECT_ID=$PROJECT_ID,OUTPUT_BUCKET_NAME=$GCS_BUCKET_NAME,GCP_REGION=$REGION,COMPLETE_TASK_FUNCTION_URL=$COMPLETE_TASK_URL \
    --memory=1Gi \
    --timeout=300s

# URLを取得して表示
FUNCTION_URL=$(gcloud functions describe generate-image --gen2 --region=$REGION --format="value(serviceConfig.uri)")
echo "Function deployed to: $FUNCTION_URL"
echo "Make sure to update image_generation_function_url in your .env file!"

echo "=================================================="
echo "Deployment Complete!"
echo "=================================================="
