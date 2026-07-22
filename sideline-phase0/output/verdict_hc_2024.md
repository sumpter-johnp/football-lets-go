# HC-regime backtest verdict, 2024 movers — does head-coach program identity travel?

## neutral_pass_rate
- movers with usable data: 16
- HC-regime MAE: 0.0853 | program MAE: 0.0707
- head-to-head: HC regime 10 – 6 program (sign-test p = 0.454)
- **edge: program identity**

## sec_per_play
- movers with usable data: 7
- HC-regime MAE: 3.2159 | program MAE: 4.9286
- head-to-head: HC regime 5 – 2 program (sign-test p = 0.453)
- **edge: HC regime**

## fourth_down_go_rate
No usable samples.

## explosive_pass_rate
- movers with usable data: 16
- HC-regime MAE: 0.0295 | program MAE: 0.0329
- head-to-head: HC regime 8 – 8 program (sign-test p = 1.000)
- **edge: HC regime**

## Overall
Across all metric × mover pairs: HC regime 23 – 16 program (sign-test p = 0.337).

Interpretation guide (pre-registered 2026-07-22):
- HC regime wins broadly -> a new-HC opponent should be scouted from the HC's prior program, not the destination's old film.
- Program wins broadly -> program identity survives even a head-coach change; leading with team-season tendencies extends to HC turnover.
- Split by metric -> the HC layer claims only the dials that traveled.

Caveats: regime-level attribution (the HC's play-caller may also have changed between stints — this test deliberately bundles that into 'regime'); scheme-vs-staff confound when coordinators move with the HC; scrambles logged as rushes; explosive_pass_rate personnel-contaminated.