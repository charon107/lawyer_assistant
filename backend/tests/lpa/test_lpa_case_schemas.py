"""Tests for LPA Case Pydantic schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.lpa_case import (
    LPACaseCreate,
    LPACaseDetailRead,
    LPACaseList,
    LPACaseRead,
    LPACaseUpdate,
    LPADocumentList,
    LPADocumentRead,
)


class TestLPACaseCreate:
    def test_valid_create(self):
        schema = LPACaseCreate(name="Test Case", description="A description")
        assert schema.name == "Test Case"
        assert schema.description == "A description"

    def test_create_minimal(self):
        schema = LPACaseCreate(name="Minimal")
        assert schema.name == "Minimal"
        assert schema.description is None

    def test_create_strips_whitespace(self):
        schema = LPACaseCreate(name="  Padded  ")
        assert schema.name == "Padded"

    def test_create_empty_name_fails(self):
        with pytest.raises(ValidationError):
            LPACaseCreate(name="")

    def test_create_name_too_long(self):
        with pytest.raises(ValidationError):
            LPACaseCreate(name="x" * 256)

    def test_create_missing_name_fails(self):
        with pytest.raises(ValidationError):
            LPACaseCreate()


class TestLPACaseUpdate:
    def test_valid_update(self):
        schema = LPACaseUpdate(name="Updated", description="New desc", status="archived")
        assert schema.name == "Updated"
        assert schema.status == "archived"

    def test_update_all_optional(self):
        schema = LPACaseUpdate()
        assert schema.name is None
        assert schema.description is None
        assert schema.status is None

    def test_update_partial(self):
        schema = LPACaseUpdate(name="Only name")
        assert schema.name == "Only name"
        assert schema.description is None

    def test_update_invalid_status(self):
        with pytest.raises(ValidationError):
            LPACaseUpdate(status="invalid_status")

    def test_update_valid_statuses(self):
        assert LPACaseUpdate(status="active").status == "active"
        assert LPACaseUpdate(status="archived").status == "archived"


class TestLPADocumentRead:
    def test_valid_read(self):
        schema = LPADocumentRead(
            id="doc-1",
            filename="test.pdf",
            mime_type="application/pdf",
            file_type="pdf",
            size=1024,
            created_at=datetime.now(UTC),
        )
        assert schema.id == "doc-1"
        assert schema.has_parsed_content is False
        assert schema.summary is None

    def test_read_with_summary(self):
        schema = LPADocumentRead(
            id="doc-1",
            filename="test.pdf",
            mime_type="application/pdf",
            file_type="pdf",
            size=1024,
            summary="A summary",
            has_parsed_content=True,
            created_at=datetime.now(UTC),
        )
        assert schema.summary == "A summary"
        assert schema.has_parsed_content is True


class TestLPACaseRead:
    def test_valid_read(self):
        schema = LPACaseRead(
            id="case-1",
            user_id="user-1",
            name="Test",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert schema.status == "active"
        assert schema.document_count == 0
        assert schema.description is None

    def test_read_with_all_fields(self):
        schema = LPACaseRead(
            id="case-1",
            user_id="user-1",
            name="Test",
            description="desc",
            status="archived",
            document_count=5,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert schema.document_count == 5
        assert schema.status == "archived"


class TestLPACaseDetailRead:
    def test_detail_inherits_case_read(self):
        schema = LPACaseDetailRead(
            id="case-1",
            user_id="user-1",
            name="Test",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert schema.documents == []

    def test_detail_with_documents(self):
        doc = LPADocumentRead(
            id="doc-1",
            filename="test.pdf",
            mime_type="application/pdf",
            file_type="pdf",
            size=1024,
            created_at=datetime.now(UTC),
        )
        schema = LPACaseDetailRead(
            id="case-1",
            user_id="user-1",
            name="Test",
            documents=[doc],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert len(schema.documents) == 1
        assert schema.documents[0].id == "doc-1"


class TestLPACaseList:
    def test_list_schema(self):
        case = LPACaseRead(
            id="c1",
            user_id="u1",
            name="Case 1",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        schema = LPACaseList(items=[case], total=1)
        assert len(schema.items) == 1
        assert schema.total == 1

    def test_empty_list(self):
        schema = LPACaseList(items=[], total=0)
        assert schema.items == []
        assert schema.total == 0


class TestLPADocumentList:
    def test_document_list(self):
        doc = LPADocumentRead(
            id="d1",
            filename="test.pdf",
            mime_type="application/pdf",
            file_type="pdf",
            size=1024,
            created_at=datetime.now(UTC),
        )
        schema = LPADocumentList(items=[doc], total=1)
        assert len(schema.items) == 1

    def test_empty_document_list(self):
        schema = LPADocumentList(items=[], total=0)
        assert schema.items == []
