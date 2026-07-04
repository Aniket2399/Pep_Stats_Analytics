import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ingestion"))
import football_data as fd


def test_map_status_live():
    assert fd.map_status("IN_PLAY") == "LIVE"
    assert fd.map_status("PAUSED") == "LIVE"

def test_map_status_scheduled():
    assert fd.map_status("TIMED") == "SCHEDULED"
    assert fd.map_status("SCHEDULED") == "SCHEDULED"

def test_map_status_finished():
    assert fd.map_status("FINISHED") == "FINISHED"
    assert fd.map_status("AWARDED") == "FINISHED"

def test_map_status_unknown_defaults_scheduled():
    assert fd.map_status("POSTPONED") == "SCHEDULED"

def test_country_to_flag_known():
    assert fd.country_to_flag("France") == "🇫🇷"
    assert fd.country_to_flag("Argentina") == "🇦🇷"

def test_country_to_flag_unknown():
    assert fd.country_to_flag("Wakanda") == "🏳️"
