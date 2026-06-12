"""LitigationMatter request / response schemas."""

from datetime import date
from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.litigation._json import parse_json_field

MatterStatus = Literal[
    "active",
    "settled",
    "dismissed",
    "judgment_won",
    "judgment_lost",
    "withdrawn",
    "closed",
    "archived",
]
MatterStage = Literal["庭前", "证据交换", "庭审", "上诉", "执行"]
OurSide = Literal["plaintiff", "defendant", "third_party"]
Risk = Literal["低", "中", "高", "严重"]

_JSON_FIELDS = ("outside_counsel", "internal_owners", "conflicts")


class LitigationMatterCreate(BaseSchema):
    case_name: str | None = Field(default=None, max_length=255)
    case_number: str | None = Field(default=None, max_length=120)
    court: str | None = Field(default=None, max_length=255)
    cause_of_action: str | None = Field(default=None, max_length=255)
    case_type: str | None = Field(default=None, max_length=120)
    jurisdiction: str | None = Field(default=None, max_length=255)
    our_side: OurSide | None = None
    counterparty: str | None = Field(default=None, max_length=255)
    stage: MatterStage | None = None
    risk: Risk | None = None
    materiality: str | None = Field(default=None, max_length=20)
    exposure_range: str | None = Field(default=None, max_length=255)
    filing_date: date | None = None
    outside_counsel: dict[str, Any] | None = None
    internal_owners: dict[str, Any] | None = None
    conflicts: dict[str, Any] | None = None
    initial_theory: str | None = None
    notes: str | None = None
    source: str = "manual"


class LitigationMatterUpdate(BaseSchema):
    case_name: str | None = Field(default=None, max_length=255)
    case_number: str | None = Field(default=None, max_length=120)
    court: str | None = Field(default=None, max_length=255)
    cause_of_action: str | None = Field(default=None, max_length=255)
    case_type: str | None = Field(default=None, max_length=120)
    jurisdiction: str | None = Field(default=None, max_length=255)
    our_side: OurSide | None = None
    counterparty: str | None = Field(default=None, max_length=255)
    status: MatterStatus | None = None
    stage: MatterStage | None = None
    risk: Risk | None = None
    materiality: str | None = Field(default=None, max_length=20)
    exposure_range: str | None = Field(default=None, max_length=255)
    filing_date: date | None = None
    next_deadline: date | None = None
    outside_counsel: dict[str, Any] | None = None
    internal_owners: dict[str, Any] | None = None
    conflicts: dict[str, Any] | None = None
    initial_theory: str | None = None
    notes: str | None = None
    # 结案字段
    closed_date: date | None = None
    outcome: str | None = Field(default=None, max_length=255)
    final_cost: str | None = Field(default=None, max_length=120)
    lessons: str | None = None


class LitigationMatterRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    case_name: str | None = None
    case_number: str | None = None
    court: str | None = None
    cause_of_action: str | None = None
    case_type: str | None = None
    jurisdiction: str | None = None
    our_side: OurSide | None = None
    counterparty: str | None = None
    status: MatterStatus = "active"
    stage: MatterStage | None = None
    risk: Risk | None = None
    materiality: str | None = None
    exposure_range: str | None = None
    filing_date: date | None = None
    next_deadline: date | None = None
    outside_counsel: dict[str, Any] | None = None
    internal_owners: dict[str, Any] | None = None
    conflicts: dict[str, Any] | None = None
    initial_theory: str | None = None
    notes: str | None = None
    source: str = "manual"
    closed_date: date | None = None
    outcome: str | None = None
    final_cost: str | None = None
    lessons: str | None = None

    @field_validator(*_JSON_FIELDS, mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class LitigationMatterList(BaseSchema):
    items: list[LitigationMatterRead]
    total: int
