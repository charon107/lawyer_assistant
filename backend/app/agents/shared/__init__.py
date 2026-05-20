"""Shared agent components — reusable across document review pipelines."""

from pathlib import Path


def prompts_dir(base_dir: Path | None = None) -> Path:
    """Locate the project-level prompts/ directory.

    Args:
        base_dir: Starting directory for the search. Defaults to the project root
                  (3 levels up from this file: shared -> agents -> app -> backend -> root).

    Returns:
        Path to the prompts/ directory.
    """
    if base_dir is None:
        # shared -> agents -> app -> backend -> root
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

    root_prompts = base_dir / "prompts"
    if root_prompts.exists():
        return root_prompts

    # Walk up ancestors as fallback
    for ancestor in base_dir.parents:
        candidate = ancestor / "prompts"
        if candidate.exists():
            return candidate

    return root_prompts
