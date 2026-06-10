"""Service layer for IpPortfolio (CRUD + arithmetic report/audit).

The portfolio is maintained via plain CRUD. ``report`` recomputes each asset's
next deadline from key dates + per-jurisdiction rules and buckets by urgency;
``audit`` adds health flags (撤三风险, 长期 pending, 缺失关键日期). No LLM.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.models.ip_portfolio import IpPortfolio
from app.repositories import ip_portfolio_repo
from app.schemas.ip.portfolio import IpPortfolioCreate, IpPortfolioUpdate
from app.services._emp_serialize import dump_for_db
from app.tasks.ip_deadline_rules import bucket_assets

_JSON_FIELDS: set[str] = set()  # next_deadlines is computed, never client-supplied

# Trademark unused for 3 years → 撤三 risk (商标法§49).
_TRADEMARK_USE_RISK_YEARS = 3


class IpPortfolioService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_assets(
        self,
        *,
        user_id: str,
        asset_type: str | None = None,
        skip: int = 0,
        limit: int = 1000,
    ) -> tuple[list[IpPortfolio], int]:
        return ip_portfolio_repo.list_by_user(
            self.db, user_id=user_id, asset_type=asset_type, skip=skip, limit=limit
        )

    def get_owned(self, asset_id: str, *, user_id: str) -> IpPortfolio:
        asset = ip_portfolio_repo.get_by_id(self.db, asset_id)
        if asset is None or asset.user_id != user_id:
            raise NotFoundError(message="Portfolio asset not found", details={"id": asset_id})
        return asset

    def create(self, *, user_id: str, data: IpPortfolioCreate) -> IpPortfolio:
        fields = dump_for_db(data, _JSON_FIELDS)
        return ip_portfolio_repo.create(self.db, user_id=user_id, **fields)

    def update(self, asset_id: str, *, user_id: str, data: IpPortfolioUpdate) -> IpPortfolio:
        asset = self.get_owned(asset_id, user_id=user_id)
        fields = dump_for_db(data, _JSON_FIELDS)
        return ip_portfolio_repo.update(self.db, asset=asset, **fields)

    def report(self, *, user_id: str, today: date | None = None) -> dict[str, Any]:
        """Recompute deadlines + bucket by urgency (90-day window)."""
        assets, _ = ip_portfolio_repo.list_by_user(self.db, user_id=user_id)
        buckets = bucket_assets(list(assets), today=today)
        return {"buckets": buckets.to_dict(), "summary": buckets.summary()}

    def audit(self, *, user_id: str, today: date | None = None) -> dict[str, Any]:
        """Health check — deadline buckets + portfolio-hygiene flags."""
        today = today or date.today()
        assets, _ = ip_portfolio_repo.list_by_user(self.db, user_id=user_id)
        flags: list[dict[str, Any]] = []
        for a in assets:
            # 撤三风险: registered trademark with no recent use signal (registration > 3y).
            if (
                a.asset_type == "trademark"
                and a.status == "registered"
                and a.registration_date is not None
                and (today - a.registration_date).days > _TRADEMARK_USE_RISK_YEARS * 365
            ):
                flags.append(
                    {
                        "asset_id": a.id,
                        "title": a.title,
                        "flag": "撤三风险（商标法§49）：注册满3年，确认近3年使用证据",
                    }
                )
            # Long-pending applications.
            if (
                a.status == "pending"
                and a.filing_date is not None
                and (today - a.filing_date).days > 2 * 365
            ):
                flags.append(
                    {
                        "asset_id": a.id,
                        "title": a.title,
                        "flag": "申请 pending 超过 2 年，确认审查进度",
                    }
                )
            # Missing key dates → can't compute deadlines.
            if (
                a.asset_type != "copyright"
                and a.registration_date is None
                and a.filing_date is None
            ):
                flags.append(
                    {"asset_id": a.id, "title": a.title, "flag": "缺失关键日期，无法推算期限"}
                )
        buckets = bucket_assets(list(assets), today=today)
        return {"buckets": buckets.to_dict(), "flags": flags, "summary": buckets.summary()}
