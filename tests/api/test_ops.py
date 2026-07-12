from fastapi.testclient import TestClient
from apex.api.app import app
from apex import config

client = TestClient(app, raise_server_exceptions=False)

def test_health_reports_table_counts(apex_db):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["tables"]["player_season"] == 3 and body["tables"]["team_season"] == 2

def test_meta_has_source(apex_db):
    r = client.get("/api/meta")
    assert r.status_code == 200 and r.json()["source"] == "apex.duckdb"

def test_503_when_db_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DUCKDB_PATH", tmp_path / "gone.duckdb")
    r = client.get("/health")
    assert r.status_code == 503

def test_meta_reports_live_updated_from_live_meta_table(apex_db):
    import duckdb
    con = duckdb.connect(str(apex_db))
    con.execute("create table live_meta as select "
                "'2026-07-12T10:00:00+00:00' as updated_at, 'live' as source")
    con.close()

    body = client.get("/api/meta").json()
    assert body["live_updated"] == "2026-07-12T10:00:00+00:00"

def test_meta_live_updated_is_null_without_the_table(apex_db, tmp_path, monkeypatch):
    """Older DBs built before live_meta existed must not 500.

    RAW_SNAPSHOT must be pointed at a path that does not exist: the mtime fallback
    would otherwise read the real data/live/matches_raw.json, which Task 5's scrape
    creates on a developer machine — passing in CI and failing locally.
    """
    from apex.live import config as live_config
    monkeypatch.setattr(live_config, "RAW_SNAPSHOT", tmp_path / "absent.json")

    body = client.get("/api/meta").json()
    assert body["live_updated"] is None
    assert body["source"] == "apex.duckdb"
