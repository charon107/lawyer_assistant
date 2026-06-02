"""CorporateProfile request / response schemas.

A user has at most one CorporateProfile (UNIQUE user_id). It stores the
compiled Markdown ``profile_content`` (agent system-prompt input) plus the
modular configuration: ``active_modules`` and the four optional per-module
config blobs (``mna`` / ``board`` / ``public`` / ``entities``), each a free
-form dict serialized to JSON text in the DB.
"""

import json
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema

ModuleStatus = Literal["not_started", "in_progress", "completed"]
SetupDepth = Literal["quick", "full"]
UsedBy = Literal["lawyer", "non_lawyer"]
CorporateModule = Literal["mna", "board", "public", "entities"]


def _parse_json_field(v: object) -> object:
    """Deserialize a JSON-text DB column into a Python value.

    SQLite stores these as TEXT; Pydantic doesn't auto-decode. We do it
    here so the API surface stays typed (lists/dicts) regardless of the
    storage backend.
    """
    if isinstance(v, str):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return v
    return v


# ----- Create ---------------------------------------------------------------


class CorporateProfileCreate(BaseSchema):
    """Payload for first-time profile creation (from cold-start)."""

    company_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    stage: str | None = Field(default=None, max_length=50)
    main_jurisdiction: str | None = Field(default=None, max_length=255)
    team_size: str | None = Field(default=None, max_length=50)
    escalation_path: str | None = Field(default=None, max_length=255)
    used_by: UsedBy = "lawyer"
    setup_depth: SetupDepth = "full"

    active_modules: list[CorporateModule] | None = None
    mna_config: dict | None = None
    board_config: dict | None = None
    public_config: dict | None = None
    entity_config: dict | None = None

    profile_content: str | None = Field(
        default=None,
        description="Compiled Markdown profile (the CLAUDE.md equivalent).",
    )
    alert_channel: str | None = Field(default=None, max_length=50)
    output_destination: str | None = Field(default=None, max_length=50)


# ----- Update ---------------------------------------------------------------


class CorporateProfileUpdate(BaseSchema):
    """Partial update — every field optional."""

    company_name: str | None = Field(default=None, max_length=255)
    industry: str | None = Field(default=None, max_length=255)
    stage: str | None = Field(default=None, max_length=50)
    main_jurisdiction: str | None = Field(default=None, max_length=255)
    team_size: str | None = Field(default=None, max_length=50)
    escalation_path: str | None = Field(default=None, max_length=255)
    used_by: UsedBy | None = None
    setup_depth: SetupDepth | None = None
    setup_status: ModuleStatus | None = None
    active_modules: list[CorporateModule] | None = None
    mna_config: dict | None = None
    board_config: dict | None = None
    public_config: dict | None = None
    entity_config: dict | None = None
    profile_content: str | None = None
    alert_channel: str | None = Field(default=None, max_length=50)
    output_destination: str | None = Field(default=None, max_length=50)


# ----- Read -----------------------------------------------------------------


class CorporateProfileRead(BaseSchema, TimestampSchema):
    """Profile as returned to the frontend."""

    id: str
    user_id: str
    company_name: str | None = None
    industry: str | None = None
    stage: str | None = None
    main_jurisdiction: str | None = None
    team_size: str | None = None
    escalation_path: str | None = None
    used_by: UsedBy = "lawyer"
    setup_depth: SetupDepth = "full"
    setup_status: ModuleStatus = "not_started"
    active_modules: list[CorporateModule] | None = None
    mna_config: dict | None = None
    board_config: dict | None = None
    public_config: dict | None = None
    entity_config: dict | None = None
    profile_content: str | None = None
    alert_channel: str | None = None
    output_destination: str | None = None

    # Decode JSON-text columns coming from SQLAlchemy.
    @field_validator(
        "active_modules",
        "mna_config",
        "board_config",
        "public_config",
        "entity_config",
        mode="before",
    )
    @classmethod
    def _decode_json(cls, v: object) -> object:
        return _parse_json_field(v)
