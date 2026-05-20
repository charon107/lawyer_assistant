"""
Stage 2: Fact Extractor — regex scan + LLM tool-call.

Two-pass extraction:
  Pass 1 — regex scan → raw_facts  (zero-cost, no LLM)
  Pass 2 — LLM agent-loop with registered tool → labeled_facts
"""

import json
import logging
import re
from collections.abc import Callable
from typing import Any

from app.agents.shared.llm_client import LLMClient

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
_DEFAULT_TOOL_NAME = "label_facts"


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
                description='从合同文本中提取关键事实并标注语义角色。请根据合同内容填写你能找到的字段，找不到的省略。示例：{"party_a": "XX公司", "contract_value": "100万元"}',
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
        """Pass 2: LLM agent-loop with registered tool, fallback to plain chat."""
        if not self._llm:
            raise RuntimeError(
                "未配置 AI 模型，无法提取事实。请在个人中心 → 设置中添加 LLM 提供商。"
            )

        # Template content goes into user message as context (NOT system prompt)
        template_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(raw_facts, source_text)

        # Pass 2a: agent_loop with tool calling
        # System prompt MUST instruct tool use — consistent with the registered tools
        tool_system_prompt = (
            "你是合同分析专家。你的任务是从合同文本中提取关键事实。\n"
            "请使用提供的工具来输出结果，不要直接输出 JSON 或其他文字。\n"
            "根据合同内容填写你能找到的字段，找不到的字段不要传。"
        )
        tool_user_message = f"{template_prompt}\n\n{user_prompt}"
        try:
            resp = self._llm.agent_loop(
                system_prompt=tool_system_prompt,
                user_message=tool_user_message,
                temperature=0.1,
                max_turns=2,
            )
            logger.info(
                "agent_loop returned: type=%s, len=%d, repr=%s",
                type(resp).__name__,
                len(resp or ""),
                repr((resp or "")[:100]),
            )
            if resp and resp.strip():
                try:
                    parsed = self._parse_json(resp)
                    if isinstance(parsed, dict) and parsed:
                        logger.info("agent_loop parse OK, keys=%s", list(parsed.keys()))
                        return parsed
                    logger.warning(
                        "agent_loop returned empty/non-dict result: %s", type(parsed).__name__
                    )
                except Exception as parse_err:
                    logger.warning(
                        "agent_loop parse failed: %s (resp was: %s)", parse_err, repr(resp[:200])
                    )
            else:
                logger.warning("agent_loop returned empty response")
        except Exception as e:
            logger.warning(
                "agent_loop failed (%s: %s), falling back to chat()", type(e).__name__, e
            )

        # Pass 2b: plain chat fallback — here we DO want JSON output
        try:
            logger.info("Attempting chat() fallback...")
            chat_prompt = (
                f"{template_prompt}\n\n"
                f"{user_prompt}\n\n"
                f"请直接输出 JSON 格式的事实标注结果。不要输出任何解释，只输出 JSON。"
            )
            resp = self._llm.chat(
                system_prompt="你是合同分析专家。只输出 JSON，不要输出 markdown 代码块或解释文字。",
                user_message=chat_prompt,
                temperature=0.1,
                max_tokens=8192,
            )
            logger.info(
                "chat() returned: len=%d, preview=%s", len(resp or ""), repr((resp or "")[:200])
            )
            if resp and resp.strip():
                try:
                    parsed = self._parse_json(resp)
                    if isinstance(parsed, dict):
                        logger.info("chat() parse OK, keys=%s", list(parsed.keys()))
                        return parsed
                except Exception as parse_err:
                    logger.warning("chat() parse failed: %s", parse_err)
        except Exception as e:
            logger.warning("chat() fallback also failed: %s", e)

        logger.info("Using rule-based fact labeling as final fallback")
        return self._rule_based_label(raw_facts, source_text)

    @staticmethod
    def _parse_json(text: str) -> dict:
        """Delegate to shared parse_json."""
        from app.agents.shared.json_parser import parse_json

        return parse_json(text)

    def _build_system_prompt(self) -> str:
        if self._prompt_template_path:
            from pathlib import Path

            path = Path(self._prompt_template_path)
            return path.read_text(encoding="utf-8") if path.exists() else ""
        from app.agents.shared import prompts_dir

        path = prompts_dir() / "fact_labeling.md"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def _build_user_prompt(self, raw_facts: dict[str, Any], source_text: str) -> str:
        # Truncate to avoid exceeding token limits
        max_chars = 6000
        truncated = source_text[:max_chars] + ("..." if len(source_text) > max_chars else "")
        return (
            f"## 预扫描原始事实\n\n```json\n{json.dumps(raw_facts, ensure_ascii=False, indent=2)}\n```\n\n"
            f"## 合同节选\n\n{truncated}\n\n"
            f"请调用 {self._fact_tool_name} 工具标注事实。不存在的字段请省略，不要传空值。"
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
