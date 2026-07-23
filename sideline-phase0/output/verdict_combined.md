# Combined backtest verdict — all cycles

Two separate hypotheses; never pooled with each other.

Retired dial: fourth_down_go_rate (2026-07-22) — zero usable movers in every cycle of both tracks; raw counts remain in the results CSVs, never scored.


## Play-caller DNA vs program identity

Cycles: 2022, 2023, 2024, 2025 — 57 movers, 135 usable metric×mover pairs.

| metric | usable | DNA MAE | program MAE | head-to-head | p |
|---|---|---|---|---|---|
| neutral_pass_rate | 55 | 0.0681 | 0.0801 | 28 – 27 | 1.000 |
| sec_per_play | 25 | 2.9160 | 4.0600 | 14 – 11 | 0.690 |
| explosive_pass_rate | 55 | 0.0259 | 0.0291 | 28 – 27 | 1.000 |

**Overall: DNA 70 – 65 program (sign-test p = 0.731) — edge: DNA.**

Per cycle: 2022: 28–16 (p=0.10); 2023: 12–17 (p=0.46); 2024: 10–23 (p=0.04); 2025: 20–9 (p=0.06)


## HC-regime identity vs program identity

Cycles: 2015, 2016, 2017, 2018, 2019, 2022, 2023, 2024, 2025 — 67 movers, 154 usable metric×mover pairs.

| metric | usable | DNA MAE | program MAE | head-to-head | p |
|---|---|---|---|---|---|
| neutral_pass_rate | 65 | 0.0750 | 0.0832 | 37 – 28 | 0.321 |
| sec_per_play | 23 | 3.0986 | 4.5000 | 16 – 7 | 0.093 |
| explosive_pass_rate | 66 | 0.0242 | 0.0274 | 37 – 29 | 0.389 |

**Overall: DNA 90 – 64 program (sign-test p = 0.044) — edge: DNA.**

Per cycle: 2015: 5–4 (p=1.00); 2016: 9–2 (p=0.07); 2017: 9–4 (p=0.27); 2018: 7–7 (p=1.00); 2019: 7–11 (p=0.48); 2022: 11–8 (p=0.65); 2023: 9–4 (p=0.27); 2024: 23–16 (p=0.34); 2025: 10–8 (p=0.81)
