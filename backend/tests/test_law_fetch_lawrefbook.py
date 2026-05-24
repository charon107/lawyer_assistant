"""Tests for app.commands.law_fetch_lawrefbook — filename parsing, dedup,
filesystem walk, and the end-to-end orchestrator with a mocked filesystem."""

from datetime import date
from pathlib import Path

import pytest

from app.commands.law_fetch_lawrefbook import (
    LawCandidate,
    _collect_candidates,
    _dedup_latest,
    _parse_filename,
    _write_output,
    run_fetch_lawrefbook,
)

# ---------------------------------------------------------------------------
# _parse_filename
# ---------------------------------------------------------------------------


class TestParseFilename:
    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("公司法.md", ("公司法", None)),
            ("公司法(2023-12-29).md", ("公司法", date(2023, 12, 29))),
            ("保守国家秘密法(2010-04-29).md", ("保守国家秘密法", date(2010, 4, 29))),
            ("公司法(2018-10-26).md", ("公司法", date(2018, 10, 26))),
            ("中华人民共和国民法典.md", ("中华人民共和国民法典", None)),
        ],
    )
    def test_parses_valid_filenames(self, filename: str, expected: tuple):
        assert _parse_filename(filename) == expected

    @pytest.mark.parametrize(
        "filename",
        ["_index.md", "法律法规模版.md", "README.md"],
    )
    def test_skips_non_law_files(self, filename: str):
        assert _parse_filename(filename) is None

    def test_returns_none_for_non_md(self):
        assert _parse_filename("公司法.txt") is None

    def test_handles_bad_date_gracefully(self):
        # Malformed date inside parens — parser falls back to no-date.
        # Our regex requires YYYY-MM-DD so a bad shape like (foo) won't match the date group.
        # Net effect: name parsing succeeds, date is None.
        result = _parse_filename("怪怪法(foo).md")
        # The regex won't match the date group (foo not YYYY-MM-DD), so the
        # whole "(foo)" is part of the name capture.
        assert result == ("怪怪法(foo)", None)


# ---------------------------------------------------------------------------
# _dedup_latest
# ---------------------------------------------------------------------------


class TestDedupLatest:
    def _cand(
        self, law_id: str, d: date | None, path: str = "x.md", cat: str = "民法商法"
    ) -> LawCandidate:
        return LawCandidate(
            law_id=law_id, effective_date=d, source_path=Path(path), npc_category=cat
        )

    def test_keeps_only_latest_dated_version(self):
        cands = [
            self._cand("公司法", date(2018, 10, 26), "old.md"),
            self._cand("公司法", date(2023, 12, 29), "new.md"),
        ]
        result = _dedup_latest(cands)
        assert len(result) == 1
        assert result[0].source_path == Path("new.md")
        assert result[0].effective_date == date(2023, 12, 29)

    def test_dated_beats_undated(self):
        cands = [
            self._cand("公司法", None, "undated.md"),
            self._cand("公司法", date(2023, 12, 29), "dated.md"),
        ]
        assert _dedup_latest(cands)[0].source_path == Path("dated.md")

    def test_independent_laws_all_kept(self):
        cands = [
            self._cand("公司法", date(2023, 12, 29)),
            self._cand("保险法", date(2015, 4, 24)),
            self._cand("劳动法", None),
        ]
        result = _dedup_latest(cands)
        assert {c.law_id for c in result} == {"公司法", "保险法", "劳动法"}

    def test_output_sorted_by_law_id(self):
        cands = [
            self._cand("专利法", None),
            self._cand("商标法", None),
            self._cand("公司法", None),
        ]
        result = _dedup_latest(cands)
        assert [c.law_id for c in result] == ["专利法", "公司法", "商标法"]

    def test_handles_three_versions(self):
        cands = [
            self._cand("某法", date(2010, 1, 1), "v1.md"),
            self._cand("某法", date(2024, 1, 1), "v3.md"),
            self._cand("某法", date(2018, 1, 1), "v2.md"),
        ]
        result = _dedup_latest(cands)
        assert len(result) == 1
        assert result[0].source_path == Path("v3.md")


# ---------------------------------------------------------------------------
# _collect_candidates — walks a fake directory tree
# ---------------------------------------------------------------------------


