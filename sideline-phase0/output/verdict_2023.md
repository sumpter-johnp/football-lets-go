# Backtest verdict, 2023 movers — does coach DNA travel?

## neutral_pass_rate
- movers with usable data: 12
- coach-DNA MAE: 0.0810 | program MAE: 0.0893
- head-to-head: coach DNA 6 – 6 program (sign-test p = 1.000)
- **edge: coach DNA**

## sec_per_play
- movers with usable data: 5
- coach-DNA MAE: 4.7581 | program MAE: 4.0000
- head-to-head: coach DNA 1 – 4 program (sign-test p = 0.375)
- **edge: program identity**

## explosive_pass_rate
- movers with usable data: 12
- coach-DNA MAE: 0.0271 | program MAE: 0.0269
- head-to-head: coach DNA 5 – 7 program (sign-test p = 0.774)
- **edge: program identity**

## Overall
Across all metric × mover pairs: coach DNA 12 – 17 program (sign-test p = 0.458).

Interpretation guide:
- Coach DNA wins broadly -> build the layer as designed.
- Program wins broadly -> demote coach DNA to a qualitative sidebar; lead with team-season tendencies.
- Split by metric -> the DNA profile only claims the dials that traveled (this is the expected outcome; partial persistence is still a win).

Caveats: one season of ~15 movers is a small n; explosive_pass_rate is personnel-contaminated; scrambles are logged as rushes.

Retired dial: fourth_down_go_rate (2026-07-22) — zero usable movers in every cycle; raw counts remain in the results CSV, never scored.