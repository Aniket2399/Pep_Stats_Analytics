import pandas as pd
from pathlib import Path
from apex import ingest, config

class FakeSB:
    def __init__(self):
        self.events_calls = []
    def matches(self, competition_id, season_id):
        return pd.DataFrame([
            {"match_id": 101, "home_team": "A", "away_team": "B"},
            {"match_id": 102, "home_team": "C", "away_team": "D"},
        ])
    def events(self, match_id):
        self.events_calls.append(match_id)
        return pd.DataFrame([{"id": f"e{match_id}", "type": "Pass", "match_id": match_id}])

def test_ingest_writes_matches_and_events(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(config, "RAW_EVENTS_DIR", tmp_path / "raw" / "events")
    monkeypatch.setattr(config, "MATCHES_PARQUET", tmp_path / "raw" / "matches.parquet")
    fake = FakeSB()
    res = ingest.ingest(_sb=fake)
    assert res["matches"] == 2 and res["events_fetched"] == 2 and res["failed"] == []
    assert config.MATCHES_PARQUET.exists()
    assert (config.RAW_EVENTS_DIR / "101.parquet").exists()

def test_ingest_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(config, "RAW_EVENTS_DIR", tmp_path / "raw" / "events")
    monkeypatch.setattr(config, "MATCHES_PARQUET", tmp_path / "raw" / "matches.parquet")
    fake = FakeSB()
    ingest.ingest(_sb=fake)
    fake.events_calls.clear()
    res = ingest.ingest(_sb=fake)          # second run
    assert res["events_fetched"] == 0 and res["events_skipped"] == 2
    assert fake.events_calls == []          # nothing re-fetched
