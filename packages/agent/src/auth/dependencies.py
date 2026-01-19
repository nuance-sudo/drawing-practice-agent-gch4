"""認証依存関数

FastAPIのDepends用認証関数を提供する。
- 本番: JWT検証
- 開発: X-User-IDヘッダーベースのモック認証
"""

import structlog
from fastapi import Header, HTTPException, status
from pydantic import BaseModel

from src.config import settings

logger = structlog.get_logger()


class AuthenticatedUser(BaseModel):
    """認証済みユーザー情報"""

    user_id: str
    email: str | None = None


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
) -> AuthenticatedUser:
    """認証済みユーザーを取得する依存関数

    Args:
        authorization: Authorization ヘッダー（Bearer JWT）
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

    # 本番モード: JWT認証
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
    user = await verify_jwt(token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(
        "jwt_auth_success",
        user_id=user.user_id,
    )
    return user


async def verify_jwt(token: str) -> AuthenticatedUser | None:
    """JWTトークンを検証する

    Args:
        token: JWTトークン

    Returns:
        AuthenticatedUser: 検証成功時のユーザー情報
        None: 検証失敗時

    Note:
        フロントエンド（Auth.js）実装後に本実装を追加。
        現在は常にNoneを返す（本番認証は未実装）。
    """
    # TODO: Auth.js実装後にJWT検証を実装
    # import jwt
    # try:
    #     payload = jwt.decode(
    #         token,
    #         settings.auth_secret,
    #         algorithms=["HS256"],
    #     )
    #     return AuthenticatedUser(
    #         user_id=payload.get("sub"),
    #         email=payload.get("email"),
    #     )
    # except jwt.InvalidTokenError:
    #     return None

    # 未実装のためトークンを使用せずにNoneを返す
    _ = token  # 引数は将来使用予定

    logger.warning(
        "jwt_verification_not_implemented",
        message="JWT verification is not yet implemented. Use mock auth for development.",
    )
    return None
