"""Live speed-layer config."""
from pathlib import Path
from apex import config as batch_config

LEAGUE = "FIFA World Cup"
SEASON = "2026"
LIVE_TTL = 45  # seconds

LIVE_DIR = Path("data/live")
RAW_SNAPSHOT = LIVE_DIR / "matches_raw.json"
LASTGOOD_SNAPSHOT = LIVE_DIR / "matches_lastgood.json"

DUCKDB_PATH = batch_config.DUCKDB_PATH  # shared serving store
