"""Phase 0 backtest: does coach DNA beat program identity?

For each offensive play-caller who changed schools between 2024 and 2025:

  predictor (a) — the coach's pooled tendency profile from prior stops
  predictor (b) — the NEW team's 2024 profile under its previous play-caller
  actual        — the new team's full-2025 profile

Per metric, per mover: |a - actual| vs |b - actual|. If (a) systematically
beats (b), tendencies follow the coach and the Coach DNA layer is validated.

Input:  movers CSV (see movers_2025.csv template)
Output: output/results.csv + output/verdict.md

Usage:
    export CFBD_API_KEY=...
    python src/backtest.py --movers movers_2025.csv
"""

import argparse
import csv
import math
from pathlib import Path

from cfbd import CFBDClient
from metrics import MIN_SAMPLES, compute_metrics, pool_metrics

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
METRIC_NAMES = list(MIN_SAMPLES)
TEST_YEAR = 2025
PRIOR_YEAR = 2024


def load_movers(path: Path) -> list[dict]:
    """CSV columns: coach, unit, new_team, prior_stops, notes
    prior_stops format: 'Team A:2022-2024; Team B:2019-2021' (seasons the coach
    CALLED PLAYS there). Rows with unit != 'offense' are skipped for now —
    all four Phase 0 metrics are offensive."""
    movers = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            if not row.get("coach") or row["coach"].startswith("#"):
                continue
            if row.get("unit", "offense").strip().lower() != "offense":
                continue
            stops = []
            for chunk in row["prior_stops"].split(";"):
                chunk = chunk.strip()
                if not chunk:
                    continue
                team, years = chunk.rsplit(":", 1)
                start, end = (int(y) for y in years.split("-"))
                stops.append((team.strip(), start, end))
            movers.append(
                {"coach": row["coach"].strip(),
                 "new_team": row["new_team"].strip(),
                 "prior_stops": stops}
            )
    return movers


def profile(client: CFBDClient, team: str, years: list[int]) -> dict:
    season_metrics = []
    for y in years:
        plays = client.plays_for_offense(team, y)
        if plays:
            season_metrics.append(compute_metrics(plays))
    return pool_metrics(season_metrics) if season_metrics else {
        m: {"value": None, "n": 0} for m in METRIC_NAMES
    }


def binom_p_two_sided(wins: int, n: int) -> float:
    """Exact two-sided sign-test p-value for wins out of n at p=0.5."""
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(min(wins, n - wins) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def run(movers_path: Path):
    client = CFBDClient()
    movers = load_movers(movers_path)
    if not movers:
        raise SystemExit(
            f"No offensive movers found in {movers_path}. Fill in the CSV first "
            "(seed HC candidates with: python src/find_hc_movers.py)."
        )
    print(f"Backtesting {len(movers)} offensive play-caller moves into {TEST_YEAR}...\n")

    rows = []
    for mv in movers:
        coach, new_team = mv["coach"], mv["new_team"]
        print(f"  {coach} -> {new_team}")

        prior_years = [
            (team, y)
            for team, start, end in mv["prior_stops"]
            for y in range(start, end + 1)
        ]
        # predictor (a): pooled profile across all prior stop seasons
        a_seasons = []
        for team, y in prior_years:
            plays = client.plays_for_offense(team, y)
            if plays:
                a_seasons.append(compute_metrics(plays))
        prof_a = pool_metrics(a_seasons) if a_seasons else None

        prof_b = profile(client, new_team, [PRIOR_YEAR])     # predictor (b)
        actual = profile(client, new_team, [TEST_YEAR])      # ground truth

        for m in METRIC_NAMES:
            av = prof_a[m]["value"] if prof_a else None
            bv = prof_b[m]["value"]
            tv = actual[m]["value"]
            an = prof_a[m]["n"] if prof_a else 0
            usable = (
                av is not None and bv is not None and tv is not None
                and an >= MIN_SAMPLES[m]
                and prof_b[m]["n"] >= MIN_SAMPLES[m]
                and actual[m]["n"] >= MIN_SAMPLES[m]
            )
            rows.append({
                "coach": coach, "new_team": new_team, "metric": m,
                "coach_dna_pred": round(av, 4) if av is not None else "",
                "program_pred": round(bv, 4) if bv is not None else "",
                "actual_2025": round(tv, 4) if tv is not None else "",
                "coach_dna_err": round(abs(av - tv), 4) if usable else "",
                "program_err": round(abs(bv - tv), 4) if usable else "",
                "n_coach": an, "n_program": prof_b[m]["n"], "n_actual": actual[m]["n"],
                "usable": usable,
                "winner": ("coach_dna" if abs(av - tv) < abs(bv - tv)
                           else "program" if abs(bv - tv) < abs(av - tv)
                           else "tie") if usable else "",
            })

    OUT.mkdir(exist_ok=True)
    results = OUT / "results.csv"
    with open(results, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    write_verdict(rows)
    print(f"\nDone. {results} and {OUT/'verdict.md'} written.")


def write_verdict(rows: list[dict]):
    lines = ["# Phase 0 verdict — does coach DNA travel?\n"]
    overall_a = overall_b = 0
    for m in METRIC_NAMES:
        sub = [r for r in rows if r["metric"] == m and r["usable"]]
        if not sub:
            lines.append(f"## {m}\nNo usable samples (check MIN_SAMPLES / data coverage).\n")
            continue
        a_wins = sum(r["winner"] == "coach_dna" for r in sub)
        b_wins = sum(r["winner"] == "program" for r in sub)
        mae_a = sum(r["coach_dna_err"] for r in sub) / len(sub)
        mae_b = sum(r["program_err"] for r in sub) / len(sub)
        p = binom_p_two_sided(a_wins, a_wins + b_wins)
        overall_a += a_wins
        overall_b += b_wins
        lines.append(
            f"## {m}\n"
            f"- movers with usable data: {len(sub)}\n"
            f"- coach-DNA MAE: {mae_a:.4f} | program MAE: {mae_b:.4f}\n"
            f"- head-to-head: coach DNA {a_wins} – {b_wins} program "
            f"(sign-test p = {p:.3f})\n"
            f"- **edge: {'coach DNA' if mae_a < mae_b else 'program identity'}**\n"
        )
    p_all = binom_p_two_sided(overall_a, overall_a + overall_b)
    lines.append(
        f"## Overall\nAcross all metric × mover pairs: coach DNA {overall_a} – "
        f"{overall_b} program (sign-test p = {p_all:.3f}).\n\n"
        "Interpretation guide:\n"
        "- Coach DNA wins broadly -> build the layer as designed.\n"
        "- Program wins broadly -> demote coach DNA to a qualitative sidebar; "
        "lead with team-season tendencies.\n"
        "- Split by metric -> the DNA profile only claims the dials that traveled "
        "(this is the expected outcome; partial persistence is still a win).\n\n"
        "Caveats: one season of ~15 movers is a small n; explosive_pass_rate is "
        "personnel-contaminated; scrambles are logged as rushes."
    )
    (OUT / "verdict.md").write_text("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--movers", default=str(ROOT / "movers_2025.csv"))
    run(Path(ap.parse_args().movers))
