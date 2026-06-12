"""LitigationDemand service — 律师函生命周期管理."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.models.litigation_demand import LitigationDemand
from app.repositories import litigation_demand_repo
from app.schemas.litigation.demand import LitigationDemandCreate, LitigationDemandUpdate


class LitigationDemandService:
    """Demand letter CRUD (发送/接收双模式)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_owned(self, demand_id: str, *, user_id: str) -> LitigationDemand:
        demand = litigation_demand_repo.get_by_id(self.db, demand_id)
        if demand is None:
            raise NotFoundError(message="律师函不存在", details={"demand_id": demand_id})
        if demand.user_id != user_id:
            raise AuthorizationError(message="无权访问该律师函")
        return demand

    def list_demands(
        self,
        *,
        user_id: str,
        mode: str | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[LitigationDemand], int]:
        return litigation_demand_repo.list_by_user(
            self.db, user_id=user_id, mode=mode, status=status, skip=skip, limit=limit
        )

    def create(self, *, user_id: str, data: LitigationDemandCreate) -> LitigationDemand:
        fields = data.model_dump(exclude_none=True)
        for key in ("intake_snapshot", "right_or_claim"):
            if key in fields and isinstance(fields[key], dict):
                fields[key] = json.dumps(fields[key], ensure_ascii=False)
        return litigation_demand_repo.create(self.db, user_id=user_id, **fields)

    def update(
        self, demand_id: str, *, user_id: str, data: LitigationDemandUpdate
    ) -> LitigationDemand:
        demand = self.get_owned(demand_id, user_id=user_id)
        fields = data.model_dump(exclude_none=True)
        for key in (
            "intake_snapshot",
            "right_or_claim",
            "pretransmit_checklist",
            "triage_result",
            "log",
        ):
            if key in fields and isinstance(fields[key], (dict, list)):
                fields[key] = json.dumps(fields[key], ensure_ascii=False)
        return litigation_demand_repo.update(self.db, demand=demand, **fields)
