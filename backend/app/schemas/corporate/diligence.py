"""DiligenceIssue request / response schemas — diligence findings."""

from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

# Canonical severity floor 🔴/🟠/🟡/🟢.
Severity = Literal["blocking", "high", "medium", "low"]
IssueStatus = Literal["open", "resolved", "waived"]


class DiligenceIssueCreate(BaseSchema):
    deal_id: str
    title: str = Field(min_length=1, max_length=500)
    category: str | None = Field(default=None, max_length=100)
    severity: Severity = "medium"
    source_doc: str | None = Field(default=None, max_length=500)
    finding: str | None = None
    recommendation: str | None = None
    cite: str | None = None


class DiligenceIssueUpdate(BaseSchema):
    title: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=100)
    severity: Severity | None = None
    source_doc: str | None = Field(default=None, max_length=500)
    finding: str | None = None
    recommendation: str | None = None
    cite: str | None = None
    status: IssueStatus | None = None


class DiligenceIssueRead(BaseSchema, TimestampSchema):
    id: str
    deal_id: str
    title: str
    category: str | None = None
    severity: Severity = "medium"
    source_doc: str | None = None
    finding: str | None = None
    recommendation: str | None = None
    cite: str | None = None
    status: IssueStatus = "open"


class DiligenceIssueList(BaseSchema):
    items: list[DiligenceIssueRead]
    total: int
