import re
from .config import CONF_REVIEW
from .schema import SCALAR_FIELDS

LONG_TEXT = {
    "ingredients_text",
    "manufacturer_name_address",
    "packer_marketer_name_address",
    "importer_name_address",
    "allergen_statement",
    "storage_conditions",
    "instructions_for_use",
}


def _script(s):
    return "devanagari" if any("\u0900" <= ch <= "\u097F" for ch in s) else "latin"


def _norm(v):
    return re.sub(r"[^a-z0-9]", "", v.lower())


def merge(extraction, all_sides_confirmed=False):
    out = {}

    for field in SCALAR_FIELDS:
        obs = [
            (r.image_index, getattr(r, field))
            for r in extraction.images
            if getattr(r, field) is not None
        ]

        if not obs:
            out[field] = {
                "status": "missing" if all_sides_confirmed else "not_found"
            }
            continue

        if field in LONG_TEXT:
            image_index, best = max(
                obs, key=lambda x: (len(x[1].value), x[1].confidence)
            )
            conflict = False
            multilingual = False
        else:
            image_index, best = max(obs, key=lambda x: x[1].confidence)

            scripts = {_script(o.value) for _, o in obs}
            multilingual = len(scripts) > 1

            # Only compare values written in the same script.
            same_script = {}
            for image_index_, observation in obs:
                same_script.setdefault(
                    _script(observation.value), []
                ).append(observation)

            conflict = any(
                len({_norm(o.value) for o in values}) > 1
                for values in same_script.values()
            )

        status = (
            "conflict"
            if conflict
            else "low_conf"
            if best.confidence < CONF_REVIEW
            else "found"
        )

        out[field] = {
            "status": status,
            "value": best.value,
            "confidence": best.confidence,
            "image_index": image_index,
            "box_2d": best.box_2d,
            "multilingual": multilingual,
            "candidates": (
                [{"image_index": i, "value": o.value} for i, o in obs]
                if conflict else None
            ),
        }

    out["claims"] = sorted({
        c for r in extraction.images for c in r.claims
    })
    out["other_declarations"] = sorted({
        c for r in extraction.images for c in r.other_declarations
    })

    return out