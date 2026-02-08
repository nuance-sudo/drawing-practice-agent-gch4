# API Documentation

## REST APIs
### Upload URL
- **Method**: GET
- **Path**: `/reviews/upload-url`
- **Purpose**: 画像アップロード用の署名付きURLを取得
- **Request**: `content_type` クエリ (image/jpeg|png)
- **Response**: `{ upload_url, public_url }`

### Create Review
- **Method**: POST
- **Path**: `/reviews`
- **Purpose**: 審査タスクを作成して非同期処理を開始
- **Request**: `{ image_url, example_image_url? }`
- **Response**: ReviewTaskResponse

### Get Review
- **Method**: GET
- **Path**: `/reviews/{task_id}`
- **Purpose**: 審査タスクの詳細取得
- **Request**: `task_id` パスパラメータ
- **Response**: ReviewTaskResponse

### List Reviews
- **Method**: GET
- **Path**: `/reviews`
- **Purpose**: 審査タスク一覧取得
- **Request**: `limit`, `start_date`, `end_date`, `status`, `tag`
- **Response**: ReviewListResponse

### Delete Review
- **Method**: DELETE
- **Path**: `/reviews/{task_id}`
- **Purpose**: 審査タスクの削除
- **Request**: `task_id` パスパラメータ
- **Response**: 204 No Content

## Internal APIs
### TaskService
- **Methods**: `create_task`, `get_task`, `list_tasks`, `update_task_status`
- **Parameters**: task_id, user_id, status, feedback, score など
- **Return Types**: ReviewTask

### RankService
- **Methods**: `get_user_rank`, `update_user_rank`
- **Parameters**: user_id, score, task_id
- **Return Types**: UserRank

### AgentEngineService
- **Methods**: `run_coaching_agent`
- **Parameters**: image_url, rank_label, user_id, session_id
- **Return Types**: dict (analysis payload)

### AnnotationService / ImageGenerationService
- **Methods**: `generate_annotated_image`, `generate_example_image`
- **Parameters**: task_id, original_image_url, analysis
- **Return Types**: URL or None

## Data Models
### ReviewTask
- **Fields**: task_id, user_id, status, image_url, annotated_image_url, example_image_url, feedback, score, tags, error_message, created_at, updated_at
- **Relationships**: user_id に紐づくタスク
- **Validation**: status は `pending|processing|completed|failed`

### DessinAnalysis
- **Fields**: proportion, tone, texture, line_quality, growth, overall_score, strengths, improvements, tags
- **Relationships**: ReviewTask.feedback に格納
- **Validation**: score は 0-100 を想定

### UserRank
- **Fields**: user_id, rank_level, total_submissions, high_scores, created_at, updated_at
- **Relationships**: ReviewTask と user_id で関連
