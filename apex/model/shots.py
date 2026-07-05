"""Model: shot-level serving table for shot maps."""
import pandas as pd

def build_shots(master: pd.DataFrame) -> pd.DataFrame:
    s = master[master["type"] == "Shot"].copy()
    out = pd.DataFrame({
        "shot_id": s["id"],
        "match_id": s["match_id"],
        "team_id": s["team_id"],
        "team": s["team"],
        "player_id": s["player_id"],
        "player": s["player"],
        "minute": s["minute"],
        "location_x": s["location_x"],
        "location_y": s["location_y"],
        "shot_statsbomb_xg": s["shot_statsbomb_xg"],
        "outcome": s["shot_outcome"],
        "body_part": s["shot_body_part"],
        "shot_type": s["shot_type"],
        "play_pattern": s["play_pattern"],
        "under_pressure": s["under_pressure"].fillna(False),
    })
    return out.reset_index(drop=True)
