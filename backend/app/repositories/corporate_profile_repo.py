"""Repository for `corporate_profiles` — per-user corporate-legal practice profile.

Stateless functions; sync SQLAlchemy `Session` (project convention for SQLite).
Repository never calls `db.commit()`; the session lifecycle decides when to commit.

JSON-text columns (`active_modules`, `mna_config`, `board_config`,
`public_config`, `entity_config`) are stored as JSON strings. Callers pass
typed Python values (list / dict); the repo serializes them on the way in.
Read paths return raw ORM rows; the schema layer's `field_validator` decodes
the JSON columns when projecting to `CorporateProfileRead`.
"""

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.corporate_profile import CorporateProfile


def _to_json(value: Any) -> str | None:
    """Serialize a list / dict / pydantic model to JSON text. None stays None."""
    if value is None:
        return None
    if hasattr(value, "model_dump"):  # pydantic BaseModel
        return json.dumps(value.model_dump(), ensure_ascii=False)
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, str):
        return value  # assume already JSON text
    raise TypeError(f"Cannot serialize {type(value).__name__} as JSON text")


def get_by_user_id(db: Session, user_id: str) -> CorporateProfile | None:
    """Return the profile for a user, or None if not yet created."""
    result = db.execute(select(CorporateProfile).where(CorporateProfile.user_id == user_id))
    return result.scalar_one_or_none()


def create(
    db: Session,
    *,
    user_id: str,
    company_name: str | None = None,
    industry: str | None = None,
    stage: str | None = None,
    main_jurisdiction: str | None = None,
    team_size: str | None = None,
    escalation_path: str | None = None,
    used_by: str = "lawyer",
    setup_depth: str = "full",
    setup_status: str = "in_progress",
    active_modules: Any = None,
    mna_config: Any = None,
    board_config: Any = None,
    public_config: Any = None,
    entity_config: Any = None,
    profile_content: str | None = None,
    alert_channel: str | None = None,
    output_destination: str | None = None,
) -> CorporateProfile:
    """Create a new corporate-legal practice profile for a user.

    Raises `IntegrityError` if a row already exists for `user_id`
    (the UNIQUE constraint enforces single-profile-per-user).
    """
    profile = CorporateProfile(
        user_id=user_id,
        company_name=company_name,
        industry=industry,
        stage=stage,
        main_jurisdiction=main_jurisdiction,
        team_size=team_size,
        escalation_path=escalation_path,
        used_by=used_by,
        setup_depth=setup_depth,
        setup_status=setup_status,
        active_modules=_to_json(active_modules),
        mna_config=_to_json(mna_config),
        board_config=_to_json(board_config),
        public_config=_to_json(public_config),
        entity_config=_to_json(entity_config),
        profile_content=profile_content,
        alert_channel=alert_channel,
        output_destination=output_destination,
    )
    db.add(profile)
    db.flush()
    db.refresh(profile)
    return profile


def update(
    db: Session,
    *,
    profile: CorporateProfile,
    company_name: str | None = None,
    industry: str | None = None,
    stage: str | None = None,
    main_jurisdiction: str | None = None,
    team_size: str | None = None,
    escalation_path: str | None = None,
    used_by: str | None = None,
    setup_depth: str | None = None,
    setup_status: str | None = None,
    active_modules: Any = None,
    mna_config: Any = None,
    board_config: Any = None,
    public_config: Any = None,
    entity_config: Any = None,
    profile_content: str | None = None,
    alert_channel: str | None = None,
    output_destination: str | None = None,
) -> CorporateProfile:
    """Partial update — only non-None fields are written.

    To explicitly clear a JSON field, pass an empty list / dict rather
    than None.
    """
    if company_name is not None:
        profile.company_name = company_name
    if industry is not None:
        profile.industry = industry
    if stage is not None:
        profile.stage = stage
    if main_jurisdiction is not None:
        profile.main_jurisdiction = main_jurisdiction
    if team_size is not None:
        profile.team_size = team_size
    if escalation_path is not None:
        profile.escalation_path = escalation_path
    if used_by is not None:
        profile.used_by = used_by
    if setup_depth is not None:
        profile.setup_depth = setup_depth
    if setup_status is not None:
        profile.setup_status = setup_status
    if active_modules is not None:
        profile.active_modules = _to_json(active_modules)
    if mna_config is not None:
        profile.mna_config = _to_json(mna_config)
    if board_config is not None:
        profile.board_config = _to_json(board_config)
    if public_config is not None:
        profile.public_config = _to_json(public_config)
    if entity_config is not None:
        profile.entity_config = _to_json(entity_config)
    if profile_content is not None:
        profile.profile_content = profile_content
    if alert_channel is not None:
        profile.alert_channel = alert_channel
    if output_destination is not None:
        profile.output_destination = output_destination

    db.flush()
    db.refresh(profile)
    return profile


def delete_by_user_id(db: Session, user_id: str) -> CorporateProfile | None:
    """Delete and return the profile (None if absent)."""
    profile = get_by_user_id(db, user_id)
    if profile is None:
        return None
    db.delete(profile)
    db.flush()
    return profile
