# Backtest verdict, 2022 movers — does coach DNA travel?

## neutral_pass_rate
- movers with usable data: 18
- coach-DNA MAE: 0.0665 | program MAE: 0.0953
- head-to-head: coach DNA 10 – 8 program (sign-test p = 0.815)
- **edge: coach DNA**

## sec_per_play
- movers with usable data: 7
- coach-DNA MAE: 1.4206 | program MAE: 3.8571
- head-to-head: coach DNA 5 – 2 program (sign-test p = 0.453)
- **edge: coach DNA**

## explosive_pass_rate
- movers with usable data: 19
- coach-DNA MAE: 0.0258 | program MAE: 0.0334
- head-to-head: coach DNA 13 – 6 program (sign-test p = 0.167)
- **edge: coach DNA**

## Overall
Across all metric × mover pairs: coach DNA 28 – 16 program (sign-test p = 0.096).

Interpretation guide:
- Coach DNA wins broadly -> build the layer as designed.
- Program wins broadly -> demote coach DNA to a qualitative sidebar; lead with team-season tendencies.
- Split by metric -> the DNA profile only claims the dials that traveled (this is the expected outcome; partial persistence is still a win).

Caveats: one season of ~15 movers is a small n; explosive_pass_rate is personnel-contaminated; scrambles are logged as rushes.

Retired dial: fourth_down_go_rate (2026-07-22) — zero usable movers in every cycle; raw counts remain in the results CSV, never scored.