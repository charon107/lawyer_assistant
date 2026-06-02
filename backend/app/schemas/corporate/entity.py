"""Entity register + compliance-calendar schemas (主体管理)."""

from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

EntityStatus = Literal["active", "dormant"]
ComplianceStatus = Literal["open", "done", "overdue"]


class CorporateEntityCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    entity_type: str | None = Field(default=None, max_length=50)
    jurisdiction: str | None = Field(default=None, max_length=255)
    controller: str | None = Field(default=None, max_length=255)
    equity_ratio: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class CorporateEntityUpdate(BaseSchema):
    name: str | None = Field(default=None, max_length=255)
    entity_type: str | None = Field(default=None, max_length=50)
    jurisdiction: str | None = Field(default=None, max_length=255)
    controller: str | None = Field(default=None, max_length=255)
    equity_ratio: str | None = Field(default=None, max_length=50)
    status: EntityStatus | None = None
    notes: str | None = None


class CorporateEntityRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    name: str
    entity_type: str | None = None
    jurisdiction: str | None = None
    controller: str | None = None
    equity_ratio: str | None = None
    status: EntityStatus = "active"
    notes: str | None = None


class CorporateEntityList(BaseSchema):
    items: list[CorporateEntityRead]
    total: int


class EntityComplianceItemCreate(BaseSchema):
    entity_id: str
    filing_type: str = Field(min_length=1, max_length=100)
    due_date: str | None = Field(default=None, max_length=50)
    recurrence: str | None = Field(default=None, max_length=50)
    notes: str | None = None


class EntityComplianceItemUpdate(BaseSchema):
    filing_type: str | None = Field(default=None, max_length=100)
    due_date: str | None = Field(default=None, max_length=50)
    recurrence: str | None = Field(default=None, max_length=50)
    status: ComplianceStatus | None = None
    notes: str | None = None


class EntityComplianceItemRead(BaseSchema, TimestampSchema):
    id: str
    entity_id: str
    filing_type: str
    due_date: str | None = None
    recurrence: str | None = None
    status: str = "open"
    notes: str | None = None


class EntityComplianceItemList(BaseSchema):
    items: list[EntityComplianceItemRead]
    total: int
