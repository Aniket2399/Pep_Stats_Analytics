"""Model: player_season aggregates + league-wide position-group percentiles."""
import pandas as pd
from .. import config

PER90_METRICS = ["goals_per90", "assists_per90", "xg_per90", "xa_per90",
                 "shots_per90", "passes_per90", "prog_passes_per90",
                 "pressures_per90", "tackles_per90", "interceptions_per90"]

def compute_minutes(master: pd.DataFrame) -> pd.DataFrame:
    """Minutes per (player_id, team_id) from Starting XI + Substitution events."""
    records = {}   # (player_id, team_id) -> minutes
    apps = {}
    for match_id, mev in master.groupby("match_id"):
        match_end = float(mev["minute"].max() or 0)
        # starters from Starting XI tactics
        on = {}   # player_id -> (team_id, start_minute)
        for _, r in mev[mev["type"] == "Starting XI"].iterrows():
            tac = r["tactics"] or {}
            for item in tac.get("lineup", []):
                pid = item["player"]["id"]
                on[pid] = (r["team_id"], 0.0)
        # substitutions: player off, replacement on
        for _, r in mev[mev["type"] == "Substitution"].sort_values("minute").iterrows():
            minute = float(r["minute"])
            off_pid = r["player_id"]
            if off_pid in on:
                tid, start = on.pop(off_pid)
                _add(records, apps, off_pid, tid, minute - start)
            rep = r["substitution_replacement_id"]
            if rep is not None:
                on[rep] = (r["team_id"], minute)
        # anyone still on played to match end
        for pid, (tid, start) in on.items():
            _add(records, apps, pid, tid, match_end - start)
    rows = [{"player_id": pid, "team_id": tid, "minutes": mins, "appearances": apps[(pid, tid)]}
            for (pid, tid), mins in records.items()]
    return pd.DataFrame(rows)

def _add(records, apps, pid, tid, mins):
    key = (pid, tid)
    records[key] = records.get(key, 0.0) + max(0.0, float(mins))
    apps[key] = apps.get(key, 0) + 1

def build_player_season(master: pd.DataFrame) -> pd.DataFrame:
    ev = master
    mins = compute_minutes(ev)

    # per-player raw aggregates (attributed to the player's own events)
    def agg(df, **named):
        g = df.groupby("player_id")
        return pd.DataFrame({name: fn(g) for name, fn in named.items()})

    shots = ev[ev["type"] == "Shot"]
    passes = ev[ev["type"] == "Pass"]
    goals = shots[shots["shot_outcome"] == "Goal"]
    # xA: sum xG of shots each pass assisted (via pass_assisted_shot_id -> shot id)
    shot_xg = shots.set_index("id")["shot_statsbomb_xg"]
    passes = passes.copy()
    passes["assisted_xg"] = passes["pass_assisted_shot_id"].map(shot_xg).fillna(0.0)

    base = pd.DataFrame({"player_id": ev["player_id"].dropna().unique()})
    def sum_by(df, col, pid_from="player_id"):
        return df.groupby(pid_from)[col].sum()
    def count_by(df, pid_from="player_id"):
        return df.groupby(pid_from).size()

    agg_df = pd.DataFrame(index=base["player_id"])
    agg_df["goals"] = count_by(goals).reindex(agg_df.index).fillna(0)
    agg_df["xg"] = sum_by(shots, "shot_statsbomb_xg").reindex(agg_df.index).fillna(0.0)
    agg_df["shots"] = count_by(shots).reindex(agg_df.index).fillna(0)
    agg_df["assists"] = sum_by(passes, "pass_goal_assist").reindex(agg_df.index).fillna(0.0)
    agg_df["xa"] = sum_by(passes, "assisted_xg").reindex(agg_df.index).fillna(0.0)
    agg_df["passes"] = count_by(passes).reindex(agg_df.index).fillna(0)
    prog = passes[(passes["pass_end_x"].fillna(0) - passes["location_x"].fillna(0)) >= 10]
    agg_df["prog_passes"] = count_by(prog).reindex(agg_df.index).fillna(0)
    agg_df["pressures"] = count_by(ev[ev["type"] == "Pressure"]).reindex(agg_df.index).fillna(0)
    agg_df["tackles"] = count_by(ev[ev["type"] == "Duel"]).reindex(agg_df.index).fillna(0)
    agg_df["interceptions"] = count_by(ev[ev["type"] == "Interception"]).reindex(agg_df.index).fillna(0)

    # identity: team, name, primary position (most frequent non-null position)
    ident = (ev.dropna(subset=["player_id"])
               .groupby("player_id")
               .agg(player=("player", "first"), team_id=("team_id", "first"),
                    team=("team", "first")))
    pos = (ev.dropna(subset=["player_id", "position"])
             .groupby("player_id")["position"]
             .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else None))
    ident["primary_position"] = pos
    ident["position_group"] = ident["primary_position"].map(config.position_group)

    out = ident.join(agg_df).reset_index().merge(mins, on="player_id", how="left")
    out["team_id"] = out["team_id_x"].fillna(out.get("team_id_y")) if "team_id_x" in out else out["team_id"]
    out = out.drop(columns=[c for c in ["team_id_x", "team_id_y"] if c in out.columns], errors="ignore")
    out["minutes"] = out["minutes"].fillna(0.0)
    out["appearances"] = out["appearances"].fillna(0).astype(int)

    # per-90
    per90 = out["minutes"].replace(0, pd.NA)
    out["goals_per90"] = out["goals"] / per90 * 90
    out["assists_per90"] = out["assists"] / per90 * 90
    out["xg_per90"] = out["xg"] / per90 * 90
    out["xa_per90"] = out["xa"] / per90 * 90
    out["shots_per90"] = out["shots"] / per90 * 90
    out["passes_per90"] = out["passes"] / per90 * 90
    out["prog_passes_per90"] = out["prog_passes"] / per90 * 90
    out["pressures_per90"] = out["pressures"] / per90 * 90
    out["tackles_per90"] = out["tackles"] / per90 * 90
    out["interceptions_per90"] = out["interceptions"] / per90 * 90
    for m in PER90_METRICS:
        out[m] = out[m].fillna(0.0)

    # league-wide percentiles within position group, among eligible players
    eligible = out["minutes"] >= config.MIN_MINUTES
    for m in PER90_METRICS:
        pct_col = "percentile_" + m
        out[pct_col] = 0.0
        for grp, idx in out[eligible].groupby("position_group").groups.items():
            ranks = out.loc[idx, m].rank(pct=True) * 100
            out.loc[idx, pct_col] = ranks.round(1)
    out["season"] = config.SEASON_LABEL
    return out
