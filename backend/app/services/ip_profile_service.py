"""Service layer for IpProfile.

Thin wrapper over the repository — translates between API schemas and ORM
rows, raises domain exceptions, JSON-encodes list/dict fields. Repository calls
never commit; the session lifecycle owns commits.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.ip_profile import IpProfile
from app.repositories import ip_profile_repo
from app.schemas.ip.profile import IpProfileCreate, IpProfileUpdate
from app.services._emp_serialize import dump_for_db

_JSON_FIELDS = {
    "integrations",
    "ip_scope",
    "registration_jurisdictions",
    "domain_ownership",
    "outside_counsel",
    "enforcement_posture",
    "brand_protection",
    "portfolio_meta",
    "seed_docs",
    "output_config",
}


class IpProfileService:
    """Business logic for the per-user ip-legal practice profile."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_my_profile(self, user_id: str) -> IpProfile:
        profile = ip_profile_repo.get_by_user_id(self.db, user_id)
        if profile is None:
            raise NotFoundError(message="IP profile not found", details={"user_id": user_id})
        return profile

    def get_my_profile_or_none(self, user_id: str) -> IpProfile | None:
        return ip_profile_repo.get_by_user_id(self.db, user_id)

    def upsert_my_profile(
        self,
        user_id: str,
        data: IpProfileCreate | IpProfileUpdate,
    ) -> IpProfile:
        fields = dump_for_db(data, _JSON_FIELDS)
        existing = ip_profile_repo.get_by_user_id(self.db, user_id)
        if existing is None:
            return ip_profile_repo.create(self.db, user_id=user_id, **fields)
        return ip_profile_repo.update(self.db, profile=existing, **fields)
