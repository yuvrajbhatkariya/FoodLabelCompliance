CHECKS = [
    {
        "rule_code": "RULE_6",
        "label": "Manufacturer/Packer/Importer identity",
        "clause": "LMPC Rule 6",
        "type": "or_group",
        "fields": [
            "manufacturer_name_address",
            "packer_marketer_name_address",
            "importer_name_address",
        ],
    },
    {
        "rule_code": "RULE_6_RSP",
        "label": "MRP declaration",
        "clause": "LMPC Rule 6(1)(e)",
        "type": "presence",
        "field": "mrp",
    },
    {
        "rule_code": "RULE_6",
        "label": "Net quantity",
        "clause": "LMPC Rule 6",
        "type": "presence",
        "field": "net_quantity",
    },
    {
        "rule_code": "RULE_6_DATE_DECLARATION",
        "label": "Manufacture/packing date",
        "clause": "LMPC Rule 6(1)(d)",
        "type": "presence",
        "field": "mfg_or_packing_date",
    },
    {
        "rule_code": "FSSAI-R5-10-A",
        "label": "Expiry/use-by date",
        "clause": "FSSAI Reg 5(10)(a)",
        "type": "presence",
        "field": "expiry_or_use_by_date",
    },
    {
        "rule_code": "FSSAI-R5-9",
        "label": "Batch/lot number",
        "clause": "FSSAI Reg 5(9)",
        "type": "presence",
        "field": "batch_lot_no",
    },
    {
        "rule_code": "FSSAI-R5-7",
        "label": "FSSAI logo & licence no.",
        "clause": "FSSAI Reg 5(7)",
        "type": "presence",
        "field": "fssai_license_no",
    },
    {
        "rule_code": "FSSAI-R5-4-VEG",
        "label": "Veg/non-veg symbol",
        "clause": "FSSAI Reg 5(4)",
        "type": "presence",
        "field": "veg_nonveg_symbol",
    },
    {
        "rule_code": "RULE_6_CONSUMER_CONTACT",
        "label": "Consumer care contact",
        "clause": "LMPC Rule 6(2)",
        "type": "presence",
        "field": "consumer_care_contact",
    },
    {
        "rule_code": "FSSAI-R5-14",
        "label": "Allergen statement",
        "clause": "FSSAI Reg 5(14)",
        "type": "presence",
        "field": "allergen_statement",
    },
]


RESULT_MAP = {
    "found": "PASS",
    "missing": "FAIL",
    "not_found": "REVIEW",
    "low_conf": "REVIEW",
    "conflict": "REVIEW",
}


def status_to_result(status):
    return RESULT_MAP.get(status, "REVIEW")