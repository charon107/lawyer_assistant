"""Law text parser — extracts articles from markdown law documents.

Supports LawRefBook/Laws markdown format:
  # 法律名称
  ## 第一章 章名
  ### 第一节 节名
  第一条 条文内容...
  第二条 条文内容...
"""

import logging
import re

from app.services.law_data.models import LawDoc, RawArticle

logger = logging.getLogger(__name__)

# Matches article headers: 第一条, 第二条, 第一百二十三条, 第一条之一
ARTICLE_RE = re.compile(
    r"^第([一二三四五六七八九十百千零]+)条(?:之([一二三四五六七八九十百千零]+))?\s+",
    re.MULTILINE,
)

# Matches chapter headers: ## 第一章 总则
CHAPTER_RE = re.compile(
    r"^##\s+第([一二三四五六七八九十百千零]+)(编|章)\s*(.*)$",
    re.MULTILINE,
)

# Matches section headers: ### 第一节 一般规定
SECTION_RE = re.compile(
    r"^###\s+第([一二三四五六七八九十百千零]+)节\s*(.*)$",
    re.MULTILINE,
)

# Matches the top-level title: # 法律名称
TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)

# Category mapping for well-known laws
CATEGORY_MAP: dict[str, tuple[str, str | None]] = {
    "民法典": ("民法", None),
    "劳动法": ("劳动法", None),
    "劳动合同法": ("劳动法", None),
    "公司法": ("商法", "公司"),
    "合伙企业法": ("商法", "合伙"),
    "著作权法": ("知识产权", "著作权"),
    "专利法": ("知识产权", "专利"),
    "商标法": ("知识产权", "商标"),
    "保守国家秘密法": ("保密法", None),
    "保密法": ("保密法", None),
    "行政许可法": ("行政法", None),
    "行政处罚法": ("行政法", None),
    "刑法": ("刑法", None),
    "社会保险法": ("社会法", None),
    "就业促进法": ("社会法", None),
}


def _cn_to_int(s: str) -> int:
    """Convert Chinese numeral string to integer."""
    cn_nums = {
        "零": 0,
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
    }
    result = 0
    unit = 0
    wan = 0
    for ch in s:
        if ch == "万":
            wan = (wan + result + (unit or 0)) * 10000
            result = 0
            unit = 0
        elif ch == "千":
            result = (result + unit) * 1000
            unit = 0
        elif ch == "百":
            result = (result + unit) * 100
            unit = 0
        elif ch == "十":
            if result == 0 and unit == 0:
                unit = 1
            result = (result + unit) * 10
            unit = 0
        else:
            unit = cn_nums.get(ch, 0)
    return wan + result + unit


def _extract_article_id(text: str) -> str:
    """Extract article ID string like '第一条' from matched text."""
    m = ARTICLE_RE.match(text)
    if not m:
        return ""
    main = _cn_to_int(m.group(1))
    suffix = m.group(2)
    if suffix:
        return f"第{_int_to_cn(main)}条之{_int_to_cn(_cn_to_int(suffix))}"
    return f"第{_int_to_cn(main)}条"


def _int_to_cn(n: int) -> str:
    """Convert integer to Chinese numeral string."""
    if n == 0:
        return "零"
    units = ["", "十", "百", "千"]
    digits = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
    result = ""
    s = str(n)
    length = len(s)
    for i, ch in enumerate(s):
        d = int(ch)
        pos = length - i - 1
        if d == 0:
            if result and not result.endswith("零"):
                result += "零"
        else:
            result += digits[d] + units[pos]
    return result.rstrip("零")


def _guess_law_id(text: str) -> str:
    """Extract law short ID from the markdown title."""
    m = TITLE_RE.search(text)
    if not m:
        return "未知法律"
    title = m.group(1).strip()
    # Remove common prefixes
    for prefix in ["中华人民共和国", "中华民国"]:
        if title.startswith(prefix):
            title = title[len(prefix) :]
    return title


def _lookup_category(law_id: str) -> tuple[str, str | None]:
    """Look up category and sub_category for a law_id."""
    return CATEGORY_MAP.get(law_id, ("其他", None))


def parse_law_text(
    text: str,
    *,
    law_id: str | None = None,
    law_name: str | None = None,
    category: str | None = None,
    sub_category: str | None = None,
    effective_date: str | None = None,
    status: str = "现行有效",
    source_type: str = "法律",
) -> LawDoc:
    """Parse law markdown text into a LawDoc with articles.

    Args:
        text: Raw markdown text of a law document.
        law_id: Override law short ID (auto-detected from title if None).
        law_name: Override law full name.
        category: Override category (auto-detected if None).
        sub_category: Override sub_category.
        effective_date: Effective date string (e.g. "2021-01-01").
        status: Law status.
        source_type: Source type (法律/行政法规/司法解释).

    Returns:
        LawDoc with parsed articles.
    """
    detected_id = law_id or _guess_law_id(text)
    detected_name = law_name or f"中华人民共和国{detected_id}"
    if category is None:
        detected_cat, detected_sub = _lookup_category(detected_id)
    else:
        detected_cat = category
        detected_sub = sub_category

    doc = LawDoc(
        law_id=detected_id,
        law_name=detected_name,
        category=detected_cat,
        sub_category=detected_sub,
        effective_date=effective_date,
        status=status,
        source_type=source_type,
    )

    # Build a list of (position, type, match) for all structural elements
    markers: list[tuple[int, str, re.Match]] = []
    for m in CHAPTER_RE.finditer(text):
        markers.append((m.start(), "chapter", m))
    for m in SECTION_RE.finditer(text):
        markers.append((m.start(), "section", m))
    for m in ARTICLE_RE.finditer(text):
        markers.append((m.start(), "article", m))
    markers.sort(key=lambda x: x[0])

    current_chapter: str | None = None
    current_section: str | None = None

    for i, (pos, kind, match) in enumerate(markers):
        if kind == "chapter":
            unit = "编" if match.group(2) == "编" else "章"
            current_chapter = (
                f"第{_int_to_cn(_cn_to_int(match.group(1)))}{unit} {match.group(3).strip()}"
            )
            current_section = None
            continue
        if kind == "section":
            current_section = (
                f"第{_int_to_cn(_cn_to_int(match.group(1)))}节 {match.group(2).strip()}"
            )
            continue
        if kind == "article":
            # Extract article content: from end of article header to next marker
            header_end = match.end()
            next_pos = markers[i + 1][0] if i + 1 < len(markers) else len(text)
            content = text[header_end:next_pos].strip()
            # Remove leading/trailing whitespace and normalize
            content = re.sub(r"\n{3,}", "\n\n", content)

            article_id_str = _extract_article_id(text[match.start() :])
            if not article_id_str:
                logger.warning("Could not extract article ID at position %d", pos)
                continue

            article = RawArticle(
                law_id=detected_id,
                law_name=detected_name,
                category=detected_cat,
                sub_category=detected_sub,
                article_id=article_id_str,
                chapter=current_chapter,
                section=current_section,
                content=content,
                effective_date=effective_date,
                status=status,
                source_type=source_type,
            )
            doc.articles.append(article)

    logger.info("Parsed %s: %d articles", detected_id, len(doc.articles))
    return doc
