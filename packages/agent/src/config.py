"""アプリケーション設定"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """アプリケーション設定

    環境変数から設定を読み込む。
    """

    # GCP設定
    gcp_project_id: str = ""
    gcp_region: str = "global"

    # Firestore設定
    firestore_database: str = "(default)"

    # Cloud Storage設定
    gcs_bucket_name: str = ""  # gs://スキームで許可するバケット名
    cdn_base_url: str = ""

    # Gemini設定
    gemini_model: str = "gemini-2.5-flash"
    gemini_image_model: str = "gemini-2.5-flash-image"
    gemini_max_output_tokens: int = 32000
    gemini_temperature: float = 1.0
    gemini_thinking_budget_tokens: int = 8192

    # アプリケーション設定
    debug: bool = False
    log_level: str = "INFO"

    # CORS設定
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()


settings = get_settings()
