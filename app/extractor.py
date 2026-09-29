from google import genai
from google.genai import types, errors
from tenacity import retry, retry_if_exception, wait_exponential, stop_after_attempt
from .config import GEMINI_API_KEY, GEMINI_MODEL
from .schema import Extraction

client = genai.Client(api_key=GEMINI_API_KEY)

PROMPT = """You are reading photos of ONE packaged food product, labelled image_0, image_1, ...
Return one entry per image. Extract only what is visible in THAT image. Never guess or infer.
- null for anything not visible in that image.
- value: transcribe exactly as printed (keep units, symbols, language).
- confidence: 0-1, how sure you are the text is read correctly.
- box_2d: [ymin, xmin, ymax, xmax] normalised 0-1000 around the text/symbol.
- veg_nonveg_symbol: 'veg' (green circle in square) or 'non_veg' (brown triangle in square).
- fssai_logo: 'present' if the FSSAI logo is visible; licence number goes in fssai_license_no.
- nutrient fields: number only, for the basis printed in nutrition_basis (e.g. 'per 100 g').
- claims: front-of-pack claim phrases verbatim (e.g. 'low fat', 'no added sugar').
- other_declarations: warning/advisory statements verbatim (e.g. 'CONTAINS CAFFEINE').
Do NOT judge compliance."""

def _retryable(e):
    return isinstance(e, errors.APIError) and e.code in (429, 500, 503)

@retry(retry=retry_if_exception(_retryable), wait=wait_exponential(multiplier=2, max=60),
       stop=stop_after_attempt(5), reraise=True)
def extract(images):  # images: list of (bytes, mime, view_label)
    parts = []
    for i, (data, mime, label) in enumerate(images):
        parts += [f"image_{i} ({label}):", types.Part.from_bytes(data=data, mime_type=mime)]
    parts.append(PROMPT)
    resp = client.models.generate_content(
        model=GEMINI_MODEL, contents=parts,
        config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=Extraction, temperature=0))
    if resp.parsed is None:
        raise ValueError("Model returned unparseable output")
    return resp.parsed