# コーディング規約

## インフラストラクチャ（Terraform / gcloud）

### 1. ディレクトリ構成

**概要**: 環境別・リソース別にファイルを分けて保守性を向上

#### 基本構成

```
packages/infra/
├── terraform/           # Terraform定義（オプション）
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── modules/
│       └── cloud-run/
└── scripts/             # gcloudスクリプト
    ├── setup-project.sh
    ├── setup-storage.sh
    ├── setup-eventarc.sh
    └── deploy.sh
```

### 2. Terraform規約

#### 命名規則

| 種別 | 規則 | 例 |
|------|------|-----|
| リソース | snake_case | `google_cloud_run_service.agent` |
| 変数 | snake_case | `project_id`, `region` |
| 出力 | snake_case | `service_url`, `bucket_name` |
| モジュール | kebab-case | `cloud-run`, `eventarc` |

```hcl
# ✅ 良い例
resource "google_cloud_run_service" "coaching_agent" {
  name     = "dessin-coaching-agent"
  location = var.region
  
  template {
    spec {
      containers {
        image = var.agent_image
      }
    }
  }
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

output "agent_url" {
  description = "URL of the deployed agent"
  value       = google_cloud_run_service.coaching_agent.status[0].url
}
```

#### ファイル構成

```hcl
# main.tf - メインリソース定義
# variables.tf - 変数定義
# outputs.tf - 出力定義
# providers.tf - プロバイダー設定
# backend.tf - ステート管理設定
```

### 3. シェルスクリプト規約

#### 基本ルール

- シェバン行を必ず記載: `#!/bin/bash`
- `set -euo pipefail` でエラー時に即終了
- 変数は `${VAR}` 形式で参照
- 関数名は snake_case

```bash
#!/bin/bash
set -euo pipefail

# ✅ 良い例
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"

# 関数定義
deploy_agent() {
    local image_tag="${1}"
    
    echo "Deploying agent with image: ${image_tag}"
    
    gcloud run deploy dessin-coaching-agent \
        --project="${PROJECT_ID}" \
        --region="${REGION}" \
        --image="${image_tag}" \
        --platform=managed
}

# 引数チェック
if [[ -z "${PROJECT_ID}" ]]; then
    echo "Error: PROJECT_ID is required" >&2
    exit 1
fi

deploy_agent "${1:-latest}"
```

### 4. セキュリティ

```bash
# ✅ 良い例 - 機密情報はSecret Managerから取得
gcloud secrets versions access latest \
    --secret="VAPID_PRIVATE_KEY" \
    --project="${PROJECT_ID}"

# ❌ 悪い例 - ハードコード禁止
VAPID_KEY="sk-xxxxxx"
```

### 5. ドキュメント

各スクリプトには使用方法コメントを記載：

```bash
#!/bin/bash
#
# deploy.sh - Cloud Runにエージェントをデプロイ
#
# Usage:
#   ./deploy.sh [image_tag]
#
# Arguments:
#   image_tag  デプロイするイメージタグ（デフォルト: latest）
#
# Environment Variables:
#   PROJECT_ID  GCPプロジェクトID（必須）
#   REGION      デプロイ先リージョン（デフォルト: asia-northeast1）
#
# Examples:
#   PROJECT_ID=my-project ./deploy.sh v1.0.0
#
```
