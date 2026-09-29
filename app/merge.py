import re
from .config import CONF_REVIEW
from .schema import SCALAR_FIELDS

LONG_TEXT = {"ingredients_text","manufacturer_name_address","packer_marketer_name_address",
             "importer_name_address","allergen_statement","storage_conditions","instructions_for_use"}

def _norm(v): return re.sub(r"[^a-z0-9]", "", v.lower())

def merge(extraction, all_sides_confirmed=False):
    out = {}
    for f in SCALAR_FIELDS:
        obs = [(r.image_index, getattr(r, f)) for r in extraction.images if getattr(r, f) is not None]
        if not obs:  # absence is only a real "missing" if the user confirmed all sides
            out[f] = {"status": "missing" if all_sides_confirmed else "not_found"}
            continue
        if f in LONG_TEXT:   # text can span panels: take the longest, never flag conflict
            i, best = max(obs, key=lambda x: len(x[1].value)); conflict = False
        else:
            i, best = max(obs, key=lambda x: x[1].confidence)
            conflict = len({_norm(o.value) for _, o in obs}) > 1
        status = "conflict" if conflict else ("low_conf" if best.confidence < CONF_REVIEW else "found")
        out[f] = {"status": status, "value": best.value, "confidence": best.confidence,
                  "image_index": i, "box_2d": best.box_2d,
                  "candidates": [{"image_index": j, "value": o.value} for j, o in obs] if conflict else None}
    out["claims"] = sorted({c for r in extraction.images for c in r.claims})
    out["other_declarations"] = sorted({c for r in extraction.images for c in r.other_declarations})
    return out