from __future__ import annotations

from typing import Any, Dict, Iterable, List


def _format_case(case: Dict[str, Any], max_headers: int = 6, max_lines: int = 10) -> str:
    headers: List[str] = (case.get("section_headers") or [])[:max_headers]
    svc: List[Dict[str, Any]] = (case.get("service_lines") or [])[:max_lines]

    out: List[str] = []
    out.append(f"[CASE] {case.get('case_id')} (source={case.get('source_file')})")
    if headers:
        out.append("Human section headers (copy sectioning behavior):")
        out.extend([f"- {h}" for h in headers])
    if svc:
        out.append("Representative human line-item patterns (copy formula phrasing; NEVER copy prices):")
        for x in svc:
            name = x.get("name") or ""
            text = x.get("text") or ""
            out.append(f"- {name}：{text}")
    return "\n".join(out)


def build_reference_block(retrieved_cases: Iterable[Dict[str, Any]]) -> str:
    blocks = [_format_case(c) for c in retrieved_cases]
    if not blocks:
        return ""

    return (
        "=== REFERENCE CASES (human-verified demonstrations) ===\n"
        "Rules (strict):\n"
        "1) Use these ONLY to copy STRUCTURE/SECTIONING/FORMULA-STYLE/UNCERTAINTY PHRASES.\n"
        "2) DO NOT copy unit prices, subtotals, totals, or any numeric results from the cases.\n"
        "3) Always use the pricing tool / current catalog for priced items; if missing, mark as need-confirmation.\n"
        "4) Prefer explicit factor formulas like 元/单位 * 数量因子 = 小计, and use 需确定/以实际为准 for unknowns.\n"
        "\n"
        + "\n\n".join(blocks)
        + "\n=== END REFERENCE CASES ==="
    )
