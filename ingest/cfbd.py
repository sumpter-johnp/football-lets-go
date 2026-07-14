"""CFBD API client for the Phase 1 ingest layer.

Evolved from sideline-phase0/src/cfbd.py: same disk-cache pattern (every GET
cached under data/cache/ keyed by a hash of endpoint+params; re-runs cost zero
API calls), same camelCase→snake_case normalization at the API boundary, plus
the endpoints Phase 1 needs (games, full team metadata, defensive plays).

Requires CFBD_API_KEY in the environment or .env (free key:
https://collegefootballdata.com/key).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

import requests

from config import REPO_ROOT, load_env

BASE_URL = "https://api.collegefootballdata.com"
CACHE_DIR = REPO_ROOT / "data" / "cache"
SLEEP_BETWEEN_CALLS = 0.35  # be polite to the free tier

_CAMEL_RE = re.compile(r"(?<!^)(?=[A-Z])")


def snake_keys(obj: dict) -> dict:
    """CFBD payloads use camelCase (playType, yardsToGoal, ...); everything
    downstream expects snake_case. Normalize at the API boundary."""
    return {_CAMEL_RE.sub("_", k).lower(): v for k, v in obj.items()}


class CFBDClient:
    def __init__(self, api_key: str | None = None):
        load_env()
        self.api_key = api_key or os.environ.get("CFBD_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "No CFBD API key found. Set CFBD_API_KEY in your environment "
                "or in .env (see .env.example).\n"
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

    def plays_for_team(self, team: str, year: int) -> list[dict]:
        """All plays involving a team-season, both sides of the ball
        (offense=team for their offensive identity, defense=team for what
        opponents did to them). Deduped by play id."""
        plays: dict[str, dict] = {}
        for side in ("offense", "defense"):
            for week in range(1, 17):
                for p in self.get(
                    "/plays",
                    {"year": year, "week": week, side: team, "seasonType": "regular"},
                ):
                    plays[str(p["id"])] = p
            for p in self.get(
                "/plays",
                {"year": year, "week": 1, side: team, "seasonType": "postseason"},
            ):
                plays[str(p["id"])] = p
        return [snake_keys(p) for p in plays.values()]

    def games_for_team(self, team: str, year: int) -> list[dict]:
        games = []
        for season_type in ("regular", "postseason"):
            games += self.get(
                "/games", {"year": year, "team": team, "seasonType": season_type}
            )
        return [snake_keys(g) for g in games]

    def fbs_teams(self, year: int) -> list[dict]:
        return [snake_keys(t) for t in self.get("/teams/fbs", {"year": year})]
