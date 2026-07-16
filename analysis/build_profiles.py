"""Build Phase 2 tendency profiles from the sideline DB.

Usage:
    python3 analysis/build_profiles.py            # writes data/profiles/
    python3 analysis/build_profiles.py --min-games 10

Outputs, all JSON:
  data/profiles/league_baseline.json      pass-rate mixing baseline (with caveat)
  data/profiles/teams/<school>_<year>.json    one per FULLY ingested team-season
  data/profiles/coaches/<coach>.json          one per attributed play-caller

Plays reach coaches only through sideline.play_attribution (game-level
overrides + verified stints) — never a raw stints join; that is the whole
point of migration 0002. Partially ingested team-seasons (opponent-side film
from games vs our ingested teams) are excluded from team profiles and pooled
coach profiles — those samples are biased by who the opponent was — but are
listed on coach JSONs as fragments so nothing silently disappears.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(REPO_ROOT / "ingest"), str(REPO_ROOT / "analysis")]

from psycopg2.extras import RealDictCursor

import db
from predictability import league_baseline, score
from tendencies import MIN_SAMPLES, profile, sticky_metrics

OUT_DIR = REPO_ROOT / "data" / "profiles"

PLAYS_SQL = """
select p.id, p.game_id, p.drive_id, p.season, p.week, p.offense_team_id,
       p.period, p.clock_seconds, p.down, p.distance, p.yards_to_goal,
       p.yards_gained, p.play_type, p.offense_score, p.defense_score,
       p.ppa, p.scoring, p.drive_number, p.play_number,
       t.school, pa.coach_id, c.name as caller, pa.basis
from sideline.plays p
join sideline.teams t on t.id = p.offense_team_id
left join sideline.play_attribution pa on pa.play_id = p.id
left join sideline.coaches c on c.id = pa.coach_id
"""

GAMES_SQL = """
select t.id as team_id, g.season, count(*) as n_games
from sideline.games g
join sideline.teams t on t.id in (g.home_team_id, g.away_team_id)
group by t.id, g.season
"""


def slug(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def dump(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n")


def stability(seasons: dict[str, dict]) -> dict:
    """Cross-season spread per sticky dial, over seasons meeting the Phase 0
    minimum sample. <2 qualifying seasons -> spread None (say so, don't fake)."""
    out = {}
    for name, min_n in MIN_SAMPLES.items():
        vals = {
            label: s[name]["value"]
            for label, s in seasons.items()
            if s[name]["value"] is not None and s[name]["n"] >= min_n
        }
        out[name] = {
            "per_season": vals,
            "spread": (max(vals.values()) - min(vals.values())) if len(vals) >= 2 else None,
            "n_seasons": len(vals),
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-games", type=int, default=10,
                    help="games in DB for a team-season to count as fully ingested")
    args = ap.parse_args()

    conn = db.connect()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(PLAYS_SQL)
        plays = cur.fetchall()
        cur.execute(GAMES_SQL)
        games = {(r["team_id"], r["season"]): r["n_games"] for r in cur.fetchall()}
    conn.close()

    full = {k for k, n in games.items() if n >= args.min_games}
    baseline = league_baseline(plays)
    dump(OUT_DIR / "league_baseline.json", {
        "caveat": (
            "Baseline from all offensive plays currently in sideline.plays — "
            "biased toward games involving the fully ingested teams. Firms up "
            "as the ingest queue lands."
        ),
        "n_plays": len(plays),
        "buckets": baseline,
    })

    # ---- team-season profiles (fully ingested only) ----
    by_team_season: dict = {}
    for p in plays:
        by_team_season.setdefault((p["offense_team_id"], p["season"], p["school"]), []).append(p)

    n_team_files = 0
    for (team_id, season, school), tplays in sorted(by_team_season.items(), key=lambda x: x[0][2]):
        if (team_id, season) not in full:
            continue
        prof = profile(tplays)
        dump(OUT_DIR / "teams" / f"{slug(school)}_{season}.json", {
            "school": school,
            "season": season,
            "games_in_db": games[(team_id, season)],
            "profile": prof,
            "predictability": score(prof["run_pass_by_down_distance"], baseline),
        })
        n_team_files += 1

    # ---- coach profiles via play_attribution ----
    by_coach: dict = {}
    for p in plays:
        if p["coach_id"] is not None and p["basis"] in ("game_override", "season_stint"):
            by_coach.setdefault(p["caller"], []).append(p)

    n_coach_files = 0
    for coach, cplays in sorted(by_coach.items()):
        by_stint: dict = {}
        for p in cplays:
            by_stint.setdefault((p["school"], p["season"], p["offense_team_id"]), []).append(p)

        complete_plays, seasons_sticky, stints, fragments = [], {}, [], []
        for (school, season, team_id), splays in sorted(by_stint.items(), key=lambda x: (x[0][1], x[0][0])):
            entry = {
                "school": school,
                "season": season,
                "n_games": len({p["game_id"] for p in splays}),
                "n_plays": len(splays),
            }
            if (team_id, season) in full:
                stints.append(entry)
                complete_plays += splays
                seasons_sticky[f"{school} {season}"] = sticky_metrics(splays)
            else:
                fragments.append(entry)

        record = {
            "coach": coach,
            "stints_profiled": stints,
            "fragments_excluded": fragments,  # partial team-seasons: biased samples, listed not profiled
        }
        if complete_plays:
            pooled = profile(complete_plays)
            record["pooled_profile"] = pooled
            record["predictability"] = score(pooled["run_pass_by_down_distance"], baseline)
            record["stability"] = stability(seasons_sticky)
            record["sticky_by_season"] = seasons_sticky
        dump(OUT_DIR / "coaches" / f"{slug(coach)}.json", record)
        n_coach_files += 1

        pooled_note = ""
        if complete_plays:
            npr = record["pooled_profile"]["sticky"]["neutral_pass_rate"]
            pooled_note = f"  neutral_pass_rate={npr['value']:.3f} (n={npr['n']})"
        print(f"{coach:22s} stints={len(stints)} fragments={len(fragments)}{pooled_note}")

    print(f"\nWrote {n_team_files} team-season profiles, {n_coach_files} coach profiles, "
          f"1 league baseline -> {OUT_DIR.relative_to(REPO_ROOT)}/")


if __name__ == "__main__":
    main()
