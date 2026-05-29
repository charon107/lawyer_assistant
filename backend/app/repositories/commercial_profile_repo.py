"""Repository for `commercial_profiles` — per-user commercial-legal practice profile.

Stateless functions; sync SQLAlchemy `Session` (project convention for SQLite).
Repository never calls `db.commit()`; the session lifecycle decides when to commit.

JSON-text columns (`playbook_sales`, `playbook_purchasing`,
`escalation_matrix`) are stored as JSON strings. Callers pass typed
Pydantic objects; the repo serializes them on the way in. Read paths
return raw ORM rows; the schema layer's `field_validator` decodes the
JSON columns when projecting to `CommercialProfileRead`.
"""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.commercial_profile import CommercialProfile


def _to_json(value: Any) -> str | None:
    """Serialize a Pydantic model / list / dict to JSON text. None stays None."""
    if value is None:
        return None
    if hasattr(value, "model_dump"):  # pydantic BaseModel
        return json.dumps(value.model_dump(), ensure_ascii=False)
    if isinstance(value, list):
        return json.dumps(
            [v.model_dump() if hasattr(v, "model_dump") else v for v in value],
            ensure_ascii=False,
        )
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, str):
        return value  # assume already JSON text
    raise TypeError(f"Cannot serialize {type(value).__name__} as JSON text")


def get_by_user_id(db: Session, user_id: str) -> CommercialProfile | None:
    """Return the profile for a user, or None if not yet created."""
    result = db.execute(select(CommercialProfile).where(CommercialProfile.user_id == user_id))
    return result.scalar_one_or_none()


def create(
    db: Session,
    *,
    user_id: str,
    company_name: str | None = None,
    entity_type: str | None = None,
    team_size: str | None = None,
    gc_name: str | None = None,
    monthly_volume: str | None = None,
    side: str = "purchasing",
    profile_content: str | None = None,
    playbook_sales: Any = None,
    playbook_purchasing: Any = None,
    escalation_matrix: Any = None,
    renewal_alert_channel: str | None = None,
    output_destination: str | None = None,
    setup_status: str = "in_progress",
) -> CommercialProfile:
    """Create a new commercial-legal practice profile for a user.

    Raises `IntegrityError` if a row already exists for `user_id`
    (the UNIQUE constraint enforces single-profile-per-user).
    """
    profile = CommercialProfile(
        user_id=user_id,
        company_name=company_name,
        entity_type=entity_type,
        team_size=team_size,
        gc_name=gc_name,
        monthly_volume=monthly_volume,
        side=side,
        setup_status=setup_status,
        profile_content=profile_content,
        playbook_sales=_to_json(playbook_sales),
        playbook_purchasing=_to_json(playbook_purchasing),
        escalation_matrix=_to_json(escalation_matrix),
        renewal_alert_channel=renewal_alert_channel,
        output_destination=output_destination,
    )
    db.add(profile)
    db.flush()
    db.refresh(profile)
    return profile


def update(
    db: Session,
    *,
    profile: CommercialProfile,
    company_name: str | None = None,
    entity_type: str | None = None,
    team_size: str | None = None,
    gc_name: str | None = None,
    monthly_volume: str | None = None,
    side: str | None = None,
    setup_status: str | None = None,
    profile_content: str | None = None,
    playbook_sales: Any = None,
    playbook_purchasing: Any = None,
    escalation_matrix: Any = None,
    renewal_alert_channel: str | None = None,
    output_destination: str | None = None,
) -> CommercialProfile:
    """Partial update — only non-None fields are written.

    To explicitly clear a JSON field, pass an empty list / dict rather
    than None.
    """
    if company_name is not None:
        profile.company_name = company_name
    if entity_type is not None:
        profile.entity_type = entity_type
    if team_size is not None:
        profile.team_size = team_size
    if gc_name is not None:
        profile.gc_name = gc_name
    if monthly_volume is not None:
        profile.monthly_volume = monthly_volume
    if side is not None:
        profile.side = side
    if setup_status is not None:
        profile.setup_status = setup_status
    if profile_content is not None:
        profile.profile_content = profile_content
    if playbook_sales is not None:
        profile.playbook_sales = _to_json(playbook_sales)
    if playbook_purchasing is not None:
        profile.playbook_purchasing = _to_json(playbook_purchasing)
    if escalation_matrix is not None:
        profile.escalation_matrix = _to_json(escalation_matrix)
    if renewal_alert_channel is not None:
        profile.renewal_alert_channel = renewal_alert_channel
    if output_destination is not None:
        profile.output_destination = output_destination

    db.flush()
    db.refresh(profile)
    return profile


def delete_by_user_id(db: Session, user_id: str) -> CommercialProfile | None:
    """Delete and return the profile (None if absent)."""
    profile = get_by_user_id(db, user_id)
    if profile is None:
        return None
    db.delete(profile)
    db.flush()
    return profile
