"""Pool every backtest cycle into one combined verdict.

Reads output/results_<year>.csv (play-caller cycles) and
output/results_hc_<year>.csv (HC-regime cycles), pools the sign tests
per metric WITHIN each hypothesis — the two are never mixed: play-caller
DNA and HC-regime identity are different claims tested on different
mover populations.

Usage:
    python3 src/verdict_combined.py     # -> output/verdict_combined.md
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

from backtest import binom_p_two_sided
from metrics import SCORED_METRICS

OUT = Path(__file__).resolve().parent.parent / "output"

FAMILIES = {
    "Play-caller DNA vs program identity": {
        "pattern": re.compile(r"^results_(\d{4})\.csv$"),
        "dna_label": "coach_dna",
        "err_a": "coach_dna_err", "err_b": "program_err",
    },
    "HC-regime identity vs program identity": {
        "pattern": re.compile(r"^results_hc_(\d{4})\.csv$"),
        "dna_label": "hc_dna",
        "err_a": "hc_dna_err", "err_b": "program_err",
    },
}


def main() -> None:
    lines = ["# Combined backtest verdict — all cycles\n",
             "Two separate hypotheses; never pooled with each other.\n",
             "Retired dial: fourth_down_go_rate (2026-07-22) — zero usable "
             "movers in every cycle of both tracks; raw counts remain in the "
             "results CSVs, never scored.\n"]

    for family, spec in FAMILIES.items():
        files = sorted(
            (int(m.group(1)), f)
            for f in OUT.iterdir()
            if (m := spec["pattern"].match(f.name))
        )
        if not files:
            continue
        rows = []
        for year, f in files:
            with open(f, newline="") as fh:
                for r in csv.DictReader(fh):
                    r["cycle"] = year
                    rows.append(r)
        usable = [r for r in rows if r["usable"] == "True"]
        movers = {(r["cycle"], r["coach"]) for r in rows}

        lines.append(f"\n## {family}\n")
        lines.append(f"Cycles: {', '.join(str(y) for y, _ in files)} — "
                     f"{len(movers)} movers, {len(usable)} usable metric×mover pairs.\n")

        overall_a = overall_b = 0
        lines.append("| metric | usable | DNA MAE | program MAE | head-to-head | p |")
        lines.append("|---|---|---|---|---|---|")
        for name in SCORED_METRICS:
            sub = [r for r in usable if r["metric"] == name]
            if not sub:
                lines.append(f"| {name} | 0 | — | — | — | — |")
                continue
            a_wins = sum(r["winner"] == spec["dna_label"] for r in sub)
            b_wins = sum(r["winner"] == "program" for r in sub)
            mae_a = sum(float(r[spec["err_a"]]) for r in sub) / len(sub)
            mae_b = sum(float(r[spec["err_b"]]) for r in sub) / len(sub)
            p = binom_p_two_sided(a_wins, a_wins + b_wins)
            overall_a += a_wins
            overall_b += b_wins
            lines.append(f"| {name} | {len(sub)} | {mae_a:.4f} | {mae_b:.4f} | "
                         f"{a_wins} – {b_wins} | {p:.3f} |")
        p_all = binom_p_two_sided(overall_a, overall_a + overall_b)
        winner = ("DNA" if overall_a > overall_b
                  else "program identity" if overall_b > overall_a else "dead even")
        lines.append(f"\n**Overall: DNA {overall_a} – {overall_b} program "
                     f"(sign-test p = {p_all:.3f}) — edge: {winner}.**\n")

        by_cycle = defaultdict(lambda: [0, 0])
        for r in usable:
            if r["winner"] == spec["dna_label"]:
                by_cycle[r["cycle"]][0] += 1
            elif r["winner"] == "program":
                by_cycle[r["cycle"]][1] += 1
        lines.append("Per cycle: " + "; ".join(
            f"{y}: {a}–{b} (p={binom_p_two_sided(a, a + b):.2f})"
            for y, (a, b) in sorted(by_cycle.items())) + "\n")

    path = OUT / "verdict_combined.md"
    path.write_text("\n".join(lines))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
