import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "src" / "data" / "sample"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))

LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
LANGFUSE_BASE_URL = os.getenv("LANGFUSE_BASE_URL", "https://us.cloud.langfuse.com")

REDIS_URL = os.getenv("REDIS_URL", "")

CANADIAN_PROVINCES = [
    "ON", "BC", "AB", "QC", "MB", "SK", "NS", "NB", "NL", "PE", "NT", "YT", "NU",
]

FINTRAC_REPORTING_THRESHOLD_CAD = 10_000.0
STRUCTURING_WINDOW_HOURS = 48
VELOCITY_SPIKE_MULTIPLIER = 5.0
DORMANT_THRESHOLD_DAYS = 180

NUM_CLIENTS = 500
NUM_TRANSACTIONS = 50_000
SUSPICIOUS_CLIENT_RATIO = 0.08
