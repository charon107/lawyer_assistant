"""LitigationMatterEvent request / response schemas."""

from datetime import date
from typing import Any, Literal

from pydantic import field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.litigation._json import parse_json_field

EventType = Literal[
    "procedure",
    "evidence",
    "substantive",
    "strategy",
    "risk_reassessment",
    "party",
    "administrative",
    "deadline",
    "closing",
]
DeadlineStatus = Literal["pending", "approaching", "overdue", "met", "waived"]

_JSON_FIELDS = ("field_changes", "associated_files")


class LitigationMatterEventCreate(BaseSchema):
    event_date: date | None = None
    event_type: EventType = "procedure"
    summary: str | None = None
    field_changes: dict[str, list[Any]] | None = None
    due_date: date | None = None
    deadline_status: DeadlineStatus | None = None
    associated_files: list[str] | None = None


class LitigationMatterEventRead(BaseSchema, TimestampSchema):
    id: str
    matter_id: str
    user_id: str
    event_date: date | None = None
    event_type: EventType = "procedure"
    summary: str | None = None
    field_changes: dict[str, list[Any]] | None = None
    due_date: date | None = None
    deadline_status: DeadlineStatus | None = None
    associated_files: list[str] | None = None

    @field_validator(*_JSON_FIELDS, mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class LitigationMatterEventList(BaseSchema):
    items: list[LitigationMatterEventRead]
    total: int
