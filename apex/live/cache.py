"""TTL snapshot cache with last-good fallback."""
import json
import logging
import os
from . import config
from .client import LiveDataError

logger = logging.getLogger(__name__)

def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))

def get_matches_cached(client, ttl, now_ts) -> tuple:
    raw = config.RAW_SNAPSHOT
    if raw.exists() and (now_ts - os.path.getmtime(raw)) < ttl:
        try:
            return json.loads(raw.read_text()), "cache"
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("corrupt raw snapshot %s: %s; falling back to scrape", raw, e)
    try:
        data = client.get_wc_matches()
    except LiveDataError as e:
        logger.warning("live scrape failed: %s", e)
        lg = config.LASTGOOD_SNAPSHOT
        if lg.exists():
            return json.loads(lg.read_text()), "cache"
        return [], "unavailable"
    _write(config.RAW_SNAPSHOT, data)
    _write(config.LASTGOOD_SNAPSHOT, data)
    return data, "live"
