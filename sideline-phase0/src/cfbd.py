"""Thin CFBD API client with a disk cache.

Every GET is cached as JSON under data/cache/ keyed by a hash of the URL+params,
so re-runs cost zero API calls. Delete the cache dir to force a refresh.

Requires CFBD_API_KEY in the environment (free key: https://collegefootballdata.com/key).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

import requests

BASE_URL = "https://api.collegefootballdata.com"
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
SLEEP_BETWEEN_CALLS = 0.35  # be polite to the free tier

_CAMEL_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _snake_keys(play: dict) -> dict:
    """The CFBD /plays payload uses camelCase (playType, yardsToGoal, ...);
    the metrics layer expects snake_case. Normalize at the API boundary so
    cached (camelCase) responses keep working without a re-download."""
    return {_CAMEL_RE.sub("_", k).lower(): v for k, v in play.items()}


class CFBDClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("CFBD_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "No CFBD API key found. Set CFBD_API_KEY in your environment.\n"
                "Get a free key at https://collegefootballdata.com/key"
            )
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def get(self, endpoint: str, params: dict) -> list | dict:
        params = {k: v for k, v in params.items() if v is not None}
        cache_key = hashlib.md5(
            (endpoint + json.dumps(params, sort_keys=True)).encode()
        ).hexdigest()
        cache_file = CACHE_DIR / f"{cache_key}.json"

        if cache_file.exists():
            return json.loads(cache_file.read_text())

        resp = requests.get(
            f"{BASE_URL}{endpoint}",
            params=params,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        cache_file.write_text(json.dumps(data))
        time.sleep(SLEEP_BETWEEN_CALLS)
        return data

    # ---- convenience wrappers ----

    def plays_for_offense(self, team: str, year: int) -> list[dict]:
        """All offensive plays for a team-season (regular + postseason)."""
        plays = []
        for week in range(1, 17):
            plays += self.get(
                "/plays",
                {"year": year, "week": week, "offense": team, "seasonType": "regular"},
            )
        plays += self.get(
            "/plays",
            {"year": year, "week": 1, "offense": team, "seasonType": "postseason"},
        )
        return [_snake_keys(p) for p in plays]

    def coaches(self, year: int) -> list[dict]:
        """Head coach records for a season (HEAD COACHES ONLY — no coordinators)."""
        return self.get("/coaches", {"year": year})

    def fbs_teams(self, year: int) -> set[str]:
        teams = self.get("/teams/fbs", {"year": year})
        return {t["school"] for t in teams}
