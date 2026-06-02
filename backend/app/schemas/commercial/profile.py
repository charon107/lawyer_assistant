"""CommercialProfile request / response schemas.

A user has at most one CommercialProfile (UNIQUE user_id). It stores
both the compiled Markdown `profile_content` (used by the agent as
system-prompt input) and structured `playbook_*` JSON (used by the
`get_playbook` tool for direct clause-by-clause queries).
"""

from typing import Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.schemas.commercial.playbook import (
    EscalationRule,
    Playbook,
    SetupDepth,
    Side,
    UsedBy,
)

ModuleStatus = Literal["not_started", "in_progress", "completed"]


def _parse_json_field(v: object) -> object:
    """Deserialize a JSON-text DB column into a Python value.

    SQLite stores these as TEXT; Pydantic doesn't auto-decode. We do
    it here so the API surface stays typed (lists/dicts) regardless of
    storage backend.
    """
    if isinstance(v, str):
        import json

        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return v
    return v


# ----- Create ---------------------------------------------------------------


class CommercialProfileCreate(BaseSchema):
    """Payload for first-time profile creation (from cold-start)."""

    company_name: str | None = Field(default=None, max_length=255)
    entity_type: str | None = Field(default=None, max_length=50)
    team_size: str | None = Field(default=None, max_length=50)
    gc_name: str | None = Field(default=None, max_length=255)
    monthly_volume: str | None = Field(default=None, max_length=50)
    side: Side = "purchasing"
    setup_depth: SetupDepth = "full"
    used_by: UsedBy = "lawyer"

    profile_content: str | None = Field(
        default=None,
        description="Compiled Markdown profile (the CLAUDE.md equivalent).",
    )
    playbook_sales: Playbook | None = None
    playbook_purchasing: Playbook | None = None
    escalation_matrix: list[EscalationRule] | None = None

    renewal_alert_channel: str | None = Field(default=None, max_length=50)
    output_destination: str | None = Field(default=None, max_length=50)


# ----- Update ---------------------------------------------------------------


class CommercialProfileUpdate(BaseSchema):
    """Partial update — every field optional."""

    company_name: str | None = Field(default=None, max_length=255)
    entity_type: str | None = Field(default=None, max_length=50)
    team_size: str | None = Field(default=None, max_length=50)
    gc_name: str | None = Field(default=None, max_length=255)
    monthly_volume: str | None = Field(default=None, max_length=50)
    side: Side | None = None
    setup_depth: SetupDepth | None = None
    used_by: UsedBy | None = None
    setup_status: ModuleStatus | None = None
    profile_content: str | None = None
    playbook_sales: Playbook | None = None
    playbook_purchasing: Playbook | None = None
    escalation_matrix: list[EscalationRule] | None = None
    renewal_alert_channel: str | None = Field(default=None, max_length=50)
    output_destination: str | None = Field(default=None, max_length=50)


# ----- Read -----------------------------------------------------------------


class CommercialProfileRead(BaseSchema, TimestampSchema):
    """Profile as returned to the frontend."""

    id: str
    user_id: str
    company_name: str | None = None
    entity_type: str | None = None
    team_size: str | None = None
    gc_name: str | None = None
    monthly_volume: str | None = None
    side: Side = "purchasing"
    setup_depth: SetupDepth = "full"
    used_by: UsedBy = "lawyer"
    setup_status: ModuleStatus = "not_started"
    profile_content: str | None = None
    playbook_sales: Playbook | None = None
    playbook_purchasing: Playbook | None = None
    escalation_matrix: list[EscalationRule] | None = None
    renewal_alert_channel: str | None = None
    output_destination: str | None = None

    # Decode JSON-text columns coming from SQLAlchemy.
    @field_validator("playbook_sales", "playbook_purchasing", mode="before")
    @classmethod
    def _decode_playbook(cls, v: object) -> object:
        return _parse_json_field(v)

    @field_validator("escalation_matrix", mode="before")
    @classmethod
    def _decode_escalation_matrix(cls, v: object) -> object:
        return _parse_json_field(v)
