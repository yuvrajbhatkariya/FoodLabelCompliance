ICON = {
    "PASS": "✅",
    "FAIL": "❌",
    "REVIEW": "⚠️",
    "NOT_APPLICABLE": "➖",
}


ORDER = {
    "FAIL": 0,
    "REVIEW": 1,
    "PASS": 2,
    "NOT_APPLICABLE": 3,
}


def overall_status(findings):
    if any(f["result"] == "FAIL" for f in findings):
        return "FAIL"

    if any(f["result"] == "REVIEW" for f in findings):
        return "REVIEW"

    return "PASS"


def render(product_name, brand, findings):
    findings = sorted(
        findings,
        key=lambda f: ORDER[f["result"]],
    )

    overall = overall_status(findings)

    lines = [
        "COMPLIANCE REPORT",
        f"Product: {product_name or 'Unknown'} | "
        f"Brand: {brand or 'Unknown'}",
        f"Overall status: {ICON[overall]} {overall}",
        "-" * 60,
    ]

    for finding in findings:
        evidence = finding.get("evidence") or {}

        line = (
            f"{ICON[finding['result']]} "
            f"{finding['label']:<35} "
            f"[{finding['clause']}]"
        )

        if evidence.get("value"):
            line += f'\n     found: "{evidence["value"]}"'

        if evidence.get("candidates"):
            line += "\n     candidates: " + " | ".join(
                candidate["value"]
                for candidate in evidence["candidates"]
            )

        lines.append(line)

    review = [
        finding
        for finding in findings
        if finding["result"] == "REVIEW"
    ]

    lines.append("-" * 60)
    lines.append(
        "Items needing your review:"
        if review
        else "No items need review."
    )

    lines.extend(
        f"  - {finding['label']}: "
        "could not confirm automatically — please check the photo."
        for finding in review
    )

    return "\n".join(lines)