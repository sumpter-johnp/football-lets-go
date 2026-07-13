# Phase 0 — Does coach DNA travel?

Out-of-sample backtest of the project's riskiest assumption: that a play-caller's
tendencies persist when he changes schools. Runs before anything else gets built.

## The test

For each offensive play-caller who moved into a new FBS job for 2025:

- **predictor (a)** — his pooled tendency profile from prior stops (coach DNA)
- **predictor (b)** — the new team's 2024 profile under the previous play-caller (program identity)
- **actual** — the new team's full-2025 profile

Whichever predictor lands closer to actual, per metric, wins. Movers are the
natural experiment; coaches who stayed put confound coach and team.

Four sticky metrics, all under a situation-neutral filter (one-score game,
Q1–Q3, no two-minute drill): early-down pass rate, seconds per snap,
4th-and-short go rate in the decision zone, and explosive-pass rate (a shot
proxy — the weakest of the four, since it's completion-contaminated).

## Run it

```bash
pip install requests pandas          # pandas optional; core uses stdlib
export CFBD_API_KEY=your_key         # free: https://collegefootballdata.com/key

# 0. prove the pipeline logic works (no API needed)
python src/selftest.py

# 1. seed head-coach mover candidates (CFBD has NO coordinator data — HCs only)
python src/find_hc_movers.py

# 2. edit movers_2025.csv: keep play-calling HCs, add coordinator movers by hand
#    from school announcements; set prior_stops to actual play-calling seasons

# 3. run the backtest (first run pulls & caches PBP; re-runs are instant)
python src/backtest.py
```

Outputs land in `output/`: `results.csv` (one row per mover × metric, with both
errors, sample sizes, and winner) and `verdict.md` (per-metric MAE comparison,
head-to-head record, sign-test p-value, and the interpretation guide).

## Design decisions worth remembering

- **The outline said "pull movers from the CFBD coaches endpoint."** That
  endpoint is head-coaches-only, so the movers list is hybrid: API-seeded HC
  movers + hand-curated coordinator movers. Don't fill the CSV from memory —
  play-calling responsibility is exactly the thing memory gets wrong.
- **Offense only for now.** All four metrics are offensive dials. A defensive
  version needs different metrics (havoc proxies) and is a follow-on.
- **Minimum sample thresholds** (`MIN_SAMPLES` in metrics.py) gate every
  comparison; a mover-metric pair below threshold is reported but excluded from
  the verdict. 4th-down decisions are rare (~12/season in the zone), so expect
  that metric to be the noisiest.
- **Known biases that don't break the comparison:** scrambles log as rushes
  (hits predictors and actuals equally); explosive rate measures receivers
  partly. Both are flagged in the verdict caveats.
- **API budget:** ~17 requests per team-season, cached to disk. A 15-mover run
  touching ~45 team-seasons ≈ 800 calls — fine on the free tier, and free on
  every re-run.

## What decides Phase 1

Partial persistence is the expected (and sufficient) result: the metrics where
coach DNA beats the program baseline are the dials the DNA profile is allowed
to claim. If program identity wins everything, the coach DNA layer demotes to
a qualitative sidebar and the project leads with team-season tendencies.

## Movers list (pre-researched)

`movers_2025.csv` ships populated with 10 verified-in-prose FBS-to-FBS offensive
play-caller moves from the 2024-25 cycle (sourced from the 247Sports Power Four
coordinator carousel and FootballScoop's 2024-25 OC tracker), including Malzahn
to FSU, Grimes to Wisconsin, Arbuckle to Oklahoma, and — usefully for the
flagship brief — Seth Doege to Arizona. Rows tagged VERIFY need a one-minute
check against a school announcement. Four excluded candidates are kept as
comments with the reason (in-season takeover, no recent play-calling, title
without play-calling duties, fired-3-games-in).

## Wikipedia staff scraper

`src/wiki_staff.py` pulls head coach / OC / DC from Wikipedia team-season page
infoboxes ("2024 Arizona Wildcats football team") via the MediaWiki API:

```bash
python src/wiki_staff.py "Arizona Wildcats" 2021 2025
python src/wiki_staff.py --teams-file big12.txt 2021 2025 > stints_raw.csv
```

Use it to cross-check movers_2025.csv and, later, to bulk-seed Phase 1's
coach_stints table. Remember: Wikipedia records title holders, not play-callers
— it narrows the search, the announcement confirms.
