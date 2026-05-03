"""
Stage 3: Chapter Reviewer — follows learn-claude-code agent-loop pattern.

Complexity-classified review with tool dispatch:
  simple   → V3 fast chat (no tools)
  complex  → R1 deep reasoning (no tools, thinks internally)
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .llm_client import LLMClient, register_tool
from .risk_rules import LPA_RULES, LPA_RULE_IDS_BY_CATEGORY

logger = logging.getLogger(__name__)

# Keywords that flag a chapter as complex
COMPLEX_KEYWORDS = [
    "管理费", "management fee",
    "分配", "distribution", "waterfall",
    "出资", "capital contribution", "capital commitment",
    "普通合伙人", "general partner",
    "关联交易", "related party", "conflict of interest",
    "除名", "removal", "termination",
    "key man", "关键人士",
    "转让", "transfer", "退伙", "withdrawal",
    "违约责任", "default", "indemnification",
    "解散", "清算", "dissolution", "liquidation",
    "投资限制",
]

SIMPLE_RULE_IDS = {"A1", "A4", "A5", "D6", "D8"}
COMPLEX_RULE_IDS = {"A2", "A3", "B1", "B2", "B3", "B4", "B5", "D1", "D2", "D3", "D4", "D5", "D7"}


class ChapterReviewer:
    """Review individual LPA chapters with complexity-aware model selection."""

    V3_MODEL = "deepseek-chat"
    R1_MODEL = "deepseek-reasoner"

    def __init__(self, llm_client: LLMClient, labeled_facts: Dict[str, Any]):
        self._llm = llm_client
        self._labeled_facts = labeled_facts

    def review(self, chapter: Dict[str, Any]) -> Dict[str, Any]:
        title = chapter.get("title", "")
        text = chapter.get("text", "")
        complexity = self.classify_complexity(title, text)

        logger.info("Reviewing [%s] '%s' (%d chars)", complexity, title, len(text))

        if complexity == "complex":
            findings = self._review_complex(title, text)
        else:
            findings = self._review_simple(title, text)

        return {"chapter": title, "complexity": complexity, "findings": findings}

    @staticmethod
    def classify_complexity(title: str, text: str) -> str:
        combined = (title + " " + text[:500]).lower()
        for kw in COMPLEX_KEYWORDS:
            if kw in combined:
                return "complex"
        return "simple"

    def _review_simple(self, title: str, text: str) -> List[Dict[str, Any]]:
        """One-shot V3 review for simple chapters."""
        system_prompt = self._build_prompt("simple")
        user_prompt = self._build_chapter_prompt(title, text)

        try:
            resp = self._llm.chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=self.V3_MODEL,
                temperature=0.1,
            )
            data = self._parse_json(resp)
            return self._validate_findings(data.get("findings", []), SIMPLE_RULE_IDS)
        except Exception as e:
            logger.error("Simple review failed for '%s': %s", title, e)
            return []

    def _review_complex(self, title: str, text: str) -> List[Dict[str, Any]]:
        """R1 deep review for complex chapters."""
        system_prompt = self._build_prompt("complex")
        user_prompt = self._build_chapter_prompt(title, text)

        try:
            resp = self._llm.chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=self.R1_MODEL,
                temperature=0.1,
                max_tokens=8192,
            )
            data = self._parse_json(resp)
            return self._validate_findings(data.get("findings", []), COMPLEX_RULE_IDS.union(SIMPLE_RULE_IDS))
        except Exception as e:
            logger.error("R1 review failed for '%s': %s; falling back to V3", title, e)
            return self._review_simple(title, text)

    def _build_prompt(self, level: str) -> str:
        name = f"{level}_review.md"
        from . import prompts_dir
        path = prompts_dir() / name
        template = path.read_text(encoding="utf-8") if path.exists() else ""
        return template.replace("{labeled_facts}", json.dumps(self._labeled_facts, ensure_ascii=False, indent=2))

    def _build_chapter_prompt(self, title: str, text: str) -> str:
        limit = 8000 if len(text) > 8000 else 6000
        return f"## {title}\n\n{text[:limit]}\n\n请按 JSON schema 输出审查结果。"

    @staticmethod
    def _parse_json(text: str) -> dict:
        text = text.strip()
        if "```" in text:
            blocks = re.findall(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
            if blocks:
                text = blocks[0]
        return json.loads(text)

    @staticmethod
    def _validate_findings(findings: List[Dict], allowed_ids: set) -> List[Dict[str, Any]]:
        out = []
        for f in findings:
            if not isinstance(f, dict):
                continue
            rid = f.get("rule_id", "")
            if rid not in allowed_ids:
                continue
            out.append({
                "rule_id": rid,
                "level": f.get("level", "未发现问题"),
                "finding": f.get("finding", ""),
                "evidence": f.get("evidence", ""),
                "suggestion": f.get("suggestion", ""),
            })
        return out
