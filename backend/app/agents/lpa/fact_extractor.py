"""
Stage 2: Fact Extractor — follows learn-claude-code tool-dispatch pattern.

Two-pass extraction:
  Pass 1 — regex scan → raw_facts  (zero-cost, no LLM)
  Pass 2 — LLM(V3) agent-loop with registered tool → labeled_facts
"""

import json
import logging
import re
from collections.abc import Callable
from typing import Any

from .llm_client import LLMClient

logger = logging.getLogger(__name__)

# ── Pass 1 regex patterns (generic, not LPA-specific) ────────────────────

AMOUNT_RE = re.compile(
    r"(?:人民币|RMB|CNY|港币|HKD|美元|USD|欧元|EUR)?[  ]*"
    r"([\d,]+(?:\.\d+)?)[  ]*(?:万[亿千百]?|[亿千百]?万?)?[  ]*(?:元|美元|港元|欧元|人民币)",
    re.IGNORECASE,
)
PERCENT_RE = re.compile(r"([\d]+(?:\.[\d]+)?)[  ]*(?:%|[百千]分之[一二三四五六七八九十\d]+)")
CHINESE_PERCENT_RE = re.compile(r"[百千]分之[一二三四五六七八九十\d]+")
DATE_RE = re.compile(
    r"(?:\d{4}[  ]*年[  ]*\d{1,2}[  ]*月[  ]*\d{1,2}[  ]*日)"
    r"|(?:\d{4}[-/]\d{1,2}[-/]\d{1,2})"
    r"|(?:\d{1,2}[  ]*个[  ]*月)"
    r"|(?:\d+[  ]*(?:个)?[  ]*(?:营业|工作|日历|自然)?日[  ]*(?:内|后|前)?)",
)
LAW_REFERENCE_RE = re.compile(r"《([^》]+)》")

# Default LPA entity patterns (backward compatibility)
_DEFAULT_ENTITY_PATTERNS = [
    r"(?:甲方|乙方|普通合伙人|有限合伙人|管理人|执行事务合伙人)[：:  ]*"
    r"([^\n。，；;]{4,60}(?:有限公司|股份有限公司|合伙企业|有限责任合伙|LLP|Ltd\.?|Inc\.?))",
]

# Default LPA GP/manager patterns (backward compatibility)
_DEFAULT_GP_MANAGER_PATTERNS = [
    re.compile(r"普通合伙人[：:  ]*([^\n。，]{4,60})"),
    re.compile(r"执行事务合伙人[：:  ]*([^\n。，]{4,60})"),
    re.compile(r"管理人[：:  ]*([^\n。，]{4,60})"),
    re.compile(r"GP[：:  ]*([^\n。，]{4,60})", re.IGNORECASE),
]


# Default LPA fact tool handler (backward compatibility)
def _default_handle_label_facts(**kwargs: Any) -> str:
    """Tool handler: receives labeled facts and returns them as JSON."""
    facts = {k: v for k, v in kwargs.items() if v is not None}
    return json.dumps(facts, ensure_ascii=False)


# Default LPA tool name
_DEFAULT_TOOL_NAME = "label_lpa_facts"


