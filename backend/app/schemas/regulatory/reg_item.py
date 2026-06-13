"""RegulatoryRegItem request / response schemas."""

from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

ItemType = Literal[
    "regulation",
    "normative",
    "nprm",
    "pre_rule",
    "enforcement",
    "guidance",
    "speech",
    "settlement",
    "other",
]
Materiality = Literal["always", "review", "fyi"]
MaterialitySource = Literal["auto_rule", "llm", "user"]
RegItemStatus = Literal["new", "triaged", "diffed", "archived"]


class RegulatoryRegItemCreate(BaseSchema):
    """手动录入（粘贴法规文本建 reg_item，source=用户提供）。"""

    regulator: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=500)
    item_type: ItemType = "other"
    summary: str | None = None
    link: str | None = Field(default=None, max_length=1000)
    published_date: date | None = None
    effective_date: date | None = None
    comment_deadline: date | None = None


class RegulatoryRegItemUpdate(BaseSchema):
    regulator: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=500)
    item_type: ItemType | None = None
    materiality: Materiality | None = None
    summary: str | None = None
    relevance_hook: str | None = None
    link: str | None = Field(default=None, max_length=1000)
    published_date: date | None = None
    effective_date: date | None = None
    comment_deadline: date | None = None
    status_verified: bool | None = None
    status: RegItemStatus | None = None


class RegulatoryRegItemRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    regulator: str | None = None
    title: str | None = None
    item_type: ItemType = "other"
    materiality: Materiality = "review"
    materiality_source: MaterialitySource = "auto_rule"
    summary: str | None = None
    relevance_hook: str | None = None
    link: str | None = None
    published_date: date | None = None
    effective_date: date | None = None
    comment_deadline: date | None = None
    source_tag: str | None = None
    source_name: str | None = None
    status_verified: bool = False
    dedup_key: str | None = None
    status: RegItemStatus = "new"


class RegulatoryRegItemList(BaseSchema):
    items: list[RegulatoryRegItemRead]
    total: int
