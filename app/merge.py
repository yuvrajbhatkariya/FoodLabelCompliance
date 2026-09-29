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

VARIANT_FIELDS = {"product_name", "brand_name"}


def _script(s):
    return "devanagari" if any("\u0900" <= c <= "\u097F" for c in s) else "latin"


def _norm(v):
    return re.sub(r"[^a-z0-9]", "", v.lower())


def _is_superset_variant(a, b):
    na, nb = _norm(a), _norm(b)
    return bool(na and nb) and (na in nb or nb in na)


def _has_conflict(obs):
    by_script = {}

    for _, item in obs:
        by_script.setdefault(_script(item.value), []).append(item.value)

    for values in by_script.values():
        if len(values) > 1 and not all(
            any(_is_superset_variant(a, b) for b in values if a != b)
            for a in values
        ):
            if len({_norm(v) for v in values}) > 1:
                return True

    return False


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
                obs,
                key=lambda x: (len(x[1].value), x[1].confidence),
            )
            conflict = False

        else:
            conflict = (
                _has_conflict(obs)
                if field in VARIANT_FIELDS
                else len({_norm(o.value) for _, o in obs}) > 1
            )

            if field in VARIANT_FIELDS and not conflict:
                image_index, best = max(
                    obs,
                    key=lambda x: (len(x[1].value), x[1].confidence),
                )
            else:
                image_index, best = max(
                    obs,
                    key=lambda x: x[1].confidence,
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