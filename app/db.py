import json
import os
import uuid
from datetime import date

from sqlalchemy import create_engine, text

from app.config import DB_URL, UPLOAD_DIR


engine = create_engine(DB_URL, pool_pre_ping=True)


def load_applicable_rules(scan_date=None):
    scan_date = scan_date or date.today()

    q = text("""
        SELECT
            id,
            rule_code,
            clause_ref,
            category,
            extraction_field_key,
            description
        FROM rules
        WHERE is_checkable = TRUE
          AND effective_from <= :d
          AND (effective_to IS NULL OR effective_to > :d)
        ORDER BY id
    """)

    with engine.connect() as c:
        return [
            dict(row._mapping)
            for row in c.execute(q, {"d": scan_date})
        ]


def save_scan(blobs, extraction, merged, confirmed):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    with engine.begin() as c:
        sid = c.execute(
            text("""
                INSERT INTO scans
                (all_sides_confirmed, extracted_json, merged_json)
                VALUES (:a, :e, :m)
            """),
            {
                "a": confirmed,
                "e": extraction.model_dump_json(),
                "m": json.dumps(merged, ensure_ascii=False),
            },
        ).lastrowid

        for data, mime, label in blobs:
            path = os.path.join(
                UPLOAD_DIR,
                f"{sid}_{label}_{uuid.uuid4().hex[:8]}.{mime.split('/')[-1]}",
            )

            with open(path, "wb") as fh:
                fh.write(data)

            c.execute(
                text("""
                    INSERT INTO scan_images
                    (scan_id, view_label, image_path)
                    VALUES (:s, :l, :p)
                """),
                {
                    "s": sid,
                    "l": label,
                    "p": path,
                },
            )

    return sid


def save_findings(sid: int, findings: list):
    with engine.begin() as c:
        image_rows = c.execute(
            text("""
                SELECT image_id
                FROM scan_images
                WHERE scan_id = :sid
                ORDER BY image_id
            """),
            {"sid": sid},
        ).fetchall()

        image_map = {
            index: row[0]
            for index, row in enumerate(image_rows)
        }

        overall = "PASS"

        for finding in findings:
            evidence = finding.get("evidence") or {}
            result = finding["result"]

            if result == "FAIL":
                overall = "FAIL"
            elif result == "REVIEW" and overall == "PASS":
                overall = "REVIEW"

            c.execute(
                text("""
                    INSERT INTO findings
                    (
                        scan_id,
                        rule_id,
                        extracted_value,
                        confidence,
                        image_id,
                        bbox,
                        result
                    )
                    VALUES
                    (
                        :sid,
                        :rid,
                        :value,
                        :confidence,
                        :image_id,
                        :bbox,
                        :result
                    )
                """),
                {
                    "sid": sid,
                    "rid": finding["rule_id"],
                    "value": evidence.get("value"),
                    "confidence": evidence.get("confidence"),
                    "image_id": image_map.get(evidence.get("image_index")),
                    "bbox": json.dumps(evidence.get("box_2d")),
                    "result": result,
                },
            )

        c.execute(
            text("""
                UPDATE scans
                SET overall_status = :status
                WHERE scan_id = :sid
            """),
            {"status": overall, "sid": sid},
        )

    return overall