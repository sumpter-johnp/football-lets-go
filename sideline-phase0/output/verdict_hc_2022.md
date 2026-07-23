# HC-regime backtest verdict, 2022 movers — does head-coach program identity travel?

## neutral_pass_rate
- movers with usable data: 7
- HC-regime MAE: 0.1011 | program MAE: 0.0982
- head-to-head: HC regime 3 – 4 program (sign-test p = 1.000)
- **edge: program identity**

## sec_per_play
- movers with usable data: 4
- HC-regime MAE: 2.1143 | program MAE: 4.0000
- head-to-head: HC regime 3 – 1 program (sign-test p = 0.625)
- **edge: HC regime**

## explosive_pass_rate
- movers with usable data: 8
- HC-regime MAE: 0.0284 | program MAE: 0.0370
- head-to-head: HC regime 5 – 3 program (sign-test p = 0.727)
- **edge: HC regime**

## Overall
Across all metric × mover pairs: HC regime 11 – 8 program (sign-test p = 0.648).

Interpretation guide (pre-registered 2026-07-22):
- HC regime wins broadly -> a new-HC opponent should be scouted from the HC's prior program, not the destination's old film.
- Program wins broadly -> program identity survives even a head-coach change; leading with team-season tendencies extends to HC turnover.
- Split by metric -> the HC layer claims only the dials that traveled.

Caveats: regime-level attribution (the HC's play-caller may also have changed between stints — this test deliberately bundles that into 'regime'); scheme-vs-staff confound when coordinators move with the HC; scrambles logged as rushes; explosive_pass_rate personnel-contaminated.

Retired dial: fourth_down_go_rate (2026-07-22) — zero usable movers in every cycle; raw counts remain in the results CSV, never scored.