"""
Stage 3: Chapter Reviewer — follows learn-claude-code agent-loop pattern.

Complexity-classified review with tool dispatch:
  simple   → V3 fast chat (no tools)
  complex  → R1 deep reasoning (no tools, thinks internally)
"""

import json
import logging
import re
from typing import Any

from .llm_client import LLMClient

logger = logging.getLogger(__name__)

# Keywords that flag a chapter as complex (backward compatibility)
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

# Backward compatibility aliases
SIMPLE_RULE_IDS = {"A1", "A4", "A5", "D6", "D8"}
COMPLEX_RULE_IDS = {"A2", "A3", "B1", "B2", "B3", "B4", "B5", "D1", "D2", "D3", "D4", "D5", "D7"}


class ChapterReviewer:
    """Review individual chapters with complexity-aware model selection."""

    V3_MODEL = "deepseek-v4-flash"
    R1_MODEL = "deepseek-v4-pro"

    def __init__(
        self,
        llm_client: LLMClient,
        labeled_facts: dict[str, Any],
        rules: dict[str, Any] | None = None,
        complex_keywords: list[str] | None = None,
        simple_rule_ids: set[str] | None = None,
        complex_rule_ids: set[str] | None = None,
        rule_keyword_map: dict[str, list[str]] | None = None,
        prompt_templates: dict[str, str] | None = None,
    ):
        self._llm = llm_client
        self._labeled_facts = labeled_facts
        self._rules = rules
        self._complex_keywords = complex_keywords or COMPLEX_KEYWORDS
        self._simple_rule_ids = simple_rule_ids or SIMPLE_RULE_IDS
        self._complex_rule_ids = complex_rule_ids or COMPLEX_RULE_IDS
        self._rule_keyword_map = rule_keyword_map or {}
        self._prompt_templates = prompt_templates or {}

    def review(self, chapter: dict[str, Any]) -> dict[str, Any]:
        title = chapter.get("title", "")
        text = chapter.get("text", "")
        complexity = self.classify_complexity(title, text, self._complex_keywords)

        logger.info("Reviewing [%s] '%s' (%d chars)", complexity, title, len(text))

        if complexity == "complex":
            findings = self._review_complex(title, text)
        else:
            findings = self._review_simple(title, text)

        return {"chapter": title, "complexity": complexity, "findings": findings}

    @staticmethod
    def classify_complexity(title: str, text: str, complex_keywords: list[str] | None = None) -> str:
        keywords = complex_keywords or COMPLEX_KEYWORDS
        combined = (title + " " + text[:500]).lower()
        for kw in keywords:
            if kw in combined:
                return "complex"
        return "simple"

    def _review_simple(self, title: str, text: str) -> list[dict[str, Any]]:
        """One-shot V3 review for simple chapters."""
        system_prompt = self._build_prompt("simple")
        user_prompt = self._build_chapter_prompt(title, text)

        try:
            resp = self._llm.chat(
                system_prompt=system_prompt,
                user_message=user_prompt,
                model=self.V3_MODEL,
                temperature=0.1,
            )
            data = self._parse_json(resp)
            return self._validate_findings(data.get("findings", []), self._simple_rule_ids)
        except Exception as e:
            logger.error("Simple review failed for '%s': %s", title, e)
            return [{
                "rule_id": "ERROR",
                "level": "审查失败",
                "finding": f"本章节审查过程中出现技术错误: {str(e)[:100]}",
                "evidence": "",
                "suggestion": "请人工审查本章节",
            }]

    def _review_complex(self, title: str, text: str) -> list[dict[str, Any]]:
        """R1 deep review for complex chapters."""
        system_prompt = self._build_prompt("complex")
        user_prompt = self._build_chapter_prompt(title, text)

        try:
            resp = self._llm.chat(
                system_prompt=system_prompt,
                user_message=user_prompt,
                model=self.R1_MODEL,
                temperature=0.1,
                max_tokens=8192,
            )
            data = self._parse_json(resp)
            return self._validate_findings(data.get("findings", []), self._complex_rule_ids.union(self._simple_rule_ids))
        except Exception as e:
            logger.error("R1 review failed for '%s': %s; falling back to V3", title, e)
            return self._review_simple(title, text)

    def _build_prompt(self, level: str) -> str:
        template_key = f"{level}_review"
        template_path = self._prompt_templates.get(template_key)
        if template_path:
            from pathlib import Path
            path = Path(template_path)
            template = path.read_text(encoding="utf-8") if path.exists() else ""
        else:
            name = f"{level}_review.md"
            from . import prompts_dir
            path = prompts_dir() / name
            template = path.read_text(encoding="utf-8") if path.exists() else ""
        return template.replace("{labeled_facts}", json.dumps(self._labeled_facts, ensure_ascii=False, indent=2))

    def _build_chapter_prompt(self, title: str, text: str) -> str:
        return f"## {title}\n\n{text}\n\n请按 JSON schema 输出审查结果。"

    @staticmethod
    def _parse_json(text: str) -> dict:
        text = text.strip()
        if "```" in text:
            blocks = re.findall(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
            if blocks:
                text = blocks[0]
        return json.loads(text)

    @staticmethod
    def _validate_findings(findings: list[dict], allowed_ids: set) -> list[dict[str, Any]]:
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
