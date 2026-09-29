from .rules_config import (
    FIELD_MAP,
    IDENTITY_FIELDS,
    PRESENCE_CATEGORIES,
    VEG_NONVEG_CATEGORIES,
    status_to_result,
)


def evaluate_veg_nonveg(rule, merged):
    symbol = merged.get(
        "veg_nonveg_symbol",
        {"status": "not_found"},
    )

    if symbol["status"] != "found":
        return status_to_result(symbol["status"]), symbol

    is_nonveg = "NONVEG" in rule["rule_code"].upper()
    expected = "non_veg" if is_nonveg else "veg"

    if symbol["value"] != expected:
        return "NOT_APPLICABLE", symbol

    return "PASS", symbol


def _evaluate_identity(merged, rules):
    identity_rules = [
        rule for rule in rules
        if FIELD_MAP.get(rule["extraction_field_key"]) in IDENTITY_FIELDS
    ]

    if not identity_rules:
        return [], set()

    fields = (
        "manufacturer_name_address",
        "packer_marketer_name_address",
        "importer_name_address",
    )

    group = {
        field: merged.get(field, {"status": "not_found"})
        for field in fields
    }

    found = [
        evidence
        for evidence in group.values()
        if evidence.get("status") == "found"
    ]

    if found:
        evidence = max(
            found,
            key=lambda x: x.get("confidence") or 0,
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
                evidence
                for evidence in group.values()
                if evidence.get("status") != "missing"
            ),
            None,
        )
        result = "REVIEW"

    rule = identity_rules[0]

    return [{
        "rule_id": rule["id"],
        "rule_code": rule["rule_code"],
        "clause": rule["clause_ref"],
        "label": "Manufacturer/Packer/Importer identity",
        "result": result,
        "evidence": evidence,
    }], {rule["id"] for rule in identity_rules}


def evaluate_from_db(merged, rules):
    findings, handled = _evaluate_identity(merged, rules)
    unmapped = []

    for rule in rules:
        if rule["id"] in handled:
            continue

        key = FIELD_MAP.get(rule["extraction_field_key"])

        if key is None:
            unmapped.append(rule["rule_code"])
            continue

        category = rule["category"]

        if category in VEG_NONVEG_CATEGORIES:
            result, evidence = evaluate_veg_nonveg(
                rule,
                merged,
            )

        elif category in PRESENCE_CATEGORIES:
            evidence = merged.get(
                key,
                {"status": "not_found"},
            )
            result = status_to_result(evidence["status"])

        else:
            continue

        findings.append({
            "rule_id": rule["id"],
            "rule_code": rule["rule_code"],
            "clause": rule["clause_ref"],
            "label": (rule["description"] or rule["rule_code"])[:60],
            "result": result,
            "evidence": evidence,
        })

    if unmapped:
        print(
            f"⚠ {len(unmapped)} loaded rules have no field mapping yet: "
            f"{unmapped[:10]}"
        )

    return findings