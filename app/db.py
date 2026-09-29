import json, os, uuid
from sqlalchemy import create_engine, text
from app.config import DB_URL, UPLOAD_DIR

engine = create_engine(DB_URL, pool_pre_ping=True)

def save_scan(blobs, extraction, merged, confirmed):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with engine.begin() as c:
        # Insert scan
        sid = c.execute(text(
            "INSERT INTO scans (all_sides_confirmed, extracted_json, merged_json) VALUES (:a,:e,:m)"
        ), {"a": confirmed, "e": extraction.model_dump_json(), "m": json.dumps(merged)}).lastrowid
        
        # Save images to disk and DB
        for data, mime, label in blobs:
            path = os.path.join(UPLOAD_DIR, f"{sid}_{label}_{uuid.uuid4().hex[:8]}.{mime.split('/')[-1]}")
            with open(path, "wb") as fh: 
                fh.write(data)
            c.execute(text(
                "INSERT INTO scan_images (scan_id, view_label, image_path) VALUES (:s,:l,:p)"
            ), {"s": sid, "l": label, "p": path})
            
    return sid

def save_product_and_findings(sid: int, normalized: dict, findings: list):
    with engine.begin() as c:
        # Insert product
        pid = c.execute(text("""
            INSERT INTO products (product_name, brand_name, fssai_license_no, mrp, net_quantity) 
            VALUES (:name, :brand, :fssai, :mrp, :net_qty)
        """), {
            "name": normalized["product_name"],
            "brand": normalized["brand_name"],
            "fssai": normalized["fssai_license_no"],
            "mrp": normalized["mrp"],
            "net_qty": normalized["net_quantity"]
        }).lastrowid

        # Link scan to product
        c.execute(text("UPDATE scans SET product_id = :pid WHERE scan_id = :sid"), 
                  {"pid": pid, "sid": sid})

        # Insert findings and compute overall status
        overall = "PASS"
        for f in findings:
            if f["result"] == "FAIL": overall = "FAIL"
            elif f["result"] == "REVIEW" and overall != "FAIL": overall = "REVIEW"

            c.execute(text("""
                INSERT INTO findings (scan_id, rule_id, extracted_value, confidence, image_id, bbox, result)
                VALUES (:sid, :rid, :val, :conf, :iid, :bbox, :res)
            """), {
                "sid": f["scan_id"], "rid": f["rule_id"], "val": f["extracted_value"],
                "conf": f["confidence"], "iid": f["image_id"], "bbox": json.dumps(f["bbox"]), "res": f["result"]
            })

        # Update scan overall status
        c.execute(text("UPDATE scans SET overall_status = :status WHERE scan_id = :sid"),
                  {"status": overall, "sid": sid})
                  
    return pid, overall