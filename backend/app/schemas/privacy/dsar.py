"""PrivacyDsar request / response schemas."""

from datetime import date
from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.privacy._json import parse_json_field

DsarRequestType = Literal["access", "copy", "delete", "correct", "explain", "restrict"]
DsarStatus = Literal[
    "received",
    "verifying",
    "locating",
    "exemption_analysis",
    "drafted",
    "responded",
    "escalated",
]

_JSON_FIELDS = ("request_types", "systems_checked", "exemptions", "log")


class PrivacyDsarCreate(BaseSchema):
    """REST intake — minimal PII. Never put the subject's full name here."""

    request_types: list[DsarRequestType] = Field(default_factory=list)
    data_subject_ref: str | None = Field(default=None, max_length=120)
    date_received: date | None = None
    response_deadline: date | None = None
    verification_method: str | None = Field(default=None, max_length=120)


class PrivacyDsarUpdate(BaseSchema):
    request_types: list[DsarRequestType] | None = None
    data_subject_ref: str | None = Field(default=None, max_length=120)
    date_received: date | None = None
    date_verified: date | None = None
    date_responded: date | None = None
    response_deadline: date | None = None
    identity_verified: bool | None = None
    verification_method: str | None = Field(default=None, max_length=120)
    systems_checked: list[dict[str, Any]] | None = None
    exemptions: list[dict[str, Any]] | None = None
    ack_letter: str | None = None
    response_letter: str | None = None
    status: DsarStatus | None = None
    escalation_flag: bool | None = None
    escalation_reason: str | None = None
    log: list[dict[str, Any]] | None = None


class PrivacyDsarRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    request_types: list[str] | None = None
    data_subject_ref: str | None = None
    date_received: date | None = None
    date_verified: date | None = None
    date_responded: date | None = None
    response_deadline: date | None = None
    identity_verified: bool = False
    verification_method: str | None = None
    systems_checked: list[dict[str, Any]] | None = None
    exemptions: list[dict[str, Any]] | None = None
    ack_letter: str | None = None
    response_letter: str | None = None
    status: DsarStatus = "received"
    escalation_flag: bool = False
    escalation_reason: str | None = None
    log: list[dict[str, Any]] | None = None

    @field_validator(*_JSON_FIELDS, mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class PrivacyDsarList(BaseSchema):
    items: list[PrivacyDsarRead]
    total: int
