from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from starlette.concurrency import run_in_threadpool

from .quality import check_image
from .extractor import extract
from .merge import merge
from .db import (
    save_scan,
    save_findings,
    load_applicable_rules,
)
from .evaluator import evaluate_from_db
from .report import render, overall_status


app = FastAPI(title="Label Compliance Checker")


@app.post("/scan")
async def scan(
    files: list[UploadFile] = File(...),
    views: str = Form("front,back,side"),
    all_sides_confirmed: bool = Form(False),
):
    if not 1 <= len(files) <= 4:
        raise HTTPException(400, "Upload 1-4 images")

    labels = [v.strip() for v in views.split(",")]
    blobs, problems = [], []

    for i, file in enumerate(files):
        data = await file.read()
        quality = check_image(data)

        if not quality["ok"]:
            problems.append({
                "image": i,
                "reasons": quality["reasons"],
            })

        blobs.append((
            data,
            file.content_type or "image/jpeg",
            labels[i] if i < len(labels) else f"view_{i}",
        ))

    if problems:
        raise HTTPException(422, {"retake": problems})

    extraction = await run_in_threadpool(extract, blobs)
    merged = merge(extraction, all_sides_confirmed)

    rules = await run_in_threadpool(load_applicable_rules)
    findings = evaluate_from_db(merged, rules)

    scan_id = await run_in_threadpool(
        save_scan,
        blobs,
        extraction,
        merged,
        all_sides_confirmed,
    )

    product_id, overall = await run_in_threadpool(
        save_findings,
        scan_id,
        merged,
        findings,
    )

    product = merged.get("product_name", {}).get("value")
    brand = merged.get("brand_name", {}).get("value")

    return {
        "scan_id": scan_id,
        "overall_status": overall,
        "merged": merged,
        "findings": findings,
        "report": render(
            merged.get("product_name", {}).get("value"),
            merged.get("brand_name", {}).get("value"),
            findings,
        ),
    }