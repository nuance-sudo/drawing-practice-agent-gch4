"""メモリツールのテスト"""

from unittest.mock import MagicMock, patch

import pytest

from dessin_coaching_agent.callbacks import (
    _build_memory_fact,
    _build_memory_metadata,
    save_analysis_to_memory,
)
from dessin_coaching_agent.memory_tools import (
    _extract_metadata,
    search_memory_by_motif,
    search_recent_memories,
)
from dessin_coaching_agent.models import (
    DessinAnalysis,
    LineQualityAnalysis,
    ProportionAnalysis,
    TextureAnalysis,
    ToneAnalysis,
)


@pytest.fixture
def sample_analysis() -> DessinAnalysis:
    """テスト用の分析結果を生成"""
    return DessinAnalysis(
        proportion=ProportionAnalysis(
            shape_accuracy="良好",
            ratio_balance="適切",
            contour_quality="安定",
            score=75.0,
        ),
        tone=ToneAnalysis(
            value_range="5段階",
            light_consistency="一貫性あり",
            three_dimensionality="良好",
            score=70.0,
        ),
        texture=TextureAnalysis(
            material_expression="基本的",
            touch_variety="限定的",
            score=65.0,
        ),
        line_quality=LineQualityAnalysis(
            stroke_quality="安定",
            pressure_control="適切",
            hatching="基本的",
            score=72.0,
        ),
        overall_score=70.5,
        strengths=["プロポーションが正確", "陰影の一貫性"],
        improvements=["質感表現の向上", "ハッチングの応用"],
        tags=["りんご", "静物"],
    )


class TestSaveAnalysisToMemory:
    """save_analysis_to_memory のテスト"""

    def test_skips_when_agent_engine_id_not_set(
        self, sample_analysis: DessinAnalysis
    ) -> None:
        """AGENT_ENGINE_ID未設定時はスキップしてFalseを返す"""
        with patch(
            "dessin_coaching_agent.callbacks.settings"
        ) as mock_settings:
            mock_settings.agent_engine_id = ""

            result = save_analysis_to_memory(sample_analysis, "test_user")

            assert result is False

    def test_saves_memory_with_metadata(
        self, sample_analysis: DessinAnalysis
    ) -> None:
        """メタデータ付きでメモリが保存される"""
        with (
            patch(
                "dessin_coaching_agent.callbacks.settings"
            ) as mock_settings,
            patch("dessin_coaching_agent.callbacks.Client") as mock_client_cls,
        ):
            mock_settings.agent_engine_id = "test-engine"
            mock_settings.gcp_project_id = "test-project"
            mock_settings.gcp_region = "us-central1"

            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client

            result = save_analysis_to_memory(sample_analysis, "test_user")

            assert result is True
            mock_client.agent_engines.memories.create.assert_called_once()

    def test_handles_exception_gracefully(
        self, sample_analysis: DessinAnalysis
    ) -> None:
        """例外発生時はFalseを返す"""
        with (
            patch(
                "dessin_coaching_agent.callbacks.settings"
            ) as mock_settings,
            patch("dessin_coaching_agent.callbacks.Client") as mock_client_cls,
        ):
            mock_settings.agent_engine_id = "test-engine"
            mock_settings.gcp_project_id = "test-project"
            mock_settings.gcp_region = "us-central1"

            mock_client = MagicMock()
            mock_client.agent_engines.memories.create.side_effect = Exception(
                "API Error"
            )
            mock_client_cls.return_value = mock_client

            result = save_analysis_to_memory(sample_analysis, "test_user")

            assert result is False


class TestBuildMemoryMetadata:
    """_build_memory_metadata のテスト"""

    def test_builds_metadata_with_all_fields(
        self, sample_analysis: DessinAnalysis
    ) -> None:
        """全フィールドを含むメタデータが構築される"""
        metadata = _build_memory_metadata(sample_analysis)

        assert "motif" in metadata
        assert "overall_score" in metadata
        assert "proportion_score" in metadata
        assert "tone_score" in metadata
        assert "texture_score" in metadata
        assert "line_quality_score" in metadata
        assert "submitted_at" in metadata


