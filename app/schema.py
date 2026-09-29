from typing import Optional, List
from pydantic import BaseModel, create_model

class Obs(BaseModel):
    value: str                       # exactly as printed
    confidence: float                # 0-1
    box_2d: Optional[List[int]]      # [ymin, xmin, ymax, xmax], 0-1000

SCALAR_FIELDS = [
 "product_name","brand_name","manufacturer_name_address","packer_marketer_name_address",
 "importer_name_address","country_of_origin","fssai_license_no","fssai_logo","veg_nonveg_symbol",
 "net_quantity","mrp","mfg_or_packing_date","expiry_or_use_by_date","best_before","batch_lot_no",
 "consumer_care_contact","ingredients_text","allergen_statement","storage_conditions",
 "instructions_for_use","serving_size","servings_per_pack","nutrition_basis",
 "energy_kcal","protein_g","carbohydrate_g","total_sugars_g","added_sugars_g","total_fat_g",
 "saturated_fat_g","trans_fat_g","cholesterol_mg","sodium_mg",
]

ImageResult = create_model(
    "ImageResult",
    image_index=(int, ...),
    claims=(List[str], ...),               # front-of-pack claim phrases, verbatim
    other_declarations=(List[str], ...),   # e.g. "CONTAINS CAFFEINE"
    **{f: (Optional[Obs], ...) for f in SCALAR_FIELDS},
)

class Extraction(BaseModel):
    images: List[ImageResult]