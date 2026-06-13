"""Repository for `regulatory_profiles`. Stateless sync; never commits."""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.regulatory_profile import RegulatoryProfile


def get_by_id(db: Session, profile_id: str) -> RegulatoryProfile | None:
    return db.get(RegulatoryProfile, profile_id)


def get_by_user_id(db: Session, user_id: str) -> RegulatoryProfile | None:
    result = db.execute(select(RegulatoryProfile).where(RegulatoryProfile.user_id == user_id))
    return result.scalar_one_or_none()


def create(db: Session, *, user_id: str, **fields: Any) -> RegulatoryProfile:
    profile = RegulatoryProfile(user_id=user_id, **fields)
    db.add(profile)
    db.flush()
    db.refresh(profile)
    return profile


def update(db: Session, *, profile: RegulatoryProfile, **fields: Any) -> RegulatoryProfile:
    for key, value in fields.items():
        if value is not None:
            setattr(profile, key, value)
    db.flush()
    db.refresh(profile)
    return profile


def set_last_feed_check(
    db: Session, *, profile: RegulatoryProfile, ts: datetime
) -> RegulatoryProfile:
    """Advance the feed-check watermark (A1: only call for OK sources / successful run)."""
    profile.last_feed_check_at = ts
    db.flush()
    db.refresh(profile)
    return profile
