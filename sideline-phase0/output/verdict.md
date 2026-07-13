# Phase 0 verdict — does coach DNA travel?

## neutral_pass_rate
- movers with usable data: 10
- coach-DNA MAE: 0.0555 | program MAE: 0.0757
- head-to-head: coach DNA 7 – 3 program (sign-test p = 0.344)
- **edge: coach DNA**

## sec_per_play
- movers with usable data: 9
- coach-DNA MAE: 2.2213 | program MAE: 5.3333
- head-to-head: coach DNA 8 – 1 program (sign-test p = 0.039)
- **edge: coach DNA**

## fourth_down_go_rate
No usable samples (check MIN_SAMPLES / data coverage).

## explosive_pass_rate
- movers with usable data: 10
- coach-DNA MAE: 0.0167 | program MAE: 0.0206
- head-to-head: coach DNA 5 – 5 program (sign-test p = 1.000)
- **edge: coach DNA**

## Overall
Across all metric × mover pairs: coach DNA 20 – 9 program (sign-test p = 0.061).

Interpretation guide:
- Coach DNA wins broadly -> build the layer as designed.
- Program wins broadly -> demote coach DNA to a qualitative sidebar; lead with team-season tendencies.
- Split by metric -> the DNA profile only claims the dials that traveled (this is the expected outcome; partial persistence is still a win).

Caveats: one season of ~15 movers is a small n; explosive_pass_rate is personnel-contaminated; scrambles are logged as rushes.