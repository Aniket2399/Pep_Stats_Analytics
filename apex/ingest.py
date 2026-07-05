"""Ingest stage: statsbombpy -> data/raw/*.parquet (only network stage)."""
import logging
from . import config

logger = logging.getLogger(__name__)

def _default_sb():
    from statsbombpy import sb
    return sb

def ingest(season_id: int = config.SEASON_ID, force: bool = False, _sb=None) -> dict:
    sb = _sb or _default_sb()
    config.RAW_EVENTS_DIR.mkdir(parents=True, exist_ok=True)

    matches = sb.matches(competition_id=config.COMPETITION_ID, season_id=season_id)
    matches.to_parquet(config.MATCHES_PARQUET, index=False)

    fetched = skipped = 0
    failed = []
    for match_id in matches["match_id"].tolist():
        out = config.RAW_EVENTS_DIR / f"{match_id}.parquet"
        if out.exists() and not force:
            skipped += 1
            continue
        try:
            ev = sb.events(match_id=match_id)
        except Exception as e:  # transient network/HTTP
            logger.warning("events fetch failed for %s: %s", match_id, e)
            failed.append(match_id)
            continue
        tmp = out.with_suffix(".parquet.tmp")     # temp-write + rename: no partial files
        ev.to_parquet(tmp, index=False)
        tmp.rename(out)
        fetched += 1

    result = {"matches": len(matches), "events_fetched": fetched,
              "events_skipped": skipped, "failed": failed}
    logger.info("ingest: %s", result)
    return result
