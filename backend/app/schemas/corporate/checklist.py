"""ClosingChecklistItem request / response schemas."""

from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

ItemType = Literal[
    "condition",
    "consent",
    "document",
    "filing",
    "shareholder_vote",
    "regulatory",
    "release",
]
ChecklistStatus = Literal["open", "in_progress", "done", "waived"]


class ClosingChecklistItemCreate(BaseSchema):
    deal_id: str
    item: str = Field(min_length=1)
    item_type: ItemType = "condition"
    source_issue_id: str | None = None
    basis: str | None = None
    approval_threshold: str | None = Field(default=None, max_length=255)
    responsible: str | None = Field(default=None, max_length=255)
    blocking: bool = True
    due: str | None = Field(default=None, max_length=50)


class ClosingChecklistItemUpdate(BaseSchema):
    item: str | None = None
    item_type: ItemType | None = None
    basis: str | None = None
    approval_threshold: str | None = Field(default=None, max_length=255)
    responsible: str | None = Field(default=None, max_length=255)
    blocking: bool | None = None
    status: ChecklistStatus | None = None
    due: str | None = Field(default=None, max_length=50)


class ClosingChecklistItemRead(BaseSchema, TimestampSchema):
    id: str
    deal_id: str
    source_issue_id: str | None = None
    item_type: ItemType = "condition"
    item: str
    basis: str | None = None
    approval_threshold: str | None = None
    responsible: str | None = None
    blocking: bool = True
    status: ChecklistStatus = "open"
    due: str | None = None


class ClosingChecklistItemList(BaseSchema):
    items: list[ClosingChecklistItemRead]
    total: int
