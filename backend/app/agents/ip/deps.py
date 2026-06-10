"""Dependency carrier for the ip-legal agent.

Lives in its own module so both `agent.py` and every `tools/*` module can
import the type at runtime without circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass
class IpDeps:
    """Dependencies passed to every ip-legal tool via RunContext.

    The WS handler owns the session lifecycle (repos never commit).

    - ``review_type`` is set by the handler per analysis skill so
      ``save_review`` records the correct type without the model guessing.
    - ``review_id`` is the pre-created ``ip_reviews`` row for the analysis
      skills the handler seeds before streaming (clearance / fto / invention /
      infringement / ip_clause / oss).
    - ``enforcement_id`` is resolved + ownership-checked by the handler before
      the ``cease_desist`` / ``takedown`` skills run.
    """

    user_id: str
    db: Session
    review_type: str | None = None
    review_id: str | None = None
    enforcement_id: str | None = None
    output_dir: str | None = None
