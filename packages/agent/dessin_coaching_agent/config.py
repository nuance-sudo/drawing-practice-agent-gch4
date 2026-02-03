"""Agent Engine用設定

環境変数から設定を読み込むシンプルな設定モジュール。
"""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Agent Engine用設定"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # GCP設定
    # 環境変数: GCP_PROJECT_ID または GOOGLE_CLOUD_PROJECT
    gcp_project_id: str = Field(
        default="",
        validation_alias=AliasChoices("GCP_PROJECT_ID", "GOOGLE_CLOUD_PROJECT"),
    )
    # 環境変数: GCP_REGION または GOOGLE_CLOUD_LOCATION
    gcp_region: str = Field(
        default="global",
        validation_alias=AliasChoices("GCP_REGION", "GOOGLE_CLOUD_LOCATION"),
    )

    # Cloud Storage設定
    gcs_bucket_name: str = ""
    cdn_base_url: str = ""

    # Gemini設定
    # 環境変数: GEMINI_MODEL, GEMINI_LOCATION, GEMINI_MAX_OUTPUT_TOKENS, GEMINI_TEMPERATURE
    gemini_model: str = "gemini-3-flash-preview"
    gemini_location: str = "global"  # モデル用ロケーション（gemini-3-*はglobalのみ）
    gemini_max_output_tokens: int = 32000
    gemini_temperature: float = 1.0

    # Agent Engine設定（Memory Bank用）
    # 環境変数: AGENT_ENGINE_ID, AGENT_ENGINE_REGION
    # デプロイ時に --env_file オプションで .env ファイルを指定することで読み込む
    agent_engine_id: str = ""
    agent_engine_region: str = "us-central1"  # リソース用リージョン


@lru_cache
def get_settings() -> Settings:
    """設定のシングルトンインスタンスを取得"""
    return Settings()


settings = get_settings()
