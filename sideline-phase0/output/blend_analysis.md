# Blend analysis — evidence for the Phase 2 lead-with decision

Decision (John, 2026-07-22): headline dial predictions lead with the 50/50 coach-history x program-identity blend; sec_per_play leads with the pure coach-side profile (pace travels with the coach). Both components always reported with sample sizes.


## HC-regime track — 154 usable pairs

MAE by blend weight (w = coach-side share):

| metric | w=0.0 | w=0.25 | w=0.5 | w=0.75 | w=1.0 |
|---|---|---|---|---|---|
| neutral_pass_rate (65) | 0.0832 | 0.0687 | 0.0594 | 0.0625 | 0.0749 |
| sec_per_play (23) | 4.5000 | 3.9924 | 3.4848 | 3.1547 | 3.0986 |
| explosive_pass_rate (66) | 0.0274 | 0.0237 | 0.0216 | 0.0220 | 0.0242 |

Sign tests, 50/50 blend head-to-head:

- blend vs pure coach-side: 83-71 (p = 0.3755)
- blend vs pure program: 103-51 (p = 0.0000)

## Play-caller track — 135 usable pairs

MAE by blend weight (w = coach-side share):

| metric | w=0.0 | w=0.25 | w=0.5 | w=0.75 | w=1.0 |
|---|---|---|---|---|---|
| neutral_pass_rate (55) | 0.0801 | 0.0643 | 0.0552 | 0.0578 | 0.0681 |
| sec_per_play (25) | 4.0600 | 3.5347 | 3.1724 | 2.9252 | 2.9160 |
| explosive_pass_rate (55) | 0.0291 | 0.0258 | 0.0240 | 0.0241 | 0.0259 |

Sign tests, 50/50 blend head-to-head:

- blend vs pure coach-side: 78-57 (p = 0.0848)
- blend vs pure program: 83-52 (p = 0.0096)

## Interpretation

The untuned 50/50 blend beats pure program identity decisively in both tracks and edges pure coach-side in both — the classic ensemble result. Program identity alone is the worst predictor on every dial in both tracks; the original 'demote coach DNA to a sidebar' fallback is dead. Pace is the exception in the other direction: MAE improves monotonically with coach weight in both tracks, consistent with the independent Phase 0 pace result (8-1) — tempo belongs to the coach.

Coach-side source hierarchy (pre-registered): verified play-caller profile when available, else HC-regime profile, else pure program with a 'no coach history' flag. The two coach-side profile families are never pooled with each other.
