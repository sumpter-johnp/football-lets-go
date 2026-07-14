# Play-caller verification checklist

Every `coach_stints.play_caller` flag is NULL until verified here. Wikipedia
records **title holders, not play-callers** — the announcement or a presser
quote confirms. This is the Phase 0 lesson encoded as process: never fill
play-calling responsibility from memory.

**Sources, in order of trust:** school announcement / press release → beat
coverage with a direct quote ("I'll be calling plays") → FootballScoop /
247Sports coordinator trackers. Record the URL.

**Offense first.** Phase 0 validated offensive dials only (pace, early-down
pass rate); the DNA layer claims nothing on defense yet. DC rows can stay
NULL until a defensive metrics version exists.

## Recording a verdict

```sql
update sideline.coach_stints cs
set play_caller = true,   -- or false
    source = cs.source || ' | <verification url>',
    notes  = coalesce(cs.notes || '; ', '') || '<one-line evidence>'
from sideline.coaches c, sideline.teams t
where cs.coach_id = c.id and cs.team_id = t.id
  and c.name = '<coach>' and t.school = '<school>'
  and cs.role = '<HC|OC|DC>' and cs.start_year = <year>;
```

Check the box here and paste the URL next to it when done.

---

## Tier 1 — Arizona (flagship brief, Sept 12) — verify first

- [ ] **Seth Doege, Arizona OC 2025–26** — confirmed play-caller for 2025?
      Retained duties into 2026? (Second year under Brennan; Phase 0's
      movers file verified Marshall 2024 play-calling, not the Arizona
      arrangement itself.) Two verdicts: `start_year=2025` stint covers both
      years — verify each season's arrangement before setting the flag.
- [ ] **Brent Brennan, Arizona HC 2024–26** — confirm he does NOT call
      offensive plays (career WR/ST background suggests not; confirm and set
      `play_caller = false` so attribution queries can exclude him cleanly).
- [ ] **Seth Doege prior stops** — from the announcement, list every season
      he actually called plays before Arizona (Phase 0 has Marshall 2024
      verified). Needed for his DNA profile → add rows to `coach_stints`
      and queue those team-seasons for CFBD ingest.

## Tier 2 — 2026 opponents, in schedule order (offense)

**New-to-team 2026 play-callers (highest value — this is the coach-DNA case):**

- [ ] wk 3, **Colorado State**: Jim L. Mora (HC, new) + Pryce Tracy (OC, new)
      — who calls it? Then Tracy's/Mora's prior play-calling stops → stints + ingest queue.
- [ ] wk 5, **TCU**: Gordon Sammis (OC, new) — does he call plays or does
      Sonny Dykes take it back? Dykes has historically delegated (Riley,
      Briles) but verify this hire's arrangement. Sammis prior stops → queue.
- [ ] wk 6, **Iowa State**: entire staff new (Jimmy Rogers HC, Tyler Roehl OC).
      Who calls plays? Prior stops likely FCS (thin CFBD data — flag expected
      coverage gap in the brief rather than faking a profile). 
- [ ] wk 10, **Utah**: entire staff new (Morgan Scalley HC promoted, Kevin
      McGiven OC). Scalley is a career DC — almost certainly delegates
      offense; verify McGiven's arrangement + his prior play-calling stops → queue.
- [ ] wk 13, **Cincinnati**: Pete Thomas (OC, new) — play-caller or does
      Satterfield keep calling? Satterfield has a history of calling his own
      offense; this one genuinely matters. Thomas prior stops → queue.

**Continuity staffs (verify once, mostly presser-quote checks):**

- [ ] wk 7, **Notre Dame**: Mike Denbrock (OC since 2024) — confirm he calls it
      (Freeman is defense-side).
- [ ] wk 8, **UCF**: Scott Frost (HC) vs Steve Cooper (OC) — Frost has
      historically called his own plays; confirm the 2025/26 arrangement.
- [ ] wk 9, **Arizona State**: Kenny Dillingham (offense-background HC) vs
      Marcus Arroyo (OC) — known shared-duties ambiguity; pin down who holds
      the call sheet.
- [ ] wk 11, **Baylor**: Jake Spavital (OC since 2024) — confirm (Aranda is
      defense-side and has never called offense).
- [ ] wk 12, **Kansas**: Jim Zebrowski (OC since 2025) vs Leipold — confirm
      (Kotelnicki-era precedent says the OC calls it).

## Tier 3 — historical attribution for ingested plays (2023–25)

Needed before Phase 2 attributes tendencies to coaches. Plays already in DB
for these team-seasons:

- [ ] **BYU 2023–25**: Aaron Roderick play-called all three seasons? (Also
      2021–22 for continuity when those seasons ingest.)
- [ ] **Arizona 2023**: Jedd Fisch (HC) vs Brennan Carroll (OC) — Fisch was
      widely reported as the primary offensive play-caller; verify and set
      flags on BOTH rows (this flips attribution of Arizona 2021–23 film).
- [ ] **Arizona 2024**: Dino Babers (OC, one year) — play-caller under Brennan?
- [ ] **TCU 2023–25**: Kendal Briles — confirm play-calling (strong prior:
      career play-caller).

## Tier 4 — Phase 0 verified facts, carry into the DB

Already verified in prose during Phase 0 (`sideline-phase0/movers_2025.csv`)
— transcribe, don't re-research:

- [ ] Gus Malzahn play-called UCF **2021–2023**, handed duties to Tim Harris
      Jr. **late 2024** (FootballScoop) → `play_caller=true` on Malzahn
      2021–23 portion; note the 2024 split on both his and Harris's rows.
- [ ] Jeff Grimes play-called Baylor **2021–23** and Kansas **2024**
      (247Sports) → flags on both stints.
- [ ] Jason Beck play-called Utah **2025** (his stint pre-dates the 2026
      staff turnover).

## Bookkeeping as you go

- Every "prior stops" answer that names a team-season we haven't ingested
  goes into an **ingest queue** list at the bottom of this file.
- If verification contradicts a scraped stint (wrong years, missing interim),
  fix the `coach_stints` row and note it here — the CSV is the audit trail,
  the DB is the truth.

### Ingest queue (fill as Tier 1/2 answers come in)

- (empty)
