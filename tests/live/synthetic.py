"""Synthetic Sofascore match_dict builder (mirrors the verified real shape)."""

def match_dict(mid=1, home="Norway", home_code="NOR", away="Egypt", away_code="EGY",
               home_score=None, away_score=None, status="finished",
               start_ts=1782500400, group_name=None, round_name=None, round_num=1):
    """Build a Sofascore-shaped match dict. Group match if group_name set; knockout if round_name set."""
    md = {
        "id": mid,
        "homeTeam": {"name": home, "nameCode": home_code},
        "awayTeam": {"name": away, "nameCode": away_code},
        "status": {"type": status, "description": status.title()},
        "startTimestamp": start_ts,
        "roundInfo": {"round": round_num} if not round_name else {"round": round_num, "name": round_name},
        "tournament": {"isGroup": group_name is not None,
                       "groupName": group_name} if group_name else {"isGroup": False},
    }
    if home_score is not None:
        md["homeScore"] = {"current": home_score}
    if away_score is not None:
        md["awayScore"] = {"current": away_score}
    return md
