import os
import functions_framework
from google.cloud import firestore
import structlog
from datetime import datetime

# structlog configuration
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logger = structlog.get_logger()

# Initialize Firestore
db = firestore.Client()

@functions_framework.http
def complete_task(request):
    """HTTP Cloud Function to mark task as completed.
    
    IAM認証がGCPレベルで自動的にチェックされます。
    サービス間呼び出しでは、呼び出し元のサービスアカウントに
    Cloud Functions Invoker ロールが必要です。
    """
    
    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            return {"error": "Invalid JSON"}, 400
            
        task_id = request_json.get("task_id")
        example_image_url = request_json.get("example_image_url")
        
        if not all([task_id, example_image_url]):
             return {"error": "Missing required fields"}, 400

        logger.info("processing_task_completion_http", task_id=task_id)
        
        # Update Firestore Task
        doc_ref = db.collection("review_tasks").document(task_id)
        
        doc_ref.update({
            "status": "completed",
            "example_image_url": example_image_url,
            "updated_at": datetime.now()
        })
        
        logger.info("task_completed_successfully", task_id=task_id)
        return {"status": "success"}, 200
        
    except Exception as e:
        logger.error("failed_to_complete_task", error=str(e))
        return {"error": str(e)}, 500
