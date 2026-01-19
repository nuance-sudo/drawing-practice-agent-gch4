"""認証依存関数
from firebase_admin import auth
import structlog
from fastapi import Header, HTTPException, status
from pydantic import BaseModel

from src.config import settings

logger = structlog.get_logger()


class AuthenticatedUser(BaseModel):
    """認証済みユーザー情報"""

    user_id: str
    email: str | None = None
    picture: str | None = None


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> AuthenticatedUser:
    """認証済みユーザーを取得する依存関数

    Args:
        authorization: Authorization ヘッダー（Bearer Token）
        x_user_id: X-User-ID ヘッダー（開発用モック認証）

    Returns:
        AuthenticatedUser: 認証済みユーザー情報

    Raises:
        HTTPException 401: 認証に失敗した場合
    """
    # 開発モード: X-User-IDヘッダーでモック認証
    if not settings.auth_enabled:
        if x_user_id:
            logger.debug(
                "mock_auth_success",
                user_id=x_user_id,
            )
            return AuthenticatedUser(user_id=x_user_id)
        # 開発モードでもヘッダーがない場合は認証エラー
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 本番モード: Firebase Authentication
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Bearerトークンを抽出
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization[7:]  # "Bearer "を除去

    # JWT検証
    try:
        decoded_token = auth.verify_id_token(token)
        user_id = decoded_token.get("uid")
        email = decoded_token.get("email")
        picture = decoded_token.get("picture")

        logger.info(
            "firebase_auth_success",
            user_id=user_id,
        )
        return AuthenticatedUser(
            user_id=user_id,
            email=email,
            picture=picture,
        )

    except Exception as e:
        logger.warning("firebase_auth_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
