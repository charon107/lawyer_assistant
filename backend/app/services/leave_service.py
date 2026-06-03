"""Service layer for leave registrations (log-leave + management).

Concrete deadline dates (medical_period_end etc.) are supplied on the Create
payload — computed at log-leave time with the user's LLM configured. The
leave-tracker cron later does pure date arithmetic over them.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.leave_registration import LeaveRegistration
from app.repositories import leave_registration_repo
from app.schemas.employment.leave import LeaveRegistrationCreate, LeaveRegistrationUpdate


class LeaveService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_leaves(
        self,
        *,
        user_id: str,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[LeaveRegistration], int]:
        return leave_registration_repo.list_by_user(
            self.db, user_id=user_id, status=status, skip=skip, limit=limit
        )

    def get_owned(self, leave_id: str, *, user_id: str) -> LeaveRegistration:
        leave = leave_registration_repo.get_by_id(self.db, leave_id)
        if leave is None or leave.user_id != user_id:
            raise NotFoundError(message="Leave not found", details={"id": leave_id})
        return leave

    def create_leave(self, *, user_id: str, data: LeaveRegistrationCreate) -> LeaveRegistration:
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        fields.setdefault("last_updated", date.today())
        return leave_registration_repo.create(self.db, user_id=user_id, **fields)

    def update_leave(
        self, leave_id: str, *, user_id: str, data: LeaveRegistrationUpdate
    ) -> LeaveRegistration:
        leave = self.get_owned(leave_id, user_id=user_id)
        fields = data.model_dump(exclude_unset=True, exclude_none=True)
        fields["last_updated"] = date.today()
        return leave_registration_repo.update(self.db, leave=leave, **fields)
