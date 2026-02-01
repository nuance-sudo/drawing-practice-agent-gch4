"""FastAPIエントリーポイント"""

import firebase_admin
import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.reviews import router as reviews_router
from src.config import settings

# Initialize Firebase Admin
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app()

# structlog設定
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
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# FastAPIアプリケーション
app = FastAPI(
    title="鉛筆デッサンコーチングエージェント API",
    description="デッサン画像を分析し、フィードバックを提供するAPIサーバー",
    version="0.1.0",
)

# CORSミドルウェア
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# HTTPException用のカスタムハンドラー（CORSヘッダーを確実に付与）
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTPExceptionにCORSヘッダーを付与"""
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

    # CORSヘッダーを手動で追加
    origin = request.headers.get("origin")
    if origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    # WWW-Authenticateヘッダーがある場合は追加
    if hasattr(exc, 'headers') and exc.headers:
        for key, value in exc.headers.items():
            response.headers[key] = value

    return response


# APIルーター登録
app.include_router(reviews_router)


@app.get("/")
async def root() -> dict[str, str]:
    """ヘルスチェックエンドポイント"""
    return {"status": "ok", "message": "Dessin Coaching Agent API"}


@app.get("/health")
async def health() -> dict[str, str]:
    """ヘルスチェック"""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event() -> None:
    """アプリケーション起動時の処理"""
    logger.info(
        "application_started",
        project_id=settings.gcp_project_id,
        debug=settings.debug,
    )


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """アプリケーション終了時の処理"""
    logger.info("application_shutdown")
