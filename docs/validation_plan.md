# Validation plan — proving the predictions work

Three layers, in time order. The engine predicts *tendencies*, never game
outcomes; validation means profile error (MAE per sticky dial), not picking
scores. "His neutral pass rate has been within ±5 points of our prediction at
every stop" is a usable claim; "we predicted the upset" dies the first time
it's wrong.

## 1. Phase 0 backtest — DONE (one season)

Out-of-sample test on 2025 movers (`sideline-phase0/`): coach DNA beat the
program-identity baseline 20–9 overall (sign-test p = 0.061). Per dial:
pace 8–1 (p = 0.039), early-down pass rate 7–3, explosive-pass rate 5–5,
4th-down go rate no usable samples. One season of ~15 movers = small n,
hence layer 2.

## 2. Backtest expansion — DONE 2026-07-22 (four cycles, two hypotheses)

**Play-caller track** (hand-verified movers, `movers_2022..2025.csv`): the
2022 cycle (19 movers, two independent agent sweeps merged 2026-07-22) joined
2023/2024/2025 for 57 movers, 135 usable metric×mover pairs. Combined:
**coach DNA 70–65 program, sign-test p = 0.731 — a wash, and violently
cycle-dependent** (2022: 28–16 DNA; 2023: 12–17; 2024: 10–23 program,
p=0.04; 2025: 20–9 DNA). The 2024 "program identity wins" verdict did not
replicate; treat single-cycle sign tests as noise. Note MAE favors coach DNA
on all three usable dials (e.g. pass rate .068 vs .080) — DNA loses its
coin-flips small and wins big.

**HC-regime track** (NEW — systematic, no hand-verification: CFBD /coaches
attribution via `hc_database.py`, backtest via `backtest_hc.py`,
pre-registered filters in the file header): 37 HC movers, 2022–2025.
**HC regime beats program identity in ALL FOUR cycles** (11–8, 9–4, 23–16,
10–8), pooled **53–36, p = 0.089**, better MAE on every usable dial. Not
p<.05, but the only directionally stable signal in the project so far.
Regime-level caveat: the HC's coordinators often move with him — this track
deliberately bundles staff+scheme into "regime".

fourth_down_go_rate: still zero usable samples in every cycle of both tracks
(MIN_SAMPLES=12 in the 34–70 yd decision zone is rarely met by one season).
Either drop the dial or widen the zone before citing it.

Cross-cycle aggregation: `python3 src/verdict_combined.py` →
`output/verdict_combined.md` (the two tracks are never pooled together).
105 HC regime profiles live in `data/profiles/head_coaches/` (regime-level;
never mix with play-caller profiles in `data/profiles/coaches/`).

**API budget (measured against the shared cache, 2026-07-15).** Offense-side
pulls cost ~17 calls per uncached team-season. The Phase 0 client now shares
the repo-root `data/cache/` with the ingest layer (identical cache keys,
verified by reproducing the Phase 0 verdict byte-for-byte from cache), so
ingest-queue pulls and backtest pulls never double-pay. Even so, the rosters
are big: **2024 cycle = 1,258 uncached calls; 2023 cycle = 1,547** (15 and
13 movers, 83 and 92 distinct team-seasons; running 2024 first shrinks 2023
via overlap). The free tier's 1,000/month cannot fit either cycle alongside
the ~670-call ingest queue. Options:

1. **Free tier**: Aug = ingest queue + start of 2024 cycle (the backtest is
   resumable — cache-first, so partial months accumulate); Sept = finish
   2024; Oct = 2023. Backtest results arrive mid-season — fine for the
   portfolio, late for the flagship brief.
2. **CFBD Patreon tier for a month or two** (~$5–10/mo, much higher call
   limit): everything — queue + both cycles — lands in early August, and the
   expanded validation can be cited in the Arizona brief. Recommended if the
   flagship matters; cancel after.

## 3. In-season prediction ledger — 2026 (the credibility loop)

`analysis/ledger.py`:

- **Freeze** (`predict --all --season 2026`) after the August ingest lands
  and before week 1. Files land in `data/ledger/predictions/`, refuse
  overwrite, and carry both Phase 0 predictors (coach DNA + program
  baseline) with provenance. Commit them — git history is the notary that
  predictions preceded the games.
- **Score** (`score --season 2026`) weekly after ingesting the opponent's
  new games. Scores against the opponent's CUMULATIVE season-to-date
  profile, never a single game (~70 plays sliced into buckets is game-script
  noise — Phase 0 design rule). Early-season numbers are provisional; n is
  printed on every row.
- By midseason the brief gains a track-record section: predicted vs actual
  per dial, coach-DNA vs program head-to-head, sample sizes shown.

Current dry-run state (2026-07-15): Arizona is the only opponent with both
predictors available today (Doege pooled profile + Arizona 2025 team
profile); TCU has program-only; the rest unlock with the August ingest.
