"""Gemini API サービス

Vertex AI経由でGeminiモデル（分析用・画像生成用）を呼び出すサービス。
"""

import base64
import asyncio
from typing import Optional, Dict, Any, List

import structlog
import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image as VertexImage
from google.cloud import aiplatform

from src.config import settings

logger = structlog.get_logger()


class GeminiServiceError(Exception):
    """Gemini API サービスエラー"""
    pass


class GeminiService:
    """Gemini API サービス"""

    def __init__(self) -> None:
        """初期化"""
        # Vertex AI初期化
        vertexai.init(
            project=settings.gcp_project_id,
            location=settings.gcp_region
        )
        
        # 分析用モデル（gemini-2.5-flash）
        self._analysis_model = GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "max_output_tokens": settings.gemini_max_output_tokens,
                "temperature": settings.gemini_temperature,
            }
        )
        


    async def analyze_dessin(
        self,
        image_data: bytes,
        analysis_prompt: str
    ) -> str:
        """デッサン画像を分析する

        Args:
            image_data: 画像データ（bytes）
            analysis_prompt: 分析用プロンプト

        Returns:
            分析結果（JSON文字列）

        Raises:
            GeminiServiceError: 分析に失敗した場合
        """
        try:
            # 画像をVertex AI形式に変換
            image_part = Part.from_data(
                data=image_data,
                mime_type="image/jpeg"  # 必要に応じて動的に判定
            )
            
            # プロンプトと画像を組み合わせて分析
            response = await asyncio.to_thread(
                self._analysis_model.generate_content,
                [analysis_prompt, image_part]
            )
            
            if not response.text:
                raise GeminiServiceError("Empty response from analysis model")
            
            logger.debug(
                "dessin_analysis_completed",
                response_length=len(response.text),
                usage_metadata=getattr(response, 'usage_metadata', None)
            )
            
            return response.text
            
        except Exception as e:
            logger.error("dessin_analysis_failed", error=str(e))
            raise GeminiServiceError(f"Failed to analyze dessin: {e}")





    async def generate_feedback_text(
        self,
        analysis_data: Dict[str, Any],
        user_rank: str,
        feedback_prompt: str
    ) -> str:
        """分析結果からフィードバックテキストを生成

        Args:
            analysis_data: 分析結果データ
            user_rank: ユーザーランク
            feedback_prompt: フィードバック生成プロンプト

        Returns:
            フィードバックテキスト

        Raises:
            GeminiServiceError: フィードバック生成に失敗した場合
        """
        try:
            # プロンプトに分析データとランク情報を組み込み
            full_prompt = f"""
{feedback_prompt}

Analysis Data: {analysis_data}
User Rank: {user_rank}
"""
            
            response = await asyncio.to_thread(
                self._analysis_model.generate_content,
                full_prompt
            )
            
            if not response.text:
                raise GeminiServiceError("Empty response from feedback generation")
            
            logger.debug(
                "feedback_generation_completed",
                response_length=len(response.text)
            )
            
            return response.text
            
        except Exception as e:
            logger.error("feedback_generation_failed", error=str(e))
            raise GeminiServiceError(f"Failed to generate feedback: {e}")

    def get_model_info(self) -> Dict[str, str]:
        """使用中のモデル情報を取得

        Returns:
            モデル情報の辞書
        """
        return {
            "analysis_model": settings.gemini_model,

            "project_id": settings.gcp_project_id,
            "region": settings.gcp_region
        }


# シングルトンインスタンス
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """GeminiServiceのシングルトンインスタンスを取得"""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service