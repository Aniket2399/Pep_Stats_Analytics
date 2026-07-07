"""Serve stage: normalize + derive + write live tables into apex.duckdb."""
import logging
import duckdb
import pandas as pd
from . import config
from .cache import get_matches_cached
from .normalize import normalize_match
from .derive import derive_live, derive_fixtures, derive_standings

logger = logging.getLogger(__name__)

_LIVE_COLS = ["id", "home_team", "away_team", "home_flag", "away_flag",
              "home_score", "away_score", "status", "minute", "stage", "kickoff"]
_FIX_COLS = ["id", "home_team", "away_team", "home_flag", "away_flag", "stage", "kickoff"]
_STAND_COLS = ["group", "rank", "team", "flag", "played", "w", "d", "l", "gf", "ga", "gd", "points"]

def serve(client, now_ts) -> dict:
    raw, source = get_matches_cached(client, config.LIVE_TTL, now_ts)
    if not raw:
        return {"source": source, "live": 0, "fixtures": 0, "standings": 0}

    matches = []
    for md in raw:
        try:
            matches.append(normalize_match(md, now_ts))
        except Exception as e:  # skip a malformed dict, keep going
            logger.warning("skipping malformed match dict %s: %s", md.get("id"), e)

    if not matches:
        logger.warning("no matches normalized (source=%s); leaving existing tables intact", source)
        return {"source": source, "live": 0, "fixtures": 0, "standings": 0}

    live = pd.DataFrame(derive_live(matches, now_ts), columns=_LIVE_COLS)
    fixtures = pd.DataFrame(derive_fixtures(matches), columns=_FIX_COLS)
    standings = pd.DataFrame(derive_standings(matches), columns=_STAND_COLS)

    # Pandas 3.0.3 uses StringDtype by default; DuckDB 1.1.3 doesn't recognize it.
    # Convert StringDtype columns to object for compatibility.
    for df in [live, fixtures, standings]:
        for col in df.columns:
            if df[col].dtype.name == "str":
                df[col] = df[col].astype(object)

    config.DUCKDB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(config.DUCKDB_PATH))
    try:
        # NOTE: "group" is a DuckDB reserved word (standings.group column) -
        # consumers must quote it as "group" in SQL.
        for name, df in [("live_matches", live), ("fixtures", fixtures), ("standings", standings)]:
            con.register("df_tmp", df)
            con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM df_tmp")
            con.unregister("df_tmp")
    finally:
        con.close()
    return {"source": source, "live": len(live), "fixtures": len(fixtures), "standings": len(standings)}
