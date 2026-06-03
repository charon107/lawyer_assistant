"""Service layer for EmploymentProfile.

Thin wrapper over the repository — translates between API schemas and ORM
rows, raises domain exceptions, JSON-encodes list/dict fields. Repository
calls never commit; the session lifecycle owns commits.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.employment_profile import EmploymentProfile
from app.repositories import employment_profile_repo
from app.schemas.employment.profile import (
    EmploymentProfileCreate,
    EmploymentProfileUpdate,
)
from app.services._emp_serialize import dump_for_db

_JSON_FIELDS = {
    "jurisdictions",
    "hiring_trigger",
    "termination_trigger",
    "high_risk_flags",
    "provincial_supplements",
    "jurisdiction_table",
    "leave_management_config",
    "escalation_matrix",
}


class EmploymentProfileService:
    """Business logic for the per-user employment-legal practice profile."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_my_profile(self, user_id: str) -> EmploymentProfile:
        profile = employment_profile_repo.get_by_user_id(self.db, user_id)
        if profile is None:
            raise NotFoundError(
                message="Employment profile not found", details={"user_id": user_id}
            )
        return profile

    def get_my_profile_or_none(self, user_id: str) -> EmploymentProfile | None:
        return employment_profile_repo.get_by_user_id(self.db, user_id)

    def upsert_my_profile(
        self,
        user_id: str,
        data: EmploymentProfileCreate | EmploymentProfileUpdate,
    ) -> EmploymentProfile:
        fields = dump_for_db(data, _JSON_FIELDS)
        existing = employment_profile_repo.get_by_user_id(self.db, user_id)
        if existing is None:
            return employment_profile_repo.create(self.db, user_id=user_id, **fields)
        return employment_profile_repo.update(self.db, profile=existing, **fields)
