"""Repository for `litigation_profiles`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy.orm import Session

from app.db.models.litigation_profile import LitigationProfile


def get_by_id(db: Session, profile_id: str) -> LitigationProfile | None:
    return db.get(LitigationProfile, profile_id)


def get_by_user_id(db: Session, user_id: str) -> LitigationProfile | None:
    from sqlalchemy import select

    result = db.execute(select(LitigationProfile).where(LitigationProfile.user_id == user_id))
    return result.scalar_one_or_none()


def create(db: Session, *, user_id: str, **fields: Any) -> LitigationProfile:
    profile = LitigationProfile(user_id=user_id, **fields)
    db.add(profile)
    db.flush()
    db.refresh(profile)
    return profile


def update(db: Session, *, profile: LitigationProfile, **fields: Any) -> LitigationProfile:
    for key, value in fields.items():
        if value is not None:
            setattr(profile, key, value)
    db.flush()
    db.refresh(profile)
    return profile