class FactExtractor:
    """Extract and label hard facts from a document — regex scan + LLM tool-call."""

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        entity_patterns: list[str] | None = None,
        fact_tool_schema: dict | None = None,
        fact_tool_handler: Callable[..., str] | None = None,
        fact_tool_name: str | None = None,
        prompt_template_path: str | None = None,
    ):
        self._llm = llm_client
        self._entity_patterns = entity_patterns or _DEFAULT_ENTITY_PATTERNS
        self._entity_re = re.compile("|".join(self._entity_patterns), re.IGNORECASE)
        self._gp_manager_patterns = _DEFAULT_GP_MANAGER_PATTERNS
        self._fact_tool_schema = fact_tool_schema
        self._fact_tool_handler = fact_tool_handler or _default_handle_label_facts
        self._fact_tool_name = fact_tool_name or _DEFAULT_TOOL_NAME
        self._prompt_template_path = prompt_template_path

        # Register tool on the LLM client instance if schema is provided
        if self._llm and self._fact_tool_schema:
            self._llm.register_tool(
                name=self._fact_tool_name,
                description=f"Label raw facts extracted from a {self._fact_tool_name} document",
                input_schema=self._fact_tool_schema,
                handler=self._fact_tool_handler,
            )

    def extract(self, document_text: str, early_chapters: str | None = None) -> dict[str, Any]:
        raw = self.extract_raw(document_text)
        source = early_chapters or document_text
        labeled = self.label_facts(raw, source)
        return {"raw_facts": raw, "labeled_facts": labeled}

    def extract_raw(self, text: str) -> dict[str, Any]:
        """Pass 1: regex scan — zero LLM cost."""
        amounts = [m.group(0).strip() for m in AMOUNT_RE.finditer(text)]
        percents = [m.group(0).strip() for m in PERCENT_RE.finditer(text)]
        percents.extend(CHINESE_PERCENT_RE.findall(text))
        dates = list({m.group(0).strip() for m in DATE_RE.finditer(text)})
        entities = []
        for m in self._entity_re.finditer(text):
            entities.append(m.group(1).strip())
        gp_candidates = []
        for pat in self._gp_manager_patterns:
            for m in pat.finditer(text):
                gp_candidates.append(m.group(1).strip())
        law_refs = list({m.group(1).strip() for m in LAW_REFERENCE_RE.finditer(text)})

        return {
            "amounts": amounts[:40],
            "percentages": percents[:30],
            "dates": dates[:30],
            "entity_names": list(dict.fromkeys(entities)),
            "gp_manager_candidates": list(dict.fromkeys(gp_candidates)),
            "law_references": list(dict.fromkeys(law_refs)),
        }

    def label_facts(self, raw_facts: dict[str, Any], source_text: str) -> dict[str, Any]:
        """Pass 2: LLM(V3) agent-loop with registered label_lpa_facts tool."""
        if not self._llm:
            return self._rule_based_label(raw_facts, source_text)

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(raw_facts, source_text)

        try:
            resp = self._llm.agent_loop(
                system_prompt=system_prompt,
                user_message=user_prompt,
                model="deepseek-v4-flash",
                temperature=0.1,
                max_turns=5,
            )
            return json.loads(resp) if isinstance(resp, str) else resp
        except Exception as e:
            logger.error("LLM fact labeling failed: %s", e)
            return self._rule_based_label(raw_facts, source_text)

    def _build_system_prompt(self) -> str:
        if self._prompt_template_path:
            from pathlib import Path

            path = Path(self._prompt_template_path)
            return path.read_text(encoding="utf-8") if path.exists() else ""
        from . import prompts_dir

        path = prompts_dir() / "fact_labeling.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def _build_user_prompt(self, raw_facts: dict[str, Any], source_text: str) -> str:
        return (
            f"## 预扫描原始事实\n\n```json\n{json.dumps(raw_facts, ensure_ascii=False, indent=2)}\n```\n\n"
            f"## 合同节选\n\n{source_text}\n\n"
            f"请调用 {self._fact_tool_name} 工具标注事实。不存在的字段请省略。"
        )

    def _rule_based_label(self, raw_facts: dict[str, Any], source_text: str) -> dict[str, Any]:
        """Zero-cost label extraction when LLM is unavailable."""
        result = {}
        entities = raw_facts.get("entity_names", [])
        gp_cands = raw_facts.get("gp_manager_candidates", [])
        result["gp_name"] = gp_cands[0] if gp_cands else (entities[0] if entities else None)
        result["manager_name"] = gp_cands[1] if len(gp_cands) > 1 else result.get("gp_name")
        result["fund_name"] = entities[-1] if entities else None
        result["gp_is_manager"] = result.get("gp_name") == result.get("manager_name")

        for pct in raw_facts.get("percentages", []):
            m = re.search(r"([\d.]+)\s*%", pct)
            if not m:
                continue
            val = float(m.group(1)) / 100
            idx = source_text.find(pct)
            ctx = source_text[max(0, idx - 100) : idx + len(pct) + 100] if idx >= 0 else ""
            if any(kw in ctx for kw in ["管理费", "management fee"]):
                result["management_fee_rate"] = val
            if any(kw in ctx for kw in ["优先回报", "hurdle", "门槛收益"]):
                result["hurdle_rate"] = val
            if any(kw in ctx for kw in ["carry", "超额收益", "绩效分成", "业绩报酬"]):
                result["gp_carry"] = val

        law_refs = raw_facts.get("law_references", [])
        result["dispute_resolution"] = law_refs[0] if law_refs else None
        return {k: v for k, v in result.items() if v is not None}
