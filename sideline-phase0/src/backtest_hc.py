"""HC-regime backtest: does a head coach's program identity travel?

This is the REGIME-level cousin of the play-caller backtest (backtest.py).
For each head coach whose first season at a new FBS school is the test year:

  predictor (a) — pooled offensive tendencies of the coach's PRIOR HC stints
                  (whoever called the plays — the claim is regime identity)
  predictor (b) — the new team's prior-year profile under its previous HC
  actual        — the new team's full test-year profile

Because attribution comes from CFBD's /coaches endpoint (head coaches only,
via hc_database.py) instead of hand-verified play-caller research, this
scales to every qualifying HC mover in every cycle. The two backtests test
DIFFERENT hypotheses and are never pooled.

Pre-registered hygiene filters (2026-07-22, before any HC cycle was run):
  * prior stints: full FBS seasons only (>=10 games), 2014+, never 2020
    (COVID), never at the destination school, never in a flagged
    ambiguous year
  * baseline: destination school must have exactly one HC with a full
    season in the prior year (midseason chaos breaks predictor (b));
    a second HC with <=2 games (bowl interim after a departure) is
    tolerated and noted — that is ~1 game of noise in a 12+ game
    baseline, the same tolerance Phase 0 gave e.g. Nebraska 2022.
    Prior year must not be 2020 -> test years 2021 and 2020 are invalid
  * actual: mover must have a full season at the destination in the test
    year; if CFBD has no game counts yet (all of 2025), the mover is
    included but flagged verify_full_season in the movers audit CSV
  * >=1 qualifying prior season required (--min-prior-seasons to raise)

Usage:
    python3 src/hc_database.py                     # build stint DB first
    python3 src/backtest_hc.py --test-year 2024 --dry-run   # est. API calls
    python3 src/backtest_hc.py --test-year 2024

Outputs: movers_hc_<year>.csv (audit: included+excluded, reasons),
         output/results_hc_<year>.csv, output/verdict_hc_<year>.md
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from backtest import binom_p_two_sided
from cfbd import CACHE_DIR, CFBDClient
from metrics import MIN_SAMPLES, SCORED_METRICS, compute_metrics, pool_metrics

ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = ROOT.parent
OUT = ROOT / "output"
STINTS_PATH = REPO_ROOT / "data" / "hc_stints.json"
METRIC_NAMES = list(MIN_SAMPLES)
COVID_YEAR = 2020
PBP_FLOOR = 2014


def load_stints() -> dict:
    if not STINTS_PATH.exists():
        raise SystemExit(f"{STINTS_PATH} missing — run: python3 src/hc_database.py")
    return json.loads(STINTS_PATH.read_text())


def school_year_index(db: dict) -> dict:
    """(school, year) -> [(coach, games, full)]"""
    idx: dict = {}
    for coach, entry in db.items():
        for s in entry["seasons"]:
            idx.setdefault((s["school"], s["year"]), []).append(
                (coach, s["games"], s["full"])
            )
    return idx


def find_movers(db: dict, test_year: int, min_prior: int) -> tuple[list, list]:
    """Returns (included, excluded) mover dicts with reasons."""
    if test_year - 1 == COVID_YEAR or test_year == COVID_YEAR:
        raise SystemExit(f"test year {test_year} touches 2020 (COVID) — invalid by design")

    idx = school_year_index(db)
    client = CFBDClient()
    fbs_now = client.fbs_teams(test_year)
    fbs_prior = client.fbs_teams(test_year - 1)

    included, excluded = [], []
    for coach, entry in db.items():
        dest = [s for s in entry["seasons"]
                if s["year"] == test_year and s["fbs"] and s["school"] in fbs_now]
        if not dest:
            continue
        if test_year in entry["ambiguous_years"]:
            excluded.append({"coach": coach, "new_team": dest[0]["school"],
                             "reason": "ambiguous multi-school test year"})
            continue
        d = dest[0]
        school = d["school"]

        if any(s["school"] == school and s["year"] < test_year for s in entry["seasons"]):
            continue  # not a mover: has history at the destination

        prior_elsewhere = [
            s for s in entry["seasons"]
            if s["year"] < test_year and s["school"] != school
        ]
        if not prior_elsewhere:
            continue  # first FBS HC job (or promoted from coordinator) — not a mover

        mover = {"coach": coach, "new_team": school}

        if d["full"] is False:
            excluded.append({**mover, "reason":
                             f"partial test-year season ({d['games']} games)"})
            continue

        priors = [
            s for s in prior_elsewhere
            if s["full"] and s["fbs"] and s["year"] >= PBP_FLOOR
            and s["year"] != COVID_YEAR
            and s["year"] not in entry["ambiguous_years"]
        ]
        if len(priors) < min_prior:
            excluded.append({**mover, "reason":
                             f"{len(priors)} qualifying prior FBS HC seasons "
                             f"(min {min_prior}); raw prior seasons: "
                             + "; ".join(f"{s['school']} {s['year']}" for s in prior_elsewhere)})
            continue

        if school not in fbs_prior:
            excluded.append({**mover, "reason": "destination not FBS in baseline year"})
            continue

        base_hcs = idx.get((school, test_year - 1), [])
        full_base = [c for c, g, f in base_hcs if f]
        interims = [(c, g) for c, g, f in base_hcs if not f]
        if len(full_base) != 1 or any((g or 0) > 2 for _, g in interims):
            excluded.append({**mover, "reason":
                             "baseline year not a single full-season HC regime: "
                             + "; ".join(f"{c} ({g} g)" for c, g, f in base_hcs)})
            continue

        mover["prior_stops"] = [(s["school"], s["year"]) for s in priors]
        mover["baseline_hc"] = full_base[0]
        if interims:
            mover["baseline_hc"] += " (+ bowl interim: " + "; ".join(
                f"{c} {g} g" for c, g in interims) + ")"
        mover["verify_full_season"] = d["full"] is None
        included.append(mover)

    return sorted(included, key=lambda m: m["coach"]), sorted(excluded, key=lambda m: m["coach"])


# ---- dry-run call estimation (replicates cfbd.CFBDClient cache keys) ----

def _cache_hit(endpoint: str, params: dict) -> bool:
    key = hashlib.md5((endpoint + json.dumps(params, sort_keys=True)).encode()).hexdigest()
    return (CACHE_DIR / f"{key}.json").exists()

def missing_calls(team: str, year: int) -> int:
    n = 0
    for week in range(1, 17):
        if not _cache_hit("/plays", {"year": year, "week": week,
                                     "offense": team, "seasonType": "regular"}):
            n += 1
    if not _cache_hit("/plays", {"year": year, "week": 1,
                                 "offense": team, "seasonType": "postseason"}):
        n += 1
    return n


ANNOTATION_MARKER = "# --- post-run verification"


def write_movers_csv(path: Path, included: list, excluded: list, test_year: int) -> None:
    # Preserve hand-appended verification blocks across regeneration (they
    # document web-sourced season checks, e.g. the 2025 full-season audit).
    annotation = ""
    if path.exists():
        text = path.read_text()
        idx = text.find(ANNOTATION_MARKER)
        if idx != -1:
            annotation = text[idx:]
    with open(path, "w", newline="") as f:
        f.write(f"# HC-regime movers, test year {test_year} — auto-generated by "
                f"backtest_hc.py from data/hc_stints.json (CFBD /coaches).\n"
                f"# Regime-level attribution: plays belong to the HC era, not a "
                f"verified play-caller. Do not mix with movers_{test_year}.csv.\n")
        w = csv.writer(f)
        w.writerow(["coach", "new_team", "prior_stops", "baseline_hc",
                    "verify_full_season"])
        for m in included:
            stops = "; ".join(f"{s}:{y}" for s, y in m["prior_stops"])
            w.writerow([m["coach"], m["new_team"], stops, m["baseline_hc"],
                        "YES — CFBD game counts missing for this year" if m["verify_full_season"] else ""])
        f.write("# --- excluded candidates ---\n")
        for m in excluded:
            f.write(f"# {m['coach']} -> {m.get('new_team','?')}: {m['reason']}\n")
        if annotation:
            f.write(annotation)


def run(test_year: int, min_prior: int, dry_run: bool) -> None:
    db = load_stints()
    included, excluded = find_movers(db, test_year, min_prior)
    print(f"HC movers into {test_year}: {len(included)} included, "
          f"{len(excluded)} excluded (see movers_hc_{test_year}.csv)")

    movers_csv = ROOT / f"movers_hc_{test_year}.csv"
    write_movers_csv(movers_csv, included, excluded, test_year)

    team_seasons = set()
    for m in included:
        team_seasons.update(m["prior_stops"])
        team_seasons.add((m["new_team"], test_year - 1))
        team_seasons.add((m["new_team"], test_year))

    est = sum(missing_calls(t, y) for t, y in team_seasons)
    print(f"{len(team_seasons)} team-seasons needed; ~{est} uncached API calls "
          f"(~{est * 17 // 60 // 17} min at 0.35s+latency each)")
    if dry_run:
        for m in included:
            flag = "  [VERIFY full season]" if m["verify_full_season"] else ""
            stops = ", ".join(f"{s} {y}" for s, y in m["prior_stops"])
            print(f"  {m['coach']:24s} -> {m['new_team']:20s} priors: {stops}{flag}")
        return

    client = CFBDClient()
    rows = []
    for m in included:
        coach, school = m["coach"], m["new_team"]
        print(f"  {coach} -> {school}")
        a_seasons = [compute_metrics(client.plays_for_offense(t, y))
                     for t, y in m["prior_stops"]]
        a_seasons = [s for s in a_seasons if any(v["n"] for v in s.values())]
        prof_a = pool_metrics(a_seasons) if a_seasons else None
        prof_b = pool_metrics([compute_metrics(
            client.plays_for_offense(school, test_year - 1))])
        actual = pool_metrics([compute_metrics(
            client.plays_for_offense(school, test_year))])

        for name in METRIC_NAMES:
            av = prof_a[name]["value"] if prof_a else None
            bv = prof_b[name]["value"]
            tv = actual[name]["value"]
            an = prof_a[name]["n"] if prof_a else 0
            usable = (
                av is not None and bv is not None and tv is not None
                and an >= MIN_SAMPLES[name]
                and prof_b[name]["n"] >= MIN_SAMPLES[name]
                and actual[name]["n"] >= MIN_SAMPLES[name]
            )
            rows.append({
                "coach": coach, "new_team": school, "metric": name,
                "hc_dna_pred": round(av, 4) if av is not None else "",
                "program_pred": round(bv, 4) if bv is not None else "",
                "actual": round(tv, 4) if tv is not None else "",
                "hc_dna_err": round(abs(av - tv), 4) if usable else "",
                "program_err": round(abs(bv - tv), 4) if usable else "",
                "n_hc": an, "n_program": prof_b[name]["n"], "n_actual": actual[name]["n"],
                "usable": usable,
                "winner": ("hc_dna" if abs(av - tv) < abs(bv - tv)
                           else "program" if abs(bv - tv) < abs(av - tv)
                           else "tie") if usable else "",
            })

    OUT.mkdir(exist_ok=True)
    results = OUT / f"results_hc_{test_year}.csv"
    with open(results, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    write_verdict(rows, OUT / f"verdict_hc_{test_year}.md", test_year,
                  any(m["verify_full_season"] for m in included))
    print(f"\nDone. {results} and verdict_hc_{test_year}.md written.")


def write_verdict(rows: list[dict], path: Path, test_year: int,
                  unverified_seasons: bool) -> None:
    lines = [f"# HC-regime backtest verdict, {test_year} movers — "
             f"does head-coach program identity travel?\n"]
    overall_a = overall_b = 0
    for name in SCORED_METRICS:
        sub = [r for r in rows if r["metric"] == name and r["usable"]]
        if not sub:
            lines.append(f"## {name}\nNo usable samples.\n")
            continue
        a_wins = sum(r["winner"] == "hc_dna" for r in sub)
        b_wins = sum(r["winner"] == "program" for r in sub)
        mae_a = sum(r["hc_dna_err"] for r in sub) / len(sub)
        mae_b = sum(r["program_err"] for r in sub) / len(sub)
        p = binom_p_two_sided(a_wins, a_wins + b_wins)
        overall_a += a_wins
        overall_b += b_wins
        lines.append(
            f"## {name}\n"
            f"- movers with usable data: {len(sub)}\n"
            f"- HC-regime MAE: {mae_a:.4f} | program MAE: {mae_b:.4f}\n"
            f"- head-to-head: HC regime {a_wins} – {b_wins} program "
            f"(sign-test p = {p:.3f})\n"
            f"- **edge: {'HC regime' if mae_a < mae_b else 'program identity'}**\n"
        )
    p_all = binom_p_two_sided(overall_a, overall_a + overall_b)
    lines.append(
        f"## Overall\nAcross all metric × mover pairs: HC regime {overall_a} – "
        f"{overall_b} program (sign-test p = {p_all:.3f}).\n\n"
        "Interpretation guide (pre-registered 2026-07-22):\n"
        "- HC regime wins broadly -> a new-HC opponent should be scouted from "
        "the HC's prior program, not the destination's old film.\n"
        "- Program wins broadly -> program identity survives even a head-coach "
        "change; leading with team-season tendencies extends to HC turnover.\n"
        "- Split by metric -> the HC layer claims only the dials that traveled.\n\n"
        "Caveats: regime-level attribution (the HC's play-caller may also have "
        "changed between stints — this test deliberately bundles that into "
        "'regime'); scheme-vs-staff confound when coordinators move with the HC; "
        "scrambles logged as rushes; explosive_pass_rate personnel-contaminated.\n\n"
        "Retired dial: fourth_down_go_rate (2026-07-22) — zero usable movers in "
        "every cycle; raw counts remain in the results CSV, never scored."
    )
    if unverified_seasons:
        lines.append(
            "\n**WARNING**: one or more movers' test-year seasons could not be "
            "verified as full seasons (CFBD /coaches game counts missing for "
            f"{test_year}). Check movers_hc_{test_year}.csv verify_full_season "
            "rows for midseason firings before trusting this verdict."
        )
    path.write_text("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-year", type=int, required=True,
                    help="first season at the new school; prior year is the baseline")
    ap.add_argument("--min-prior-seasons", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true",
                    help="list movers + estimate uncached API calls, no fetches")
    args = ap.parse_args()
    run(args.test_year, args.min_prior_seasons, args.dry_run)
