"""Tests for app.commands.law_merge — source resolution priority, missing-dir
handling, and the end-to-end orchestrator."""

from pathlib import Path

import pytest

from app.commands.law_merge import (
    _index_markdown_dir,
    _resolve_sources,
    _write_merged,
    run_merge,
)

# ---------------------------------------------------------------------------
# _index_markdown_dir
# ---------------------------------------------------------------------------


class TestIndexMarkdownDir:
    def test_indexes_md_files_by_stem(self, tmp_path: Path):
        (tmp_path / "公司法.md").write_text("a", encoding="utf-8")
        (tmp_path / "保险法.md").write_text("b", encoding="utf-8")
        result = _index_markdown_dir(tmp_path)
        assert set(result.keys()) == {"公司法", "保险法"}
        assert result["公司法"].name == "公司法.md"

    def test_returns_empty_for_missing_dir(self, tmp_path: Path):
        ghost = tmp_path / "does_not_exist"
        assert _index_markdown_dir(ghost) == {}

    def test_ignores_non_md_files(self, tmp_path: Path):
        (tmp_path / "law.md").write_text("yes", encoding="utf-8")
        (tmp_path / "junk.txt").write_text("no", encoding="utf-8")
        (tmp_path / "config.yaml").write_text("no", encoding="utf-8")
        assert set(_index_markdown_dir(tmp_path).keys()) == {"law"}


# ---------------------------------------------------------------------------
# _resolve_sources — the priority logic
# ---------------------------------------------------------------------------


class TestResolveSources:
    def test_lawrefbook_wins_on_overlap(self):
        ws = {"公司法": Path("ws/公司法.md")}
        lrb = {"公司法": Path("lrb/公司法.md")}
        selected, overlap, ws_only = _resolve_sources(ws, lrb)
        assert overlap == ["公司法"]
        assert ws_only == []
        assert selected["公司法"].path == Path("lrb/公司法.md")
        assert selected["公司法"].source_name == "lawrefbook"

    def test_wikisource_used_for_gap_only_laws(self):
        ws = {"民法典": Path("ws/民法典.md")}
        lrb = {"公司法": Path("lrb/公司法.md")}
        selected, overlap, ws_only = _resolve_sources(ws, lrb)
        assert overlap == []
        assert ws_only == ["民法典"]
        assert selected["民法典"].source_name == "wikisource"
        assert selected["公司法"].source_name == "lawrefbook"

    def test_union_contains_both_when_no_overlap(self):
        ws = {"a": Path("ws/a.md"), "b": Path("ws/b.md")}
        lrb = {"c": Path("lrb/c.md"), "d": Path("lrb/d.md")}
        selected, overlap, ws_only = _resolve_sources(ws, lrb)
        assert overlap == []
        assert set(ws_only) == {"a", "b"}
        assert set(selected.keys()) == {"a", "b", "c", "d"}
        assert {s.source_name for s in selected.values()} == {
            "wikisource",
            "lawrefbook",
        }

    def test_realistic_phase2_topology(self):
        """Simulate the real 17 Wikisource + 219 LawRefBook layout.

        13 overlap, 4 Wikisource-only, 206 LawRefBook-only.
        """
        wikisource_only = {
            "民法典": Path("ws/民法典.md"),
            "行政复议法": Path("ws/行政复议法.md"),
            "行政诉讼法": Path("ws/行政诉讼法.md"),
            "工伤保险条例": Path("ws/工伤保险条例.md"),
        }
        overlap = {
            "公司法": (Path("ws/公司法.md"), Path("lrb/公司法.md")),
            "刑法": (Path("ws/刑法.md"), Path("lrb/刑法.md")),
            "商标法": (Path("ws/商标法.md"), Path("lrb/商标法.md")),
        }
        lawrefbook_only = {
            "保险法": Path("lrb/保险法.md"),
            "证券法": Path("lrb/证券法.md"),
        }
        ws = {**wikisource_only, **{k: v[0] for k, v in overlap.items()}}
        lrb = {**{k: v[1] for k, v in overlap.items()}, **lawrefbook_only}

        selected, overlapping, ws_only = _resolve_sources(ws, lrb)

        assert set(overlapping) == set(overlap.keys())
        assert set(ws_only) == set(wikisource_only.keys())
        # Wikisource-only laws keep their source
        for law_id in wikisource_only:
            assert selected[law_id].source_name == "wikisource"
        # Overlap laws come from LawRefBook
        for law_id, (_, lrb_path) in overlap.items():
            assert selected[law_id].path == lrb_path
            assert selected[law_id].source_name == "lawrefbook"
        # LawRefBook-only laws have lawrefbook source
        for law_id in lawrefbook_only:
            assert selected[law_id].source_name == "lawrefbook"


# ---------------------------------------------------------------------------
# _write_merged
# ---------------------------------------------------------------------------


