"""EmploymentExpansion request / response schemas."""

from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.employment._json import parse_json_field

EmploymentStructure = Literal["direct", "labor_dispatch", "outsourcing"]
ExpansionStatus = Literal["active", "completed", "cancelled"]


class ExpansionCreate(BaseSchema):
    slug: str = Field(max_length=100)
    province: str = Field(max_length=100)
    headcount: str | None = Field(default=None, max_length=100)
    position_types: list[str] | None = None
    expected_timeline: str | None = Field(default=None, max_length=255)


class ExpansionUpdate(BaseSchema):
    headcount: str | None = Field(default=None, max_length=100)
    position_types: list[str] | None = None
    expected_timeline: str | None = Field(default=None, max_length=255)
    employment_structure: EmploymentStructure | None = None
    analysis_result: dict[str, Any] | None = None
    tracking_items: list[dict[str, Any]] | None = None
    status: ExpansionStatus | None = None


class ExpansionRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    slug: str
    province: str
    headcount: str | None = None
    position_types: list[str] | None = None
    expected_timeline: str | None = None
    employment_structure: EmploymentStructure | None = None
    analysis_result: dict[str, Any] | None = None
    tracking_items: list[dict[str, Any]] | None = None
    status: ExpansionStatus = "active"

    @field_validator("position_types", "analysis_result", "tracking_items", mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class ExpansionList(BaseSchema):
    items: list[ExpansionRead]
    total: int
