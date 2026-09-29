import os
import mimetypes
import json

from app.quality import check_image
from app.extractor import extract
from app.merge import merge
from app.db import save_scan
from app.evaluator import evaluate
from app.report import render


t1 = "test_images/t1/front.jpeg"
t2 = "test_images/t1/side2.jpeg"
t3 = "test_images/t1/side1.jpeg"
t4 = "test_images/t1/side3.jpeg"

ALL_SIDES_CONFIRMED = True


def run_pipeline():
    image_slots = [
        (t1, "front"),
        (t2, "back"),
        (t3, "side"),
        (t4, "base"),
    ]

    blobs, problems = [], []

    print("--- STEP 1: LOADING & CHECKING IMAGES ---")

    for path, label in image_slots:
        if not path:
            continue

        if not os.path.exists(path):
            print(f"❌ File not found: {path}")
            return

        with open(path, "rb") as f:
            data = f.read()

        quality = check_image(data)

        if not quality["ok"]:
            problems.append({
                "file": path,
                "reasons": quality["reasons"],
            })
        else:
            print(f"✓ [{label}] quality passed")

        mime, _ = mimetypes.guess_type(path)
        blobs.append((data, mime or "image/jpeg", label))

    if not blobs:
        print("❌ No images provided.")
        return

    if problems:
        print("\n❌ Quality Gate Failed:")
        for problem in problems:
            print(
                f" - {problem['file']}: "
                f"{', '.join(problem['reasons'])}"
            )
        return

    print(f"\n--- STEP 2: SENDING {len(blobs)} IMAGES TO GEMINI ---")

    try:
        extraction = extract(blobs)
        print("✓ Extraction completed")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return

    print("\n--- STEP 3: MERGING ---")
    merged = merge(
        extraction,
        all_sides_confirmed=ALL_SIDES_CONFIRMED,
    )

    print("\n--- STEP 4: EVALUATING ---")
    findings = evaluate(merged)

    print("\n--- STEP 5: SAVING ---")
    try:
        scan_id = save_scan(
            blobs,
            extraction,
            merged,
            ALL_SIDES_CONFIRMED,
        )
        print(f"✓ scan_id: {scan_id}")
    except Exception as e:
        print(f"❌ Database save failed: {e}")
        return

    print("\n" + render(
        merged.get("product_name", {}).get("value"),
        merged.get("brand_name", {}).get("value"),
        findings,
    ))

    print("\n--- MERGED JSON ---")
    print(json.dumps(merged, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    run_pipeline()