class TestWriteMerged:
    def _make(self, src_dir: Path, name: str, body: str):
        from app.commands.law_merge import _SourceFile

        path = src_dir / f"{name}.md"
        path.write_text(body, encoding="utf-8")
        return _SourceFile(path=path, source_name="wikisource")

    def test_writes_each_selected_to_named_file(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        selected = {
            "公司法": self._make(src, "公司法_raw", "公司法 body"),
            "保险法": self._make(src, "保险法_raw", "保险法 body"),
        }
        written, skipped = _write_merged(selected, out, force=False)
        assert written == 2
        assert skipped == 0
        assert (out / "公司法.md").read_text(encoding="utf-8") == "公司法 body"
        assert (out / "保险法.md").read_text(encoding="utf-8") == "保险法 body"

    def test_skips_existing_without_force(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        (out / "公司法.md").write_text("OLD", encoding="utf-8")
        selected = {"公司法": self._make(src, "公司法_new", "NEW")}
        written, skipped = _write_merged(selected, out, force=False)
        assert written == 0
        assert skipped == 1
        assert (out / "公司法.md").read_text(encoding="utf-8") == "OLD"

    def test_force_overwrites(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        (out / "公司法.md").write_text("OLD", encoding="utf-8")
        selected = {"公司法": self._make(src, "公司法_new", "NEW")}
        written, skipped = _write_merged(selected, out, force=True)
        assert written == 1
        assert skipped == 0
        assert (out / "公司法.md").read_text(encoding="utf-8") == "NEW"


# ---------------------------------------------------------------------------
# run_merge — orchestrator with real filesystem
# ---------------------------------------------------------------------------


class TestRunMerge:
    def _populate_sources(self, root: Path) -> tuple[Path, Path]:
        ws = root / "ws"
        lrb = root / "lrb"
        ws.mkdir()
        lrb.mkdir()
        # 4 Wikisource-only laws (the real Phase 2 gaps)
        for law_id in ("民法典", "行政复议法", "行政诉讼法", "工伤保险条例"):
            (ws / f"{law_id}.md").write_text(f"WS:{law_id}", encoding="utf-8")
        # 2 overlap laws (Wikisource version)
        (ws / "公司法.md").write_text("WS:公司法 旧版", encoding="utf-8")
        (ws / "刑法.md").write_text("WS:刑法 旧版", encoding="utf-8")
        # Same 2 in LawRefBook (preferred)
        (lrb / "公司法.md").write_text("LRB:公司法 2023", encoding="utf-8")
        (lrb / "刑法.md").write_text("LRB:刑法 最新", encoding="utf-8")
        # 3 LawRefBook-only laws
        for law_id in ("保险法", "证券法", "海商法"):
            (lrb / f"{law_id}.md").write_text(f"LRB:{law_id}", encoding="utf-8")
        return ws, lrb

    def test_end_to_end_merge(self, tmp_path: Path):
        ws, lrb = self._populate_sources(tmp_path)
        out = tmp_path / "merged"
        report = run_merge(wikisource_dir=ws, lawrefbook_dir=lrb, output_dir=out)

        # Total: 4 ws-only + 2 overlap (lrb wins) + 3 lrb-only = 9
        assert report.total_output == 9
        assert report.from_wikisource == 4
        assert report.from_lawrefbook == 5  # 2 overlap + 3 lrb-only
        assert set(report.overlapping_law_ids) == {"公司法", "刑法"}
        assert set(report.wikisource_only_law_ids) == {
            "民法典",
            "行政复议法",
            "行政诉讼法",
            "工伤保险条例",
        }
        assert report.written == 9
        assert report.skipped == 0

        # Overlap laws come from LawRefBook
        assert (out / "公司法.md").read_text(encoding="utf-8") == "LRB:公司法 2023"
        assert (out / "刑法.md").read_text(encoding="utf-8") == "LRB:刑法 最新"
        # Wikisource gap laws survive
        assert (out / "民法典.md").read_text(encoding="utf-8") == "WS:民法典"
        assert (out / "行政复议法.md").read_text(encoding="utf-8") == "WS:行政复议法"

    def test_raises_when_both_sources_empty(self, tmp_path: Path):
        ws = tmp_path / "ws"
        lrb = tmp_path / "lrb"
        ws.mkdir()
        lrb.mkdir()
        out = tmp_path / "merged"
        with pytest.raises(SystemExit):
            run_merge(wikisource_dir=ws, lawrefbook_dir=lrb, output_dir=out)

    def test_tolerates_missing_source_dir(self, tmp_path: Path):
        """If only one source exists (e.g., LawRefBook fetched but Wikisource
        not yet), the merge should still succeed."""
        lrb = tmp_path / "lrb"
        lrb.mkdir()
        (lrb / "公司法.md").write_text("LRB only", encoding="utf-8")
        out = tmp_path / "merged"
        report = run_merge(
            wikisource_dir=tmp_path / "missing",
            lawrefbook_dir=lrb,
            output_dir=out,
        )
        assert report.total_output == 1
        assert (out / "公司法.md").read_text(encoding="utf-8") == "LRB only"

    def test_skipped_files_when_existing_and_no_force(self, tmp_path: Path):
        ws, lrb = self._populate_sources(tmp_path)
        out = tmp_path / "merged"
        out.mkdir()
        (out / "公司法.md").write_text("PRESERVE ME", encoding="utf-8")
        report = run_merge(wikisource_dir=ws, lawrefbook_dir=lrb, output_dir=out, force=False)
        # 1 file skipped (公司法), 8 written
        assert report.skipped == 1
        assert report.written == 8
        assert (out / "公司法.md").read_text(encoding="utf-8") == "PRESERVE ME"
