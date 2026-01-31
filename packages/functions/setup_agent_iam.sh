#!/bin/bash
# エージェントサービスからCloud Functionsを呼び出すためのIAM権限設定スクリプト

set -e

REGION="${REGION:-us-central1}"
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
AGENT_SERVICE_NAME="dessin-coaching-agent"
AGENT_REGION="${AGENT_REGION:-us-central1}"  # エージェントサービスのリージョン

echo "=================================================="
echo "Setting up IAM permissions for agent service"
echo "=================================================="
echo "Project ID: $PROJECT_ID"
echo "Functions Region: $REGION"
echo "Agent Service: $AGENT_SERVICE_NAME (Region: $AGENT_REGION)"
echo ""

# エージェントサービスのサービスアカウントを取得
echo "Getting agent service account..."
AGENT_SA=$(gcloud run services describe $AGENT_SERVICE_NAME \
    --region=$AGENT_REGION \
    --project=$PROJECT_ID \
    --format="value(spec.template.spec.serviceAccountName)" 2>/dev/null || echo "")

if [ -z "$AGENT_SA" ]; then
    # サービスアカウントが設定されていない場合、デフォルトのサービスアカウントを使用
    AGENT_SA="${PROJECT_ID}@appspot.gserviceaccount.com"
    echo "Using default service account: $AGENT_SA"
else
    echo "Agent Service Account: $AGENT_SA"
fi

# generate-image関数に権限を付与
echo ""
echo "Granting Cloud Run Invoker role to $AGENT_SA for generate-image function..."
gcloud run services add-iam-policy-binding generate-image \
    --region=$REGION \
    --project=$PROJECT_ID \
    --member="serviceAccount:${AGENT_SA}" \
    --role="roles/run.invoker" \
    || {
        echo "Warning: Failed to grant IAM permission for generate-image."
        echo "Please check manually."
    }

# annotate-image関数に権限を付与
echo ""
echo "Granting Cloud Run Invoker role to $AGENT_SA for annotate-image function..."
gcloud run services add-iam-policy-binding annotate-image \
    --region=$REGION \
    --project=$PROJECT_ID \
    --member="serviceAccount:${AGENT_SA}" \
    --role="roles/run.invoker" \
    || {
        echo "Warning: Failed to grant IAM permission for annotate-image."
        echo "Please check manually."
    }

echo ""
echo "=================================================="
echo "IAM permissions granted successfully!"
echo "=================================================="
echo "Agent service ($AGENT_SA) can now invoke Cloud Functions."
