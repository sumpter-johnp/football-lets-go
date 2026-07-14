-- Project Sideline (opponent intelligence engine) — Phase 1 data foundation.
-- Applied to the HomeBase Supabase project as migration `sideline_phase1_schema`
-- (2026-07-13). Lives entirely in the `sideline` schema; never touches the web
-- app's `public` schema. Not exposed via the Supabase API; accessed server-side
-- from Python only.

create schema sideline;

create table sideline.teams (
  id bigint generated always as identity primary key,
  school text not null unique,              -- CFBD canonical name, e.g. 'BYU'
  conference text,
  classification text,                      -- 'fbs' / 'fcs'
  cfbd_id integer unique
);

create table sideline.coaches (
  id bigint generated always as identity primary key,
  name text not null unique
);

-- coach × team × role × years; play_caller is the field that matters and the
-- one Wikipedia/CFBD get wrong — null means unverified, only true/false after
-- checking a school announcement (per Phase 0 lesson).
create table sideline.coach_stints (
  id bigint generated always as identity primary key,
  coach_id bigint not null references sideline.coaches(id),
  team_id bigint not null references sideline.teams(id),
  role text not null check (role in ('HC', 'OC', 'DC', 'other')),
  unit text check (unit in ('offense', 'defense', 'special')),
  play_caller boolean,                      -- null = not yet verified against an announcement
  start_year int not null,
  end_year int,                             -- null = current
  source text,                              -- announcement URL / wikipedia page
  notes text,
  unique (coach_id, team_id, role, start_year)
);

create table sideline.games (
  id bigint primary key,                    -- CFBD game id
  season int not null,
  week int,
  season_type text,                         -- 'regular' / 'postseason'
  start_date timestamptz,
  home_team_id bigint references sideline.teams(id),
  away_team_id bigint references sideline.teams(id),
  home_points int,
  away_points int,
  neutral_site boolean
);

-- One row per play, situation fields as CFBD returns them (snake_cased),
-- ppa = CFBD's EPA-like predicted-points-added metric.
create table sideline.plays (
  id text primary key,                      -- CFBD play id (string-typed in API)
  game_id bigint references sideline.games(id),
  drive_id text,
  season int not null,
  week int,
  offense_team_id bigint references sideline.teams(id),
  defense_team_id bigint references sideline.teams(id),
  period int,
  clock_seconds int,                        -- seconds remaining in period
  down int,
  distance int,
  yardline int,
  yards_to_goal int,
  yards_gained int,
  play_type text,
  play_text text,
  offense_score int,
  defense_score int,
  ppa numeric,
  scoring boolean,
  drive_number int,
  play_number int
);

create index plays_offense_season_idx on sideline.plays (offense_team_id, season);
create index plays_game_idx on sideline.plays (game_id);
create index plays_situation_idx on sideline.plays (down, distance, period);
create index coach_stints_team_idx on sideline.coach_stints (team_id, start_year);

-- Defense in depth: RLS on (deny-by-default, no policies). Server-side ingestion
-- uses the service role, which bypasses RLS; web-app API roles get no grants at all.
alter table sideline.teams enable row level security;
alter table sideline.coaches enable row level security;
alter table sideline.coach_stints enable row level security;
alter table sideline.games enable row level security;
alter table sideline.plays enable row level security;
