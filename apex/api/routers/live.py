"""Live (Sofascore WC 2026) read routes."""
import logging
import subprocess
import sys
from pathlib import Path
from fastapi import APIRouter, Depends
from ..db import get_db
from .. import queries

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/live", tags=["live"])

# Repo root (apex/api/routers/live.py -> parents[3]); config paths are relative to it.
_ROOT = Path(__file__).resolve().parents[3]

@router.post("/refresh")
def refresh_live():
    """Trigger the speed layer to fetch the latest scores and rebuild the WC
    tables. Runs in a subprocess (separate DuckDB write connection); on a failed
    live scrape the pipeline falls back to the last-good snapshot."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "apex.live.cli", "refresh"],
            cwd=str(_ROOT), capture_output=True, text=True, timeout=90,
        )
        log = (proc.stderr or proc.stdout)[-400:]
        if proc.returncode != 0:
            # capture_output keeps this out of the host's log stream; log it here or
            # a broken refresh leaves no trace anywhere but the HTTP response body.
            logger.error("live refresh failed (exit %d): %s", proc.returncode, log)
        return {"ok": proc.returncode == 0, "log": log}
    except Exception as e:  # subprocess failure / timeout — report, don't crash the API
        logger.exception("live refresh could not run")
        return {"ok": False, "error": str(e)}

@router.get("/matches")
def get_live_matches(con=Depends(get_db)):
    return queries.live_matches(con)

@router.get("/fixtures")
def get_fixtures(con=Depends(get_db)):
    return queries.fixtures(con)

@router.get("/standings")
def get_live_standings(con=Depends(get_db)):
    return queries.live_standings(con)

@router.get("/knockout")
def get_knockout(con=Depends(get_db)):
    return queries.knockout(con)
