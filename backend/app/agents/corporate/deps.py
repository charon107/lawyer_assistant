"""Dependency carrier for the corporate-legal agent.

Lives in its own module so both `agent.py` and every `tools/*` module
can import the type at runtime without circular imports. PydanticAI
evaluates RunContext type parameters at tool registration time and needs
the class to exist in the tool module's namespace.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass
class CorporateDeps:
    """Dependencies passed to every corporate-legal tool via RunContext.

    The WS/REST handler owns the session lifecycle (repos never commit).

    - ``deal_id`` is the active deal every M&A-core skill scopes to; the
      handler resolves + ownership-checks it before running the agent.
    - ``tabular_review_id`` is pre-created by the handler for a
      tabular-review run so ``write_tabular_review`` has a row to update.
    - ``output_dir`` is where Excel/CSV exports are written.
    """

    user_id: str
    db: Session
    deal_id: str | None = None
    tabular_review_id: str | None = None
    output_dir: str | None = None
