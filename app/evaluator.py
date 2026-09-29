from .rules_config import CHECKS, status_to_result


def evaluate(merged):
    findings = []

    for check in CHECKS:
        if check["type"] == "presence":
            evidence = merged.get(
                check["field"], {"status": "not_found"}
            )
            findings.append({
                **check,
                "result": status_to_result(evidence["status"]),
                "evidence": evidence,
            })
            continue

        group = {
            field: merged.get(field, {"status": "not_found"})
            for field in check["fields"]
        }

        found = [
            evidence for evidence in group.values()
            if evidence.get("status") == "found"
        ]

        if found:
            evidence = max(
                found,
                key=lambda x: x.get("confidence") or 0
            )
            result = "PASS"
        elif all(
            evidence.get("status") == "missing"
            for evidence in group.values()
        ):
            evidence = None
            result = "FAIL"
        else:
            evidence = next(
                (
                    value for value in group.values()
                    if value.get("status") != "missing"
                ),
                None,
            )
            result = "REVIEW"

        findings.append({
            **check,
            "result": result,
            "evidence": evidence,
        })

    return findings