"""RegulatoryAnalysis response schemas (written by WS Agent; REST reads history)."""

from typing import Any, Literal

from pydantic import field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.regulatory._json import parse_json_field

AnalysisType = Literal["policy_diff", "policy_redraft"]
Severity = Literal["blocking", "high", "medium", "low"]
AnalysisStatus = Literal["draft", "final"]


class RegulatoryAnalysisRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    reg_item_id: str | None = None
    analysis_type: AnalysisType
    subject: str | None = None
    regulation_name: str | None = None
    policy_affected: str | None = None
    severity: Severity | None = None
    scope_limited: bool = False
    scope_note: str | None = None
    status_verified: bool = False
    result_summary: str | None = None
    result_memo: str | None = None
    result_json: dict[str, Any] | list[Any] | None = None
    status: AnalysisStatus = "draft"

    @field_validator("result_json", mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class RegulatoryAnalysisList(BaseSchema):
    items: list[RegulatoryAnalysisRead]
    total: int
