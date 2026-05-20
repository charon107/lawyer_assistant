"""LPA Case schemas."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class CaseCreate(BaseSchema):
    """Schema for creating an LPA case."""

    name: str = Field(..., max_length=255, min_length=1, description="Case name")
    description: str | None = Field(default=None, description="Case description")
    document_type: Literal[
        "lpa",
        "contract",
        "nda",
        "employment",
        "lease",
        "loan",
        "sales",
        "service",
        "ip_license",
        "equity_investment",
        "construction",
        "articles_of_association",
        "marital_property",
        "will_estate",
    ] = Field(default="lpa", description="Document type")


class CaseUpdate(BaseSchema):
    """Schema for updating an LPA case."""

    name: str | None = Field(default=None, max_length=255, min_length=1)
    description: str | None = None
    status: Literal["active", "archived"] | None = None


class DocumentRead(BaseSchema):
    """Schema for reading a document attached to a case."""

    id: str
    filename: str
    mime_type: str
    file_type: str
    size: int
    summary: str | None = None
    has_parsed_content: bool = False
    analysis_status: str | None = None
    created_at: datetime


class CaseRead(BaseSchema, TimestampSchema):
    """Schema for reading an LPA case."""

    id: str
    user_id: str
    name: str
    description: str | None = None
    status: str = "active"
    document_type: str = "lpa"
    document_count: int = 0


class CaseDetailRead(CaseRead):
    """Schema for reading an LPA case with documents."""

    documents: list[DocumentRead] = Field(default_factory=list)


class CaseList(BaseSchema):
    """Schema for listing LPA cases."""

    items: list[CaseRead]
    total: int


class DocumentList(BaseSchema):
    """Schema for listing documents in a case."""

    items: list[DocumentRead]
    total: int


# Backward compatibility aliases
LPACaseCreate = CaseCreate
LPACaseUpdate = CaseUpdate
LPADocumentRead = DocumentRead
LPACaseRead = CaseRead
LPACaseDetailRead = CaseDetailRead
LPACaseList = CaseList
LPADocumentList = DocumentList
