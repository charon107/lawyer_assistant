"""Tests for CATEGORY_MAP coverage in app.services.law_data.parser.

Every law we explicitly fetch (see ``app.commands.law_fetch.LAW_TARGETS``)
must have a matching entry in CATEGORY_MAP — otherwise `_lookup_category`
falls back to ``("其他", None)`` and the law cannot be filtered by the
8 skill domains the agents rely on.

This is the regression net for the 2026-05-23 fix where 行政复议法,
行政诉讼法, and 工伤保险条例 were silently classified as 其他.
"""

import pytest

from app.commands.law_fetch import LAW_TARGETS
from app.services.law_data.parser import CATEGORY_MAP, _lookup_category

SKILL_DOMAINS = {"民法", "劳动法", "商法", "知识产权", "行政法", "刑法", "保密法", "社会法"}


def test_every_fetched_law_has_category_map_entry():
    """Each law_id in LAW_TARGETS must appear in CATEGORY_MAP."""
    fetched_ids = {target["law_id"] for target in LAW_TARGETS}
    missing = sorted(fetched_ids - set(CATEGORY_MAP.keys()))
    assert not missing, (
        f"These fetched laws are missing from CATEGORY_MAP and will be "
        f"classified as '其他': {missing}"
    )


def test_every_fetched_law_resolves_to_a_skill_domain():
    """Each law_id must map to one of the 8 declared skill domains."""
    bad = {}
    for target in LAW_TARGETS:
        law_id = target["law_id"]
        cat, _ = _lookup_category(law_id)
        if cat not in SKILL_DOMAINS:
            bad[law_id] = cat
    assert not bad, (
        f"These laws don't resolve to a skill domain: {bad}. "
        f"Allowed domains: {sorted(SKILL_DOMAINS)}"
    )


@pytest.mark.parametrize(
    "law_id,expected_category",
    [
        ("工伤保险条例", "社会法"),
        ("行政复议法", "行政法"),
        ("行政诉讼法", "行政法"),
    ],
)
def test_2026_05_23_categorization_regressions(law_id: str, expected_category: str):
    """The 3 laws that were silently misclassified before today's fix."""
    cat, _ = _lookup_category(law_id)
    assert cat == expected_category, (
        f"{law_id} should be classified as {expected_category}, got {cat}"
    )