class TestBuildMemoryFact:
    """_build_memory_fact のテスト"""

    def test_builds_fact_text(self, sample_analysis: DessinAnalysis) -> None:
        """分析結果からfactテキストが構築される"""
        fact = _build_memory_fact(sample_analysis)

        assert "総合スコア: 70.5/100" in fact
        assert "プロポーション: 75.0/100" in fact
        assert "りんご" in fact


class TestSearchMemoryByMotif:
    """search_memory_by_motif のテスト"""

    def test_skips_when_agent_engine_id_not_set(self) -> None:
        """AGENT_ENGINE_ID未設定時は空リストを返す"""
        with patch(
            "dessin_coaching_agent.memory_tools.settings"
        ) as mock_settings:
            mock_settings.agent_engine_id = ""

            result = search_memory_by_motif("りんご", "test_user")

            assert result == []

    def test_returns_memories_for_motif(self) -> None:
        """モチーフでフィルタしたメモリが返される"""
        with (
            patch(
                "dessin_coaching_agent.memory_tools.settings"
            ) as mock_settings,
            patch(
                "dessin_coaching_agent.memory_tools.Client"
            ) as mock_client_cls,
        ):
            mock_settings.agent_engine_id = "test-engine"
            mock_settings.gcp_project_id = "test-project"
            mock_settings.gcp_region = "us-central1"

            mock_memory = MagicMock()
            mock_memory.fact = "テスト分析結果"
            mock_memory.metadata = {}

            mock_retrieved = MagicMock()
            mock_retrieved.memory = mock_memory

            mock_client = MagicMock()
            mock_client.agent_engines.memories.retrieve.return_value = [
                mock_retrieved
            ]
            mock_client_cls.return_value = mock_client

            result = search_memory_by_motif("りんご", "test_user")

            assert len(result) == 1
            assert result[0]["fact"] == "テスト分析結果"


class TestSearchRecentMemories:
    """search_recent_memories のテスト"""

    def test_skips_when_agent_engine_id_not_set(self) -> None:
        """AGENT_ENGINE_ID未設定時は空リストを返す"""
        with patch(
            "dessin_coaching_agent.memory_tools.settings"
        ) as mock_settings:
            mock_settings.agent_engine_id = ""

            result = search_recent_memories("test_user")

            assert result == []

    def test_limits_results(self) -> None:
        """指定された件数までの結果を返す"""
        with (
            patch(
                "dessin_coaching_agent.memory_tools.settings"
            ) as mock_settings,
            patch(
                "dessin_coaching_agent.memory_tools.Client"
            ) as mock_client_cls,
        ):
            mock_settings.agent_engine_id = "test-engine"
            mock_settings.gcp_project_id = "test-project"
            mock_settings.gcp_region = "us-central1"

            mock_memories = []
            for i in range(10):
                mock_memory = MagicMock()
                mock_memory.fact = f"分析結果{i}"
                mock_memory.metadata = {}
                mock_retrieved = MagicMock()
                mock_retrieved.memory = mock_memory
                mock_memories.append(mock_retrieved)

            mock_client = MagicMock()
            mock_client.agent_engines.memories.retrieve.return_value = (
                mock_memories
            )
            mock_client_cls.return_value = mock_client

            result = search_recent_memories("test_user", limit=3)

            assert len(result) == 3


class TestExtractMetadata:
    """_extract_metadata のテスト"""

    def test_extracts_string_value(self) -> None:
        """string_valueが正しく抽出される"""
        mock_value = MagicMock()
        mock_value.string_value = "テスト値"
        mock_value.double_value = None
        mock_value.bool_value = None
        mock_value.timestamp_value = None

        result = _extract_metadata({"key": mock_value})

        assert result["key"] == "テスト値"

    def test_extracts_double_value(self) -> None:
        """double_valueが正しく抽出される"""
        mock_value = MagicMock()
        mock_value.string_value = None
        mock_value.double_value = 75.5
        mock_value.bool_value = None
        mock_value.timestamp_value = None

        result = _extract_metadata({"score": mock_value})

        assert result["score"] == 75.5
