"""All SQL for the serving API. Parameterized; reserved word 'group' quoted."""
import math
import os
from apex import config
from .db import table_exists

_TABLES = ["player_season", "team_season", "shots", "live_matches", "fixtures", "standings"]

def _clean(v):
    if isinstance(v, float) and not math.isfinite(v):
        return None
    return v

def _rows(con, sql, params=()):
    cur = con.execute(sql, list(params))
    cols = [d[0] for d in cur.description]
    return [{c: _clean(v) for c, v in zip(cols, row)} for row in cur.fetchall()]

def _one(con, sql, params=()):
    rows = _rows(con, sql, params)
    return rows[0] if rows else None

def clubs(con):
    if not table_exists(con, "team_season"):
        return []
    return _rows(con, "SELECT team_id, team FROM team_season ORDER BY team")

def players(con, club=None, position=None, limit=None):
    if not table_exists(con, "player_season"):
        return []
    sql = "SELECT * FROM player_season WHERE 1=1"
    params = []
    if club is not None:
        sql += " AND team_id = ?"; params.append(club)
    if position is not None:
        sql += " AND position_group = ?"; params.append(position)
    sql += " ORDER BY minutes DESC"
    if limit is not None:
        sql += " LIMIT ?"; params.append(limit)
    return _rows(con, sql, params)

def player(con, player_id):
    if not table_exists(con, "player_season"):
        return None
    return _one(con, "SELECT * FROM player_season WHERE player_id = ? "
                     "ORDER BY minutes DESC LIMIT 1", [player_id])

def teams(con):
    if not table_exists(con, "team_season"):
        return []
    return _rows(con, "SELECT * FROM team_season ORDER BY team")

def team(con, team_id):
    if not table_exists(con, "team_season"):
        return None
    return _one(con, "SELECT * FROM team_season WHERE team_id = ?", [team_id])

def standings(con):
    if not table_exists(con, "team_season"):
        return []
    return _rows(con, "SELECT * FROM team_season ORDER BY points DESC, gd DESC, gf DESC")

def shots(con, club=None, player=None, match=None):
    if not table_exists(con, "shots"):
        return []
    sql = "SELECT * FROM shots WHERE 1=1"
    params = []
    if club is not None:
        sql += " AND team_id = ?"; params.append(club)
    if player is not None:
        sql += " AND player_id = ?"; params.append(player)
    if match is not None:
        sql += " AND match_id = ?"; params.append(match)
    return _rows(con, sql, params)

def live_matches(con):
    if not table_exists(con, "live_matches"):
        return []
    return _rows(con, "SELECT * FROM live_matches ORDER BY kickoff")

def fixtures(con):
    if not table_exists(con, "fixtures"):
        return []
    return _rows(con, "SELECT * FROM fixtures ORDER BY kickoff")

def live_standings(con):
    if not table_exists(con, "standings"):
        return []
    return _rows(con, 'SELECT * FROM standings ORDER BY "group", rank')

def knockout(con):
    if not table_exists(con, "knockout"):
        return []
    return _rows(con, "SELECT * FROM knockout ORDER BY kickoff")

def table_counts(con):
    out = {}
    for t in _TABLES:
        out[t] = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] if table_exists(con, t) else 0
    return out

def _mtime_iso(path):
    import datetime
    if path.exists():
        return datetime.datetime.fromtimestamp(os.path.getmtime(path),
                                                tz=datetime.timezone.utc).isoformat()
    return None

def meta(con=None):
    """live_updated comes from the live_meta table, not a file mtime: the DB is the
    only artifact the Docker image copies, so a mtime-based answer is null in prod."""
    from apex.live import config as live_config
    live_updated = None
    if con is not None and table_exists(con, "live_meta"):
        row = con.execute("SELECT updated_at FROM live_meta LIMIT 1").fetchone()
        live_updated = row[0] if row else None
    if live_updated is None:                       # local dev / pre-live_meta DBs
        live_updated = _mtime_iso(live_config.RAW_SNAPSHOT)
    return {
        "historic_updated": _mtime_iso(config.PLAYER_SEASON_PARQUET),
        "live_updated": live_updated,
        "source": "apex.duckdb",
    }
