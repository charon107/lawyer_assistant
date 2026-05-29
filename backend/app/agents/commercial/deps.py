"""Dependency carrier for the commercial-legal agent.

Lives in its own module so that both `agent.py` and every `tools/*`
module can import the type at runtime without circular imports.
PydanticAI evaluates RunContext type parameters at tool registration
time and needs the class to actually exist in the tool module's
namespace.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass
class CommercialDeps:
    """Dependencies passed to every commercial-legal tool via RunContext.

    The WS handler is responsible for opening + closing the session
    (project convention: repos never commit). `review_id` is set by
    the handler BEFORE running the agent so `write_contract_review`
    has a row to update; it stays None for skills (later phases) that
    don't write a review.
    """

    user_id: str
    db: Session
    review_id: str | None = None
