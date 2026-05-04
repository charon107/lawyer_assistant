"""LPA Contract Review Agent package."""

from pathlib import Path


def prompts_dir() -> Path:
    """Resolve the prompts/ directory from anywhere in the package.

    Search order:
    1. Package-local: backend/app/agents/lpa/prompts/ (Docker deployments)
    2. Project root: <root>/prompts/ (development)
    3. Walk up ancestors looking for prompts/ (fallback)
    """
    this = Path(__file__).resolve()

    # 1. Package-local prompts (for Docker — copy prompts/ here in Dockerfile)
    pkg_prompts = this.parent / "prompts"
    if pkg_prompts.exists():
        return pkg_prompts

    # 2. Project root: lpa -> agents -> app -> backend -> root
    root = this.parent.parent.parent.parent
    root_prompts = root / "prompts"
    if root_prompts.exists():
        return root_prompts

    # 3. Walk up ancestors
    for ancestor in this.parents:
        candidate = ancestor / "prompts"
        if candidate.exists():
            return candidate

    return root_prompts
