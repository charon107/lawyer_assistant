"""Dependency carrier for the regulatory-legal agent.

Lives in its own module so both ``agent.py`` and every ``tools/*`` module can
import the type at runtime without circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session


@dataclass
class RegulatoryDeps:
    """Dependencies passed to every regulatory-legal tool via RunContext.

    The WS handler owns the session lifecycle (repos never commit).

    - ``analysis_type`` is set by the handler per analysis skill so
      ``save_analysis`` records the correct type without the model guessing.
    - ``analysis_id`` is the pre-created ``regulatory_analyses`` row for the
      policy_diff / policy_redraft skills the handler seeds before streaming.
    - ``reg_item_id`` is the reg item a policy-diff targets.
    - ``fetched_provenance`` (review decision C2): the set of dedup_keys / links
      that ``fetch_reg_feeds`` actually returned THIS session. ``save_reg_item``
      trusts an item's source only if it appears here; otherwise it is force-
      stamped ``[模型知识—需验证]`` + ``status_verified=False`` so the model can
      never silently inject a fabricated regulation.
    """

    user_id: str
    db: Session
    analysis_type: str | None = None
    analysis_id: str | None = None
    reg_item_id: str | None = None
    output_dir: str | None = None
    fetched_provenance: set[str] = field(default_factory=set)
