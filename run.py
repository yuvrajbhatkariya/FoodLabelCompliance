import os
import mimetypes
import json
from app.quality import check_image
from app.extractor import extract
from app.merge import merge
from app.db import save_scan

# =====================================================================
# 1. SET YOUR IMAGE PATHS HERE
# =====================================================================
t1 = "test_images/t1/front.jpeg"   # Front view
t2 = "test_images/t1/side2.jpeg"   # Back view
t3 = "test_images/t1/side1.jpeg"   # Side view (leave empty "" if not available)
t4 = "test_images/t1/side3.jpeg"                      # Base / top view (leave empty "" if not available)

ALL_SIDES_CONFIRMED = True   # Set False if some sides are missing
# =====================================================================


def run_pipeline():
    # Map slots to view labels
    image_slots = [
        (t1, "front"),
        (t2, "back"),
        (t3, "side"),
        (t4, "base")
    ]

    blobs = []
    problems = []

    print("--- STEP 1: LOADING & CHECKING IMAGES ---")
    active_index = 0
    for path, default_label in image_slots:
        path = path.strip() if path else ""
        if not path:
            continue

        if not os.path.exists(path):
            print(f"❌ File not found: {path}")
            return

        with open(path, "rb") as f:
            data = f.read()

        # Quality Gate Check (Laplacian sharpness & resolution)
        q = check_image(data)
        if not q["ok"]:
            problems.append({"file": path, "reasons": q["reasons"]})
        else:
            print(f"  ✓ [{default_label}] {path} passed quality checks.")

        mime, _ = mimetypes.guess_type(path)
        blobs.append((data, mime or "image/jpeg", default_label))
        active_index += 1

    if not blobs:
        print("❌ No valid images provided in t1, t2, t3, or t4.")
        return

    if problems:
        print("\n❌ Quality Gate Failed! Retake needed:")
        for prob in problems:
            print(f"   - {prob['file']}: {', '.join(prob['reasons'])}")
        return

    print(f"\n--- STEP 2: SENDING {len(blobs)} IMAGES TO GEMINI ---")
    try:
        extraction = extract(blobs)
        print("  ✓ Extraction completed successfully.")
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return

    print("\n--- STEP 3: MERGING EXTRACTED FIELDS ---")
    merged = merge(extraction, all_sides_confirmed=ALL_SIDES_CONFIRMED)
    print("  ✓ Merge completed.")

    print("\n--- STEP 4: SAVING TO DATABASE ---")
    try:
        scan_id = save_scan(blobs, extraction, merged, ALL_SIDES_CONFIRMED)
        print(f"  ✓ Saved to database with scan_id: {scan_id}")
    except Exception as e:
        print(f"❌ Database save failed: {e}")
        return

    print("\n" + "=" * 50)
    print("FINAL MERGED DATA (Sample Fields):")
    print("=" * 50)
    for field in ["product_name", "brand_name", "mrp", "net_quantity", "fssai_license_no", "veg_nonveg_symbol"]:
        val_info = merged.get(field, {})
        print(f"  {field.ljust(22)}: {val_info.get('value')} (status: {val_info.get('status')})")

    print("\nFull JSON output:")
    print(json.dumps(merged, indent=2))


if __name__ == "__main__":
    run_pipeline()