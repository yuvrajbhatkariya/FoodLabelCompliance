import cv2, numpy as np
from .config import MIN_SIDE_PX, MIN_SHARPNESS

def check_image(data: bytes) -> dict:
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return {"ok": False, "reasons": ["unreadable image"]}
    h, w = img.shape[:2]
    sharp = cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    reasons = []
    if min(h, w) < MIN_SIDE_PX: reasons.append(f"low resolution {w}x{h}")
    if sharp < MIN_SHARPNESS:   reasons.append(f"blurry (score {sharp:.0f})")
    return {"ok": not reasons, "reasons": reasons}