import os, sys
sys.path.insert(0, "/Users/annie/Documents/All_Projects/FIFA_Data_Project")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))

import fakeredis
import pytest
from api.cache import CacheManager
import ingestion.football_data as fd  # noqa
from ingestion.football_data import FootballDataError


def make_cache():
    c = CacheManager.__new__(CacheManager)      # bypass real-redis __init__
    c.redis_client = fakeredis.FakeStrictRedis(decode_responses=True)
    return c


def test_cached_miss_then_hit():
    from api import main
    cache = make_cache()
    calls = {"n": 0}
    def fetch():
        calls["n"] += 1
        return {"v": 1}
    d1, s1 = main.cached(cache, "k", 60, fetch)
    d2, s2 = main.cached(cache, "k", 60, fetch)
    assert (d1, s1) == ({"v": 1}, "live")
    assert (d2, s2) == ({"v": 1}, "cache")
    assert calls["n"] == 1  # second call served from cache

def test_cached_falls_back_to_lastgood():
    from api import main
    cache = make_cache()
    main.cached(cache, "k", 1, lambda: {"v": "good"})   # seeds k + k:lastgood
    cache.redis_client.delete("k")                      # expire live key
    def boom():
        raise FootballDataError("down")
    d, s = main.cached(cache, "k", 1, boom)
    assert d == {"v": "good"} and s == "cache"

def test_envelope_mock_when_no_lastgood():
    from api import main
    cache = make_cache()
    def boom():
        raise FootballDataError("down")
    env = main.envelope(cache, "k", 60, boom, mock={"m": True})
    assert env["source"] == "mock" and env["data"] == {"m": True}
    assert "fetched_at" in env

def test_envelope_live():
    from api import main
    cache = make_cache()
    env = main.envelope(cache, "k2", 60, lambda: [1, 2], mock=[])
    assert env["source"] == "live" and env["data"] == [1, 2]
