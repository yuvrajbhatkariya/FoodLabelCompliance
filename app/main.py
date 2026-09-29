from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from starlette.concurrency import run_in_threadpool

from .quality import check_image
from .extractor import extract
from .merge import merge
from .db import save_scan
from .evaluator import evaluate
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
    findings = evaluate(merged)

    product = merged.get("product_name", {}).get("value")
    brand = merged.get("brand_name", {}).get("value")
    overall = overall_status(findings)

    scan_id = await run_in_threadpool(
        save_scan,
        blobs,
        extraction,
        merged,
        all_sides_confirmed,
    )

    return {
        "scan_id": scan_id,
        "overall_status": overall,
        "merged": merged,
        "findings": findings,
        "report": render(product, brand, findings),
    }