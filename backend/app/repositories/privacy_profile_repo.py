"""Repository for `privacy_profiles`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.privacy_profile import PrivacyProfile


def get_by_user_id(db: Session, user_id: str) -> PrivacyProfile | None:
    result = db.execute(select(PrivacyProfile).where(PrivacyProfile.user_id == user_id))
    return result.scalar_one_or_none()


def create(db: Session, *, user_id: str, **fields: Any) -> PrivacyProfile:
    profile = PrivacyProfile(user_id=user_id, **fields)
    db.add(profile)
    db.flush()
    db.refresh(profile)
    return profile


def update(db: Session, *, profile: PrivacyProfile, **fields: Any) -> PrivacyProfile:
    for key, value in fields.items():
        if value is not None:
            setattr(profile, key, value)
    db.flush()
    db.refresh(profile)
    return profile
