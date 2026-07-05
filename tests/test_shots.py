from apex.model import shots as sh
from apex import clean
from tests.synthetic import raw_events, matches_df

def _m():
    return matches_df([{ "match_id": 1, "match_date": "2016-01-01", "match_week": 1,
        "home_team_id": 1, "home_team": "H", "away_team_id": 2, "away_team": "A",
        "home_score": 1, "away_score": 0}])

def test_build_shots_extracts_shot_rows_only():
    ev = raw_events(1, [
        {"id": "p", "type": "Pass", "team": "H", "team_id": 1, "location": [10.0, 40.0]},
        {"id": "s", "type": "Shot", "team": "H", "team_id": 1, "player": "X", "player_id": 9,
         "minute": 30, "location": [112.0, 38.0], "shot_statsbomb_xg": 0.55,
         "shot_outcome": "Goal", "shot_body_part": "Right Foot", "shot_type": "Open Play"},
    ])
    out = sh.build_shots(clean.clean({1: ev}, _m()))
    assert len(out) == 1
    r = out.iloc[0]
    assert r.shot_id == "s" and r.team_id == 1 and r.minute == 30
    assert (r.location_x, r.location_y) == (112.0, 38.0)
    assert round(r.shot_statsbomb_xg, 2) == 0.55 and r.outcome == "Goal"
    assert set(["shot_id","match_id","team_id","team","player_id","player","minute",
                "location_x","location_y","shot_statsbomb_xg","outcome","body_part",
                "shot_type","play_pattern","under_pressure"]).issubset(out.columns)
