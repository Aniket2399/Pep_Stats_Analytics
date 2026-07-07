import duckdb
from apex.live import serve as sv, config, cache
from tests.live.synthetic import match_dict

class StubClient:
    def __init__(self, matches): self.matches = matches
    def get_wc_matches(self): return self.matches

def _paths(tmp, monkeypatch):
    monkeypatch.setattr(config, "LIVE_DIR", tmp)
    monkeypatch.setattr(config, "RAW_SNAPSHOT", tmp / "raw.json")
    monkeypatch.setattr(config, "LASTGOOD_SNAPSHOT", tmp / "lastgood.json")
    monkeypatch.setattr(config, "DUCKDB_PATH", tmp / "apex.duckdb")

def test_serve_creates_three_tables(tmp_path, monkeypatch):
    _paths(tmp_path, monkeypatch)
    matches = [
        match_dict(mid=1, status="inprogress", start_ts=1000, group_name="Group A",
                   home="A", away="B", home_score=1, away_score=0),
        match_dict(mid=2, status="notstarted", start_ts=9_000_000_000,
                   round_name="Round of 16", round_num=5, home="C", away="D"),
        match_dict(mid=3, status="finished", start_ts=1000, group_name="Group A",
                   home="A", away="B", home_score=2, away_score=1),
    ]
    res = sv.serve(StubClient(matches), now_ts=1000 + 60)
    assert res["source"] == "live"
    con = duckdb.connect(str(config.DUCKDB_PATH))
    assert con.execute("select count(*) from fixtures").fetchone()[0] == 1        # match 2
    assert con.execute("select count(*) from standings").fetchone()[0] == 2       # A,B in Group A
    assert con.execute("select count(*) from live_matches").fetchone()[0] >= 1    # match 1 live

def test_serve_empty_leaves_existing_tables(tmp_path, monkeypatch):
    _paths(tmp_path, monkeypatch)
    # prime a table
    duckdb.connect(str(config.DUCKDB_PATH)).execute("create table live_matches as select 1 as id")
    class Empty:
        def get_wc_matches(self): from apex.live.client import LiveDataError; raise LiveDataError("x")
    res = sv.serve(Empty(), now_ts=0)
    assert res["source"] == "unavailable"
    con = duckdb.connect(str(config.DUCKDB_PATH))
    assert con.execute("select count(*) from live_matches").fetchone()[0] == 1    # untouched

def test_serve_unparseable_matches_leave_tables_intact(tmp_path, monkeypatch):
    _paths(tmp_path, monkeypatch)
    # prime all three tables with 1 row each
    con = duckdb.connect(str(config.DUCKDB_PATH))
    con.execute("create table live_matches as select 1 as id")
    con.execute("create table fixtures as select 1 as id")
    con.execute("create table standings as select 1 as id")
    con.close()

    class StubClient:
        def get_wc_matches(self): return [{"id": 1}]  # missing status/homeTeam -> fails normalize

    res = sv.serve(StubClient(), now_ts=1000)
    assert res["live"] == 0 and res["fixtures"] == 0 and res["standings"] == 0

    con = duckdb.connect(str(config.DUCKDB_PATH))
    assert con.execute("select count(*) from live_matches").fetchone()[0] == 1     # untouched
    assert con.execute("select count(*) from fixtures").fetchone()[0] == 1         # untouched
    assert con.execute("select count(*) from standings").fetchone()[0] == 1        # untouched
