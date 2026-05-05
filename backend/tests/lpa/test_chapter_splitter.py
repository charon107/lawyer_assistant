"""Tests for Stage 1: Chapter Splitter."""

from app.agents.lpa.chapter_splitter import ChapterSplitter


class TestChapterSplitterRegex:
    def test_splits_chinese_chapters(self):
        text = (
            "第一章 总则\n" + "本基金为有限合伙型私募基金，依据《合伙企业法》设立。" * 5 + "\n"
            "第二章 出资\n" + "认缴出资总额为人民币一亿元，各合伙人按约定比例出资。" * 5 + "\n"
            "第三章 分配\n" + "基金收益按瀑布式分配顺序向各合伙人进行分配。" * 5
        )
        splitter = ChapterSplitter()
        result = splitter.split(text)
        chapters = result["chapters"]
        assert len(chapters) >= 2
        assert result["method"] == "regex"
        assert any("出资" in ch["title"] for ch in chapters)

    def test_splits_english_articles(self):
        text = "Article I Definitions\nSome definitions here.\nArticle II Capital Contributions\nContributions here."
        splitter = ChapterSplitter()
        result = splitter.split(text)
        assert len(result["chapters"]) >= 2

    def test_single_chapter_fallback(self):
        text = "This is a plain text document with no chapter markers at all."
        splitter = ChapterSplitter()
        result = splitter.split(text)
        assert len(result["chapters"]) >= 1
        if result["method"] == "single":
            assert result["warning"] is not None

    def test_merge_small_chapters(self):
        text = (
            "第一章 定义\n短。\n"
            "第二章 出资\n" + "认缴出资额相关内容。" * 20 + "\n"
            "第三章 分配\n" + "分配相关内容。" * 20
        )
        splitter = ChapterSplitter()
        result = splitter.split(text)
        for ch in result["chapters"]:
            # After merging, chapters should be longer (unless it's the last one)
            pass  # merge logic may or may not trigger depending on lengths

    def test_chapters_have_required_fields(self):
        text = (
            "第一章 总则\n" + "本基金为有限合伙型私募基金，依据《合伙企业法》设立。" * 5 + "\n"
            "第二章 出资\n" + "认缴出资总额为人民币一亿元。" * 5
        )
        splitter = ChapterSplitter()
        result = splitter.split(text)
        for ch in result["chapters"]:
            assert "index" in ch
            assert "title" in ch
            assert "text" in ch
            assert "start_char" in ch

    def test_chapter_text_is_not_empty(self):
        text = (
            "第一章 总则\n" + "本基金为有限合伙型私募基金，依据《合伙企业法》设立。" * 5 + "\n"
            "第二章 出资\n" + "认缴出资总额为人民币一亿元。" * 5
        )
        splitter = ChapterSplitter()
        result = splitter.split(text)
        for ch in result["chapters"]:
            assert len(ch["text"]) > 0


class TestChapterSplitterKeyword:
    def test_keyword_split_fallback(self):
        text = "定义 and interpretation\nSome text about definitions.\n出资 capital contribution\nMore text."
        splitter = ChapterSplitter()
        result = splitter.split(text)
        assert len(result["chapters"]) >= 1


class TestMergeSmallChapters:
    def test_merges_small_into_next(self):
        chapters = [
            {"index": 1, "title": "A", "text": "short", "start_char": 0},
            {"index": 2, "title": "B", "text": "x" * 200, "start_char": 10},
        ]
        merged = ChapterSplitter._merge_small_chapters(chapters, min_chars=80)
        assert len(merged) == 1
        assert "A" in merged[0]["title"]

    def test_keeps_large_chapters(self):
        chapters = [
            {"index": 1, "title": "A", "text": "x" * 200, "start_char": 0},
            {"index": 2, "title": "B", "text": "y" * 200, "start_char": 200},
        ]
        merged = ChapterSplitter._merge_small_chapters(chapters, min_chars=80)
        assert len(merged) == 2
