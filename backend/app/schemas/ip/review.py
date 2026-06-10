"""IpReview request / response schemas."""

from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.ip._json import parse_json_field

ReviewType = Literal["clearance", "fto", "invention", "infringement", "ip_clause", "oss"]
IpCategory = Literal["trademark", "copyright", "patent", "trade_secret", "design"]
# clearance/oss: GREEN/YELLOW/RED · invention: PURSUE/INVESTIGATE/REJECT
# infringement: IGNORE/COMMUNICATE/CEASE_DESIST/LITIGATE
Classification = Literal[
    "GREEN",
    "YELLOW",
    "RED",
    "PURSUE",
    "INVESTIGATE",
    "REJECT",
    "IGNORE",
    "COMMUNICATE",
    "CEASE_DESIST",
    "LITIGATE",
]
Severity = Literal["blocking", "high", "medium", "low"]


class IpReviewCreate(BaseSchema):
    review_type: ReviewType
    subject: str | None = Field(default=None, max_length=255)
    counterparty: str | None = Field(default=None, max_length=255)
    ip_category: IpCategory | None = None


class IpReviewRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    review_type: ReviewType
    subject: str | None = None
    counterparty: str | None = None
    ip_category: IpCategory | None = None
    classification: Classification | None = None
    severity: Severity | None = None
    result_summary: str | None = None
    result_memo: str | None = None
    result_json: dict[str, Any] | None = None
    status: str = "draft"

    @field_validator("result_json", mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class IpReviewList(BaseSchema):
    items: list[IpReviewRead]
    total: int
