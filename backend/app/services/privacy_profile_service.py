"""Service layer for PrivacyProfile.

Thin wrapper over the repository — translates between API schemas and ORM
rows, raises domain exceptions, JSON-encodes list/dict fields. Repository
calls never commit; the session lifecycle owns commits.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.privacy_profile import PrivacyProfile
from app.repositories import privacy_profile_repo
from app.schemas.privacy.profile import PrivacyProfileCreate, PrivacyProfileUpdate
from app.services._emp_serialize import dump_for_db

_JSON_FIELDS = {
    "regulatory_footprint",
    "integrations",
    "dpa_playbook",
    "policy_commitments",
    "pia_house_style",
    "dsar_process",
    "escalation_matrix",
    "seed_docs",
    "output_config",
}


class PrivacyProfileService:
    """Business logic for the per-user privacy-legal practice profile."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_my_profile(self, user_id: str) -> PrivacyProfile:
        profile = privacy_profile_repo.get_by_user_id(self.db, user_id)
        if profile is None:
            raise NotFoundError(message="Privacy profile not found", details={"user_id": user_id})
        return profile

    def get_my_profile_or_none(self, user_id: str) -> PrivacyProfile | None:
        return privacy_profile_repo.get_by_user_id(self.db, user_id)

    def upsert_my_profile(
        self,
        user_id: str,
        data: PrivacyProfileCreate | PrivacyProfileUpdate,
    ) -> PrivacyProfile:
        fields = dump_for_db(data, _JSON_FIELDS)
        existing = privacy_profile_repo.get_by_user_id(self.db, user_id)
        if existing is None:
            return privacy_profile_repo.create(self.db, user_id=user_id, **fields)
        return privacy_profile_repo.update(self.db, profile=existing, **fields)
