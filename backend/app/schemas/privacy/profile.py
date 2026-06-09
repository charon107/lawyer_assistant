"""PrivacyProfile request / response schemas."""

from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.privacy._json import parse_json_field

ModuleStatus = Literal["not_started", "in_progress", "completed"]
SetupDepth = Literal["quick", "full"]
UserRole = Literal["attorney", "non_attorney_with_lawyer", "non_attorney_without"]

_JSON_FIELDS = (
    "regulatory_footprint",
    "integrations",
    "dpa_playbook",
    "policy_commitments",
    "pia_house_style",
    "dsar_process",
    "escalation_matrix",
    "seed_docs",
    "output_config",
)


class PrivacyProfileCreate(BaseSchema):
    company_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    regulatory_footprint: list[str] | None = None
    data_residency: str | None = Field(default=None, max_length=255)
    dpo_info: str | None = Field(default=None, max_length=255)
    open_reg_matters: str | None = None
    user_role: UserRole = "attorney"
    lawyer_contact: str | None = Field(default=None, max_length=255)
    practice_setting: str | None = Field(default=None, max_length=60)
    integrations: dict[str, Any] | None = None
    dpa_playbook: dict[str, Any] | None = None
    policy_commitments: dict[str, Any] | None = None
    pia_house_style: dict[str, Any] | None = None
    dsar_process: dict[str, Any] | None = None
    escalation_matrix: list[dict[str, Any]] | None = None
    seed_docs: dict[str, Any] | None = None
    output_config: dict[str, Any] | None = None
    setup_depth: SetupDepth = "full"
    profile_content: str | None = None
    alert_channel: str | None = Field(default=None, max_length=50)
    output_destination: str | None = Field(default=None, max_length=50)


class PrivacyProfileUpdate(BaseSchema):
    company_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    regulatory_footprint: list[str] | None = None
    data_residency: str | None = Field(default=None, max_length=255)
    dpo_info: str | None = Field(default=None, max_length=255)
    open_reg_matters: str | None = None
    user_role: UserRole | None = None
    lawyer_contact: str | None = Field(default=None, max_length=255)
    practice_setting: str | None = Field(default=None, max_length=60)
    integrations: dict[str, Any] | None = None
    dpa_playbook: dict[str, Any] | None = None
    policy_commitments: dict[str, Any] | None = None
    pia_house_style: dict[str, Any] | None = None
    dsar_process: dict[str, Any] | None = None
    escalation_matrix: list[dict[str, Any]] | None = None
    seed_docs: dict[str, Any] | None = None
    output_config: dict[str, Any] | None = None
    setup_depth: SetupDepth | None = None
    setup_status: ModuleStatus | None = None
    profile_content: str | None = None
    alert_channel: str | None = Field(default=None, max_length=50)
    output_destination: str | None = Field(default=None, max_length=50)


class PrivacyProfileRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    company_name: str | None = None
    industry: str | None = None
    regulatory_footprint: list[str] | None = None
    data_residency: str | None = None
    dpo_info: str | None = None
    open_reg_matters: str | None = None
    user_role: UserRole = "attorney"
    lawyer_contact: str | None = None
    practice_setting: str | None = None
    integrations: dict[str, Any] | None = None
    dpa_playbook: dict[str, Any] | None = None
    policy_commitments: dict[str, Any] | None = None
    pia_house_style: dict[str, Any] | None = None
    dsar_process: dict[str, Any] | None = None
    escalation_matrix: list[dict[str, Any]] | None = None
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


class PrivacyModuleStatusResponse(BaseSchema):
    """`/privacy/status` — whether the module is configured."""

    module_name: str = "privacy-legal"
    setup_status: ModuleStatus = "not_started"
    configured: bool = False
