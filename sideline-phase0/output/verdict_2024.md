# Backtest verdict, 2024 movers — does coach DNA travel?

## neutral_pass_rate
- movers with usable data: 15
- coach-DNA MAE: 0.0682 | program MAE: 0.0573
- head-to-head: coach DNA 5 – 10 program (sign-test p = 0.302)
- **edge: program identity**

## sec_per_play
- movers with usable data: 4
- coach-DNA MAE: 4.7938 | program MAE: 1.6250
- head-to-head: coach DNA 0 – 4 program (sign-test p = 0.125)
- **edge: program identity**

## explosive_pass_rate
- movers with usable data: 14
- coach-DNA MAE: 0.0316 | program MAE: 0.0311
- head-to-head: coach DNA 5 – 9 program (sign-test p = 0.424)
- **edge: program identity**

## Overall
Across all metric × mover pairs: coach DNA 10 – 23 program (sign-test p = 0.035).

Interpretation guide:
- Coach DNA wins broadly -> build the layer as designed.
- Program wins broadly -> demote coach DNA to a qualitative sidebar; lead with team-season tendencies.
- Split by metric -> the DNA profile only claims the dials that traveled (this is the expected outcome; partial persistence is still a win).

Caveats: one season of ~15 movers is a small n; explosive_pass_rate is personnel-contaminated; scrambles are logged as rushes.

Retired dial: fourth_down_go_rate (2026-07-22) — zero usable movers in every cycle; raw counts remain in the results CSV, never scored.