"""LitigationAnalysis request / response schemas."""

from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.litigation._json import parse_json_field

AnalysisType = Literal[
    "matter_briefing",
    "chronology",
    "claim_chart",
    "subpoena_triage",
    "legal_hold",
    "oc_status",
    "brief_section",
    "deposition_prep",
    "privilege_log",
]
Severity = Literal["blocking", "high", "medium", "low"]
AnalysisStatus = Literal["draft", "final"]

_JSON_FIELDS = ("result_json",)


class LitigationAnalysisCreate(BaseSchema):
    """Pre-create row before WS agent runs (handler sets analysis_type)."""

    matter_id: str | None = Field(default=None, max_length=36)
    subject: str | None = Field(default=None, max_length=255)
    counterparty: str | None = Field(default=None, max_length=255)


class LitigationAnalysisRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    matter_id: str | None = None
    analysis_type: AnalysisType
    subject: str | None = None
    counterparty: str | None = None
    classification: str | None = None
    severity: Severity | None = None
    result_summary: str | None = None
    result_memo: str | None = None
    result_json: dict[str, Any] | None = None
    status: AnalysisStatus = "draft"

    @field_validator(*_JSON_FIELDS, mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class LitigationAnalysisList(BaseSchema):
    items: list[LitigationAnalysisRead]
    total: int
