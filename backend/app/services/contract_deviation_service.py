"""Service layer for ContractDeviation reads.

Deviations are *written* by the agent tool (`write_contract_deviation`) during
a review run, not via REST. The REST surface only needs the per-clause
aggregation that drives the playbook-monitor dashboard, so this service is
read-only.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.repositories import contract_deviation_repo
from app.schemas.commercial.deviation import ClauseDeviationCount


class ContractDeviationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_clause_counts(
        self,
        user_id: str,
        *,
        since: datetime | None = None,
    ) -> list[ClauseDeviationCount]:
        """Per-clause deviation counts for the current user, most frequent first.

        `since` optionally bounds the window (e.g. the rolling 12 months the
        playbook-monitor cares about).
        """
        rows = contract_deviation_repo.aggregate_by_clause(self.db, user_id=user_id, since=since)
        return [
            ClauseDeviationCount(clause_key=key, clause_label=label, count=count)
            for key, label, count in rows
        ]
