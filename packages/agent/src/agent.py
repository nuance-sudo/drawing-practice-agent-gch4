"""鉛筆デッサンコーチングエージェント定義

ADK（Agents Development Kit）を使用してエージェントを構築。
"""

import structlog
from google.adk.agents import Agent

from src.config import settings
from src.prompts.coaching import get_dessin_analysis_system_prompt
from src.tools.analysis import analyze_dessin_image

logger = structlog.get_logger()

# ルートエージェント定義
root_agent = Agent(
    name="dessin-coaching-agent",
    model=settings.gemini_model,
    description="鉛筆デッサンを分析し、改善フィードバックを提供するコーチングエージェント",
    instruction=get_dessin_analysis_system_prompt(),
    tools=[analyze_dessin_image],
)
