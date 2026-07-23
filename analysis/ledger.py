"""Prediction ledger: freeze tendency predictions BEFORE game week, score them
against cumulative actuals later. This is the in-season credibility loop — by
midseason the brief can show a track record instead of asking for trust.

Usage:
    python3 analysis/ledger.py predict Arizona --season 2026     # one opponent
    python3 analysis/ledger.py predict --all --season 2026       # every verified 2026 caller's team
    python3 analysis/ledger.py score --season 2026               # score all frozen predictions

predict writes data/ledger/predictions/<season>_<team>.json and REFUSES to
overwrite (--force to override; the whole point is that predictions are
provably frozen — commit them and the git history is the notary). Each file
carries BOTH Phase 0 predictors so the natural experiment continues in-season:
  coach_dna — the verified play-caller's pooled sticky dials from prior stops
              (data/profiles/coaches/<slug>.json)
  program   — the team's previous-season profile (data/profiles/teams/)
Either can be null (first-time caller, un-ingested seasons); the reason is
recorded instead. Freeze AFTER the August ingest lands so coach_dna rests on
full DNA bases, and BEFORE the games being predicted.

score computes each opponent's cumulative season-to-date sticky profile from
sideline.plays and reports per-metric absolute errors for both predictors.
Scoring unit is the CUMULATIVE profile, never a single game — ~70 plays
sliced into buckets is noise contaminated by game script (Phase 0 design
rule). Early-season scores are provisional by construction; n is printed so
nobody over-reads a 2-game sample.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(REPO_ROOT / "ingest"), str(REPO_ROOT / "analysis")]

from psycopg2.extras import RealDictCursor

import db
from build_profiles import slug
from tendencies import MIN_SAMPLES, SCORED_METRICS, blend_value, sticky_metrics

PROFILES = REPO_ROOT / "data" / "profiles"
LEDGER = REPO_ROOT / "data" / "ledger"

CALLER_SQL = """
select c.name as coach, cs.role, cs.notes
from sideline.coach_stints cs
join sideline.coaches c on c.id = cs.coach_id
join sideline.teams t on t.id = cs.team_id
where t.school = %s
  and cs.play_caller
  and coalesce(cs.unit, 'offense') = 'offense'
  and cs.start_year <= %s and coalesce(cs.end_year, %s) >= %s
"""

ALL_TEAMS_SQL = """
select distinct t.school
from sideline.coach_stints cs
join sideline.teams t on t.id = cs.team_id
where cs.play_caller
  and coalesce(cs.unit, 'offense') = 'offense'
  and cs.start_year <= %s and coalesce(cs.end_year, %s) >= %s
