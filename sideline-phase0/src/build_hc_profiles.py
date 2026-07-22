"""Build head-coach REGIME profiles -> data/profiles/head_coaches/<slug>.json

Regime-level DNA: the offense a program ran with this head coach in charge,
regardless of who called the plays. Complements (never pools with) the
play-caller profiles in data/profiles/coaches/ — see hc_database.py for why
the distinction matters.

Season eligibility mirrors backtest_hc.py: full FBS seasons (>=10 games),
2014+, never 2020, never an ambiguous multi-school year. Seasons whose play
data is not already in the shared disk cache are SKIPPED by default (listed
on the JSON so nothing silently disappears) — running the HC backtests first
caches every mover's film, so the usual flow costs zero API calls:

    python3 src/hc_database.py
    python3 src/backtest_hc.py --test-year 2024   # (etc.)
    python3 src/build_hc_profiles.py

To force-fetch a specific coach's uncached seasons (~17 calls per season):
    python3 src/build_hc_profiles.py --fetch --coach "Scott Frost"
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

from backtest_hc import COVID_YEAR, PBP_FLOOR, load_stints, missing_calls
from cfbd import CFBDClient
from metrics import MIN_SAMPLES, compute_metrics, pool_metrics

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = REPO_ROOT / "data" / "profiles" / "head_coaches"


def slug(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def stability(seasons: dict[str, dict]) -> dict:
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


def eligible_seasons(entry: dict) -> tuple[list, list]:
    ok, skipped = [], []
    for s in entry["seasons"]:
        why = None
        if not s["fbs"]:
            why = "non-FBS"
        elif s["year"] < PBP_FLOOR:
            why = f"pre-{PBP_FLOOR} PBP floor"
        elif s["year"] == COVID_YEAR:
            why = "COVID season (pre-registered exclusion)"
        elif s["year"] in entry["ambiguous_years"]:
            why = "ambiguous multi-school year"
        elif s["full"] is False:
            why = f"partial season ({s['games']} games)"
        (skipped if why else ok).append((s, why))
    return ok, skipped


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--coach", action="append", default=[],
                    help="only these coaches (repeatable); default: all with cached film")
    ap.add_argument("--fetch", action="store_true",
                    help="fetch uncached seasons from the API (default: skip them)")
    args = ap.parse_args()

    db = load_stints()
    targets = args.coach or sorted(db)
    client = CFBDClient()

    written = 0
    for coach in targets:
        entry = db.get(coach)
        if entry is None:
            print(f"!! {coach}: not in hc_stints.json (name must match CFBD exactly)")
            continue

        ok, skipped = eligible_seasons(entry)
        cached = [s for s, _ in ok if missing_calls(s["school"], s["year"]) == 0]
        uncached = [s for s, _ in ok if missing_calls(s["school"], s["year"]) > 0]
        use = [s for s, _ in ok] if args.fetch else cached
        if not use:
            continue  # nothing cached and not fetching — no file, keep dir clean

        season_metrics, sticky_by_season, profiled = [], {}, []
        for s in use:
            plays = client.plays_for_offense(s["school"], s["year"])
            if not plays:
                skipped.append((s, "no plays returned"))
                continue
            m = compute_metrics(plays)
            season_metrics.append(m)
            sticky_by_season[f"{s['school']} {s['year']}"] = m
            profiled.append({"school": s["school"], "year": s["year"],
                             "games": s["games"]})

        if not season_metrics:
            continue

        record = {
            "coach": coach,
            "level": "hc_regime",
            "caveat": (
                "Regime-level attribution: plays belong to the head-coach era, "
                "not a verified play-caller. Do not pool with "
                "data/profiles/coaches/ (play-caller DNA)."
            ),
            "stints": entry["stints"],
            "seasons_profiled": profiled,
            "seasons_excluded": [
                {"school": s["school"], "year": s["year"], "reason": why}
                for s, why in skipped
            ] + ([] if args.fetch else [
                {"school": s["school"], "year": s["year"], "reason": "not cached (rerun with --fetch --coach)"}
                for s in uncached
            ]),
            "pooled_profile": pool_metrics(season_metrics),
            "sticky_by_season": sticky_by_season,
            "stability": stability(sticky_by_season),
        }
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / f"{slug(coach)}.json").write_text(
            json.dumps(record, indent=2) + "\n")
        written += 1

        npr = record["pooled_profile"]["neutral_pass_rate"]
        note = (f"  neutral_pass_rate={npr['value']:.3f} (n={npr['n']})"
                if npr["value"] is not None else "")
        print(f"{coach:24s} seasons={len(profiled)}{note}")

    print(f"\nWrote {written} HC regime profiles -> {OUT_DIR.relative_to(REPO_ROOT)}/")


if __name__ == "__main__":
    main()
