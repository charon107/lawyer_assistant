"""LawRefBook fetcher — extracts the latest version of each Chinese law from
github.com/LawRefBook/Laws and writes one markdown file per law to the
output directory.

Usage (via law-db CLI):
    uv run law-db fetch-lawrefbook
    uv run law-db fetch-lawrefbook --source data/laws_lawrefbook --force

Design notes:
- LawRefBook ships multiple historical versions per law (e.g. 公司法(2018) +
  公司法(2023)). We collapse those down to the latest version only — the
  Phase 2 scope decision (only-latest, no version_id schema).
- The 民法典 subdirectory is intentionally skipped. LawRefBook fragments the
  Civil Code into 8 编 files; the Wikisource fetch ships the integrated
  1260-article version which is preferred for cross-编 search context.
- The git clone cache lives at ``data/.lawrefbook_cache/`` (gitignored). On
  subsequent runs we ``git pull --ff-only`` instead of re-cloning.
- We do NOT filter against the 17 Wikisource laws here — that conflict
  resolution belongs to Ticket 2.2 (merge step).
"""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.commands import error, info, success, warning

logger = logging.getLogger(__name__)

LAWREFBOOK_REPO_URL = "https://github.com/LawRefBook/Laws.git"
DEFAULT_CACHE_DIR = Path("data/.lawrefbook_cache")
DEFAULT_OUTPUT_DIR = Path("data/laws_lawrefbook")

# Top-level NPC categories inside the LawRefBook repo that hold law markdown
# files. 民法典/ is excluded — Wikisource owns the Civil Code.
NPC_CATEGORIES: tuple[str, ...] = (
    "刑法",
    "宪法相关法",
    "民法商法",
    "社会法",
    "行政法",
    # Procedural laws (民事诉讼法, 刑事诉讼法, 仲裁法, 公证法 …).
    # Originally omitted; users hitting `get_law_article(law_id="民事诉讼法")`
    # got "未找到" because of this gap.
    "诉讼与非诉讼程序法",
)

# Filename pattern: "公司法(2023-12-29).md" or "保险法.md"
_FILENAME_RE = re.compile(r"^(?P<name>.+?)(?:\((?P<date>\d{4}-\d{2}-\d{2})\))?\.md$")

# Skip these non-law files even if they live in a category subdir
_SKIP_FILES: frozenset[str] = frozenset({"_index.md", "法律法规模版.md", "README.md"})


@dataclass(frozen=True, slots=True)
class LawCandidate:
    """A single LawRefBook source file parsed into structured metadata."""

    law_id: str
    effective_date: date | None
    source_path: Path
    npc_category: str


class LawRefBookError(RuntimeError):
    """Raised when git operations or directory layout assumptions fail."""


def _parse_filename(filename: str) -> tuple[str, date | None] | None:
    """Parse ``公司法(2023-12-29).md`` or ``保险法.md`` into ``(law_id, date)``.

    Returns ``None`` for non-law files (indices, templates, README).
    """
    if filename in _SKIP_FILES:
        return None
    match = _FILENAME_RE.match(filename)
    if match is None:
        return None
    name = match.group("name").strip()
    if not name:
        return None
    date_str = match.group("date")
    if date_str is None:
        return name, None
    try:
        return name, date.fromisoformat(date_str)
    except ValueError:
        logger.warning("Unparseable date in filename %s — keeping as None", filename)
        return name, None


