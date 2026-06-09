"""PrivacyReview request / response schemas."""

from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.privacy._json import parse_json_field

ReviewType = Literal["triage", "pia", "dpa", "gap", "policy_sweep"]
Direction = Literal["entrusted", "handler"]
Classification = Literal["PROCEED", "PIA_REQUIRED", "DPIA_MANDATORY", "STOP"]
Severity = Literal["blocking", "high", "medium", "low"]
Recommendation = Literal["APPROVED", "WITH_CONDITIONS", "CHANGES_REQUIRED", "NOT_APPROVED"]


class PrivacyReviewCreate(BaseSchema):
    review_type: ReviewType
    subject: str | None = Field(default=None, max_length=255)
    counterparty: str | None = Field(default=None, max_length=255)
    direction: Direction | None = None


class PrivacyReviewRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    review_type: ReviewType
    subject: str | None = None
    counterparty: str | None = None
    direction: Direction | None = None
    classification: Classification | None = None
    severity: Severity | None = None
    recommendation: Recommendation | None = None
    result_summary: str | None = None
    result_memo: str | None = None
    result_json: dict[str, Any] | None = None
    status: str = "draft"

    @field_validator("result_json", mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class PrivacyReviewList(BaseSchema):
    items: list[PrivacyReviewRead]
    total: int
