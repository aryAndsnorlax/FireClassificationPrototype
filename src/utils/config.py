"""Shared configuration: paths, API keys, constants."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_INTERIM = ROOT_DIR / "data" / "interim"
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
MODELS_DIR = ROOT_DIR / "models"

# --- API keys / secrets ---
FIRMS_MAP_KEY = os.getenv("FIRMS_MAP_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# --- Region of interest: India bounding box (min_lon, min_lat, max_lon, max_lat) ---
_bbox_raw = os.getenv("INDIA_BBOX", "68,6,97,37")
INDIA_BBOX = tuple(float(x) for x in _bbox_raw.split(","))

# --- Classification labels ---
FIRE_CLASSES = [
    "industrial_fire",          # accidental — explosion, leak, plant fire
    "persistent_industrial",    # normal operation — flare, kiln, stack
    "coal_seam_fire",           # mine / coal seam
    "agricultural_burning",     # crop residue burning
    "wildfire",                 # forest / vegetation fire
    "unknown",                  # doesn't fit cleanly — flag for review
]

# --- Thresholds (starting points — tune during Phase 4) ---
FACILITY_PROXIMITY_M = 1000        # distance to count as "near" a facility
PERSISTENCE_FREQ_THRESHOLD = 0.6   # fraction of days detected to call "persistent"
FRP_ANOMALY_RATIO = 3.0            # FRP vs baseline ratio to flag as possible accident
