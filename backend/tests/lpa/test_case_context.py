"""Tests for case context integration in agent.py."""

from unittest.mock import MagicMock, patch

from app.api.routes.v1.agent import _build_case_system_prompt


def _mock_get_db_session(mock_db):
    """Create a mock generator function that mimics get_db_session."""

    def _gen():
        yield mock_db

    return _gen


class TestBuildCaseSystemPrompt:
    """Tests for _build_case_system_prompt function."""

    def test_returns_prompt_with_case_and_documents(self):
        mock_case = MagicMock()
        case_id = "case-abc"
        mock_case.id = case_id
        mock_case.user_id = "user-123"
        mock_case.name = "Test LPA Review"
        mock_case.description = "Review of partnership agreement"

        mock_doc = MagicMock()
        mock_doc.filename = "agreement.pdf"
        mock_doc.summary = "Partnership agreement with 2% management fee"
        mock_doc.parsed_content = "Full parsed content here..."

        mock_db = MagicMock()

        with (
            patch("app.api.routes.v1.agent.get_db_session", _mock_get_db_session(mock_db)),
            patch("app.repositories.lpa_case_repo.get_case_by_id", return_value=mock_case),
            patch("app.repositories.lpa_case_repo.get_documents_by_case", return_value=[mock_doc]),
        ):
            result = _build_case_system_prompt(case_id, "user-123")

        assert result is not None
        assert "Test LPA Review" in result
        assert "Review of partnership agreement" in result
        assert "agreement.pdf" in result
        assert "Partnership agreement with 2% management fee" in result
        assert "Full parsed content here..." in result

    def test_returns_prompt_with_no_documents(self):
        mock_case = MagicMock()
        mock_case.id = "case-abc"
        mock_case.user_id = "user-123"
        mock_case.name = "Empty Case"
        mock_case.description = None

        mock_db = MagicMock()

        with (
            patch("app.api.routes.v1.agent.get_db_session", _mock_get_db_session(mock_db)),
            patch("app.repositories.lpa_case_repo.get_case_by_id", return_value=mock_case),
            patch("app.repositories.lpa_case_repo.get_documents_by_case", return_value=[]),
        ):
            result = _build_case_system_prompt("case-abc", "user-123")

        assert result is not None
        assert "Empty Case" in result
        assert "暂无材料" in result

    def test_returns_none_when_case_not_found(self):
        mock_db = MagicMock()

        with (
            patch("app.api.routes.v1.agent.get_db_session", _mock_get_db_session(mock_db)),
            patch("app.repositories.lpa_case_repo.get_case_by_id", return_value=None),
        ):
            result = _build_case_system_prompt("nonexistent", "user-123")

        assert result is None

    def test_returns_none_when_wrong_user(self):
        mock_case = MagicMock()
        mock_case.user_id = "other-user"

        mock_db = MagicMock()

        with (
            patch("app.api.routes.v1.agent.get_db_session", _mock_get_db_session(mock_db)),
            patch("app.repositories.lpa_case_repo.get_case_by_id", return_value=mock_case),
        ):
            result = _build_case_system_prompt("case-abc", "user-123")

        assert result is None

    def test_returns_none_on_exception(self):
        with patch("app.api.routes.v1.agent.get_db_session", side_effect=RuntimeError("DB failed")):
            result = _build_case_system_prompt("case-abc", "user-123")

        assert result is None

    def test_truncates_long_document_content(self):
        mock_case = MagicMock()
        mock_case.id = "case-abc"
        mock_case.user_id = "user-123"
        mock_case.name = "Case"
        mock_case.description = None

        mock_doc = MagicMock()
        mock_doc.filename = "long.pdf"
        mock_doc.summary = None
        mock_doc.parsed_content = "x" * 20000  # very long

        mock_db = MagicMock()

        with (
            patch("app.api.routes.v1.agent.get_db_session", _mock_get_db_session(mock_db)),
            patch("app.repositories.lpa_case_repo.get_case_by_id", return_value=mock_case),
            patch("app.repositories.lpa_case_repo.get_documents_by_case", return_value=[mock_doc]),
        ):
            result = _build_case_system_prompt("case-abc", "user-123")

        assert result is not None
        # Content should be truncated to 8000 chars
        assert "x" * 8000 in result
        assert "x" * 8001 not in result

    def test_document_without_summary_or_content(self):
        mock_case = MagicMock()
        mock_case.id = "case-abc"
        mock_case.user_id = "user-123"
        mock_case.name = "Case"
        mock_case.description = None

        mock_doc = MagicMock()
        mock_doc.filename = "empty.pdf"
        mock_doc.summary = None
        mock_doc.parsed_content = None

        mock_db = MagicMock()

        with (
            patch("app.api.routes.v1.agent.get_db_session", _mock_get_db_session(mock_db)),
            patch("app.repositories.lpa_case_repo.get_case_by_id", return_value=mock_case),
            patch("app.repositories.lpa_case_repo.get_documents_by_case", return_value=[mock_doc]),
        ):
            result = _build_case_system_prompt("case-abc", "user-123")

        assert result is not None
        assert "empty.pdf" in result


class TestGetAgentSystemPromptParam:
    """Tests for the system_prompt parameter added to get_agent factory."""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_get_agent_accepts_system_prompt(self):
        from app.agents.assistant import get_agent

        agent = get_agent(system_prompt="Custom prompt for case context")
        assert agent.system_prompt == "Custom prompt for case context"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_get_agent_default_system_prompt(self):
        from app.agents.assistant import get_agent
        from app.agents.prompts import DEFAULT_SYSTEM_PROMPT

        agent = get_agent()
        assert agent.system_prompt == DEFAULT_SYSTEM_PROMPT
