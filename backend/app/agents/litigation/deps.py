"""Dependency carrier for the litigation-legal agent.

Lives in its own module so both `agent.py` and every `tools/*` module can
import the type at runtime without circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass
class LitigationDeps:
    """Dependencies passed to every litigation-legal tool via RunContext.

    The WS handler owns the session lifecycle (repos never commit).

    - ``analysis_type`` is set by the handler per analysis skill so
      ``save_analysis`` records the correct type without the model guessing.
    - ``analysis_id`` is the pre-created ``litigation_analyses`` row for the
      analysis skills the handler seeds before streaming.
    - ``demand_id`` is resolved + ownership-checked by the handler before
      the ``demand_draft`` / ``demand_received`` skills run.
    - ``matter_id`` is the matter context for matter-briefing.
    """

    user_id: str
    db: Session
    analysis_type: str | None = None
    analysis_id: str | None = None
    demand_id: str | None = None
    matter_id: str | None = None
    output_dir: str | None = None
