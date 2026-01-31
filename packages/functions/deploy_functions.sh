#!/bin/bash
set -e



# 設定（環境に合わせて変更してください）
# Cloud Functionsのデプロイリージョン（Gemini APIはコード内でglobalエンドポイントを使用）
REGION="${REGION:-us-central1}"
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
# IAM認証を使用（--no-allow-unauthenticated）
gcloud functions deploy complete-task \
    --gen2 \
    --runtime=python312 \
    --region=$REGION \
    --source=packages/functions/complete_task \
    --entry-point=complete_task \
    --trigger-http \
    --no-allow-unauthenticated \
    --set-env-vars=GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION

# URLを取得
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
    --no-allow-unauthenticated \
    --set-env-vars=GCP_PROJECT_ID=$PROJECT_ID,OUTPUT_BUCKET_NAME=$GCS_BUCKET_NAME,COMPLETE_TASK_FUNCTION_URL=$COMPLETE_TASK_URL,GEMINI_MODEL=gemini-2.5-flash-image \
    --memory=1Gi \
    --timeout=300s

# generate-image関数のサービスアカウントを取得
GENERATE_IMAGE_SA=$(gcloud functions describe generate-image --gen2 --region=$REGION --format="value(serviceConfig.serviceAccountEmail)")
echo "Generate Image Service Account: $GENERATE_IMAGE_SA"

# Cloud Functions Gen2は内部的にCloud Runサービスとして実行されるため、
# Cloud RunのIAMポリシーバインディングコマンドを使用
# Gen2関数のサービス名は "FUNCTION_NAME" 形式
echo "Granting Cloud Run Invoker role to $GENERATE_IMAGE_SA for complete-task function..."
gcloud run services add-iam-policy-binding complete-task \
    --region=$REGION \
    --member="serviceAccount:${GENERATE_IMAGE_SA}" \
    --role="roles/run.invoker" \
    || echo "Warning: Failed to grant IAM permission. You may need to grant it manually."

# URLを取得して表示
FUNCTION_URL=$(gcloud functions describe generate-image --gen2 --region=$REGION --format="value(serviceConfig.uri)")
echo "Function deployed to: $FUNCTION_URL"
echo "Make sure to update image_generation_function_url in your .env file!"

echo "=================================================="
echo "Deploying 'annotate-image' function..."
echo "=================================================="

gcloud functions deploy annotate-image \
    --gen2 \
    --runtime=python312 \
    --region=$REGION \
    --source=packages/functions/annotate_image \
    --entry-point=annotate_image \
    --trigger-http \
    --no-allow-unauthenticated \
    --set-env-vars=GCP_PROJECT_ID=$PROJECT_ID,OUTPUT_BUCKET_NAME=$GCS_BUCKET_NAME,GEMINI_MODEL=gemini-3-flash-preview \
    --memory=1Gi \
    --timeout=300s

ANNOTATE_FUNCTION_URL=$(gcloud functions describe annotate-image --gen2 --region=$REGION --format="value(serviceConfig.uri)")
echo "Annotate Image URL: $ANNOTATE_FUNCTION_URL"
echo "Make sure to update annotation_function_url in your .env file!"

echo "=================================================="
echo "Deployment Complete!"
echo "=================================================="
