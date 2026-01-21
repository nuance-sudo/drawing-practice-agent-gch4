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
        
        # 画像生成用モデル（gemini-2.5-flash-image）
        self._image_model = GenerativeModel(
            model_name=settings.gemini_image_model,
            generation_config={
                "max_output_tokens": 8192,  # 画像生成用は少なめ
                "temperature": 0.7,  # 画像生成は少し創造性を抑える
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

    async def generate_image(
        self,
        prompt: str,
        original_image_data: Optional[bytes] = None
    ) -> bytes:
        """Gemini 2.5 Flash Imageで画像を生成

        Args:
            prompt: 画像生成プロンプト
            original_image_data: 参考にする元画像（オプション）

        Returns:
            生成画像データ（bytes）

        Raises:
            GeminiServiceError: 画像生成に失敗した場合
        """
        try:
            # プロンプトを準備
            content_parts = [prompt]
            
            # 元画像がある場合は参考として追加
            if original_image_data:
                image_part = Part.from_data(
                    data=original_image_data,
                    mime_type="image/jpeg"
                )
                content_parts.append(image_part)
            
            logger.debug(
                "image_generation_request",
                prompt_length=len(prompt),
                has_reference_image=original_image_data is not None
            )
            
            # 画像生成を実行
            response = await asyncio.to_thread(
                self._image_model.generate_content,
                content_parts
            )
            
            # レスポンスから画像データを抽出
            image_data = self._extract_image_from_response(response)
            
            logger.debug(
                "image_generation_completed",
                image_size_bytes=len(image_data),
                usage_metadata=getattr(response, 'usage_metadata', None)
            )
            
            return image_data
            
        except Exception as e:
            logger.error("image_generation_failed", error=str(e))
            raise GeminiServiceError(f"Failed to generate image: {e}")

    def _extract_image_from_response(self, response) -> bytes:
        """Geminiレスポンスから画像データを抽出

        Args:
            response: Geminiのレスポンス

        Returns:
            画像データ（bytes）

        Raises:
            GeminiServiceError: 画像データが見つからない場合
        """
        try:
            # レスポンスの候補から画像パートを探す
            for candidate in response.candidates:
                for part in candidate.content.parts:
                    # inline_dataがある場合（base64エンコードされた画像）
                    if hasattr(part, 'inline_data') and part.inline_data:
                        if part.inline_data.mime_type.startswith('image/'):
                            # base64デコード
                            image_data = base64.b64decode(part.inline_data.data)
                            return image_data
                    
                    # file_dataがある場合（ファイル参照）
                    elif hasattr(part, 'file_data') and part.file_data:
                        # この場合は別途ファイルを取得する必要がある
                        # 現在の実装では対応しない
                        logger.warning("file_data_not_supported", file_uri=part.file_data.file_uri)
            
            # 画像が見つからない場合
            raise GeminiServiceError("No image data found in response")
            
        except Exception as e:
            raise GeminiServiceError(f"Failed to extract image from response: {e}")

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
            "image_model": settings.gemini_image_model,
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