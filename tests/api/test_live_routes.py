import logging
import subprocess
from fastapi.testclient import TestClient
from apex.api.app import app
from apex.api.routers import live as live_router

client = TestClient(app, raise_server_exceptions=False)

def test_live_matches(apex_db):
    r = client.get("/api/live/matches")
    assert r.status_code == 200 and {m["home_team"] for m in r.json()} == {"Spain", "USA"}

def test_live_fixtures(apex_db):
    assert [f["home_team"] for f in client.get("/api/live/fixtures").json()] == ["Brazil"]

def test_live_standings_grouped(apex_db):
    st = client.get("/api/live/standings").json()
    assert [r["team"] for r in st] == ["Mexico", "South Africa"]
    assert st[0]["group"] == "Group A"

def _fake_run(returncode, stderr=""):
    def run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, returncode, stdout="", stderr=stderr)
    return run

def test_refresh_logs_the_subprocess_failure(monkeypatch, caplog):
    """capture_output hides the traceback from the log stream, so the route must
    log it explicitly — otherwise a broken refresh is invisible in Render's logs."""
    monkeypatch.setattr(
        live_router.subprocess, "run",
        _fake_run(1, "ModuleNotFoundError: No module named 'pandas'"),
    )
    with caplog.at_level(logging.ERROR):
        body = client.post("/api/live/refresh").json()

    assert body["ok"] is False
    assert "pandas" in caplog.text

def test_refresh_does_not_log_an_error_on_success(monkeypatch, caplog):
    monkeypatch.setattr(live_router.subprocess, "run", _fake_run(0))
    with caplog.at_level(logging.ERROR):
        body = client.post("/api/live/refresh").json()

    assert body["ok"] is True
    assert caplog.text == ""
