# Coach DNA — qualitative layer

One file per verified 2026 play-caller: the public record on philosophy,
tempo, risk, and play-calling process, with a source URL on every claim.
Complements the quantitative profiles in `data/profiles/coaches/` — Phase 3
brief synthesis reads both. Play-caller identities were verified in
`docs/play_caller_checklist.md`; nothing here relies on memory.

Evidence grades: **CONFIRMED** = direct quote / on-record statement;
**SECONDHAND** = reporter characterization. Direct quotes appear only when
the exact words appear in the cited source.

| 2026 game | Team | Play-caller | File | Stat profile |
|---|---|---|---|---|
| Sept 12 (flagship) | Arizona | Seth Doege (OC) | [seth-doege.md](seth-doege.md) | `seth-doege.json` |
| wk 3 | Colorado State | Pryce Tracy (OC) | [pryce-tracy.md](pryce-tracy.md) | none — first-time caller |
| wk 5 | TCU | Gordon Sammis (OC) | [gordon-sammis.md](gordon-sammis.md) | UConn 24-25 (Aug ingest) |
| wk 6 | Iowa State | Tyler Roehl (OC) | [tyler-roehl.md](tyler-roehl.md) | none — FCS data too thin |
| wk 7 | Notre Dame | Mike Denbrock (OC) | [mike-denbrock.md](mike-denbrock.md) | ND 24-25 (not yet queued) |
| wk 8 | UCF | Scott Frost (HC) | [scott-frost.md](scott-frost.md) | fragments only so far |
| wk 9 | Arizona State | Marcus Arroyo (OC) | [marcus-arroyo.md](marcus-arroyo.md) | fragments only so far |
| wk 11 | Baylor | Jake Spavital (OC) | [jake-spavital.md](jake-spavital.md) | fragments only so far |
| wk 12 | Kansas | Andy Kotelnicki (assoc HC) | [andy-kotelnicki.md](andy-kotelnicki.md) | KU 21-23 + PSU 24-25 (Aug ingest) |
| wk 13 | Cincinnati | Scott Satterfield (HC) | [scott-satterfield.md](scott-satterfield.md) | fragments only so far |
| rivalry | Utah | Kevin McGiven (OC) | [kevin-mcgiven.md](kevin-mcgiven.md) | USU 25 + SJSU + OSU (Aug ingest) |

## HC-regime layer (decision 2026-07-22: full context layer)

Regime-level profiles (`data/profiles/head_coaches/`, built systematically
from CFBD /coaches — validated 90–64, p=.044 over nine backtest cycles) slot
into the brief's Coach DNA section with FOUR jobs, per John's 2026-07-22
call. A regime profile NEVER overrides a verified play-caller profile
(pre-registered hierarchy: play-caller > HC-regime > none-flag), and the two
families are never pooled.

1. **Coverage** — coach-side blend input where no play-caller stat profile
   exists yet. Bites NOW for the two HC-callers (Frost 4 profiled seasons,
   Satterfield 9) whose play-caller rows above say "fragments only"; for an
   HC-caller the regime profile is nearly play-caller-grade anyway (caveat:
   bundles their coordinators).
2. **Corroboration flags** — where both layers exist, the brief marks each
   dial agree/diverge. Arizona: Doege pace 30 vs Brennan regime 31.2 =
   AGREE (independently corroborates the say/do tempo tension flagged in
   [seth-doege.md](seth-doege.md)); Doege neutral pass .423 vs regime .522 =
   DIVERGE (the SJSU-era pass-heaviness belonged to Brennan's old OCs — the
   offense is Doege's, not a Brennan house style; that itself is the
   insight).
3. **Deep-pool descriptive stats** — regime pooling gives usable n on dials
   a single season can't support. Flagship example: Brennan's 4th-down
   decision-zone go rate is .14 on n=50 across 8 seasons — historically
   conservative — against his own 2025 "extremely aggressive on fourth
   down" narrative. The 2025 aggression is new/situational, not a regime
   trait. (fourth_down_go_rate is retired from SCORED verdicts; descriptive
   use with n and the retirement caveat is exactly what it's still for.)
4. **Credibility box** — the brief cites the nine-cycle validation
   (`sideline-phase0/output/verdict_combined.md`) and the blend evidence
   (`output/blend_analysis.md`) in one short sidebar.

Regime coverage of the 2026 slate (profiled seasons reflect today's play
cache and deepen with the August ingest):

| Team | HC | Regime profile | Stints |
|---|---|---|---|
| Arizona | Brent Brennan | 8 seasons | SJSU 2017-23; Arizona 2024- |
| Colorado State | Jay Norvell | 5 seasons | Nevada 2017-21; CSU 2022- |
| TCU | Sonny Dykes | 9 seasons | Cal 2014-16; SMU 2018-21; TCU 2022- |
| Iowa State | Matt Campbell | 3 seasons | Toledo 2014-15; ISU 2016- |
| Notre Dame | Marcus Freeman | 3 seasons | ND 2021- |
| UCF | Scott Frost | 4 seasons | UCF 2016-17; Nebraska 2018-22; UCF 2025- |
| Arizona State | Kenny Dillingham | none — first HC job | — |
| Baylor | Dave Aranda | 4 seasons | Baylor 2020- |
| Kansas | Lance Leipold | 5 seasons | Buffalo 2015-20; Kansas 2021- |
| Cincinnati | Scott Satterfield | 9 seasons | App St 2014-18; Louisville 2019-22; Cincy 2023- |
| Utah | Kyle Whittingham | 4 seasons | Utah 2014- |
