"""
football-data.org v4 client for FIFA World Cup 2026.
The ONLY module that talks to the provider. Returns normalized data only.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Optional

import requests

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
