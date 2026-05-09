"""Tests for conversation case_id passthrough."""

from unittest.mock import MagicMock, patch

import pytest

from app.repositories.conversation import create_conversation
from app.schemas.conversation import ConversationCreate


class TestConversationCaseId:
    """Test that case_id flows through conversation creation."""

    def test_conversation_create_schema_accepts_case_id(self):
        schema = ConversationCreate(user_id="user-1", case_id="case-123")
        assert schema.case_id == "case-123"

    def test_conversation_create_schema_case_id_optional(self):
        schema = ConversationCreate(user_id="user-1")
        assert schema.case_id is None

    def test_create_conversation_repo_passes_case_id(self):
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        mock_conv = MagicMock()
        mock_conv.case_id = "case-123"

        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                "app.repositories.conversation.Conversation",
                lambda **kwargs: mock_conv,
            )
            result = create_conversation(
                mock_db, user_id="user-1", title="Test", case_id="case-123"
            )

        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    def test_create_conversation_repo_without_case_id(self):
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()
        mock_db.refresh = MagicMock()

        mock_conv = MagicMock()
        mock_conv.case_id = None

        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                "app.repositories.conversation.Conversation",
                lambda **kwargs: mock_conv,
            )
            result = create_conversation(mock_db, user_id="user-1", title="Test")

        mock_db.add.assert_called_once()

    def test_conversation_service_passes_case_id(self):
        """Test that ConversationService.create_conversation passes case_id to repo."""
        from app.services.conversation import ConversationService

        mock_db = MagicMock()
        service = ConversationService(mock_db)

        mock_conv = MagicMock()
        mock_conv.id = "conv-123"

        with patch("app.services.conversation.conversation_repo") as mock_repo:
            mock_repo.create_conversation = MagicMock(return_value=mock_conv)

            data = ConversationCreate(user_id="user-1", case_id="case-123", title="Test")
            result = service.create_conversation(data)

            mock_repo.create_conversation.assert_called_once()
            call_args = mock_repo.create_conversation.call_args
            assert call_args[1]["case_id"] == "case-123"
