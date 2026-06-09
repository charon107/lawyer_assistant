"""Dependency carrier for the privacy-legal agent.

Lives in its own module so both `agent.py` and every `tools/*` module can
import the type at runtime without circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session


@dataclass
class PrivacyDeps:
    """Dependencies passed to every privacy-legal tool via RunContext.

    The WS handler owns the session lifecycle (repos never commit).

    - ``review_type`` is set by the handler per skill so ``save_review``
      records the correct type without the model guessing.
    - ``review_id`` is the pre-created ``privacy_reviews`` row for skills the
      handler seeds before streaming (triage / dpa / pia / gap / policy_sweep).
    - ``dsar_id`` is resolved + ownership-checked by the handler before the
      ``dsar`` skill runs.
    """

    user_id: str
    db: Session
    review_type: str | None = None
    review_id: str | None = None
    dsar_id: str | None = None
    output_dir: str | None = None
