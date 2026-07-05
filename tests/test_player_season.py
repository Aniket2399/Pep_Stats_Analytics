import pandas as pd
from apex.model import player_season as ps
from tests.synthetic import raw_events
from apex import clean
from tests.synthetic import matches_df

def _tactics(pids):
    return {"lineup": [{"player": {"id": p, "name": f"P{p}"}, "position": {"name": "Center Forward"}} for p in pids]}

def _matches(ids):
    return matches_df([{ "match_id": mid, "match_date": "2016-01-01", "match_week": 1,
        "home_team_id": 1, "home_team": "H", "away_team_id": 2, "away_team": "A",
        "home_score": 1, "away_score": 0} for mid in ids])

def test_compute_minutes_starter_full_and_subbed():
    ev = raw_events(101, [
        {"id": "sx", "type": "Starting XI", "team": "H", "team_id": 1,
         "minute": 0, "tactics": _tactics([10, 11])},
        {"id": "sub", "type": "Substitution", "team": "H", "team_id": 1, "minute": 60,
         "player": "P10", "player_id": 10, "substitution_replacement_id": 12,
         "substitution_replacement": "P12"},
        {"id": "last", "type": "Pass", "team": "H", "team_id": 1, "minute": 90,
         "player_id": 11, "location": [1.0, 1.0]},
    ])
    mins = ps.compute_minutes(clean.clean({101: ev}, _matches([101])))
    m = mins.set_index("player_id")["minutes"].to_dict()
    assert m[10] == 60      # started, off at 60
    assert m[11] == 90      # played full match
    assert m[12] == 30      # on at 60, to full time 90

def test_build_player_season_xg_xa_and_percentile():
    # two forwards over enough minutes; P10 scores/creates more -> higher percentile
    rows = []
    for mid in range(1, 11):                      # 10 matches -> >450 mins each
        rows.append({"id": f"sx{mid}", "type": "Starting XI", "team": "H", "team_id": 1,
                     "minute": 0, "tactics": _tactics([10, 11])})
        rows.append({"id": f"last{mid}", "type": "Pass", "team": "H", "team_id": 1,
                     "minute": 90, "player_id": 11, "location": [1.0, 1.0]})
        rows.append({"id": f"sh{mid}", "type": "Shot", "team": "H", "team_id": 1,
                     "player": "P10", "player_id": 10, "position": "Center Forward",
                     "location": [110.0, 40.0], "shot_statsbomb_xg": 0.5, "shot_outcome": "Goal"})
        rows.append({"id": f"pa{mid}", "type": "Pass", "team": "H", "team_id": 1,
                     "player": "P11", "player_id": 11, "position": "Center Forward",
                     "location": [80.0, 40.0], "pass_assisted_shot_id": f"sh{mid}"})
    master = clean.clean({1: raw_events(1, rows)}, _matches([1]))
    # give each event a unique id/match so it validates across 10 "matches" folded into one frame
    out = ps.build_player_season(master)
    p10 = out[out.player_id == 10].iloc[0]
    p11 = out[out.player_id == 11].iloc[0]
    assert round(p10.xg, 1) == 5.0                 # 10 shots x 0.5
    assert round(p11.xa, 1) == 5.0                 # assisted 10 shots x 0.5 xG
    assert p10.percentile_xg_per90 >= p11.percentile_xg_per90
    assert set(["player_id","team_id","team","minutes","position_group",
                "goals","xg","xa","percentile_xg_per90"]).issubset(out.columns)


def test_percentile_ranks_eligible_players():
    # Two same-position (FWD) players, each started in 6 distinct matches with no
    # substitutions -> each accrues >= 450 minutes (6 * 91 = 546), clearing
    # MIN_MINUTES=450 so percentiles are computed from real ranking rather than
    # defaulting to 0 for everyone. P10 has a much higher per-90 xG than P11.
    match_ids = [301, 302, 303, 304, 305, 306]
    events_by_match = {}
    for mid in match_ids:
        rows = [
            {"id": f"sx{mid}", "type": "Starting XI", "team": "H", "team_id": 1,
             "minute": 0, "tactics": _tactics([10, 11])},
            {"id": f"sh10_{mid}", "type": "Shot", "team": "H", "team_id": 1,
             "player": "P10", "player_id": 10, "position": "Center Forward",
             "location": [110.0, 40.0], "shot_statsbomb_xg": 0.6, "shot_outcome": "Goal",
             "minute": 30},
            {"id": f"sh11_{mid}", "type": "Shot", "team": "H", "team_id": 1,
             "player": "P11", "player_id": 11, "position": "Center Forward",
             "location": [110.0, 40.0], "shot_statsbomb_xg": 0.1, "shot_outcome": "Off T",
             "minute": 40},
            {"id": f"last{mid}", "type": "Pass", "team": "H", "team_id": 1, "minute": 90,
             "player_id": 11, "position": "Center Forward", "location": [1.0, 1.0]},
        ]
        events_by_match[mid] = raw_events(mid, rows)
    master = clean.clean(events_by_match, _matches(match_ids))
    out = ps.build_player_season(master)
    p10 = out[out.player_id == 10].iloc[0]
    p11 = out[out.player_id == 11].iloc[0]

    assert p10.minutes >= 450
    assert p11.minutes >= 450
    assert p10.position_group == "FWD"
    assert p11.position_group == "FWD"
    assert p10.xg_per90 > p11.xg_per90
    assert p10.percentile_xg_per90 > p11.percentile_xg_per90
