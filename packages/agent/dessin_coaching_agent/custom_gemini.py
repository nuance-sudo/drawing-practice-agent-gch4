"""カスタムGeminiモデル

gemini-3-flash-previewなどのglobalリージョン専用モデルに対応。
Agent Engineはus-central1などの特定リージョンにデプロイされるが、
モデル呼び出し時はglobalリージョンを使用するようにオーバーライド。

429 RESOURCE_EXHAUSTEDエラーに対するリトライ設定を含む。
参考: https://google.github.io/adk-docs/agents/models/#error-code-429-resource_exhausted
"""

import os
from functools import cached_property

from google.adk.models import Gemini
from google.genai import Client, types

from .config import settings

# 429エラー対応: 3回リトライ、指数バックオフ（初期1秒、最大30秒）
RETRY_OPTIONS = types.HttpRetryOptions(
    attempts=3,
    initial_delay=1.0,
    max_delay=30.0,
    exp_base=2.0,
    http_status_codes=[429],
)


class GlobalGemini(Gemini):
    """globalリージョン用Geminiモデル

    Agent EngineのデプロイリージョンとGeminiモデルの利用可能リージョンが
    異なる場合に使用。gemini-3-flash-previewなどはglobalでのみ利用可能。

    429 RESOURCE_EXHAUSTEDエラーに対しては自動的に最大3回リトライする。
    """

    # 429エラー（レート制限）に対するリトライ設定
    retry_options: types.HttpRetryOptions = RETRY_OPTIONS

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
