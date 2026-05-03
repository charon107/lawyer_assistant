"""LPA Contract Review Agent package."""

from pathlib import Path


def prompts_dir() -> Path:
    """Resolve the prompts/ directory from anywhere in the package."""
    # Try project-root-relative first
    this = Path(__file__).resolve()
    # this = backend/app/agents/lpa/__init__.py
    # Go up to project root: lpa -> agents -> app -> backend -> root
    root = this.parent.parent.parent.parent
    prompts = root / "prompts"
    if prompts.exists():
        return prompts
    # Fallback: look relative to the calling module
    for ancestor in this.parents:
        candidate = ancestor / "prompts"
        if candidate.exists():
            return candidate
    return prompts
