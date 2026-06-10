"""IpPortfolio request / response schemas."""

from datetime import date
from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.ip._json import parse_json_field

AssetType = Literal[
    "trademark",
    "patent_invention",
    "patent_utility",
    "patent_design",
    "copyright",
    "domain",
    "other",
]
AssetStatus = Literal["pending", "registered", "granted", "lapsed", "abandoned"]

_JSON_FIELDS = ("next_deadlines",)


class IpPortfolioCreate(BaseSchema):
    asset_type: AssetType
    jurisdiction: str | None = Field(default=None, max_length=60)
    title: str | None = Field(default=None, max_length=255)
    owner_entity: str | None = Field(default=None, max_length=255)
    status: AssetStatus = "registered"
    application_number: str | None = Field(default=None, max_length=120)
    registration_number: str | None = Field(default=None, max_length=120)
    filing_date: date | None = None
    registration_date: date | None = None
    grant_date: date | None = None
    priority_date: date | None = None
    business_owner: str | None = Field(default=None, max_length=255)
    agent_managed: bool = False
    notes: str | None = None
    source: str = "manual"


class IpPortfolioUpdate(BaseSchema):
    asset_type: AssetType | None = None
    jurisdiction: str | None = Field(default=None, max_length=60)
    title: str | None = Field(default=None, max_length=255)
    owner_entity: str | None = Field(default=None, max_length=255)
    status: AssetStatus | None = None
    application_number: str | None = Field(default=None, max_length=120)
    registration_number: str | None = Field(default=None, max_length=120)
    filing_date: date | None = None
    registration_date: date | None = None
    grant_date: date | None = None
    priority_date: date | None = None
    business_owner: str | None = Field(default=None, max_length=255)
    agent_managed: bool | None = None
    notes: str | None = None


class IpPortfolioRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    asset_type: AssetType
    jurisdiction: str | None = None
    title: str | None = None
    owner_entity: str | None = None
    status: AssetStatus = "registered"
    application_number: str | None = None
    registration_number: str | None = None
    filing_date: date | None = None
    registration_date: date | None = None
    grant_date: date | None = None
    priority_date: date | None = None
    next_deadlines: list[dict[str, Any]] | None = None
    business_owner: str | None = None
    agent_managed: bool = False
    notes: str | None = None
    source: str = "manual"

    @field_validator(*_JSON_FIELDS, mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class IpPortfolioList(BaseSchema):
    items: list[IpPortfolioRead]
    total: int
