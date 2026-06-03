"""Repository for `employment_profiles`. Stateless sync; never commits."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.employment_profile import EmploymentProfile


def get_by_user_id(db: Session, user_id: str) -> EmploymentProfile | None:
    result = db.execute(select(EmploymentProfile).where(EmploymentProfile.user_id == user_id))
    return result.scalar_one_or_none()


def create(db: Session, *, user_id: str, **fields: Any) -> EmploymentProfile:
    profile = EmploymentProfile(user_id=user_id, **fields)
    db.add(profile)
    db.flush()
    db.refresh(profile)
    return profile


def update(db: Session, *, profile: EmploymentProfile, **fields: Any) -> EmploymentProfile:
    for key, value in fields.items():
        if value is not None:
            setattr(profile, key, value)
    db.flush()
    db.refresh(profile)
    return profile
