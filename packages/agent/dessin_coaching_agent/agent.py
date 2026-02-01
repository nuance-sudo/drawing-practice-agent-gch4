"""鉛筆デッサンコーチングエージェント定義

ADK（Agent Development Kit）を使用してエージェントを構築。
Vertex AI Agent Engineへのデプロイに対応。
"""

from google.adk.agents import Agent

from .config import settings
from .custom_gemini import GlobalGemini
from .prompts import get_dessin_analysis_system_prompt
from .tools import analyze_dessin_image

# globalリージョン用Geminiモデル
# gemini-3-flash-previewはglobalリージョンでのみ利用可能
gemini_model = GlobalGemini(model=settings.gemini_model)

# ルートエージェント定義
root_agent = Agent(
    name="dessin_coaching_agent",
    model=gemini_model,
    description="鉛筆デッサンを分析し、改善フィードバックを提供するコーチングエージェント",
    instruction=get_dessin_analysis_system_prompt(),
    tools=[analyze_dessin_image],
)


