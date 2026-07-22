# HC-regime backtest verdict, 2025 movers — does head-coach program identity travel?

## neutral_pass_rate
- movers with usable data: 6
- HC-regime MAE: 0.0599 | program MAE: 0.0540
- head-to-head: HC regime 3 – 3 program (sign-test p = 1.000)
- **edge: program identity**

## sec_per_play
- movers with usable data: 5
- HC-regime MAE: 2.8850 | program MAE: 2.9000
- head-to-head: HC regime 3 – 2 program (sign-test p = 1.000)
- **edge: HC regime**

## fourth_down_go_rate
No usable samples.

## explosive_pass_rate
- movers with usable data: 7
- HC-regime MAE: 0.0217 | program MAE: 0.0225
- head-to-head: HC regime 4 – 3 program (sign-test p = 1.000)
- **edge: HC regime**

## Overall
Across all metric × mover pairs: HC regime 10 – 8 program (sign-test p = 0.815).

Interpretation guide (pre-registered 2026-07-22):
- HC regime wins broadly -> a new-HC opponent should be scouted from the HC's prior program, not the destination's old film.
- Program wins broadly -> program identity survives even a head-coach change; leading with team-season tendencies extends to HC turnover.
- Split by metric -> the HC layer claims only the dials that traveled.

Caveats: regime-level attribution (the HC's play-caller may also have changed between stints — this test deliberately bundles that into 'regime'); scheme-vs-staff confound when coordinators move with the HC; scrambles logged as rushes; explosive_pass_rate personnel-contaminated.

**WARNING**: one or more movers' test-year seasons could not be verified as full seasons (CFBD /coaches game counts missing for 2025). Check movers_hc_2025.csv verify_full_season rows for midseason firings before trusting this verdict.