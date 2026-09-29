ICON = {
    "PASS": "✅",
    "FAIL": "❌",
    "REVIEW": "⚠️",
}

ORDER = {
    "FAIL": 0,
    "REVIEW": 1,
    "PASS": 2,
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
        key=lambda f: ORDER[f["result"]]
    )

    overall = overall_status(findings)

    lines = [
        "COMPLIANCE REPORT",
        f"Product: {product_name or 'Unknown'} | Brand: {brand or 'Unknown'}",
        f"Overall status: {ICON[overall]} {overall}",
        "-" * 60,
    ]

    for f in findings:
        evidence = f.get("evidence") or {}

        line = (
            f"{ICON[f['result']]} "
            f"{f['label']:<35} [{f['clause']}]"
        )

        if evidence.get("value"):
            line += f'\n     found: "{evidence["value"]}"'

        if evidence.get("candidates"):
            line += "\n     candidates: " + " | ".join(
                c["value"] for c in evidence["candidates"]
            )

        lines.append(line)

    review = [f for f in findings if f["result"] == "REVIEW"]

    lines.append("-" * 60)
    lines.append(
        "Items needing your review:"
        if review else
        "No items need review."
    )

    lines.extend(
        f"  - {f['label']}: could not confirm automatically — "
        "please check the photo."
        for f in review
    )

    return "\n".join(lines)