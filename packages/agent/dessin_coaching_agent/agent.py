"""鉛筆デッサンコーチングエージェント定義

ADK（Agent Development Kit）を使用してエージェントを構築。
Vertex AI Agent Engineへのデプロイに対応。
Memory Bank統合により成長トラッキング機能をサポート。
"""

import logging

from google.adk.agents import Agent
from google.adk.tools.preload_memory_tool import PreloadMemoryTool

from .config import settings
from .custom_gemini import GlobalGemini
from .memory_tools import search_memory_by_motif, search_recent_memories
from .prompts import get_dessin_analysis_system_prompt
from .tools import analyze_dessin_image

# logging 設定（Agent Engine の stdout に出力）
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s %(message)s",
    )

# globalリージョン用Geminiモデル
# gemini-3-flash-previewはglobalリージョンでのみ利用可能
gemini_model = GlobalGemini(model=settings.gemini_model)

# Memory Bankからユーザーの過去メモリを自動プリロードするツール
preload_memory_tool = PreloadMemoryTool()

# ルートエージェント定義
root_agent = Agent(
    name="dessin_coaching_agent",
    model=gemini_model,
    description="鉛筆デッサンを分析し、改善フィードバックを提供するコーチングエージェント",
    instruction=get_dessin_analysis_system_prompt(),
    tools=[
        analyze_dessin_image,
        preload_memory_tool,
        search_memory_by_motif,
        search_recent_memories,
    ],
)
