"""Service layer for IpEnforcement (intake + management).

REST intake creates the matter; the WS ``cease_desist`` / ``takedown`` skills
draft the letter and write it back via the ``save_letter`` tool.

For takedown counter-notices the 15-working-day clock is seeded at intake when
the form omits an explicit deadline.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.ip_enforcement import IpEnforcement
from app.repositories import ip_enforcement_repo
from app.schemas.ip.enforcement import IpEnforcementCreate, IpEnforcementUpdate
from app.services._emp_serialize import dump_for_db

_JSON_FIELDS = {"right_at_issue", "due_diligence", "send_gate", "log"}

# 15 working days ≈ 21 calendar days (《信息网络传播权保护条例》§16 反通知后等待期).
_COUNTER_NOTICE_CALENDAR_DAYS = 21


class IpEnforcementService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_enforcement(
        self,
        *,
        user_id: str,
        matter_type: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[IpEnforcement], int]:
        return ip_enforcement_repo.list_by_user(
            self.db,
            user_id=user_id,
            matter_type=matter_type,
            status=status,
            skip=skip,
            limit=limit,
        )

    def get_owned(self, enforcement_id: str, *, user_id: str) -> IpEnforcement:
        row = ip_enforcement_repo.get_by_id(self.db, enforcement_id)
        if row is None or row.user_id != user_id:
            raise NotFoundError(
                message="Enforcement matter not found", details={"id": enforcement_id}
            )
        return row

    def create(self, *, user_id: str, data: IpEnforcementCreate) -> IpEnforcement:
        fields = dump_for_db(data, _JSON_FIELDS)
        # Seed the 15-working-day clock for a takedown counter-notice if not given.
        if (
            data.matter_type == "takedown"
            and data.mode == "counter"
            and not fields.get("response_deadline")
        ):
            fields["response_deadline"] = date.today() + timedelta(
                days=_COUNTER_NOTICE_CALENDAR_DAYS
            )
        return ip_enforcement_repo.create(self.db, user_id=user_id, **fields)

    def update(
        self, enforcement_id: str, *, user_id: str, data: IpEnforcementUpdate
    ) -> IpEnforcement:
        row = self.get_owned(enforcement_id, user_id=user_id)
        fields = dump_for_db(data, _JSON_FIELDS)
        return ip_enforcement_repo.update(self.db, enforcement=row, **fields)