order by t.school
"""

PLAYS_SQL = """
select p.*
from sideline.plays p
join sideline.teams t on t.id = p.offense_team_id
where t.school = %s and p.season = %s
"""


def load_json(path: Path) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def predictors_for(school: str, season: int, coach: str) -> dict:
    """Both Phase 0 predictors, each with provenance or a null + reason."""
    out: dict = {}

    coach_file = PROFILES / "coaches" / f"{slug(coach)}.json"
    cp = load_json(coach_file)
    if cp and cp.get("pooled_profile"):
        out["coach_dna"] = {
            "sticky": cp["pooled_profile"]["sticky"],
            "based_on": cp["stints_profiled"],
            "source": str(coach_file.relative_to(REPO_ROOT)),
        }
    else:
        reason = "no coach profile file" if cp is None else \
            "no pooled profile (prior play-calling seasons not ingested, or first-time caller)"
        out["coach_dna"] = {"sticky": None, "reason": reason}

    team_file = PROFILES / "teams" / f"{slug(school)}_{season - 1}.json"
    tp = load_json(team_file)
    if tp:
        out["program"] = {
            "sticky": tp["profile"]["sticky"],
            "based_on": [{"school": school, "season": season - 1,
                          "n_games": tp["games_in_db"]}],
            "source": str(team_file.relative_to(REPO_ROOT)),
        }
    else:
        out["program"] = {"sticky": None,
                          "reason": f"{school} {season - 1} not fully ingested"}
    return out


def predict(school: str, season: int, force: bool, dry_run: bool) -> None:
    conn = db.connect()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(CALLER_SQL, (school, season, season, season))
        callers = cur.fetchall()
    conn.close()

    if not callers:
        print(f"SKIP {school}: no verified {season} play-caller in coach_stints")
        return
    if len(callers) > 1:
        names = ", ".join(c["coach"] for c in callers)
        print(f"SKIP {school}: multiple verified callers for {season} ({names}) — resolve first")
        return

    coach = callers[0]["coach"]
    record = {
        "school": school,
        "season": season,
        "play_caller": coach,
        "caller_role": callers[0]["role"],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "metrics": list(MIN_SAMPLES),
        "predictors": predictors_for(school, season, coach),
        "note": (
            "Frozen prediction — do not edit after games begin. Scoring unit is "
            "the cumulative season profile, never a single game."
        ),
    }

    path = LEDGER / "predictions" / f"{season}_{slug(school)}.json"
    if dry_run:
        dna = record["predictors"]["coach_dna"]["sticky"]
        prog = record["predictors"]["program"]["sticky"]
        print(f"DRY RUN {school} {season}: caller={coach} "
              f"coach_dna={'ok' if dna else 'null'} program={'ok' if prog else 'null'}")
        return
    if path.exists() and not force:
        print(f"REFUSED {path.name}: already frozen (--force to overwrite)")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2) + "\n")
    print(f"froze {path.relative_to(REPO_ROOT)} (caller: {coach})")


def score(season: int) -> None:
    pred_dir = LEDGER / "predictions"
    files = sorted(pred_dir.glob(f"{season}_*.json")) if pred_dir.exists() else []
    if not files:
        print(f"No frozen predictions for {season} in {pred_dir.relative_to(REPO_ROOT)}/")
        return

    conn = db.connect()
    rows, lines = [], [f"# Ledger scores — {season} (cumulative to date)", ""]
    for f in files:
        pred = json.loads(f.read_text())
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(PLAYS_SQL, (pred["school"], season))
            plays = cur.fetchall()
        if not plays:
            lines.append(f"## {pred['school']} — PENDING (no {season} plays ingested yet)")
            lines.append("")
            continue
        actual = sticky_metrics(plays)
        n_games = len({p["game_id"] for p in plays})
        lines.append(f"## {pred['school']} (caller: {pred['play_caller']}, "
                     f"{n_games} games ingested)")
        lines.append("")
        lines.append("| metric | blend pred (headline) | coach_dna pred | program pred | actual "
                     "| blend err | dna err | prog err | winner | n_actual |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for m in pred["metrics"]:
            a = actual[m]["value"]
            n = actual[m]["n"]
            row = {"school": pred["school"], "metric": m, "actual": a, "n_actual": n}
            cells = {}
            for name in ("coach_dna", "program"):
                p = pred["predictors"][name]["sticky"]
                v = p[m]["value"] if p and p.get(m) else None
                cells[name] = v
                row[f"{name}_pred"] = v
                row[f"{name}_err"] = abs(v - a) if v is not None and a is not None else None
            # Headline prediction per the Phase 2 lead-with decision — derived
            # here from the two FROZEN components, so provenance is intact.
            bv = blend_value(m, cells["coach_dna"], cells["program"])
            row["blend_pred"] = bv
            row["blend_err"] = abs(bv - a) if bv is not None and a is not None else None
            # retired dials are reported but never scored or tallied
            usable = a is not None and n >= MIN_SAMPLES[m] and m in SCORED_METRICS
            winner = None
            if usable and row["coach_dna_err"] is not None and row["program_err"] is not None:
                winner = "coach_dna" if row["coach_dna_err"] <= row["program_err"] else "program"
            row["usable"] = usable
            row["winner"] = winner
            rows.append(row)
            fmt = lambda v: f"{v:.3f}" if isinstance(v, float) else (str(v) if v is not None else "—")
            flag = winner or ("retired" if m not in SCORED_METRICS
                             else "low n" if not usable else "—")
            lines.append(
                f"| {m} | {fmt(bv)} | {fmt(cells['coach_dna'])} | {fmt(cells['program'])} | {fmt(a)} "
                f"| {fmt(row['blend_err'])} | {fmt(row['coach_dna_err'])} | {fmt(row['program_err'])} "
                f"| {flag} | {n} |")
        lines.append("")
    conn.close()

    usable = [r for r in rows if r.get("winner")]
    dna_wins = sum(r["winner"] == "coach_dna" for r in usable)
    lines.append(f"**Head-to-head (usable pairs only): coach DNA {dna_wins} — "
                 f"{len(usable) - dna_wins} program.**")
    with_blend = [r for r in usable if r["blend_err"] is not None]
    if with_blend:
        mb = sum(r["blend_err"] for r in with_blend) / len(with_blend)
        blend_beats = sum(r["blend_err"] <= min(r["coach_dna_err"], r["program_err"])
                          for r in with_blend)
        lines.append(f"\nBlend (headline) mean abs err {mb:.3f} over "
                     f"{len(with_blend)} usable pairs; at-or-better than both "
                     f"pure predictors on {blend_beats}/{len(with_blend)}.")

    LEDGER.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    (LEDGER / f"scored_{season}_{stamp}.json").write_text(json.dumps(rows, indent=2) + "\n")
    (LEDGER / f"scored_{season}_{stamp}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nwrote data/ledger/scored_{season}_{stamp}.{{json,md}}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("predict", help="freeze predictions for an opponent (or --all)")
    p.add_argument("school", nargs="?", help="CFBD school name, e.g. Arizona")
    p.add_argument("--all", action="store_true", help="every team with a verified caller that season")
    p.add_argument("--season", type=int, required=True)
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    s = sub.add_parser("score", help="score frozen predictions vs cumulative actuals")
    s.add_argument("--season", type=int, required=True)
    args = ap.parse_args()

    if args.cmd == "score":
        score(args.season)
        return
    if args.all:
        conn = db.connect()
        with conn.cursor() as cur:
            cur.execute(ALL_TEAMS_SQL, (args.season, args.season, args.season))
            schools = [r[0] for r in cur.fetchall()]
        conn.close()
        for school in schools:
            predict(school, args.season, args.force, args.dry_run)
    elif args.school:
        predict(args.school, args.season, args.force, args.dry_run)
    else:
        ap.error("predict needs a school or --all")


if __name__ == "__main__":
    main()
