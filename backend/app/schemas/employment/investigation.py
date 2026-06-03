"""Internal-investigation request / response schemas."""

from datetime import date, datetime
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.employment._json import parse_json_field

InvestigationType = Literal["HR", "financial", "executive", "whistleblower", "other"]
InvestigationStatus = Literal["open", "investigating", "memo_draft", "closed"]


class InvestigationCreate(BaseSchema):
    investigation_name: str = Field(max_length=255)
    allegation: str | None = None
    investigation_type: InvestigationType | None = None
    scope: str | None = None
    attorney_directed: bool = False


class LogEntryCreate(BaseSchema):
    entry_type: str | None = Field(default=None, max_length=30)
    date_of_event: date | None = None
    source: str | None = Field(default=None, max_length=500)
    source_type: str | None = Field(default=None, max_length=40)
    issues: list[str] | None = None
    significance: str | None = Field(default=None, max_length=20)
    summary: str | None = None
    quote: str | None = None
    contradicts_entry_seq: int | None = None
    corroborates_entry_seq: int | None = None
    pull_criterion: str | None = Field(default=None, max_length=255)


class LogEntryRead(BaseSchema, TimestampSchema):
    id: str
    investigation_id: str
    entry_seq: int
    entry_type: str | None = None
    date_of_event: date | None = None
    source: str | None = None
    source_type: str | None = None
    issues: list[str] | None = None
    significance: str | None = None
    summary: str | None = None
    quote: str | None = None
    contradicts_entry_seq: int | None = None
    corroborates_entry_seq: int | None = None
    pull_criterion: str | None = None
    privilege: str | None = None

    @field_validator("issues", mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class SourceRead(BaseSchema):
    id: str
    investigation_id: str
    source_seq: int
    source: str
    status: str = "open"
    notes: str | None = None


class SourceUpdate(BaseSchema):
    status: str | None = Field(default=None, max_length=20)
    notes: str | None = None


class GapRead(BaseSchema):
    id: str
    investigation_id: str
    gap_seq: int
    description: str
    identified_from: str | None = None
    source_to_obtain: str | None = None
    priority: str = "medium"
    status: str = "open"


class InvestigationRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    investigation_name: str
    allegation: str | None = None
    investigation_type: InvestigationType | None = None
    scope: str | None = None
    status: InvestigationStatus = "open"
    attorney_directed: bool = False
    privilege_note: str | None = None
    memo: str | None = None
    opened_at: datetime | None = None
    closed_at: datetime | None = None


class InvestigationDetail(InvestigationRead):
    log_entries: list[LogEntryRead] = Field(default_factory=list)
    sources: list[SourceRead] = Field(default_factory=list)
    gaps: list[GapRead] = Field(default_factory=list)


class InvestigationList(BaseSchema):
    items: list[InvestigationRead]
    total: int
