"""EmploymentReview request / response schemas."""

from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.employment._json import parse_json_field

ReviewType = Literal[
    "hiring", "termination", "worker_classification", "policy", "wage_hour", "handbook"
]
ResultStatus = Literal["proceed", "needs_fix", "stop", "in_progress"]


class EmploymentReviewCreate(BaseSchema):
    review_type: ReviewType
    employee_name: str | None = Field(default=None, max_length=255)
    position: str | None = Field(default=None, max_length=255)
    jurisdiction: str | None = Field(default=None, max_length=100)
    input_description: str | None = None
    file_path: str | None = Field(default=None, max_length=500)
    file_name: str | None = Field(default=None, max_length=255)


class EmploymentReviewRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    review_type: ReviewType
    employee_name: str | None = None
    position: str | None = None
    jurisdiction: str | None = None
    input_description: str | None = None
    file_path: str | None = None
    file_name: str | None = None
    result_status: ResultStatus | None = None
    result_summary: str | None = None
    result_memo: str | None = None
    result_json: dict[str, Any] | None = None
    high_risk_flags: list[str] | None = None
    required_approver: str | None = None
    escalation_sent: bool = False

    @field_validator("result_json", "high_risk_flags", mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class EmploymentReviewList(BaseSchema):
    items: list[EmploymentReviewRead]
    total: int
