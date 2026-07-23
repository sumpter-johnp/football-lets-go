# HC-regime backtest verdict, 2019 movers — does head-coach program identity travel?

## neutral_pass_rate
- movers with usable data: 9
- HC-regime MAE: 0.1001 | program MAE: 0.0875
- head-to-head: HC regime 4 – 5 program (sign-test p = 1.000)
- **edge: program identity**

## sec_per_play
- movers with usable data: 1
- HC-regime MAE: 3.5401 | program MAE: 2.0000
- head-to-head: HC regime 0 – 1 program (sign-test p = 1.000)
- **edge: program identity**

## explosive_pass_rate
- movers with usable data: 8
- HC-regime MAE: 0.0196 | program MAE: 0.0180
- head-to-head: HC regime 3 – 5 program (sign-test p = 0.727)
- **edge: program identity**

## Overall
Across all metric × mover pairs: HC regime 7 – 11 program (sign-test p = 0.481).

Interpretation guide (pre-registered 2026-07-22):
- HC regime wins broadly -> a new-HC opponent should be scouted from the HC's prior program, not the destination's old film.
- Program wins broadly -> program identity survives even a head-coach change; leading with team-season tendencies extends to HC turnover.
- Split by metric -> the HC layer claims only the dials that traveled.

Caveats: regime-level attribution (the HC's play-caller may also have changed between stints — this test deliberately bundles that into 'regime'); scheme-vs-staff confound when coordinators move with the HC; scrambles logged as rushes; explosive_pass_rate personnel-contaminated.

Retired dial: fourth_down_go_rate (2026-07-22) — zero usable movers in every cycle; raw counts remain in the results CSV, never scored.