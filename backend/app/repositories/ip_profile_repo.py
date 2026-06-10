"""Repository for `ip_profiles`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.ip_profile import IpProfile


def get_by_user_id(db: Session, user_id: str) -> IpProfile | None:
    result = db.execute(select(IpProfile).where(IpProfile.user_id == user_id))
    return result.scalar_one_or_none()


def create(db: Session, *, user_id: str, **fields: Any) -> IpProfile:
    profile = IpProfile(user_id=user_id, **fields)
    db.add(profile)
    db.flush()
    db.refresh(profile)
    return profile


def update(db: Session, *, profile: IpProfile, **fields: Any) -> IpProfile:
    for key, value in fields.items():
        if value is not None:
            setattr(profile, key, value)
    db.flush()
    db.refresh(profile)
    return profile
