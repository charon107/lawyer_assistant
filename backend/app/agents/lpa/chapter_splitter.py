"""
Stage 1: Chapter Splitter — follows learn-claude-code simplicity pattern.

Three-pass strategy:
  Pass 1 — regex matching for standard chapter markers (zero-cost)
  Pass 2 — LLM fallback for irregular / unmarked headings
  Pass 3 — human-verifiable chapter list (returned to UI for approval)
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Main pattern: matches Chinese chapter/article/section headers
CHAPTER_RE = re.compile(
    r"^[  \t]*(第[一二三四五六七八九十百零\d]+[章节条])[  \t]*(.*)",
    re.MULTILINE,
)

# Pattern for "一、"、"二、" numbered sections (common in contracts)
SECTION_NUM_RE = re.compile(
    r"^[  \t]*([一二三四五六七八九十]+)[、.．][  \t]*(.*)",
    re.MULTILINE,
)

# English fallback patterns
ARTICLE_RE = re.compile(
    r"^[  \t]*(?:Article|ARTICLE|Art\.?)[  \t]+([IVXLCDM\d]+)[  \t]*[：:.\s-]*(.*)",
    re.MULTILINE | re.IGNORECASE,
)
SECTION_RE = re.compile(
    r"^[  \t]*(?:Section|SECTION|Sec\.?|§)[  \t]+(\d+)[  \t]*[：:.\s-]*(.*)",
    re.MULTILINE | re.IGNORECASE,
)

# Import from canonical source to avoid duplication
from .configs.lpa import CHAPTER_KEYWORDS as LPA_CHAPTER_KEYWORDS


class ChapterSplitter:
    """Split a parsed document into logical chapters."""

    def __init__(self, llm_client=None, chapter_keywords: list[str] | None = None):
        self._llm = llm_client
        self._chapter_keywords = chapter_keywords or LPA_CHAPTER_KEYWORDS

    def split(self, document_text: str) -> dict[str, Any]:
        chapters = self._split_by_regex(document_text)

        if not chapters or len(chapters) < 2:
            chapters = self._split_by_keyword(document_text)

        if not chapters or len(chapters) < 2:
            if self._llm:
                chapters = self._split_by_llm(document_text)
                return {"chapters": chapters, "method": "llm", "warning": None}
            return {
                "chapters": [{"index": 1, "title": "全文", "text": document_text, "start_char": 0}],
                "method": "single",
                "warning": "无法自动拆分章节",
            }

        chapters = self._merge_small_chapters(chapters)
        return {"chapters": chapters, "method": "regex", "warning": None}

    def _split_by_regex(self, text: str) -> list[dict[str, Any]]:
        """Pass 1: find all chapter markers and split between them."""
        markers: list[tuple[int, str]] = []

        for match in CHAPTER_RE.finditer(text):
            num = match.group(1)
            title = match.group(2).strip()
            full = f"{num} {title}" if title else num
            markers.append((match.start(), full))

        if not markers:
            # Try "一、" numbered sections (common in Chinese contracts)
            for match in SECTION_NUM_RE.finditer(text):
                num = match.group(1)
                title = match.group(2).strip()
                full = f"{num}、{title}" if title else f"{num}、"
                markers.append((match.start(), full))

        if not markers:
            # Try English patterns
            for pat in (ARTICLE_RE, SECTION_RE):
                for match in pat.finditer(text):
                    full = match.group(0).split("\n")[0].strip()
                    markers.append((match.start(), full))
                if markers:
                    break

        if not markers:
            return []

        markers.sort(key=lambda x: x[0])

        chapters = []
        for i, (pos, title) in enumerate(markers):
            next_pos = markers[i + 1][0] if i + 1 < len(markers) else len(text)
            chapter_text = text[pos:next_pos].strip()

            # Skip TOC/preamble fragments (very short chapters at the start)
            if len(chapter_text) < 100 and i < 2:
                continue

            chapters.append(
                {
                    "index": len(chapters) + 1,
                    "title": title,
                    "text": chapter_text,
                    "start_char": pos,
                }
            )

        return chapters

    def _split_by_keyword(self, text: str) -> list[dict[str, Any]]:
        """Heuristic: use keyword density to guess chapter boundaries."""
        lines = text.split("\n")
        boundary_indices = []

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or len(stripped) > 80:
                continue
            lower = stripped.lower()
            for kw in self._chapter_keywords:
                if kw in lower and len(stripped) >= 4:
                    boundary_indices.append(idx)
                    break

        if not boundary_indices:
            return []

        boundary_indices = sorted(set(boundary_indices))
        chapters = []
        for i, line_idx in enumerate(boundary_indices):
            char_start = sum(len(l) + 1 for l in lines[:line_idx])
            next_idx = boundary_indices[i + 1] if i + 1 < len(boundary_indices) else len(lines)
            next_char = sum(len(l) + 1 for l in lines[:next_idx])
            chapters.append(
                {
                    "index": i + 1,
                    "title": lines[line_idx].strip(),
                    "text": text[char_start:next_char].strip(),
                    "start_char": char_start,
                }
            )
        return chapters

    def _split_by_llm(self, text: str) -> list[dict[str, Any]]:
        """Pass 2: LLM fallback for irregular formats."""
        from . import prompts_dir

        prompt_path = prompts_dir() / "chapter_split.md"
        base = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
        prompt = f"{base}\n\n## 合同全文（首 12000 字）\n{text[:12000]}"

        try:
            resp = self._llm(prompt)
            data = json.loads(resp) if isinstance(resp, str) else resp
            raw = data.get("chapters", [])
        except Exception as e:
            logger.error("LLM chapter split failed: %s", e)
            return []

        chapters = []
        for item in raw:
            s = item.get("start_char", item.get("start_line", 0))
            e = item.get("end_char", item.get("end_line", len(text)))
            if isinstance(s, int) and isinstance(e, int) and s < len(text):
                chapters.append(
                    {
                        "index": item.get("index", len(chapters) + 1),
                        "title": item.get("title", f"第{len(chapters) + 1}章"),
                        "text": text[s:e].strip(),
                        "start_char": s,
                    }
                )
        return chapters

    @staticmethod
    def _merge_small_chapters(
        chapters: list[dict[str, Any]], min_chars: int = 80
    ) -> list[dict[str, Any]]:
        """Merge chapters that are too small into the next chapter."""
        if len(chapters) <= 1:
            return chapters

        merged = []
        i = 0
        while i < len(chapters):
            ch = chapters[i]
            if len(ch["text"]) < min_chars and i + 1 < len(chapters):
                next_ch = chapters[i + 1]
                merged.append(
                    {
                        "index": len(merged) + 1,
                        "title": f"{ch['title']}、{next_ch['title']}",
                        "text": ch["text"] + "\n\n" + next_ch["text"],
                        "start_char": ch["start_char"],
                    }
                )
                i += 2
            else:
                merged.append(
                    {
                        "index": len(merged) + 1,
                        "title": ch["title"],
                        "text": ch["text"],
                        "start_char": ch["start_char"],
                    }
                )
                i += 1

        return merged
