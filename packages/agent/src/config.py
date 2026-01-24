"""アプリケーション設定"""

from functools import lru_cache
from typing import Annotated

from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors_origins(v: str | list[str]) -> list[str]:
    """カンマ区切りの文字列をリストに変換"""
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list):
        return v
    # JSON配列形式の文字列の場合のフォールバック等はPydanticに任せるかここで処理
    # 今回はカンマ区切り文字列のサポートが主目的
    return v  # type: ignore  # Pydanticが後続のバリデーションで処理することを期待


class Settings(BaseSettings):
    """アプリケーション設定

    環境変数から設定を読み込む。
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # GCP設定
    gcp_project_id: str = ""
    gcp_region: str = "global"

    # Firestore設定
    firestore_database: str = "(default)"

    # Cloud Storage設定
    gcs_bucket_name: str = ""  # Cloud Storageバケット名
    cdn_base_url: str = ""

    image_generation_function_url: str = ""  # Cloud Run Function URL

    # Gemini設定
    gemini_model: str = "gemini-2.5-flash"

    gemini_max_output_tokens: int = 32000
    gemini_temperature: float = 1.0
    gemini_thinking_budget_tokens: int = 8192

    # アプリケーション設定
    debug: bool = False
    log_level: str = "INFO"

    # 認証設定
    auth_enabled: bool = True  # False: モック認証（開発用）
    auth_secret: str = ""  # JWT署名用シークレット

    # CORS設定
    # pydantic-settingsがJSONパースを試みて失敗するのを防ぐため、strも許容する型定義にする
    cors_origins: Annotated[list[str] | str, BeforeValidator(parse_cors_origins)] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://drawing-practice-agent.web.app",
        "https://drawing-practice-agent.firebaseapp.com",
    ]


@lru_cache
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()


settings = get_settings()
