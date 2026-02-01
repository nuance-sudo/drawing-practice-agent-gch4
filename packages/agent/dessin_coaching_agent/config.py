"""Agent Engine用設定

環境変数から設定を読み込むシンプルな設定モジュール。
"""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Agent Engine用設定"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # GCP設定
    gcp_project_id: str = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    gcp_region: str = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")

    # Cloud Storage設定
    gcs_bucket_name: str = ""
    cdn_base_url: str = ""

    # Gemini設定
    gemini_model: str = "gemini-3-flash-preview"
    gemini_location: str = "global"  # gemini-3-flash-previewはglobalリージョン
    gemini_max_output_tokens: int = 32000
    gemini_temperature: float = 1.0


@lru_cache
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()


settings = get_settings()
