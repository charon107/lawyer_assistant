"""EmploymentProfile request / response schemas."""

from typing import Any, Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.employment._json import parse_json_field

ModuleStatus = Literal["not_started", "in_progress", "completed"]
SetupDepth = Literal["quick", "full"]
OfficeModel = Literal["remote_first", "in_office", "hybrid"]
UserRole = Literal["attorney", "non_attorney_with_lawyer", "non_attorney_without"]

_JSON_FIELDS = (
    "jurisdictions",
    "hiring_trigger",
    "termination_trigger",
    "high_risk_flags",
    "provincial_supplements",
    "jurisdiction_table",
    "leave_management_config",
    "escalation_matrix",
)


class EmploymentProfileCreate(BaseSchema):
    company_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    jurisdictions: list[str] | None = None
    default_jurisdiction: str | None = Field(default=None, max_length=100)
    office_model: OfficeModel = "in_office"
    user_role: UserRole = "attorney"
    lawyer_contact: str | None = Field(default=None, max_length=255)
    hiring_trigger: str | dict[str, Any] | None = None
    termination_trigger: str | dict[str, Any] | None = None
    standard_severance: str | None = Field(default=None, max_length=40)
    high_risk_flags: list[str] | None = None
    policy_location: str | None = Field(default=None, max_length=255)
    provincial_supplements: dict[str, Any] | None = None
    jurisdiction_table: dict[str, Any] | None = None
    leave_management_config: dict[str, Any] | None = None
    escalation_matrix: list[dict[str, Any]] | None = None
    setup_depth: SetupDepth = "full"
    profile_content: str | None = None
    alert_channel: str | None = Field(default=None, max_length=50)
    output_destination: str | None = Field(default=None, max_length=50)


class EmploymentProfileUpdate(BaseSchema):
    company_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    jurisdictions: list[str] | None = None
    default_jurisdiction: str | None = Field(default=None, max_length=100)
    office_model: OfficeModel | None = None
    user_role: UserRole | None = None
    lawyer_contact: str | None = Field(default=None, max_length=255)
    hiring_trigger: str | dict[str, Any] | None = None
    termination_trigger: str | dict[str, Any] | None = None
    standard_severance: str | None = Field(default=None, max_length=40)
    high_risk_flags: list[str] | None = None
    policy_location: str | None = Field(default=None, max_length=255)
    provincial_supplements: dict[str, Any] | None = None
    jurisdiction_table: dict[str, Any] | None = None
    leave_management_config: dict[str, Any] | None = None
    escalation_matrix: list[dict[str, Any]] | None = None
    setup_depth: SetupDepth | None = None
    setup_status: ModuleStatus | None = None
    profile_content: str | None = None
    alert_channel: str | None = Field(default=None, max_length=50)
    output_destination: str | None = Field(default=None, max_length=50)


class EmploymentProfileRead(BaseSchema, TimestampSchema):
    id: str
    user_id: str
    company_name: str | None = None
    industry: str | None = None
    jurisdictions: list[str] | None = None
    default_jurisdiction: str | None = None
    office_model: OfficeModel = "in_office"
    user_role: UserRole = "attorney"
    lawyer_contact: str | None = None
    hiring_trigger: str | dict[str, Any] | None = None
    termination_trigger: str | dict[str, Any] | None = None
    standard_severance: str | None = None
    high_risk_flags: list[str] | None = None
    policy_location: str | None = None
    provincial_supplements: dict[str, Any] | None = None
    jurisdiction_table: dict[str, Any] | None = None
    leave_management_config: dict[str, Any] | None = None
    escalation_matrix: list[dict[str, Any]] | None = None
    setup_depth: SetupDepth = "full"
    setup_status: ModuleStatus = "not_started"
    profile_content: str | None = None
    alert_channel: str | None = None
    output_destination: str | None = None

    @field_validator(*_JSON_FIELDS, mode="before")
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return parse_json_field(v)

    @field_validator("user_role", mode="before")
    @classmethod
    def _coerce_user_role(cls, v: object) -> object:
        """Accept legacy values written before the enum was tightened."""
        _ROLE_MAP = {"lawyer": "attorney", "non_lawyer": "non_attorney_without"}
        if isinstance(v, str) and v in _ROLE_MAP:
            return _ROLE_MAP[v]
        return v


class EmploymentModuleStatusResponse(BaseSchema):
    """`/employment/status` — whether the module is configured."""

    module_name: str = "employment-legal"
    setup_status: ModuleStatus = "not_started"
    configured: bool = False
