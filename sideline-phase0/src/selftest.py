"""Self-test with synthetic play-by-play — no API key needed.

Fabricates two coaching 'personalities' (a pass-happy fast coach and a
run-heavy slow coach), generates plays, and checks that:
  1. compute_metrics recovers the personalities' dials
  2. situation filters actually exclude garbage-time / 4th-quarter plays
  3. the backtest error math picks the right winner

Run: python src/selftest.py
"""

import random

from metrics import compute_metrics, pool_metrics


def synth_plays(pass_rate: float, pace: int, go_rate: float, n_drives=120, seed=1):
    rng = random.Random(seed)
    plays = []
    for d in range(n_drives):
        clock = 900
        period = rng.choice([1, 2, 3, 4])
        for i in range(rng.randint(4, 9)):
            down = rng.choice([1, 1, 2, 2, 3, 4])
            is_pass = rng.random() < pass_rate
            if down == 4:
                pt = ("Rush" if rng.random() < 0.5 else "Pass Reception") \
                    if rng.random() < go_rate else "Punt"
            else:
                pt = "Pass Reception" if is_pass else "Rush"
            clock -= pace + rng.randint(-3, 3)
            plays.append({
                "drive_id": d, "period": period, "down": down,
                "distance": rng.choice([1, 2, 3, 7, 10]),
                "yards_to_goal": rng.randint(35, 69),
                "offense_score": 7, "defense_score": 10,   # one-score
                "clock": {"minutes": max(clock, 0) // 60, "seconds": max(clock, 0) % 60},
                "play_type": pt,
                "yards_gained": rng.randint(15, 30) if (is_pass and rng.random() < 0.15) else rng.randint(0, 9),
            })
    return plays


def approx(a, b, tol):
    return a is not None and abs(a - b) <= tol


def main():
    fails = []

    # Coach A: 62% pass, 20s pace, aggressive on 4th. Coach B: 42% pass, 30s, conservative.
    a = compute_metrics(synth_plays(0.62, 20, 0.80, seed=1))
    b = compute_metrics(synth_plays(0.42, 30, 0.20, seed=2))

    checks = [
        ("A pass rate ~0.62", approx(a["neutral_pass_rate"]["value"], 0.62, 0.06)),
        ("B pass rate ~0.42", approx(b["neutral_pass_rate"]["value"], 0.42, 0.06)),
        ("A pace ~20s", approx(a["sec_per_play"]["value"], 20, 3)),
        ("B pace ~30s", approx(b["sec_per_play"]["value"], 30, 3)),
        ("A go rate > B go rate",
         a["fourth_down_go_rate"]["value"] > b["fourth_down_go_rate"]["value"]),
        ("sample sizes recorded", a["neutral_pass_rate"]["n"] > 100),
    ]

    # Q4 / blowout plays must be filtered out
    garbage = synth_plays(0.9, 15, 1.0, seed=3)
    for p in garbage:
        p["period"] = 4
    g = compute_metrics(garbage)
    checks.append(("Q4 plays excluded", g["neutral_pass_rate"]["n"] == 0))

    blowout = synth_plays(0.9, 15, 1.0, seed=4)
    for p in blowout:
        p["offense_score"], p["defense_score"] = 0, 28
    bl = compute_metrics(blowout)
    checks.append(("blowout plays excluded", bl["neutral_pass_rate"]["n"] == 0))

    # pooling: two seasons of the same coach should stay near the coach's dial
    pooled = pool_metrics([
        compute_metrics(synth_plays(0.60, 22, 0.7, seed=5)),
        compute_metrics(synth_plays(0.64, 22, 0.7, seed=6)),
    ])
    checks.append(("pooled pass rate ~0.62", approx(pooled["neutral_pass_rate"]["value"], 0.62, 0.06)))

    # error math: coach-DNA prediction closer to actual than program baseline
    actual = compute_metrics(synth_plays(0.61, 21, 0.75, seed=7))  # coach's style at new stop
    err_a = abs(a["neutral_pass_rate"]["value"] - actual["neutral_pass_rate"]["value"])
    err_b = abs(b["neutral_pass_rate"]["value"] - actual["neutral_pass_rate"]["value"])
    checks.append(("backtest picks coach DNA when it should", err_a < err_b))

    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            fails.append(name)

    if fails:
        raise SystemExit(f"\n{len(fails)} check(s) failed.")
    print("\nAll checks passed — pipeline logic is sound.")


if __name__ == "__main__":
    main()
