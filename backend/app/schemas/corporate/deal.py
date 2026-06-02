"""CorporateDeal request / response schemas — the deal / matter workspace."""

from typing import Literal

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema

DealStatus = Literal["active", "closed", "archived"]
DealSide = Literal["buyer", "seller", "na"]
Confidentiality = Literal["standard", "elevated", "clean_team"]


class CorporateDealCreate(BaseSchema):
    code: str = Field(min_length=1, max_length=100, description="Lowercase-hyphen slug (简称).")
    client: str | None = Field(default=None, max_length=255)
    counterparty: str | None = Field(default=None, max_length=255)
    deal_type: str | None = Field(default=None, max_length=50)
    side: DealSide | None = None
    confidentiality_level: Confidentiality = "standard"
    key_facts: str | None = None
    overrides: str | None = None
    notes: str | None = None
    dataroom_location: str | None = Field(default=None, max_length=500)
    materiality_contract: str | None = Field(default=None, max_length=255)
    materiality_litigation: str | None = Field(default=None, max_length=255)


class CorporateDealUpdate(BaseSchema):
    client: str | None = Field(default=None, max_length=255)
    counterparty: str | None = Field(default=None, max_length=255)
    deal_type: str | None = Field(default=None, max_length=50)
    side: DealSide | None = None
    confidentiality_level: Confidentiality | None = None
    status: DealStatus | None = None
    key_facts: str | None = None
    overrides: str | None = None
    notes: str | None = None
    dataroom_location: str | None = Field(default=None, max_length=500)
    materiality_contract: str | None = Field(default=None, max_length=255)
    materiality_litigation: str | None = Field(default=None, max_length=255)


class CorporateDealRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    code: str
    client: str | None = None
    counterparty: str | None = None
    deal_type: str | None = None
    side: DealSide | None = None
    confidentiality_level: Confidentiality = "standard"
    status: DealStatus = "active"
    key_facts: str | None = None
    overrides: str | None = None
    notes: str | None = None
    dataroom_location: str | None = None
    materiality_contract: str | None = None
    materiality_litigation: str | None = None


class CorporateDealList(BaseSchema):
    items: list[CorporateDealRead]
    total: int
