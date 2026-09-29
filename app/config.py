import os
from dotenv import load_dotenv
load_dotenv(override=True)

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL   = os.environ["GEMINI_MODEL"]   # pick a free-tier Flash model from ai.google.dev/pricing
DB_URL         = os.environ["DB_URL"]         # mysql+pymysql://user:pass@localhost/FoodLabelDB
UPLOAD_DIR     = os.getenv("UPLOAD_DIR", "uploads")

MIN_SIDE_PX   = 1000    # reject tiny images
MIN_SHARPNESS = 100.0   # Laplacian variance; tune on your own photos
CONF_REVIEW   = 0.50    # below this a field is "low_conf" and goes to REVIEW