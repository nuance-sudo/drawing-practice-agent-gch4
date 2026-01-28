#!/bin/bash
# エージェントサービスからgenerate-image関数を呼び出すためのIAM権限設定スクリプト

set -e

REGION="${REGION:-asia-northeast1}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
AGENT_SERVICE_NAME="dessin-coaching-agent"
FUNCTION_NAME="generate-image"

echo "=================================================="
echo "Setting up IAM permissions for agent service"
echo "=================================================="
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Agent Service: $AGENT_SERVICE_NAME"
echo "Function: $FUNCTION_NAME"
echo ""

# エージェントサービスのサービスアカウントを取得
echo "Getting agent service account..."
AGENT_SA=$(gcloud run services describe $AGENT_SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null || echo "")

if [ -z "$AGENT_SA" ]; then
    # サービスアカウントが設定されていない場合、デフォルトのサービスアカウントを使用
    AGENT_SA="${PROJECT_ID}@appspot.gserviceaccount.com"
    echo "Using default service account: $AGENT_SA"
else
    echo "Agent Service Account: $AGENT_SA"
fi

# generate-image関数（Cloud Functions Gen2）にエージェントサービスのサービスアカウントを呼び出し可能にする権限を付与
echo ""
echo "Granting Cloud Run Invoker role to $AGENT_SA for $FUNCTION_NAME function..."
gcloud run services add-iam-policy-binding $FUNCTION_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --member="serviceAccount:${AGENT_SA}" \
    --role="roles/run.invoker" \
    || {
        echo "Error: Failed to grant IAM permission."
        echo "Please check:"
        echo "  1. The function '$FUNCTION_NAME' exists in region '$REGION'"
        echo "  2. You have permission to modify IAM policies"
        echo "  3. The service account '$AGENT_SA' exists"
        exit 1
    }

echo ""
echo "=================================================="
echo "IAM permission granted successfully!"
echo "=================================================="
echo "Agent service ($AGENT_SA) can now invoke $FUNCTION_NAME function."
