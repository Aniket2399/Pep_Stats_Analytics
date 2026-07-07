from fastapi.testclient import TestClient
from apex.api.app import app

client = TestClient(app, raise_server_exceptions=False)

def test_clubs(apex_db):
    r = client.get("/api/clubs")
    assert r.status_code == 200
    assert [c["team"] for c in r.json()] == ["Alpha", "Beta"]

def test_players_filter(apex_db):
    r = client.get("/api/players", params={"club": 1, "position": "FWD"})
    assert r.status_code == 200 and [p["player"] for p in r.json()] == ["Striker A"]

def test_player_detail_and_404(apex_db):
    assert client.get("/api/players/10").json()["player"] == "Striker A"
    assert client.get("/api/players/99999").status_code == 404

def test_players_bad_param_422(apex_db):
    assert client.get("/api/players", params={"club": "abc"}).status_code == 422

def test_teams_and_team_404(apex_db):
    assert len(client.get("/api/teams").json()) == 2
    assert client.get("/api/teams/2").json()["team"] == "Beta"
    assert client.get("/api/teams/404").status_code == 404

def test_standings_and_shots(apex_db):
    assert [t["team"] for t in client.get("/api/standings").json()] == ["Alpha", "Beta"]
    assert [s["shot_id"] for s in client.get("/api/shots", params={"club": 1}).json()] == ["s1"]
