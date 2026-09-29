from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from starlette.concurrency import run_in_threadpool
from .quality import check_image
from .extractor import extract
from .merge import merge
from .db import save_scan

app = FastAPI(title="Label Compliance Checker")

@app.post("/scan")
async def scan(files: list[UploadFile] = File(...),
               views: str = Form("front,back,side"),
               all_sides_confirmed: bool = Form(False)):
    if not 1 <= len(files) <= 4:
        raise HTTPException(400, "Upload 1-4 images")
    labels = [v.strip() for v in views.split(",")]
    blobs, problems = [], []
    for i, f in enumerate(files):
        data = await f.read()
        q = check_image(data)
        if not q["ok"]:
            problems.append({"image": i, "reasons": q["reasons"]})
        blobs.append((data, f.content_type or "image/jpeg", labels[i] if i < len(labels) else f"view_{i}"))
    if problems:
        raise HTTPException(422, {"retake": problems})
    extraction = await run_in_threadpool(extract, blobs)
    merged = merge(extraction, all_sides_confirmed)
    return {"scan_id": save_scan(blobs, extraction, merged, all_sides_confirmed), "merged": merged}