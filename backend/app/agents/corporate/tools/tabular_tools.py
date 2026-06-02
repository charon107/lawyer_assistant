"""Tabular-review write tool + Excel export for the corporate-legal agent.

`write_tabular_review` is the LAST tool a tabular-review run calls: it
persists the typed schema + extracted rows to the pre-created
`tabular_reviews` row and writes an `.xlsx` (state-coloured, with a hidden
source column per data column and a `_schema` sheet) plus a `.csv`.
"""

import csv
import json
from pathlib import Path
from typing import Any

from pydantic_ai import ModelRetry, RunContext

from app.agents.corporate.deps import CorporateDeps
from app.repositories import tabular_review_repo

# state → fill colour (answered=white, unclear/needs_review=yellow, not_present=grey)
_STATE_FILL = {
    "answered": "FFFFFFFF",
    "unclear": "FFFFF2CC",
    "needs_review": "FFFFF2CC",
    "not_present": "FFD9D9D9",
}


def _coerce_list(value: Any, field_name: str) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            decoded = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ModelRetry(f"参数 {field_name} 必须是 JSON 数组。") from exc
        if not isinstance(decoded, list):
            raise ModelRetry(f"参数 {field_name} 必须是数组，收到 {type(decoded).__name__}。")
        return decoded
    raise ModelRetry(f"参数 {field_name} 必须是数组，收到 {type(value).__name__}。")


def _export_xlsx(
    *,
    out_dir: Path,
    review_id: str,
    title: str,
    columns: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> str:
    """Write the review to an .xlsx and return its path."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()
    ws = wb.active
    ws.title = "Review"

    col_keys = [c.get("id") or c.get("key") for c in columns]
    col_labels = [c.get("label") or c.get("id") or c.get("key") for c in columns]

    # Header: document + one column per data point + a hidden source column each.
    header = ["文件", *col_labels]
    source_cols = [f"_src::{k}" for k in col_keys]
    header += source_cols
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for row in rows:
        cells = row.get("cells", {}) if isinstance(row, dict) else {}
        values = [row.get("document", "") if isinstance(row, dict) else ""]
        sources = []
        for key in col_keys:
            cell = cells.get(key, {}) if isinstance(cells, dict) else {}
            if isinstance(cell, dict):
                values.append(
                    cell.get("value") if cell.get("value") is not None else cell.get("state", "")
                )
                sources.append(f"{cell.get('quote', '')} @ {cell.get('location', '')}".strip(" @"))
            else:
                values.append(cell)
                sources.append("")
        ws.append([*values, *sources])
        # colour the data cells by state
        excel_row = ws.max_row
        for idx, key in enumerate(col_keys, start=2):
            cell = cells.get(key, {}) if isinstance(cells, dict) else {}
            state = cell.get("state", "answered") if isinstance(cell, dict) else "answered"
            argb = _STATE_FILL.get(state, "FFFFFFFF")
            ws.cell(row=excel_row, column=idx).fill = PatternFill("solid", fgColor=argb)

    # hide source columns
    for offset in range(len(source_cols)):
        col_letter = ws.cell(row=1, column=2 + len(col_keys) + offset).column_letter
        ws.column_dimensions[col_letter].hidden = True

    # self-documenting schema sheet
    schema_ws = wb.create_sheet("_schema")
    schema_ws.append(["id", "label", "type", "prompt"])
    for c in columns:
        schema_ws.append(
            [c.get("id") or c.get("key"), c.get("label"), c.get("type"), c.get("prompt")]
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"tabular-review-{review_id}.xlsx"
    wb.save(path)
    return str(path)


def _export_csv(
    *, out_dir: Path, review_id: str, columns: list[dict[str, Any]], rows: list[dict[str, Any]]
) -> str:
    col_keys = [c.get("id") or c.get("key") for c in columns]
    col_labels = [c.get("label") or k for c, k in zip(columns, col_keys, strict=False)]
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"tabular-review-{review_id}.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["文件", *col_labels])
        for row in rows:
            cells = row.get("cells", {}) if isinstance(row, dict) else {}
            line = [row.get("document", "") if isinstance(row, dict) else ""]
            for key in col_keys:
                cell = cells.get(key, {}) if isinstance(cells, dict) else {}
                line.append(
                    (cell.get("value") if cell.get("value") is not None else cell.get("state", ""))
                    if isinstance(cell, dict)
                    else cell
                )
            writer.writerow(line)
    return str(path)


async def write_tabular_review(
    ctx: RunContext[CorporateDeps],
    columns: list[dict[str, Any]] | str,
    rows: list[dict[str, Any]] | str,
    source_docs: list[str] | str | None = None,
) -> str:
    """把表格审查的模式与结果写回数据库并导出 Excel/CSV（tabular-review 的最后一步）。

    Args:
        columns: 列定义数组，每列 {id, label, type, prompt, options?}。
        rows: 结果行数组，每行 {document, cells: {列id: {value, state, quote, location}}}。
        source_docs: 覆盖的来源文件列表。

    Returns:
        JSON 字符串，含 review_id 与导出文件路径。
    """
    deps = ctx.deps
    if deps.tabular_review_id is None:
        raise RuntimeError(
            "CorporateDeps.tabular_review_id is None — the handler must pre-create "
            "the TabularReview row before running this skill."
        )
    review = tabular_review_repo.get_by_id(deps.db, deps.tabular_review_id)
    if review is None or review.deal_id is None:
        raise PermissionError(f"Tabular review {deps.tabular_review_id} not found.")
    from app.agents.corporate.tools.deal_tools import _load_owned_deal

    _load_owned_deal(deps)  # ownership: deal_id on deps must match the review's deal + user

    cols = _coerce_list(columns, "columns")
    row_list = _coerce_list(rows, "rows")
    docs = _coerce_list(source_docs, "source_docs")

    out_dir = Path(deps.output_dir) if deps.output_dir else Path("outputs") / "corporate"
    xlsx_path = _export_xlsx(
        out_dir=out_dir, review_id=review.id, title=review.title, columns=cols, rows=row_list
    )
    _export_csv(out_dir=out_dir, review_id=review.id, columns=cols, rows=row_list)

    tabular_review_repo.update(
        deps.db,
        review=review,
        columns=cols,
        rows=row_list,
        source_docs=docs,
        status="completed",
        export_path=xlsx_path,
    )
    return json.dumps(
        {"review_id": review.id, "export_path": xlsx_path, "row_count": len(row_list)},
        ensure_ascii=False,
    )