class TestCollectCandidates:
    def _make_tree(self, root: Path) -> None:
        """Build a minimal LawRefBook-shaped tree under ``root``."""
        for cat, files in {
            "民法商法": [
                "公司法(2018-10-26).md",
                "公司法(2023-12-29).md",
                "保险法.md",
                "_index.md",
            ],
            "行政法": ["行政许可法(2019-04-23).md", "法律法规模版.md"],
            "刑法": ["刑法.md"],
            "宪法相关法": [],  # missing files OK
            "社会法": ["劳动合同法(2012-12-28).md"],
            # 民法典/ deliberately omitted — skipped at collection time
        }.items():
            cat_dir = root / cat
            cat_dir.mkdir(parents=True)
            for filename in files:
                (cat_dir / filename).write_text("# test", encoding="utf-8")

    def test_collects_all_law_files_skipping_indexes(self, tmp_path: Path):
        self._make_tree(tmp_path)
        cands = _collect_candidates(tmp_path)
        names = {c.law_id for c in cands}
        # 4 unique law_ids (公司法 has 2 versions, both should be in candidates)
        assert names == {"公司法", "保险法", "行政许可法", "刑法", "劳动合同法"}
        # 2 versions of 公司法 in candidates BEFORE dedup
        assert sum(1 for c in cands if c.law_id == "公司法") == 2

    def test_skips_missing_category_dirs(self, tmp_path: Path):
        # Only populate 刑法; others are missing
        (tmp_path / "刑法").mkdir()
        (tmp_path / "刑法" / "刑法.md").write_text("# 刑法", encoding="utf-8")
        cands = _collect_candidates(tmp_path)
        assert [c.law_id for c in cands] == ["刑法"]

    def test_民法典_subdir_is_not_walked(self, tmp_path: Path):
        # Even if 民法典/ exists with files, _collect_candidates ignores it
        # because it's not in NPC_CATEGORIES.
        (tmp_path / "民法典").mkdir()
        (tmp_path / "民法典" / "总则.md").write_text("# 总则", encoding="utf-8")
        cands = _collect_candidates(tmp_path)
        assert all("民法典" not in str(c.source_path) for c in cands)
        assert "总则" not in {c.law_id for c in cands}


# ---------------------------------------------------------------------------
# _write_output
# ---------------------------------------------------------------------------


class TestWriteOutput:
    def _make_candidate(self, law_id: str, src_dir: Path, content: str = "# stub"):
        path = src_dir / f"{law_id}_src.md"
        path.write_text(content, encoding="utf-8")
        return LawCandidate(
            law_id=law_id, effective_date=None, source_path=path, npc_category="民法商法"
        )

    def test_writes_each_candidate_to_named_file(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        cands = [
            self._make_candidate("公司法", src, "公司法 body"),
            self._make_candidate("保险法", src, "保险法 body"),
        ]
        written, skipped = _write_output(cands, out, force=False)
        assert written == 2
        assert skipped == 0
        assert (out / "公司法.md").read_text(encoding="utf-8") == "公司法 body"
        assert (out / "保险法.md").read_text(encoding="utf-8") == "保险法 body"

    def test_skips_existing_when_not_force(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        (out / "公司法.md").write_text("old content", encoding="utf-8")
        cand = self._make_candidate("公司法", src, "new content")
        written, skipped = _write_output([cand], out, force=False)
        assert written == 0
        assert skipped == 1
        assert (out / "公司法.md").read_text(encoding="utf-8") == "old content"

    def test_overwrites_when_force(self, tmp_path: Path):
        src = tmp_path / "src"
        src.mkdir()
        out = tmp_path / "out"
        out.mkdir()
        (out / "公司法.md").write_text("old content", encoding="utf-8")
        cand = self._make_candidate("公司法", src, "new content")
        written, skipped = _write_output([cand], out, force=True)
        assert written == 1
        assert skipped == 0
        assert (out / "公司法.md").read_text(encoding="utf-8") == "new content"


# ---------------------------------------------------------------------------
# run_fetch_lawrefbook — orchestrator (with cache pre-populated)
# ---------------------------------------------------------------------------


class TestRunFetchLawRefBook:
    def _populate_cache(self, cache: Path) -> None:
        cache.mkdir(parents=True)
        # Fake a clone-like layout
        for cat, files in {
            "民法商法": {
                "公司法(2018-10-26).md": "# 2018 公司法",
                "公司法(2023-12-29).md": "# 2023 公司法",
                "保险法(2015-04-24).md": "# 保险法",
            },
            "刑法": {"刑法.md": "# 刑法 base"},
            "行政法": {"_index.md": "# index"},  # must be skipped
            "宪法相关法": {},  # empty
            "社会法": {},  # empty
        }.items():
            (cache / cat).mkdir(parents=True)
            for fname, body in files.items():
                (cache / cat / fname).write_text(body, encoding="utf-8")

    def test_end_to_end_dedup_and_write(self, tmp_path: Path):
        cache = tmp_path / "cache"
        out = tmp_path / "out"
        self._populate_cache(cache)
        # Skip the git clone by pre-populating cache; run_fetch will see it
        # exists and try `git pull` — we need to bypass that.
        run_fetch_lawrefbook(output=out, force=False, cache_dir=cache)
        # 3 unique laws after dedup: 公司法 (2023 wins), 保险法, 刑法
        actual = sorted(p.name for p in out.glob("*.md"))
        assert actual == ["保险法.md", "公司法.md", "刑法.md"]
        # 2023 公司法 should have won
        assert "2023" in (out / "公司法.md").read_text(encoding="utf-8")

    def test_raises_on_missing_cache_and_no_clone(self, tmp_path: Path, monkeypatch):
        """If cache is missing AND git clone fails, surface a clear error."""
        import subprocess

        def fake_run(args, **kwargs):
            return subprocess.CompletedProcess(
                args, returncode=1, stdout="", stderr="fake clone failure"
            )

        monkeypatch.setattr("app.commands.law_fetch_lawrefbook.subprocess.run", fake_run)
        cache = tmp_path / "never_exists"
        out = tmp_path / "out"
        with pytest.raises(SystemExit):
            run_fetch_lawrefbook(output=out, force=False, cache_dir=cache)
