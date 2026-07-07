from apex.api import db, queries as q

def _con():
    return db.get_connection()

def test_clubs_sorted():
    con = _con()
    assert [c["team"] for c in q.clubs(con)] == ["Alpha", "Beta"]

def test_players_filter_by_club_and_position():
    con = _con()
    alpha = q.players(con, club=1)
    assert {p["player"] for p in alpha} == {"Striker A", "Mid A"}
    fwd = q.players(con, club=1, position="FWD")
    assert [p["player"] for p in fwd] == ["Striker A"]

def test_players_sorted_by_minutes_desc_and_limit():
    con = _con()
    top = q.players(con, limit=1)
    assert top[0]["player"] == "Striker A"   # 540 minutes, highest

def test_player_single_and_missing():
    con = _con()
    assert q.player(con, 10)["player"] == "Striker A"
    assert q.player(con, 99999) is None

def test_standings_ordered_by_points():
    con = _con()
    assert [t["team"] for t in q.standings(con)] == ["Alpha", "Beta"]

def test_teams_and_team():
    con = _con()
    assert len(q.teams(con)) == 2
    assert q.team(con, 2)["team"] == "Beta"
    assert q.team(con, 404) is None

def test_shots_filters():
    con = _con()
    assert len(q.shots(con)) == 2
    assert [s["shot_id"] for s in q.shots(con, club=1)] == ["s1"]
    assert [s["shot_id"] for s in q.shots(con, player=20)] == ["s2"]

def test_live_queries():
    con = _con()
    assert {m["home_team"] for m in q.live_matches(con)} == {"Spain", "USA"}
    assert [f["home_team"] for f in q.fixtures(con)] == ["Brazil"]
    st = q.live_standings(con)
    assert [r["team"] for r in st] == ["Mexico", "South Africa"]
    assert st[0]["group"] == "Group A"     # reserved word handled

def test_table_counts():
    con = _con()
    counts = q.table_counts(con)
    assert counts["player_season"] == 3 and counts["team_season"] == 2

def test_clean_handles_nan_and_inf():
    from apex.api import queries
    assert queries._clean(float("nan")) is None
    assert queries._clean(float("inf")) is None
    assert queries._clean(float("-inf")) is None
    assert queries._clean(1.5) == 1.5
    assert queries._clean("x") == "x"
