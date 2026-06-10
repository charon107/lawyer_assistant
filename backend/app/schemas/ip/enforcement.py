"""IpEnforcement request / response schemas."""

from datetime import date
from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.ip._json import parse_json_field

MatterType = Literal["cease_desist", "takedown"]
# cease_desist: send/receive · takedown: send/respond/counter
EnforcementMode = Literal["send", "receive", "respond", "counter"]
EnforcementStatus = Literal[
    "intake",
    "drafting",
    "gated",
    "sent",
    "responded",
    "escalated",
    "closed",
]

_JSON_FIELDS = ("right_at_issue", "due_diligence", "send_gate", "log")


class IpEnforcementCreate(BaseSchema):
    """REST intake — creates the matter; the WS skill drafts the letter."""

    matter_type: MatterType
    mode: EnforcementMode = "send"
    counterparty: str | None = Field(default=None, max_length=255)
    right_at_issue: dict[str, Any] | None = None
    infringement_facts: str | None = None
    response_deadline: date | None = None


class IpEnforcementUpdate(BaseSchema):
    mode: EnforcementMode | None = None
    counterparty: str | None = Field(default=None, max_length=255)
    right_at_issue: dict[str, Any] | None = None
    infringement_facts: str | None = None
    due_diligence: dict[str, Any] | None = None
    response_deadline: date | None = None
    letter_draft: str | None = None
    outbound_letter: str | None = None
    send_gate: dict[str, Any] | None = None
    recommended_action: str | None = None
    status: EnforcementStatus | None = None
    escalation_flag: bool | None = None
    escalation_reason: str | None = None
    log: list[dict[str, Any]] | None = None


class IpEnforcementRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    matter_type: MatterType
    mode: EnforcementMode = "send"
    counterparty: str | None = None
    right_at_issue: dict[str, Any] | None = None
    infringement_facts: str | None = None
    due_diligence: dict[str, Any] | None = None
    response_deadline: date | None = None
    letter_draft: str | None = None
    outbound_letter: str | None = None
    send_gate: dict[str, Any] | None = None
    recommended_action: str | None = None
    status: EnforcementStatus = "intake"
    escalation_flag: bool = False
    escalation_reason: str | None = None
    log: list[dict[str, Any]] | None = None

    @field_validator(*_JSON_FIELDS, mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class IpEnforcementList(BaseSchema):
    items: list[IpEnforcementRead]
    total: int
