"""Tests for document analysis feature."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.repositories import lpa_case_repo
from app.schemas.document_analysis import (
    DocumentAnalysisResult,
    LegalParty,
    LegalRelationship,
    RiskPoint,
)

# --- Schema Tests ---


class TestDocumentAnalysisResult:
    def test_valid_json_parses_correctly(self):
        data = {
            "parties": [{"name": "张三", "role": "甲方", "type": "自然人"}],
            "contract_type": "借款合同",
            "key_terms": [{"term": "借款金额", "content": "100万元", "location": "第三条"}],
            "legal_relationships": [
                {
                    "parties": ["张三", "李四"],
                    "relationship_type": "借贷关系",
                    "description": "张三向李四借款",
                }
            ],
            "applicable_laws": ["民法典第六百六十七条"],
            "risk_points": [
                {
                    "category": "法律风险",
                    "level": "高",
                    "description": "未约定利息",
                    "suggestion": "补充利息条款",
                }
            ],
            "dispute_focal_points": ["还款期限争议"],
            "summary": "这是一份借款合同",
        }
        result = DocumentAnalysisResult.model_validate(data)
        assert result.contract_type == "借款合同"
        assert len(result.parties) == 1
        assert result.parties[0].name == "张三"
        assert len(result.risk_points) == 1
        assert result.risk_points[0].level == "高"

    def test_minimal_valid_data(self):
        data = {"contract_type": "合同", "summary": "摘要"}
        result = DocumentAnalysisResult.model_validate(data)
        assert result.contract_type == "合同"
        assert result.parties == []
        assert result.key_terms == []
        assert result.risk_points == []

    def test_json_roundtrip(self):
        data = {
            "contract_type": "保密协议",
            "summary": "测试摘要",
            "parties": [{"name": "A公司", "role": "披露方"}],
        }
        result = DocumentAnalysisResult.model_validate(data)
        json_str = result.model_dump_json()
        restored = DocumentAnalysisResult.model_validate_json(json_str)
        assert restored.contract_type == result.contract_type
        assert len(restored.parties) == 1

    def test_missing_contract_type_raises(self):
        data = {"summary": "摘要"}
        with pytest.raises(Exception):
            DocumentAnalysisResult.model_validate(data)

    def test_missing_summary_raises(self):
        data = {"contract_type": "合同"}
        with pytest.raises(Exception):
            DocumentAnalysisResult.model_validate(data)


# --- Repository Tests ---


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def mock_analysis():
    analysis = MagicMock()
    analysis.id = "analysis-123"
    analysis.chat_file_id = "doc-123"
    analysis.status = "pending"
    analysis.analysis_json = None
    analysis.error_message = None
    analysis.completed_at = None
    analysis.created_at = datetime.now(UTC)
    return analysis


class TestCreateDocumentAnalysis:
    def test_creates_pending_analysis(self, mock_session):
        mock_session.add = MagicMock()
        mock_session.flush = MagicMock()
        mock_session.refresh = MagicMock()

        with patch("app.repositories.lpa_case_repo.DocumentAnalysis") as MockModel:
            mock_instance = MagicMock()
            MockModel.return_value = mock_instance
            result = lpa_case_repo.create_document_analysis(mock_session, chat_file_id="doc-123")

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
        assert result == mock_instance


class TestUpdateDocumentAnalysisStatus:
    def test_update_to_completed(self, mock_session, mock_analysis):
        mock_session.get.return_value = mock_analysis
        mock_session.flush = MagicMock()
        mock_session.refresh = MagicMock()

        result = lpa_case_repo.update_document_analysis_status(
            mock_session,
            analysis_id="analysis-123",
            status="completed",
            analysis_json='{"contract_type":"test","summary":"s"}',
        )

        assert mock_analysis.status == "completed"
        assert mock_analysis.completed_at is not None
        mock_session.flush.assert_called_once()

    def test_update_to_failed_with_error(self, mock_session, mock_analysis):
        mock_session.get.return_value = mock_analysis
        mock_session.flush = MagicMock()
        mock_session.refresh = MagicMock()

        result = lpa_case_repo.update_document_analysis_status(
            mock_session,
            analysis_id="analysis-123",
            status="failed",
            error_message="Parse error",
        )

        assert mock_analysis.status == "failed"
        assert mock_analysis.error_message == "Parse error"

    def test_update_not_found(self, mock_session):
        mock_session.get.return_value = None
        result = lpa_case_repo.update_document_analysis_status(
            mock_session, analysis_id="nonexistent", status="completed"
        )
        assert result is None


class TestGetDocumentAnalysis:
    def test_found(self, mock_session, mock_analysis):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_analysis
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_document_analysis(mock_session, "doc-123")
        assert result == mock_analysis

    def test_not_found(self, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_document_analysis(mock_session, "nonexistent")
        assert result is None


class TestGetAnalysesByCase:
    def test_returns_dict_by_chat_file_id(self, mock_session):
        mock_a1 = MagicMock()
        mock_a1.chat_file_id = "doc-1"
        mock_a2 = MagicMock()
        mock_a2.chat_file_id = "doc-2"

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_a1, mock_a2]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_analyses_by_case(mock_session, "case-123")
        assert len(result) == 2
        assert result["doc-1"] == mock_a1
        assert result["doc-2"] == mock_a2

    def test_empty_case(self, mock_session):
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = lpa_case_repo.get_analyses_by_case(mock_session, "case-123")
        assert result == {}


# --- Context Formatting Tests ---


class TestFormatAnalysisForPrompt:
    def test_full_analysis_formatting(self):
        from app.api.routes.v1.agent import _format_analysis_for_prompt

        analysis = DocumentAnalysisResult(
            parties=[
                LegalParty(name="张三", role="甲方", type="自然人"),
                LegalParty(name="李四", role="乙方", type="自然人"),
            ],
            contract_type="借款合同",
            key_terms=[],
            legal_relationships=[
                LegalRelationship(
                    parties=["张三", "李四"],
                    relationship_type="借贷关系",
                    description="张三向李四借款100万",
                )
            ],
            applicable_laws=["民法典第六百六十七条"],
            risk_points=[RiskPoint(category="法律风险", level="高", description="未约定还款期限")],
            dispute_focal_points=["还款期限"],
            summary="借款合同摘要",
        )

        result = _format_analysis_for_prompt(analysis)
        assert "张三(甲方)" in result
        assert "借款合同" in result
        assert "借贷关系" in result
        assert "民法典第六百六十七条" in result
        assert "[高]" in result
        assert "还款期限" in result

    def test_minimal_analysis_formatting(self):
        from app.api.routes.v1.agent import _format_analysis_for_prompt

        analysis = DocumentAnalysisResult(contract_type="合同", summary="摘要")
        result = _format_analysis_for_prompt(analysis)
        assert "合同" in result
        assert "摘要" in result


# --- Prompt Tests ---


class TestDocumentAnalysisPrompt:
    def test_prompt_contains_content_placeholder(self):
        from app.agents.prompts import DOCUMENT_ANALYSIS_PROMPT

        assert "{content}" in DOCUMENT_ANALYSIS_PROMPT

    def test_prompt_requests_json_output(self):
        from app.agents.prompts import DOCUMENT_ANALYSIS_PROMPT

        assert "JSON" in DOCUMENT_ANALYSIS_PROMPT
        assert "parties" in DOCUMENT_ANALYSIS_PROMPT
        assert "contract_type" in DOCUMENT_ANALYSIS_PROMPT
        assert "risk_points" in DOCUMENT_ANALYSIS_PROMPT