def _ensure_cache(cache_dir: Path) -> None:
    """Clone the LawRefBook repo if absent, otherwise fast-forward pull.

    If ``cache_dir`` exists but is not a git checkout (no ``.git`` directory),
    treat it as a pre-populated source and skip git operations — useful in
    tests with synthetic fixtures and for users who curate their own copy.

    Raises ``LawRefBookError`` on any git failure so the caller can stop
    before iterating an inconsistent tree.
    """
    if cache_dir.exists():
        if not (cache_dir / ".git").is_dir():
            info(f"Using pre-populated LawRefBook cache (not a git clone): {cache_dir}")
            return
        info(f"Updating LawRefBook cache: {cache_dir}")
        result = subprocess.run(
            ["git", "-C", str(cache_dir), "pull", "--ff-only"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise LawRefBookError(f"git pull failed in {cache_dir}: {result.stderr.strip()}")
        return

    info(f"Cloning LawRefBook into: {cache_dir}")
    cache_dir.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "git",
            "clone",
            "--depth=1",
            LAWREFBOOK_REPO_URL,
            str(cache_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise LawRefBookError(f"git clone failed: {result.stderr.strip()}")


def _collect_candidates(cache_dir: Path) -> list[LawCandidate]:
    """Walk the LawRefBook tree and parse every law file into a candidate."""
    candidates: list[LawCandidate] = []
    for category in NPC_CATEGORIES:
        category_dir = cache_dir / category
        if not category_dir.is_dir():
            warning(f"  Missing LawRefBook category dir: {category_dir}")
            continue
        for md_path in sorted(category_dir.glob("*.md")):
            parsed = _parse_filename(md_path.name)
            if parsed is None:
                continue
            law_id, eff_date = parsed
            candidates.append(
                LawCandidate(
                    law_id=law_id,
                    effective_date=eff_date,
                    source_path=md_path,
                    npc_category=category,
                )
            )
    return candidates


def _dedup_latest(candidates: list[LawCandidate]) -> list[LawCandidate]:
    """Group by ``law_id``, keep the candidate with the max effective_date.

    A ``None`` date is treated as the oldest possible (so any dated version
    wins over an undated one — matches LawRefBook's curation pattern where
    dated files are the explicit amendments).
    """
    by_id: dict[str, LawCandidate] = {}
    for cand in candidates:
        existing = by_id.get(cand.law_id)
        if existing is None:
            by_id[cand.law_id] = cand
            continue
        existing_key = existing.effective_date or date.min
        current_key = cand.effective_date or date.min
        if current_key > existing_key:
            by_id[cand.law_id] = cand
    return sorted(by_id.values(), key=lambda c: c.law_id)


def _write_output(selected: list[LawCandidate], output: Path, force: bool) -> tuple[int, int]:
    """Copy each selected source file to ``output/{law_id}.md``."""
    output.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = 0
    for cand in selected:
        target = output / f"{cand.law_id}.md"
        if target.exists() and not force:
            skipped += 1
            continue
        shutil.copyfile(cand.source_path, target)
        written += 1
    return written, skipped


def run_fetch_lawrefbook(
    output: Path,
    force: bool = False,
    cache_dir: Path | None = None,
) -> None:
    """Fetch LawRefBook → dedup per law_id (latest version) → copy to output."""
    cache = cache_dir if cache_dir is not None else DEFAULT_CACHE_DIR
    try:
        _ensure_cache(cache)
    except LawRefBookError as exc:
        error(str(exc))
        error(
            "Hint: confirm `git` is installed and "
            f"{LAWREFBOOK_REPO_URL} is reachable from this host."
        )
        raise SystemExit(2) from exc

    candidates = _collect_candidates(cache)
    info(f"Collected {len(candidates)} candidate files across {len(NPC_CATEGORIES)} NPC categories")

    selected = _dedup_latest(candidates)
    multi_version = len(candidates) - len(selected)
    info(
        f"After deduping multi-version files: {len(selected)} unique laws "
        f"({multi_version} older versions discarded)"
    )

    written, skipped = _write_output(selected, Path(output), force=force)
    success(
        f"\nLawRefBook fetch complete: {written} written, "
        f"{skipped} skipped (already existed). Use --force to overwrite."
    )
    info(f"Output dir: {Path(output).resolve()}")
    if skipped > 0 and not force:
        info("  (run with --force to refresh existing files)")
