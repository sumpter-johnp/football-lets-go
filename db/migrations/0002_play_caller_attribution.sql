-- Project Sideline — game-level play-caller attribution.
-- Applied to the HomeBase Supabase project as migration
-- `play_caller_attribution` (2026-07-15).
--
-- coach_stints is year-granular, but three verified handoffs happened
-- MID-season, so a naive stints join would misattribute film:
--   * Arizona 2024   — Babers games 1-3, Matt Adkins from game 4 (Utah, 9/28/24)
--   * Arizona St 2023 — Baldwin weeks 1-3, Dillingham from week 4 (USC game)
--   * UCF 2024       — Malzahn through 10/26 (BYU); handoff announced 10/28/24,
--                      Tim Harris Jr. called from 11/2 (Arizona) on
--                      (https://mynews13.com/fl/orlando/sports/2024/10/29/ucf-s-malzahn-fires-defensive-coordinator--will-no-longer-calls-offensive-plays)
--
-- Design: game_play_callers holds explicit per-game overrides (only split
-- seasons need rows). play_attribution resolves every play: override first,
-- else the season-level stint when the team-season has exactly ONE verified
-- caller, else flagged 'ambiguous' (split season missing overrides) or
-- 'unattributed' (no verified stint). Phase 2 must consume plays through
-- play_attribution, never by joining stints directly.
--
-- KNOWN FUTURE OVERRIDE (game not yet ingested): Kansas 2023 Guaranteed Rate
-- Bowl was called by interim Jim Zebrowski, not Kotelnicki. The season-level
-- fallback would silently credit Kotelnicki — insert the override when the
-- Aug 1 batch lands (reminder lives in ingest/run_ingest_queue.sh).

create table sideline.game_play_callers (
  game_id bigint not null references sideline.games(id),
  team_id bigint not null references sideline.teams(id),
  unit text not null default 'offense' check (unit in ('offense', 'defense')),
  coach_id bigint not null references sideline.coaches(id),
  source text,
  notes text,
  primary key (game_id, team_id, unit)
);

alter table sideline.game_play_callers enable row level security;

-- team-season -> verified offensive caller(s) per coach_stints. sole_coach_id
-- is only meaningful when n_callers = 1; split seasons have n_callers > 1 and
-- must be resolved by game_play_callers rows.
create view sideline.season_play_callers as
select
  cs.team_id,
  yr.season,
  count(*) as n_callers,
  min(cs.coach_id) as sole_coach_id
from sideline.coach_stints cs
cross join lateral generate_series(
  cs.start_year, coalesce(cs.end_year, extract(year from current_date)::int)
) as yr(season)
where cs.play_caller
  and coalesce(cs.unit, 'offense') = 'offense'   -- HC rows carry null unit
group by cs.team_id, yr.season;

-- One row per play: who called it, and on what basis.
create view sideline.play_attribution as
select
  p.id as play_id,
  p.game_id,
  p.season,
  p.week,
  p.offense_team_id,
  coalesce(gpc.coach_id, case when spc.n_callers = 1 then spc.sole_coach_id end) as coach_id,
  case
    when gpc.coach_id is not null then 'game_override'
    when spc.n_callers = 1 then 'season_stint'
    when spc.n_callers > 1 then 'ambiguous'      -- split season missing overrides
    else 'unattributed'                          -- no verified stint covers it
  end as basis
from sideline.plays p
left join sideline.game_play_callers gpc
  on gpc.game_id = p.game_id
 and gpc.team_id = p.offense_team_id
 and gpc.unit = 'offense'
left join sideline.season_play_callers spc
  on spc.team_id = p.offense_team_id
 and spc.season = p.season;

-- QA rollup: play counts by team-season x caller x basis. 'ambiguous' rows
-- here mean a split season is missing its game_play_callers rows.
create view sideline.attribution_coverage as
select
  t.school,
  pa.season,
  pa.basis,
  c.name as play_caller,
  count(*) as plays
from sideline.play_attribution pa
join sideline.teams t on t.id = pa.offense_team_id
left join sideline.coaches c on c.id = pa.coach_id
group by t.school, pa.season, pa.basis, c.name;

-- ---- Seed overrides for the split seasons currently ingested ----

insert into sideline.game_play_callers (game_id, team_id, unit, coach_id, source, notes)
select v.game_id, t.id, 'offense', c.id, v.source, v.notes
from (values
  -- Arizona 2024: Babers games 1-3
  (401636608, 'Arizona', 'Dino Babers', 'coach_stints Tier 3 verification', 'Game 1 (New Mexico 9/1/24) — Babers called games 1-3'),
  (401636614, 'Arizona', 'Dino Babers', 'coach_stints Tier 3 verification', 'Game 2 (NAU 9/8/24) — Babers called games 1-3'),
  (401636864, 'Arizona', 'Dino Babers', 'coach_stints Tier 3 verification', 'Game 3 (at Kansas State 9/14/24) — Babers'' last game calling'),
  -- Arizona 2024: Adkins from game 4 (Utah upset) through season end
  (401636886, 'Arizona', 'Matt Adkins', 'coach_stints Tier 3 verification', 'Game 4 (at Utah 9/29/24) — Adkins'' first game calling'),
  (401636887, 'Arizona', 'Matt Adkins', 'coach_stints Tier 3 verification', 'Adkins from game 4 on'),
  (401636893, 'Arizona', 'Matt Adkins', 'coach_stints Tier 3 verification', 'Adkins from game 4 on'),
  (401636897, 'Arizona', 'Matt Adkins', 'coach_stints Tier 3 verification', 'Adkins from game 4 on'),
  (401636905, 'Arizona', 'Matt Adkins', 'coach_stints Tier 3 verification', 'Adkins from game 4 on'),
  (401636916, 'Arizona', 'Matt Adkins', 'coach_stints Tier 3 verification', 'Adkins from game 4 on'),
  (401636923, 'Arizona', 'Matt Adkins', 'coach_stints Tier 3 verification', 'Adkins from game 4 on'),
  (401636935, 'Arizona', 'Matt Adkins', 'coach_stints Tier 3 verification', 'Adkins from game 4 on'),
  (401636940, 'Arizona', 'Matt Adkins', 'coach_stints Tier 3 verification', 'Adkins from game 4 on'),
  -- Arizona State 2023: only ingested game is wk 13 Territorial Cup — Dillingham era (wk 4+)
  (401524064, 'Arizona State', 'Kenny Dillingham', 'coach_stints Tier 2 verification', 'Territorial Cup 11/25/23 — Dillingham called from week 4 on'),
  -- UCF 2024: Malzahn through BYU 10/26; Harris from Arizona 11/2
  (401636866, 'UCF', 'Gus Malzahn', 'https://mynews13.com/fl/orlando/sports/2024/10/29/ucf-s-malzahn-fires-defensive-coordinator--will-no-longer-calls-offensive-plays', 'at TCU 9/14/24 — pre-handoff (announced 10/28/24)'),
  (401636911, 'UCF', 'Gus Malzahn', 'https://mynews13.com/fl/orlando/sports/2024/10/29/ucf-s-malzahn-fires-defensive-coordinator--will-no-longer-calls-offensive-plays', 'vs BYU 10/26/24 — Malzahn''s last game calling; handoff announced 10/28/24'),
  (401636916, 'UCF', 'Tim Harris Jr.', 'https://mynews13.com/fl/orlando/sports/2024/10/29/ucf-s-malzahn-fires-defensive-coordinator--will-no-longer-calls-offensive-plays', 'vs Arizona 11/2/24 — Harris'' first game calling')
) as v(game_id, school, coach, source, notes)
join sideline.teams t on t.school = v.school
join sideline.coaches c on c.name = v.coach;
