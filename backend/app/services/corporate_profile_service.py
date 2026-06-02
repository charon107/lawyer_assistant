"""Service layer for CorporateProfile.

Thin wrapper over the repository — translates between API schemas and ORM
rows, and raises domain exceptions. Repository calls never commit; the
session lifecycle (FastAPI dependency) owns commits.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.corporate_profile import CorporateProfile
from app.repositories import corporate_profile_repo
from app.schemas.corporate.profile import (
    CorporateProfileCreate,
    CorporateProfileUpdate,
)


class CorporateProfileService:
    """Business logic for the per-user corporate-legal practice profile."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_my_profile(self, user_id: str) -> CorporateProfile:
        """Return the profile for `user_id`.

        Raises:
            NotFoundError: if the user has not yet started the
                corporate-legal cold-start (no row exists).
        """
        profile = corporate_profile_repo.get_by_user_id(self.db, user_id)
        if profile is None:
            raise NotFoundError(
                message="Corporate profile not found",
                details={"user_id": user_id},
            )
        return profile

    def get_my_profile_or_none(self, user_id: str) -> CorporateProfile | None:
        """Same as get_my_profile but returns None instead of raising.

        Used by the /status endpoint, which needs to differentiate
        "no profile yet" from "profile exists but incomplete".
        """
        return corporate_profile_repo.get_by_user_id(self.db, user_id)

    def upsert_my_profile(
        self,
        user_id: str,
        data: CorporateProfileCreate | CorporateProfileUpdate,
    ) -> CorporateProfile:
        """Create-or-update the user's profile.

        On first call (no row) we create with the supplied scalar fields
        and JSON payloads. On subsequent calls only the non-None fields in
        `data` are written.
        """
        existing = corporate_profile_repo.get_by_user_id(self.db, user_id)
        if existing is None:
            create_kwargs = data.model_dump(exclude_unset=True, exclude_none=True)
            create_kwargs.pop("user_id", None)
            return corporate_profile_repo.create(
                self.db,
                user_id=user_id,
                **create_kwargs,
            )
        update_kwargs = data.model_dump(exclude_unset=True, exclude_none=True)
        update_kwargs.pop("user_id", None)
        return corporate_profile_repo.update(
            self.db,
            profile=existing,
            **update_kwargs,
        )
