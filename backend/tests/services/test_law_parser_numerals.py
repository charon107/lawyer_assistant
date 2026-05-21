"""Tests for Chinese numeral conversion in app.services.law_data.parser.

The parser needs to round-trip Chinese article numbers like ``第一千二百六十条``
(found in 民法典) through ``_cn_to_int`` and ``_int_to_cn`` without corrupting
the value and without producing non-idiomatic forms like ``一十二`` for 12.

These tests cover the silent corruption bug that produced wrong article_ids
for all articles >= 第一百一十条 before the fix.
"""

import pytest

from app.services.law_data.parser import _cn_to_int, _int_to_cn, parse_law_text


class TestCnToInt:
    """Chinese numeral → integer."""

    @pytest.mark.parametrize(
        "cn,want",
        [
            # Units
            ("零", 0),
            ("一", 1),
            ("九", 9),
            # Tens (special: bare 十 means 10)
            ("十", 10),
            ("十一", 11),
            ("十二", 12),
            ("十九", 19),
            ("二十", 20),
            ("二十三", 23),
            ("九十九", 99),
            # Hundreds
            ("一百", 100),
            ("一百零一", 101),
            ("一百一十", 110),
            ("一百二十三", 123),
            ("九百九十九", 999),
            # Thousands (covers the 民法典 1260-article range)
            ("一千", 1000),
            ("一千零一", 1001),
            ("一千零四十八", 1048),
            ("一千二百", 1200),
            ("一千二百六十", 1260),
        ],
    )
    def test_parses_canonical_chinese_numerals(self, cn: str, want: int):
        assert _cn_to_int(cn) == want


class TestIntToCn:
    """Integer → idiomatic Chinese numeral."""

    @pytest.mark.parametrize(
        "n,want",
        [
            (0, "零"),
            (1, "一"),
            (9, "九"),
            # 10-19 use bare 十, NOT 一十
            (10, "十"),
            (11, "十一"),
            (12, "十二"),
            (19, "十九"),
            # 20+ uses the leading digit
            (20, "二十"),
            (23, "二十三"),
            (99, "九十九"),
            (100, "一百"),
            (101, "一百零一"),
            (110, "一百一十"),
            (123, "一百二十三"),
            (999, "九百九十九"),
            (1000, "一千"),
            (1001, "一千零一"),
            (1048, "一千零四十八"),
            (1200, "一千二百"),
            (1260, "一千二百六十"),
        ],
    )
    def test_emits_idiomatic_chinese(self, n: int, want: str):
        assert _int_to_cn(n) == want


class TestRoundTrip:
    """cn → int → cn must round-trip across the full 民法典 article range."""

    @pytest.mark.parametrize("n", [1, 9, 10, 11, 50, 99, 100, 110, 500, 999, 1000, 1048, 1260])
    def test_int_cn_int_preserves_value(self, n: int):
        cn = _int_to_cn(n)
        assert _cn_to_int(cn) == n

    @pytest.mark.parametrize(
        "cn",
        [
            "十",
            "十二",
            "二十",
            "九十九",
            "一百一十",
            "一百二十三",
            "一千零四十八",
            "一千二百六十",
        ],
    )
    def test_cn_int_cn_preserves_canonical_form(self, cn: str):
        n = _cn_to_int(cn)
        assert _int_to_cn(n) == cn


class TestParseLawText:
    """End-to-end: a synthetic law with 4-digit article numbers must parse cleanly."""

    def test_parses_article_with_thousands_digit(self):
        text = (
            "# 中华人民共和国测试法\n\n"
            "## 第一编 总则\n\n"
            "第一条 内容一。\n\n"
            "第一千二百六十条 最后一条内容。\n\n"
            "第一千二百六十条之一 附加条款。\n"
        )
        doc = parse_law_text(text)
        assert len(doc.articles) == 3
        assert doc.articles[0].article_id == "第一条"
        assert doc.articles[1].article_id == "第一千二百六十条"
        assert doc.articles[2].article_id == "第一千二百六十条之一"

    def test_no_silent_id_corruption_for_three_digit_articles(self):
        """Regression: before the fix, 第一百一十条 was stored as 第一千零一十条."""
        text = (
            "# 中华人民共和国测试法\n\n"
            "## 第一章 总则\n\n"
            "第一百一十条 测试内容。\n\n"
            "第一百二十三条 另一条内容。\n"
        )
        doc = parse_law_text(text)
        assert [a.article_id for a in doc.articles] == [
            "第一百一十条",
            "第一百二十三条",
        ]
