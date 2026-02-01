#!/bin/bash
set -e

# .envファイルを読み込み（存在する場合）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo "Loading environment variables from $SCRIPT_DIR/.env"
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

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
    --set-env-vars=GCP_PROJECT_ID=$PROJECT_ID,OUTPUT_BUCKET_NAME=$GCS_BUCKET_NAME,COMPLETE_TASK_FUNCTION_URL=$COMPLETE_TASK_URL,GEMINI_MODEL=gemini-3-pro-image-preview \
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
echo "Deploying 'process-review' function..."
echo "=================================================="

# Agent Engine関連の環境変数を取得（必須）
if [ -z "${AGENT_ENGINE_ID:-}" ]; then
    echo "ERROR: AGENT_ENGINE_ID environment variable is required"
    echo "Get it from env.yaml or set it: export AGENT_ENGINE_ID=xxx"
    exit 1
fi
AGENT_ENGINE_LOCATION="${AGENT_ENGINE_LOCATION:-us-central1}"

gcloud functions deploy process-review \
    --gen2 \
    --runtime=python312 \
    --region=$REGION \
    --source=packages/functions/process_review \
    --entry-point=process_review_handler \
    --trigger-http \
    --no-allow-unauthenticated \
    --set-env-vars=GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,AGENT_ENGINE_ID=$AGENT_ENGINE_ID,AGENT_ENGINE_LOCATION=$AGENT_ENGINE_LOCATION,ANNOTATION_FUNCTION_URL=$ANNOTATE_FUNCTION_URL,IMAGE_GENERATION_FUNCTION_URL=$FUNCTION_URL,GEMINI_MODEL=gemini-3-flash-preview \
    --memory=2Gi \
    --timeout=600s \
    --cpu=1

PROCESS_REVIEW_URL=$(gcloud functions describe process-review --gen2 --region=$REGION --format="value(serviceConfig.uri)")
echo "Process Review URL: $PROCESS_REVIEW_URL"
echo "Make sure to update process_review_function_url in your .env file!"

# Cloud Runサービス（API Server）からprocess-reviewを呼び出せるようにIAM設定
# Cloud RunのサービスアカウントにCloud Functionsの呼び出し権限を付与
echo "Setting up IAM for Cloud Tasks to invoke process-review..."

# プロジェクトのデフォルトサービスアカウントに invoker 権限を付与
gcloud run services add-iam-policy-binding process-review \
    --region=$REGION \
    --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
    --role="roles/run.invoker" \
    || echo "Warning: Failed to grant IAM permission for appspot SA."

# Cloud Tasks サービスアカウントにも invoker 権限を付与
gcloud run services add-iam-policy-binding process-review \
    --region=$REGION \
    --member="serviceAccount:service-$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')@gcp-sa-cloudtasks.iam.gserviceaccount.com" \
    --role="roles/run.invoker" \
    || echo "Warning: Failed to grant IAM permission for Cloud Tasks SA."

echo "=================================================="
echo "Deployment Complete!"
echo "=================================================="
echo ""
echo "Function URLs:"
echo "  - Complete Task: $COMPLETE_TASK_URL"
echo "  - Generate Image: $FUNCTION_URL"
echo "  - Annotate Image: $ANNOTATE_FUNCTION_URL"
echo "  - Process Review: $PROCESS_REVIEW_URL"
echo ""
echo "Next steps:"
echo "1. Update .env with the process_review_function_url"
echo "2. Run packages/infra/create_cloud_tasks_queue.sh to create the Cloud Tasks queue"
echo "3. Redeploy the Cloud Run API server"
