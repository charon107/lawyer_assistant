"""MaterialContractItem request / response schemas — disclosure schedule."""

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class MaterialContractItemCreate(BaseSchema):
    deal_id: str
    contract: str = Field(min_length=1, max_length=500)
    counterparty: str | None = Field(default=None, max_length=255)
    threshold_basis: str | None = Field(default=None, max_length=255)
    disclosed: bool = False
    cite: str | None = None
    notes: str | None = None
    source_issue_id: str | None = None


class MaterialContractItemUpdate(BaseSchema):
    contract: str | None = Field(default=None, max_length=500)
    counterparty: str | None = Field(default=None, max_length=255)
    threshold_basis: str | None = Field(default=None, max_length=255)
    disclosed: bool | None = None
    cite: str | None = None
    notes: str | None = None


class MaterialContractItemRead(BaseSchema, TimestampSchema):
    id: str
    deal_id: str
    source_issue_id: str | None = None
    contract: str
    counterparty: str | None = None
    threshold_basis: str | None = None
    disclosed: bool = False
    cite: str | None = None
    notes: str | None = None


class MaterialContractItemList(BaseSchema):
    items: list[MaterialContractItemRead]
    total: int
