"""
football-data.org v4 client for FIFA World Cup 2026.
The ONLY module that talks to the provider. Returns normalized data only.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional

import requests
from dotenv import load_dotenv

# Load .env so FOOTBALL_API_KEY is available to any entrypoint using this client
# (the FastAPI server, the scraper, or standalone runs).
load_dotenv()

logger = logging.getLogger(__name__)

BASE_URL = "https://api.football-data.org/v4"
COMPETITION = "WC"


class FootballDataError(Exception):
    """Raised on any provider failure (bad key, quota, network, non-200)."""


_STATUS = {
    "IN_PLAY": "LIVE", "PAUSED": "LIVE",
    "SCHEDULED": "SCHEDULED", "TIMED": "SCHEDULED",
    "FINISHED": "FINISHED", "AWARDED": "FINISHED",
}


def map_status(s: str) -> str:
    mapped = _STATUS.get(s)
    if mapped is None:
        logger.warning("Unknown match status %r -> SCHEDULED", s)
        return "SCHEDULED"
    return mapped


_FLAGS = {
    "France": "🇫🇷", "Argentina": "🇦🇷", "Spain": "🇪🇸", "England": "🏴",
    "Brazil": "🇧🇷", "Germany": "🇩🇪", "Portugal": "🇵🇹", "Netherlands": "🇳🇱",
    "Belgium": "🇧🇪", "Croatia": "🇭🇷", "Italy": "🇮🇹", "Uruguay": "🇺🇾",
    "Colombia": "🇨🇴", "Ghana": "🇬🇭", "Morocco": "🇲🇦", "Canada": "🇨🇦",
    "United States": "🇺🇸", "Mexico": "🇲🇽", "Japan": "🇯🇵", "South Korea": "🇰🇷",
    "Senegal": "🇸🇳", "Nigeria": "🇳🇬", "Australia": "🇦🇺", "Switzerland": "🇨🇭",
    "Denmark": "🇩🇰", "Poland": "🇵🇱", "Norway": "🇳🇴", "Paraguay": "🇵🇾",
    "Ecuador": "🇪🇨", "Serbia": "🇷🇸", "Cameroon": "🇨🇲", "Ivory Coast": "🇨🇮",
    "Saudi Arabia": "🇸🇦", "Qatar": "🇶🇦", "Iran": "🇮🇷", "Wales": "🏴",
    "Costa Rica": "🇨🇷", "Tunisia": "🇹🇳", "Algeria": "🇩🇿", "Egypt": "🇪🇬",
}


def country_to_flag(name: str) -> str:
    flag = _FLAGS.get(name)
    if flag is None:
        logger.warning("No flag emoji for %r", name)
        return "🏳️"
    return flag


def elapsed_minutes(utc_date: str, now: datetime) -> int:
    start = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
    mins = int((now - start).total_seconds() // 60)
    return max(0, min(mins, 130))


class FootballDataClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = BASE_URL):
        self.api_key = api_key or os.getenv("FOOTBALL_API_KEY")
        self.base_url = base_url

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        try:
            resp = requests.get(
                f"{self.base_url}/{path}",
                headers={"X-Auth-Token": self.api_key or ""},
                params=params or {},
                timeout=15,
            )
        except requests.RequestException as e:
            raise FootballDataError(f"request failed: {e}")
        if resp.status_code != 200:
            raise FootballDataError(f"HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    def _normalize_match(self, m: dict, now: Optional[datetime] = None) -> dict:
        status = map_status(m["status"])
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        ft = (m.get("score") or {}).get("fullTime") or {}
        if status == "LIVE":
            minute = m.get("minute")
            if minute is not None:
                time = f"{minute}'"
            else:
                time = f"{elapsed_minutes(m['utcDate'], now or datetime.now(timezone.utc))}'"
        else:
            time = m["utcDate"]
        return {
            "id": m["id"],
            "team1": {"name": home, "flag": country_to_flag(home), "score": ft.get("home") or 0},
            "team2": {"name": away, "flag": country_to_flag(away), "score": ft.get("away") or 0},
            "time": time,
            "stadium": m.get("venue"),
            "status": status,
        }

    def get_matches(self) -> dict:
        matches = self._get(f"competitions/{COMPETITION}/matches").get("matches", [])
        live, upcoming, recent = [], [], []
        for m in matches:
            s = map_status(m["status"])
            if s == "LIVE":
                live.append(self._normalize_match(m))
            elif s == "SCHEDULED":
                upcoming.append(m)
            else:
                recent.append(m)
        upcoming.sort(key=lambda x: x["utcDate"])
        recent.sort(key=lambda x: x["utcDate"], reverse=True)
        return {
            "live": live,
            "upcoming": [self._normalize_match(m) for m in upcoming[:10]],
            "recent": [self._normalize_match(m) for m in recent[:5]],
        }

    def get_match(self, mid: int) -> Optional[dict]:
        m = self._get(f"matches/{mid}")
        if not m or "id" not in m:
            return None
        return self._normalize_match(m)

    def get_standings(self) -> list:
        data = self._get(f"competitions/{COMPETITION}/standings")
        rows = []
        for block in data.get("standings", []):
            if block.get("type") != "TOTAL":
                continue
            group = block.get("group")
            for r in block.get("table", []):
                rows.append({
                    "group": group,
                    "rank": r["position"],
                    "team": r["team"]["name"],
                    "flag": country_to_flag(r["team"]["name"]),
                    "w": r["won"], "d": r["draw"], "l": r["lost"],
                    "gf": r["goalsFor"], "ga": r["goalsAgainst"], "pts": r["points"],
                })
        return rows

    def get_topscorers(self) -> list:
        data = self._get(f"competitions/{COMPETITION}/scorers")
        rows = []
        for i, s in enumerate(data.get("scorers", []), start=1):
            nat = s["player"].get("nationality") or s.get("team", {}).get("name", "")
            rows.append({
                "rank": i,
                "player": s["player"]["name"],
                "team": s.get("team", {}).get("name", ""),
                "flag": country_to_flag(nat),
                "goals": s.get("goals") or 0,
                "assists": s.get("assists") or 0,
            })
        return rows

    def get_events(self, mid: int) -> list:
        m = self._get(f"matches/{mid}")
        out = []
        for g in m.get("goals", []) or []:
            out.append({
                "minute": g.get("minute"),
                "type": "goal",
                "team": g.get("team", {}).get("name", ""),
                "player": g.get("scorer", {}).get("name", ""),
            })
        return out
