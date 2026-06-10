"""IpProfile request / response schemas."""

from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.ip._json import parse_json_field

ModuleStatus = Literal["not_started", "in_progress", "completed"]
SetupDepth = Literal["quick", "full"]
# 4 work-product-header variants hinge on this (《专利代理条例》第17条).
UserRole = Literal[
    "attorney",
    "patent_agent",
    "non_attorney_with_lawyer",
    "non_attorney_without",
]

_JSON_FIELDS = (
    "integrations",
    "ip_scope",
    "registration_jurisdictions",
    "domain_ownership",
    "outside_counsel",
    "enforcement_posture",
    "brand_protection",
    "portfolio_meta",
    "seed_docs",
    "output_config",
)


class IpProfileCreate(BaseSchema):
    company_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    user_role: UserRole = "attorney"
    lawyer_contact: str | None = Field(default=None, max_length=255)
    supervising_lawyer: str | None = Field(default=None, max_length=255)
    integrations: dict[str, Any] | None = None
    ip_scope: list[str] | None = None
    registration_jurisdictions: list[str] | None = None
    ip_management_system: str | None = Field(default=None, max_length=120)
    domain_ownership: dict[str, Any] | None = None
    outside_counsel: list[dict[str, Any]] | None = None
    enforcement_posture: dict[str, Any] | None = None
    brand_protection: dict[str, Any] | None = None
    portfolio_meta: dict[str, Any] | None = None
    seed_docs: dict[str, Any] | None = None
    output_config: dict[str, Any] | None = None
    setup_depth: SetupDepth = "full"
    profile_content: str | None = None
    alert_channel: str | None = Field(default=None, max_length=50)
    output_destination: str | None = Field(default=None, max_length=50)


class IpProfileUpdate(BaseSchema):
    company_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    user_role: UserRole | None = None
    lawyer_contact: str | None = Field(default=None, max_length=255)
    supervising_lawyer: str | None = Field(default=None, max_length=255)
    integrations: dict[str, Any] | None = None
    ip_scope: list[str] | None = None
    registration_jurisdictions: list[str] | None = None
    ip_management_system: str | None = Field(default=None, max_length=120)
    domain_ownership: dict[str, Any] | None = None
    outside_counsel: list[dict[str, Any]] | None = None
    enforcement_posture: dict[str, Any] | None = None
    brand_protection: dict[str, Any] | None = None
    portfolio_meta: dict[str, Any] | None = None
    seed_docs: dict[str, Any] | None = None
    output_config: dict[str, Any] | None = None
    setup_depth: SetupDepth | None = None
    setup_status: ModuleStatus | None = None
    profile_content: str | None = None
    alert_channel: str | None = Field(default=None, max_length=50)
    output_destination: str | None = Field(default=None, max_length=50)


class IpProfileRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    company_name: str | None = None
    industry: str | None = None
    user_role: UserRole = "attorney"
    lawyer_contact: str | None = None
    supervising_lawyer: str | None = None
    integrations: dict[str, Any] | None = None
    ip_scope: list[str] | None = None
    registration_jurisdictions: list[str] | None = None
    ip_management_system: str | None = None
    domain_ownership: dict[str, Any] | None = None
    outside_counsel: list[dict[str, Any]] | None = None
    enforcement_posture: dict[str, Any] | None = None
    brand_protection: dict[str, Any] | None = None
    portfolio_meta: dict[str, Any] | None = None
    seed_docs: dict[str, Any] | None = None
    output_config: dict[str, Any] | None = None
    setup_depth: SetupDepth = "full"
    setup_status: ModuleStatus = "not_started"
    profile_content: str | None = None
    alert_channel: str | None = None
    output_destination: str | None = None

    @field_validator(*_JSON_FIELDS, mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)


class IpModuleStatusResponse(BaseSchema):
    """`/ip/status` — whether the module is configured."""

    module_name: str = "ip-legal"
    setup_status: ModuleStatus = "not_started"
    configured: bool = False
