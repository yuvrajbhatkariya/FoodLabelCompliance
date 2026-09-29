FIELD_MAP = {
    "manufacture_month_year": "mfg_or_packing_date",
    "consumer_complaint_contact": "consumer_care_contact",
    "retail_sale_price": "mrp",
    "quantity_declaration_general": "net_quantity",
    "quantity_declaration_method": "net_quantity",
    "manufacturer_address": "manufacturer_name_address",

    "business_entities.fssai_license_no": "fssai_license_no",

    "product_ingredients.is_allergen,product_ingredients.allergen_category":
        "allergen_statement",

    "products.is_vegetarian,packaging_metrology.veg_logo_square_size_mm,packaging_metrology.nonveg_logo_triangle_side_mm":
        "veg_nonveg_symbol",
}


PRESENCE_CATEGORIES = {
    "Labelling",
    "Business identity",
    "Batch/Lot",
    "Date Marking",
    "FSSAI Licensing",
    "Allergen",
    "Pricing",
    "Quantity",
}


VEG_NONVEG_CATEGORIES = {
    "Veg/Non-Veg",
    "Veg-NonVeg",
    "Veg/NonVeg",
}


IDENTITY_FIELDS = {
    "manufacturer_name_address",
    "packer_marketer_name_address",
    "importer_name_address",
}


def status_to_result(status):
    return {
        "found": "PASS",
        "missing": "FAIL",
        "not_found": "REVIEW",
        "low_conf": "REVIEW",
        "conflict": "REVIEW",
    }.get(status, "REVIEW")