"""Build the head-coach stint database from the CFBD /coaches endpoint.

CFBD's coaches endpoint covers HEAD COACHES only (no coordinators), which
makes it the one attribution source we can pull systematically instead of
hand-verifying. The claim a head-coach profile makes is therefore
REGIME-level — "the offense this program ran under HC X" — regardless of
who called the plays. That is a different hypothesis than play-caller DNA
and the two are never pooled.

Output: data/hc_stints.json at the repo root —
  {coach: {"seasons": [{year, school, games, wins, losses, fbs, full}],
           "stints":  [{school, first, last, n_full}],
           "ambiguous_years": [...]}}

full = games >= FULL_SEASON_GAMES and year != 2020 (COVID seasons are
excluded from everything downstream, pre-registered 2026-07-22).
full = null when CFBD has no game counts for the year (as of 2026-07-22
that is all of 2025: /coaches returns games=0 with SRS/SP populated) —
school assignment is trusted, season completeness is NOT verified.
ambiguous_years flags a name appearing at 2+ schools in the same year with
2+ games at each — usually a midseason move by one person, but possibly two
people sharing a name; downstream movers logic skips those years.

Usage:
    python3 src/hc_database.py                 # writes ../data/hc_stints.json
    python3 src/hc_database.py --start 2014 --end 2025

~2 API calls per season (coaches + fbs teams), all cached.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cfbd import CFBDClient

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_PATH = REPO_ROOT / "data" / "hc_stints.json"

FULL_SEASON_GAMES = 10
COVID_YEAR = 2020


def coach_name(rec: dict) -> str:
    first = rec.get("first_name", rec.get("firstName", "")) or ""
    last = rec.get("last_name", rec.get("lastName", "")) or ""
    return f"{first} {last}".strip()


def build(start: int, end: int) -> dict:
    client = CFBDClient()
    coaches: dict[str, dict] = {}

    for year in range(start, end + 1):
        fbs = client.fbs_teams(year)
        records = client.coaches(year)
        # CFBD backfills game counts late: if NO coach has games for a
        # season, the counts are missing upstream, not the assignments.
        year_has_games = any(
            (s.get("games") or 0) > 0
            for rec in records for s in rec.get("seasons", [])
            if s.get("year") == year
        )
        for rec in records:
            name = coach_name(rec)
            if not name:
                continue
            for s in rec.get("seasons", []):
                if s.get("year") != year or not s.get("school"):
                    continue
                games = s.get("games", 0) or 0
                if games <= 0 and year_has_games:
                    continue
                entry = coaches.setdefault(name, {"seasons": []})
                entry["seasons"].append({
                    "year": year,
                    "school": s["school"],
                    "games": games if year_has_games else None,
                    "wins": s.get("wins", 0) or 0,
                    "losses": s.get("losses", 0) or 0,
                    "fbs": s["school"] in fbs,
                    "full": (games >= FULL_SEASON_GAMES and year != COVID_YEAR)
                            if year_has_games else None,
                })

    for name, entry in coaches.items():
        seasons = sorted(entry["seasons"], key=lambda s: (s["year"], s["school"]))
        entry["seasons"] = seasons

        by_year: dict[int, list] = {}
        for s in seasons:
            by_year.setdefault(s["year"], []).append(s)
        entry["ambiguous_years"] = sorted(
            y for y, ss in by_year.items()
            if len(ss) > 1 and sum((s["games"] or 0) >= 2 or s["games"] is None
                                   for s in ss) > 1
        )

        stints, cur = [], None
        for s in seasons:
            if cur and s["school"] == cur["school"] and s["year"] == cur["last"] + 1:
                cur["last"] = s["year"]
                cur["n_full"] += int(bool(s["full"]))
            else:
                cur = {"school": s["school"], "first": s["year"],
                       "last": s["year"], "n_full": int(bool(s["full"]))}
                stints.append(cur)
        entry["stints"] = stints

    return coaches


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2014,
                    help="first season pulled (2014 = PBP quality floor)")
    ap.add_argument("--end", type=int, default=2025)
    args = ap.parse_args()

    coaches = build(args.start, args.end)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(coaches, indent=2, sort_keys=True) + "\n")

    n_seasons = sum(len(c["seasons"]) for c in coaches.values())
    n_amb = sum(1 for c in coaches.values() if c["ambiguous_years"])
    print(f"{len(coaches)} head coaches, {n_seasons} coach-seasons "
          f"({args.start}-{args.end}) -> {OUT_PATH.relative_to(REPO_ROOT)}")
    print(f"{n_amb} coaches with ambiguous (multi-school) years — flagged, "
          f"skipped by the movers logic in those years.")


if __name__ == "__main__":
    main()
