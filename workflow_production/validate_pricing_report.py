import json
from typing import List, Dict, Any, Callable, Tuple, Optional

def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _qty_product(qf: Any) -> Optional[float]:
    if not isinstance(qf, dict) or not qf:
        return None
    prod = 1.0
    for _, v in qf.items():
        fv = _safe_float(v)
        if fv is None:
            return None
        prod *= fv
    return prod


def validate_pricing_report(
    dissectedPlanJson: Any,
    pricingReportJson: Any,
    catalog_lookup_func: Callable[[str], Dict[str, Any]],
    *,
    priced_match_threshold: float = 0.85,
) -> Tuple[List[str], str, Dict[str, Any]]:
    """
    Validation policy (aligned to your new workflow):
    - isOutsourced=false: must be fully computable and math-correct.
    - isOutsourced=true:
        * subtotal must be 0
        * may still carry unitPrice/unit from catalog (preferred)
        * math is NOT enforced (because quantity dims may be missing)
    - If catalog bestMatch exists but is unpriced (unitPrice None or unit empty), do NOT treat as “false outsourced”.
    - Only error on outsourced items when:
        * catalog has a priced bestMatch but report didn't carry it (unitPrice=0 or unit='NA' or mismatch).
    """
    errors: List[str] = []
    hints: Dict[str, Any] = {}

    # Parse inputs
    # Handle dissectedPlanJson
    if isinstance(dissectedPlanJson, str):
        try:
            plan = json.loads(dissectedPlanJson)
        except json.JSONDecodeError:
            return ["Error: dissectedPlanJson is not valid JSON"], "", {}
    else:
        plan = dissectedPlanJson

    # Handle pricingReportJson
    if isinstance(pricingReportJson, str):
        try:
            report = json.loads(pricingReportJson)
        except json.JSONDecodeError:
            return ["Error: pricingReportJson is not valid JSON"], "", {}
    else:
        report = pricingReportJson

    if not isinstance(plan, dict) or "sections" not in plan:
        return ["Error: dissectedPlanJson missing 'sections'"], "", {}
    if not isinstance(report, dict) or "sections" not in report:
        return ["Error: pricingReportJson missing 'sections'"], "", {}

    plan_sections = plan.get("sections", [])
    report_sections = report.get("sections", [])

    # 1) Alignment check
    if len(plan_sections) != len(report_sections):
        errors.append(f"Section count mismatch: plan={len(plan_sections)} report={len(report_sections)}")

    # 2) Walk sections + math
    total_cost_calc = 0.0

    for i, section in enumerate(report_sections):
        section_total_calc = 0.0
        items = section.get("items", [])

        # header alignment (best-effort if count mismatch)
        if i < len(plan_sections):
            expected_header = plan_sections[i].get("header", "")
            got_header = section.get("sectionHeader", "")
            if expected_header != got_header:
                errors.append(f"Section header mismatch at index {i}: expected '{expected_header}', got '{got_header}'")

        for item in items:
            name = item.get("name", "Unknown")
            is_outsourced = bool(item.get("isOutsourced", False))
            unit_price_report = _safe_float(item.get("unitPrice"))
            unit_report = (item.get("unit") or "").strip()
            subtotal_report = _safe_float(item.get("subtotal")) or 0.0
            qf = item.get("quantityFactors", {})

            # Look up catalog
            lookup = catalog_lookup_func(name)
            best = lookup.get("bestMatch")
            confidence = float(lookup.get("confidence") or 0.0)

            # Store hint context (helpful for retry_delta)
            if best and confidence >= priced_match_threshold:
                hints[name] = best

            # If outsourced: enforce subtotal==0, skip math checks
            if is_outsourced:
                if abs(subtotal_report - 0.0) > 1e-6:
                    errors.append(f"Outsourced item '{name}' must have subtotal=0, got {subtotal_report}")

                # If we have a strong catalog match:
                if best and confidence >= priced_match_threshold:
                    cat_price = best.get("unitPrice")
                    cat_unit = (best.get("unit") or "").strip()

                    # Case A: catalog row exists but is unpriced/unfinished -> OK to be outsourced
                    if cat_price is None or cat_unit == "":
                        # Prefer report to show unitPrice=0 and unit='NA' (or empty),
                        # but do not fail hard if it differs.
                        continue

                    # Case B: catalog row is priced -> report should carry the same unitPrice/unit
                    cat_price_f = _safe_float(cat_price)
                    if cat_price_f is None:
                        # treat as unpriced
                        continue

                    # If report "forgot" pricing, that's an error (this is your original HE issue)
                    if unit_price_report is None or abs(unit_price_report - cat_price_f) > 1e-6 or unit_report != cat_unit:
                        errors.append(
                            f"Outsourced item '{name}' has priced catalog match but report didn't carry pricing: "
                            f"catalog='{best.get('service')}' sheet={best.get('sheetName')} "
                            f"price={cat_price_f} unit='{cat_unit}' "
                            f"vs report price={unit_price_report} unit='{unit_report}'"
                        )
                continue  # outsourced ends here

            # If NOT outsourced: must be priced + math correct + (optionally) dims complete
            if unit_price_report is None:
                errors.append(f"Non-outsourced item '{name}' missing unitPrice")
                continue

            prod = _qty_product(qf)
            if prod is None:
                errors.append(f"Non-outsourced item '{name}' has invalid/empty quantityFactors")
                continue

            calc = unit_price_report * prod
            if abs(calc - subtotal_report) > 0.01:
                errors.append(f"Math error for '{name}': calculated {calc}, got {subtotal_report}")

            section_total_calc += subtotal_report

            # If catalog priced bestMatch exists, ensure carried price/unit match
            if best and confidence >= priced_match_threshold:
                cat_price = best.get("unitPrice")
                cat_unit = (best.get("unit") or "").strip()
                cat_price_f = _safe_float(cat_price)
                if cat_price_f is not None and cat_unit != "":
                    if abs(unit_price_report - cat_price_f) > 1e-6 or unit_report != cat_unit:
                        errors.append(
                            f"Pricing mismatch for '{name}': report price={unit_price_report}, unit='{unit_report}' "
                            f"but catalog '{best.get('service')}' sheet={best.get('sheetName')} "
                            f"price={cat_price_f}, unit='{cat_unit}'"
                        )

        # Section total check
        report_section_total = _safe_float(section.get("sectionTotal")) or 0.0
        if abs(section_total_calc - report_section_total) > 0.01:
            errors.append(
                f"Section total error for '{section.get('sectionHeader','')}' "
                f"calculated {section_total_calc}, got {report_section_total}"
            )

        total_cost_calc += section_total_calc

    # Total cost check
    report_total = _safe_float(report.get("totalCost")) or 0.0
    if abs(total_cost_calc - report_total) > 0.01:
        errors.append(f"Total cost error: calculated {total_cost_calc}, got {report_total}")

    # Build retry_delta
    retry_delta = ""
    if errors:
        retry_delta += "Validation Errors:\n"
        for err in errors:
            retry_delta += f"- {err}\n"

        if hints:
            retry_delta += "\nCatalog Hints (strong matches):\n"
            for name, m in hints.items():
                retry_delta += (
                    f"- For '{name}': service='{m.get('service')}', "
                    f"sheet='{m.get('sheetName')}', price={m.get('unitPrice')}, unit='{m.get('unit')}'\n"
                )

    return errors, retry_delta, hints
