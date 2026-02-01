"""カスタムGeminiモデル

gemini-3-flash-previewなどのglobalリージョン専用モデルに対応。
Agent Engineはus-central1などの特定リージョンにデプロイされるが、
モデル呼び出し時はglobalリージョンを使用するようにオーバーライド。
"""

import os
from functools import cached_property

from google.adk.models import Gemini
from google.genai import Client, types

from .config import settings


class GlobalGemini(Gemini):
    """globalリージョン用Geminiモデル

    Agent EngineのデプロイリージョンとGeminiモデルの利用可能リージョンが
    異なる場合に使用。gemini-3-flash-previewなどはglobalでのみ利用可能。
    """

    @cached_property
    def api_client(self) -> Client:
        """globalリージョンでAPIクライアントを初期化

        Returns:
            globalリージョン設定のClient
        """
        return Client(
            vertexai=True,
            project=os.environ.get("GOOGLE_CLOUD_PROJECT", settings.gcp_project_id),
            location=settings.gemini_location,  # "global"
            http_options=types.HttpOptions(
                headers=self._tracking_headers(),
                retry_options=self.retry_options,
            ),
        )
