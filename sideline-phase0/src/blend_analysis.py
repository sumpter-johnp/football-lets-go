"""Evidence behind the Phase 2 lead-with decision (2026-07-22): blend leads.

For every usable metric x mover pair in both backtest tracks we have the
coach-side prediction (play-caller DNA or HC-regime), the program-identity
prediction, and the actual. This script sweeps blend weights and runs sign
tests of the 50/50 blend against each pure predictor.

Key honesty point: w = 0.5 is the a-priori default, not tuned on this data —
the headline claim ("the untuned blend beats both pures") carries no
researcher degrees of freedom. The pace exception (sec_per_play best at full
coach weight) IS an in-sample observation, but it replicates the independent
Phase 0 pace result (8-1, p = .039) and is monotone in both tracks.

Usage:
    python3 src/blend_analysis.py    # -> output/blend_analysis.md
"""

from __future__ import annotations

import csv
from pathlib import Path

from backtest import binom_p_two_sided
from metrics import SCORED_METRICS

OUT = Path(__file__).resolve().parent.parent / "output"

TRACKS = {
    "HC-regime": ("results_hc_20*.csv", "hc_dna_pred"),
    "Play-caller": ("results_20*.csv", "coach_dna_pred"),
}
WEIGHTS = (0.0, 0.25, 0.5, 0.75, 1.0)


def load(pattern: str, a_col: str) -> list[tuple]:
    rows = []
    for f in sorted(OUT.glob(pattern)):
        for r in csv.DictReader(open(f)):
            if r["usable"] == "True" and r["metric"] in SCORED_METRICS:
                rows.append((float(r[a_col]), float(r["program_pred"]),
                             float(r["actual"]), r["metric"]))
    return rows


def main() -> None:
    lines = ["# Blend analysis — evidence for the Phase 2 lead-with decision\n",
             "Decision (John, 2026-07-22): headline dial predictions lead with "
             "the 50/50 coach-history x program-identity blend; sec_per_play "
             "leads with the pure coach-side profile (pace travels with the "
             "coach). Both components always reported with sample sizes.\n"]

    for track, (pattern, a_col) in TRACKS.items():
        rows = load(pattern, a_col)
        lines.append(f"\n## {track} track — {len(rows)} usable pairs\n")

        lines.append("MAE by blend weight (w = coach-side share):\n")
        lines.append("| metric | " + " | ".join(f"w={w}" for w in WEIGHTS) + " |")
        lines.append("|---|" + "---|" * len(WEIGHTS))
        for m in SCORED_METRICS:
            sub = [(a, b, act) for a, b, act, mm in rows if mm == m]
            cells = []
            for w in WEIGHTS:
                mae = sum(abs(w * a + (1 - w) * b - act) for a, b, act in sub) / len(sub)
                cells.append(f"{mae:.4f}")
            lines.append(f"| {m} ({len(sub)}) | " + " | ".join(cells) + " |")

        lines.append("\nSign tests, 50/50 blend head-to-head:\n")
        for opp, pick in [("pure coach-side", lambda a, b: a),
                          ("pure program", lambda a, b: b)]:
            w = l = 0
            for a, b, act, _ in rows:
                be, oe = abs(0.5 * a + 0.5 * b - act), abs(pick(a, b) - act)
                if be < oe:
                    w += 1
                elif oe < be:
                    l += 1
            lines.append(f"- blend vs {opp}: {w}-{l} "
                         f"(p = {binom_p_two_sided(w, w + l):.4f})")

    lines.append(
        "\n## Interpretation\n\n"
        "The untuned 50/50 blend beats pure program identity decisively in "
        "both tracks and edges pure coach-side in both — the classic ensemble "
        "result. Program identity alone is the worst predictor on every dial "
        "in both tracks; the original 'demote coach DNA to a sidebar' fallback "
        "is dead. Pace is the exception in the other direction: MAE improves "
        "monotonically with coach weight in both tracks, consistent with the "
        "independent Phase 0 pace result (8-1) — tempo belongs to the coach.\n\n"
        "Coach-side source hierarchy (pre-registered): verified play-caller "
        "profile when available, else HC-regime profile, else pure program "
        "with a 'no coach history' flag. The two coach-side profile families "
        "are never pooled with each other.")

    path = OUT / "blend_analysis.md"
    path.write_text("\n".join(lines) + "\n")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
