"""Merge Wikisource + LawRefBook source directories into a single import-ready
markdown set under ``data/laws_merged/``.

Merge rule (Phase 2 scope decision, 2026-05-23):
- LawRefBook wins for every law_id present in both sources. LawRefBook tracks
  amendment dates explicitly (e.g. ``公司法(2023-12-29).md`` → latest revision
  after the 2.1 dedup), so it is the authoritative source for laws that
  appear in both places.
- Wikisource fills in the gaps. The 4 known gaps as of 2026-05-23 are
  民法典 / 行政复议法 / 行政诉讼法 / 工伤保险条例.

Output: ``data/laws_merged/{law_id}.md`` — one file per unique law_id,
suitable for ``law-db import --source data/laws_merged``.

This step is dynamic — if LawRefBook later adds 民法典 as an integrated
file, it will take over automatically. No hard-coded gap list.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.commands import error, info, success, warning

logger = logging.getLogger(__name__)

DEFAULT_WIKISOURCE_DIR = Path("data/laws")
DEFAULT_LAWREFBOOK_DIR = Path("data/laws_lawrefbook")
DEFAULT_OUTPUT_DIR = Path("data/laws_merged")


@dataclass(frozen=True, slots=True)
class MergeReport:
    """Summary of a merge run, useful for tests and CLI output."""

    total_output: int
    from_wikisource: int
    from_lawrefbook: int
    overlapping_law_ids: tuple[str, ...]
    wikisource_only_law_ids: tuple[str, ...]
    written: int
    skipped: int


@dataclass(slots=True)
class _SourceFile:
    """One markdown source candidate."""

    path: Path
    source_name: str  # "wikisource" or "lawrefbook"


def _index_markdown_dir(directory: Path) -> dict[str, Path]:
    """Return ``{law_id: path}`` for every ``.md`` file in ``directory``.

    Missing directory is treated as empty (warned but not fatal — useful when
    only one source has been fetched).
    """
    if not directory.is_dir():
        warning(f"  Source dir missing: {directory} (treating as empty)")
        return {}
    return {p.stem: p for p in sorted(directory.glob("*.md"))}


def _resolve_sources(
    wikisource: dict[str, Path], lawrefbook: dict[str, Path]
) -> tuple[dict[str, _SourceFile], list[str], list[str]]:
    """Apply the merge rule and return per-law decisions + overlap stats.

    LawRefBook overrides Wikisource for any law_id present in both. The
    ``overlapping_ids`` list captures which Wikisource files got dropped so
    callers can audit the substitution.
    """
    selected: dict[str, _SourceFile] = {}
    # Seed with Wikisource (default)
    for law_id, path in wikisource.items():
        selected[law_id] = _SourceFile(path=path, source_name="wikisource")
    # LawRefBook overrides
    overlapping = sorted(set(wikisource) & set(lawrefbook))
    for law_id, path in lawrefbook.items():
        selected[law_id] = _SourceFile(path=path, source_name="lawrefbook")
    wikisource_only = sorted(set(wikisource) - set(lawrefbook))
    return selected, overlapping, wikisource_only


def _write_merged(
    selected: dict[str, _SourceFile], output_dir: Path, force: bool
) -> tuple[int, int]:
    """Copy each selected source file to ``output_dir/{law_id}.md``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped = 0
    for law_id, src in sorted(selected.items()):
        target = output_dir / f"{law_id}.md"
        if target.exists() and not force:
            skipped += 1
            continue
        shutil.copyfile(src.path, target)
        written += 1
    return written, skipped


def run_merge(
    wikisource_dir: Path | None = None,
    lawrefbook_dir: Path | None = None,
    output_dir: Path | None = None,
    force: bool = False,
) -> MergeReport:
    """Merge two source directories into a single import-ready directory."""
    ws_dir = wikisource_dir if wikisource_dir is not None else DEFAULT_WIKISOURCE_DIR
    lrb_dir = lawrefbook_dir if lawrefbook_dir is not None else DEFAULT_LAWREFBOOK_DIR
    out_dir = output_dir if output_dir is not None else DEFAULT_OUTPUT_DIR

    info(f"Merging sources into: {out_dir}")
    info(f"  - Wikisource: {ws_dir}")
    info(f"  - LawRefBook: {lrb_dir}")

    ws_files = _index_markdown_dir(ws_dir)
    lrb_files = _index_markdown_dir(lrb_dir)

    if not ws_files and not lrb_files:
        error(
            "Both source directories are empty. Run `law-db fetch` and/or `law-db fetch-lawrefbook` first."
        )
        raise SystemExit(2)

    selected, overlapping, ws_only = _resolve_sources(ws_files, lrb_files)
    from_lrb = sum(1 for s in selected.values() if s.source_name == "lawrefbook")
    from_ws = sum(1 for s in selected.values() if s.source_name == "wikisource")

    info(f"  Wikisource: {len(ws_files)} files; LawRefBook: {len(lrb_files)} files")
    info(f"  Overlap (LawRefBook wins): {len(overlapping)} laws")
    info(f"  Wikisource only: {len(ws_only)} laws — {', '.join(ws_only) or '(none)'}")

    written, skipped = _write_merged(selected, Path(out_dir), force=force)
    success(
        f"\nMerge complete: {len(selected)} unique laws → {out_dir} "
        f"({written} written, {skipped} skipped)"
    )
    info(f"  From Wikisource: {from_ws}  |  From LawRefBook: {from_lrb}")
    if skipped > 0 and not force:
        info("  (run with --force to overwrite existing merged files)")

    return MergeReport(
        total_output=len(selected),
        from_wikisource=from_ws,
        from_lawrefbook=from_lrb,
        overlapping_law_ids=tuple(overlapping),
        wikisource_only_law_ids=tuple(ws_only),
        written=written,
        skipped=skipped,
    )
