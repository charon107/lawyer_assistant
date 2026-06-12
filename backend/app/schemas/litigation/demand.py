"""LitigationDemand request / response schemas."""

from datetime import date
from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.litigation._json import parse_json_field

DemandType = Literal[
    "payment",
    "breach_cure",
    "stop_infringement",
    "evidence_preservation",
    "settlement",
    "other",
]
DemandMode = Literal["send", "receive"]
DemandStatus = Literal[
    "intake",
    "drafting",
    "gated",
    "sent",
    "received",
    "responded",
    "escalated",
    "closed",
]
SentVia = Literal["邮件", "快递", "当面"]

_JSON_FIELDS = (
    "intake_snapshot",
    "right_or_claim",
    "pretransmit_checklist",
    "triage_result",
    "log",
)


class LitigationDemandCreate(BaseSchema):
    matter_id: str | None = Field(default=None, max_length=36)
    demand_type: DemandType = "other"
    mode: DemandMode = "send"
    counterparty: str | None = Field(default=None, max_length=255)
    intake_snapshot: dict[str, Any] | None = None
    right_or_claim: dict[str, Any] | None = None
    response_deadline: date | None = None


class LitigationDemandUpdate(BaseSchema):
    demand_type: DemandType | None = None
    mode: DemandMode | None = None
    counterparty: str | None = Field(default=None, max_length=255)
    intake_snapshot: dict[str, Any] | None = None
    right_or_claim: dict[str, Any] | None = None
    letter_draft: str | None = None
    outbound_letter: str | None = None
    pretransmit_checklist: dict[str, Any] | None = None
    response_deadline: date | None = None
    triage_result: dict[str, Any] | None = None
    recommended_action: str | None = None
    status: DemandStatus | None = None
    escalation_flag: bool | None = None
    escalation_reason: str | None = None
    sent_date: date | None = None
    sent_via: SentVia | None = None
    log: list[dict[str, Any]] | None = None


class LitigationDemandRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    matter_id: str | None = None
    demand_type: DemandType = "other"
    mode: DemandMode = "send"
    counterparty: str | None = None
    intake_snapshot: dict[str, Any] | None = None
    right_or_claim: dict[str, Any] | None = None
    letter_draft: str | None = None
    outbound_letter: str | None = None
    pretransmit_checklist: dict[str, Any] | None = None
    response_deadline: date | None = None
    triage_result: dict[str, Any] | None = None
    recommended_action: str | None = None
    status: DemandStatus = "intake"
    escalation_flag: bool = False
    escalation_reason: str | None = None
    sent_date: date | None = None
    sent_via: SentVia | None = None
    log: list[dict[str, Any]] | None = None

    @field_validator(*_JSON_FIELDS, mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class LitigationDemandList(BaseSchema):
    items: list[LitigationDemandRead]
    total: int
