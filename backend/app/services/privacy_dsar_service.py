"""Service layer for PrivacyDsar (intake + management).

REST intake creates the record (PII-minimized); the WS ``dsar`` skill drafts
the two letters and writes them back via the ``save_dsar_letters`` tool.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.privacy_dsar import PrivacyDsar
from app.repositories import privacy_dsar_repo
from app.schemas.privacy.dsar import PrivacyDsarCreate, PrivacyDsarUpdate
from app.services._emp_serialize import dump_for_db

_JSON_FIELDS = {"request_types", "systems_checked", "exemptions", "log"}


class PrivacyDsarService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_dsar(
        self,
        *,
        user_id: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PrivacyDsar], int]:
        return privacy_dsar_repo.list_by_user(
            self.db, user_id=user_id, status=status, skip=skip, limit=limit
        )

    def get_owned(self, dsar_id: str, *, user_id: str) -> PrivacyDsar:
        dsar = privacy_dsar_repo.get_by_id(self.db, dsar_id)
        if dsar is None or dsar.user_id != user_id:
            raise NotFoundError(message="DSAR not found", details={"id": dsar_id})
        return dsar

    def create(self, *, user_id: str, data: PrivacyDsarCreate) -> PrivacyDsar:
        fields = dump_for_db(data, _JSON_FIELDS)
        # Default the clock-start to today if the intake form omitted it.
        if not fields.get("date_received"):
            fields["date_received"] = date.today()
        return privacy_dsar_repo.create(self.db, user_id=user_id, **fields)

    def update(self, dsar_id: str, *, user_id: str, data: PrivacyDsarUpdate) -> PrivacyDsar:
        dsar = self.get_owned(dsar_id, user_id=user_id)
        fields = dump_for_db(data, _JSON_FIELDS)
        return privacy_dsar_repo.update(self.db, dsar=dsar, **fields)
