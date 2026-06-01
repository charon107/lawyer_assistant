"""Service layer for PlaybookProposal.

Proposals are *created* by the Phase C playbook-monitor when a clause has been
deviated from often enough. The REST surface lets the lawyer list them and
accept / dismiss each one. Per-user isolation is enforced the same way as the
other commercial services.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import AuthorizationError, NotFoundError
from app.db.models.playbook_proposal import PlaybookProposal
from app.repositories import playbook_proposal_repo
from app.schemas.commercial.proposal import PlaybookProposalUpdate


class PlaybookProposalService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_my_proposal(self, user_id: str, proposal_id: str) -> PlaybookProposal:
        """Return one proposal owned by `user_id`.

        Raises:
            NotFoundError: row doesn't exist.
            AuthorizationError: row exists but belongs to a different user.
        """
        proposal = playbook_proposal_repo.get_by_id(self.db, proposal_id)
        if proposal is None:
            raise NotFoundError(
                message="Playbook proposal not found",
                details={"proposal_id": proposal_id},
            )
        if proposal.user_id != user_id:
            raise AuthorizationError(message="You do not have access to this proposal")
        return proposal

    def list_my_proposals(
        self,
        user_id: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[PlaybookProposal], int]:
        """Paginated list for the current user."""
        return playbook_proposal_repo.list_by_user(self.db, user_id, skip=skip, limit=limit)

    def update_my_proposal(
        self,
        user_id: str,
        proposal_id: str,
        data: PlaybookProposalUpdate,
    ) -> PlaybookProposal:
        """Accept / dismiss / edit an owned proposal."""
        proposal = self.get_my_proposal(user_id, proposal_id)
        update_kwargs = data.model_dump(exclude_unset=True, exclude_none=True)
        update_kwargs.pop("user_id", None)
        return playbook_proposal_repo.update(self.db, proposal=proposal, **update_kwargs)
