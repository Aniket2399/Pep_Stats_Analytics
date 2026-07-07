from apex.live import cli

def test_refresh_calls_serve_once(monkeypatch):
    calls = {"n": 0}
    monkeypatch.setattr(cli, "serve", lambda client, now_ts: calls.__setitem__("n", calls["n"] + 1) or {"source": "live", "live": 1, "fixtures": 0, "standings": 0})
    monkeypatch.setattr(cli, "SofascoreClient", lambda: object())
    rc = cli.main(["refresh"])
    assert rc == 0 and calls["n"] == 1

def test_watch_swallows_errors_and_stops_on_interrupt(monkeypatch):
    def _boom(client, now_ts):
        raise RuntimeError("boom")
    def _sleep(seconds):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "serve", _boom)
    monkeypatch.setattr(cli, "SofascoreClient", lambda: object())
    monkeypatch.setattr(cli.time, "sleep", _sleep)
    rc = cli.main(["watch", "--interval", "0"])
    assert rc == 0
