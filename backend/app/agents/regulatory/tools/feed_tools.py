"""Feed tools — deterministic fetch + provenance-enforced reg-item writes.

Review decision C2 (AI trust boundary): ``save_reg_item`` does NOT trust the
model's claimed source. An item is only accepted with its given source_tag /
status_verified if its dedup_key or link was actually returned by
``fetch_reg_feeds`` THIS session (recorded in ``ctx.deps.fetched_provenance``).
Otherwise it is force-stamped ``[模型知识—需验证]`` + ``status_verified=False``
so a fabricated regulation can never silently enter the monitoring hub.
"""

from pydantic_ai import RunContext

from app.agents.regulatory.deps import RegulatoryDeps
from app.agents.regulatory.tools._validators import normalize_item_type, normalize_materiality
from app.repositories import regulatory_comment_repo, regulatory_reg_item_repo

_UNVERIFIED_TAG = "[模型知识—需验证]"


def fetch_reg_feeds(ctx: RunContext[RegulatoryDeps]) -> str:
    """确定性抓取已配置的 RSS/Atom/JSON 源（无 LLM），返回候选事项。

    抓取结果的 dedup_key / link 记入本会话溯源集（C2），供 save_reg_item 校验。
    HTML-only 源标记"需手动录入"（v1 不自动抓）。

    Returns:
        Markdown 候选事项列表，或覆盖薄弱/抓取失败的诚实报告。
    """
    try:
        from app.tasks import regulatory_feed_fetcher
    except ImportError:
        return (
            "## feed 抓取层尚未就绪\n\n"
            "自动抓取在 Phase 4 落地。当前可由用户在「手动粘贴」处录入法规文本，"
            "或稍后重试。**不要用模型记忆补充法规。**"
        )

    profile_repo_result = regulatory_feed_fetcher.fetch_for_user(
        ctx.deps.db, user_id=ctx.deps.user_id
    )
    candidates = profile_repo_result.candidates
    # C2: 记录本会话真实抓取到的溯源标识
    for c in candidates:
        if c.get("dedup_key"):
            ctx.deps.fetched_provenance.add(str(c["dedup_key"]))
        if c.get("link"):
            ctx.deps.fetched_provenance.add(str(c["link"]))

    if not candidates:
        return (
            "## 抓取完成，未发现新事项\n\n"
            f"源健康：{profile_repo_result.ok_count}/{profile_repo_result.total_count} 成功"
            + (
                f"，失败：{', '.join(profile_repo_result.errored_sources)}"
                if profile_repo_result.errored_sources
                else ""
            )
            + "\n\n**不得静默填补**——如覆盖不足，请用户扩窗/换源/粘贴，由律师定。"
        )

    lines = [
        f"## 抓取到 {len(candidates)} 条候选（源健康："
        f"{profile_repo_result.ok_count}/{profile_repo_result.total_count} 成功"
        + (
            f"，失败：{', '.join(profile_repo_result.errored_sources)}）"
            if profile_repo_result.errored_sources
            else "）"
        )
    ]
    for c in candidates:
        lines.append(
            f"- **{c.get('title', '（无标题）')}** | {c.get('regulator', '—')} | "
            f"类型 {c.get('item_type', 'other')} | {c.get('source_tag', '—')} | "
            f"dedup_key={c.get('dedup_key', '—')}"
        )
    return "\n".join(lines)


def save_reg_item(
    ctx: RunContext[RegulatoryDeps],
    title: str,
    regulator: str,
    item_type: str,
    summary: str,
    *,
    materiality: str | None = None,
    relevance_hook: str | None = None,
    link: str | None = None,
    source_tag: str | None = None,
    source_name: str | None = None,
    dedup_key: str | None = None,
) -> str:
    """保存/精化一条法规动态事项（C2 溯源强制）。

    Args:
        title: 标题。
        regulator: 发布监管机构。
        item_type: regulation/normative/nprm/pre_rule/enforcement/guidance/speech/settlement/other。
        summary: 一行摘要。
        materiality: always/review/fyi（默认 review — A2）。
        relevance_hook: 关联性钩子。
        link / source_tag / source_name / dedup_key: 来源溯源。

    Returns:
        确认信息（含是否被降级为未验证）。
    """
    item_type_n = normalize_item_type(item_type)
    materiality_n = normalize_materiality(materiality)

    # C2: 溯源校验 —— 仅当 dedup_key 或 link 在本会话真实抓取集中，才信任声明的来源。
    provenance_ok = bool(
        (dedup_key and dedup_key in ctx.deps.fetched_provenance)
        or (link and link in ctx.deps.fetched_provenance)
    )
    if provenance_ok:
        final_tag = source_tag or "[联网检索—需复核]"
        status_verified = False  # 抓取到不等于法规现行有效已核实
        downgraded = False
    else:
        final_tag = _UNVERIFIED_TAG
        status_verified = False
        downgraded = True

    item = regulatory_reg_item_repo.create(
        ctx.deps.db,
        user_id=ctx.deps.user_id,
        title=title,
        regulator=regulator,
        item_type=item_type_n,
        materiality=materiality_n,
        materiality_source="llm",
        summary=summary,
        relevance_hook=relevance_hook,
        link=link,
        source_tag=final_tag,
        source_name=source_name,
        dedup_key=dedup_key,
        status_verified=status_verified,
        status="triaged",
    )
    note = (
        f"已保存事项（id={item.id}，重要度={materiality_n}）。"
        if not downgraded
        else (
            f"⚠️ 该事项未匹配本会话抓取结果，已强制标记 {_UNVERIFIED_TAG} + 未验证"
            f"（id={item.id}）。请勿将其当作已核实法规。"
        )
    )
    return note


def save_comment_period(
    ctx: RunContext[RegulatoryDeps],
    regulation: str,
    regulator: str,
    summary: str,
    comment_deadline: str,
    *,
    reg_item_id: str | None = None,
    link: str | None = None,
    owner: str | None = None,
) -> str:
    """识别征求意见稿 → 写 regulatory_comments + comment_deadline（decision=undecided）。

    Args:
        comment_deadline: 截止日期 YYYY-MM-DD。

    Returns:
        确认信息。
    """
    from datetime import date

    try:
        deadline = date.fromisoformat(comment_deadline.strip())
    except (ValueError, AttributeError):
        return f"## 截止日期格式错误\n\n`{comment_deadline}` 不是 YYYY-MM-DD，请确认后重试。"

    comment = regulatory_comment_repo.create(
        ctx.deps.db,
        user_id=ctx.deps.user_id,
        reg_item_id=reg_item_id or ctx.deps.reg_item_id,
        regulation=regulation,
        regulator=regulator,
        summary=summary,
        link=link,
        comment_deadline=deadline,
        detected=date.today(),
        decision="undecided",
        owner=owner,
    )
    return f"已登记意见征集（id={comment.id}，截止 {deadline.isoformat()}，决策待定）。"
