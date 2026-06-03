"""Dependency carrier for the employment-legal agent.

Lives in its own module so both `agent.py` and every `tools/*` module can
import the type at runtime without circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass
class EmploymentDeps:
    """Dependencies passed to every employment-legal tool via RunContext.

    The WS handler owns the session lifecycle (repos never commit).

    - ``review_type`` is set by the handler per skill so ``save_review_result``
      records the correct type without the model guessing.
    - ``investigation_id`` / ``expansion_id`` are resolved + ownership-checked
      by the handler before running an investigation / expansion skill.
    """

    user_id: str
    db: Session
    review_type: str | None = None
    investigation_id: str | None = None
    expansion_id: str | None = None
    output_dir: str | None = None
