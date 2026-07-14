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

## Tier 1 — Arizona (flagship brief, Sept 12) — VERIFIED 2026-07-13 ✅

- [x] **Seth Doege, Arizona OC 2025–26** — `play_caller = true`, both seasons.
      2025: Brennan's own postgame remarks — "Coach Doege called a great game"
      ([Colorado 11/1/25 postgame PDF](https://cubuffs.com/documents/download/2025/11/2/Postgame_Quotes.pdf),
      repeated after the [Territorial Cup](https://www.azdesertswarm.com/football/72966/arizona-wildcats-football-postgame-comments-territorial-cup-brent-brennan-treydan-stukes)).
      2026: returning for Year 2 per [Tucson.com interview, 7/3/26](https://tucson.com/sports/college/football/wildcats/article_fdcfa6c4-f6fd-4e8a-8529-c8d6301b7a39.html),
      coordinator extension through 2028.
- [x] **Brent Brennan, Arizona HC 2024–26** — `play_caller = false`. Credits
      Doege with play-calling in his own postgame remarks; career WR/ST
      background, no play-calling history.
- [x] **Seth Doege prior stops** — narrower than hoped: **Marshall 2024 is his
      only prior play-calling season.** Official Arizona bio: Bowling Green
      2016–18 (GA/WR/STC), USC 2019–21 (QC → TEs), Ole Miss 2022 (analyst),
      Purdue 2023 (TEs), Marshall 2024 (OC — [announced as play-caller at
      hire](https://wchstv.com/sports/top-sports/marshall-hires-seth-doege-as-new-offensive-coordinator)).
      Marshall 2024 stint added to `coach_stints` (`play_caller = true`);
      Marshall 2024 queued for ingest. **Brief implication:** his DNA profile
      rests on one Marshall season + Arizona 2025 — sample-size caveat
      mandatory, and Arizona 2025 self-scout becomes the stronger signal.

## Tier 2 — 2026 opponents, in schedule order (offense) — VERIFIED 2026-07-13 ✅

All verdicts recorded in `coach_stints` with sources + notes. Summary
(grade in parens; LIKELY = solid indirect evidence, upgrade when a direct
quote appears):

| wk | Team | 2026 play-caller | Grade | DNA base (prior play-calling) |
|---|---|---|---|---|
| 3 | Colorado State | **Pryce Tracy** (OC) | CONFIRMED | **None — first-time caller.** No baseline exists |
| 5 | TCU | **Gordon Sammis** (OC) | CONFIRMED | UConn 2024–25 (queued). NOT W&M — title was OL/run-game |
| 6 | Iowa State | **Tyler Roehl** (OC) | LIKELY | NDSU 2019–23, FCS — public PBP too thin; say so in brief |
| 7 | Notre Dame | **Mike Denbrock** (OC) | CONFIRMED | ND 2024–25 in-scope; (LSU before, not yet needed) |
| 8 | UCF | **Scott Frost (HC)** — not OC Cooper | CONFIRMED '25 / LIKELY '26 | UCF 2025 + his HC history; Cooper flagged false |
| 9 | Arizona State | **Marcus Arroyo** (OC) | CONFIRMED '24–25 / LIKELY '26 | ASU 2024–25 (early-'24 Dillingham-contaminated) |
| 11 | Baylor | **Jake Spavital** (OC) | CONFIRMED '24 / LIKELY '25–26 | Baylor 2024–25 in-scope |
| 12 | Kansas | **Andy Kotelnicki** (assoc HC) | CONFIRMED | KU 2021–23 verified; PSU 2024–25 OC title only — play-calling UNVERIFIED |
| 13 | Cincinnati | **Scott Satterfield (HC)** — not co-OCs Thomas/Cardwell | CONFIRMED | Cincy 2023–25 ("fourth season calling") |

**Findings that corrected our data:**
- **Kansas**: Wikipedia's 2026 page missed Kotelnicki's January return from
  Penn State — he retakes play-calling; Zebrowski (2025 caller) slides to
  passing-game coordinator. Stint table corrected.
- **Cincinnati**: Satterfield has called plays all along (2023–26); OCs Glenn
  and now Thomas/Cardwell were/are never the play-caller. Attribution 2023–25
  goes to Satterfield.
- **ASU 2023 splits mid-season**: Baldwin weeks 1–3 → Dillingham week 4 on.
  Dillingham HC stint split into 2023 (caller) and 2024–26 (not) rows.
- **Two HC play-callers on the 2026 slate**: Frost and Satterfield — for
  these teams, HC history (not OC history) is the DNA source.

## Tier 3 — historical attribution for ingested plays (2023–25)

Needed before Phase 2 attributes tendencies to coaches. Plays already in DB
for these team-seasons:

- [ ] **BYU 2023–25**: Aaron Roderick play-called all three seasons? (Also
      2021–22 for continuity when those seasons ingest.)
- [ ] **Arizona 2023**: Jedd Fisch (HC) vs Brennan Carroll (OC) — Fisch was
      widely reported as the primary offensive play-caller; verify and set
      flags on BOTH rows (this flips attribution of Arizona 2021–23 film).
- [ ] **Arizona 2024**: Dino Babers (OC, one year) — play-caller under Brennan?
- [x] **TCU 2023–25**: Kendal Briles — CONFIRMED via Tier 2 research (coverage
      of Sammis's hire names Briles the 2023–25 caller; departed for South
      Carolina). Recorded in DB.

## Tier 4 — Phase 0 verified facts, carry into the DB

Already verified in prose during Phase 0 (`sideline-phase0/movers_2025.csv`)
— transcribe, don't re-research:

- [ ] Gus Malzahn play-called UCF **2021–2023**, handed duties to Tim Harris
      Jr. **late 2024** (FootballScoop) → `play_caller=true` on Malzahn
      2021–23 portion; note the 2024 split on both his and Harris's rows.
- [x] Jeff Grimes play-called Baylor **2021–23** (LIKELY grade — widely
      credited, Broyles finalist, no flat quote found) and Kansas **2024**
      (CONFIRMED — called all season; week-4 booth move was location only).
      Recorded in DB via Tier 2 research.
- [ ] Jason Beck play-called Utah **2025** (his stint pre-dates the 2026
      staff turnover).

## Bookkeeping as you go

- Every "prior stops" answer that names a team-season we haven't ingested
  goes into an **ingest queue** list at the bottom of this file.
- If verification contradicts a scraped stint (wrong years, missing interim),
  fix the `coach_stints` row and note it here — the CSV is the audit trail,
  the DB is the truth.

### Ingest queue (fill as Tier 1/2 answers come in)

- [ ] **Marshall 2024** — Doege's only pre-Arizona play-calling season:
      `python3 ingest/ingest_team_season.py Marshall 2024`
- [ ] **UConn 2024 2025** — Sammis (TCU) play-calling seasons
- [ ] **Utah State 2025** — McGiven (Utah) confirmed play-calling season
- [ ] **Oregon State 2016 2017** — McGiven; 2016 confirmed primary caller,
      2017 use with caution (Andersen mid-season resignation)
- [ ] **Kansas 2021–23 + 2025** — Kotelnicki's verified KU seasons + the
      Zebrowski 2025 season (Kansas already scoped; lands with the Aug 1 batch)
- [ ] Penn State 2024–25 — **hold**: Kotelnicki's play-calling there is
      UNVERIFIED; verify before spending the ~74 API calls
- [ ] San Jose State 2018–23 — **hold**: McGiven per-season play-calling
      unverified; verify before ingesting six seasons
- North Dakota State 2019–23 (Roehl) — **not ingestable**: FCS PBP coverage
  too thin; the brief states the gap honestly instead
