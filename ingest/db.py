"""Postgres access for the sideline schema.

Connects directly to the Supabase project's Postgres (the sideline schema is
deliberately NOT exposed via the Supabase API). Needs SUPABASE_DB_URL in the
environment or .env — use the Session pooler URI from the Supabase dashboard
(Connect → Session pooler), which works on IPv4 networks; the direct
db.<ref>.supabase.co host is IPv6-only.
"""

from __future__ import annotations

import os

import psycopg2
from psycopg2.extras import execute_values

from config import load_env


def connect():
    load_env()
    url = os.environ.get("SUPABASE_DB_URL")
    if not url:
        raise RuntimeError(
            "No SUPABASE_DB_URL found. Add it to .env (see .env.example).\n"
            "Supabase dashboard → Connect → Session pooler URI."
        )
    return psycopg2.connect(url)


def upsert_teams(cur, teams: list[dict]) -> dict[str, int]:
    """Upsert team rows; returns {school: team_id} for every school passed in."""
    rows = [
        (t["school"], t.get("conference"), t.get("classification"), t.get("cfbd_id"))
        for t in teams
    ]
    execute_values(
        cur,
        """
        insert into sideline.teams (school, conference, classification, cfbd_id)
        values %s
        on conflict (school) do update
          set conference     = coalesce(excluded.conference, sideline.teams.conference),
              classification = coalesce(excluded.classification, sideline.teams.classification),
              cfbd_id        = coalesce(excluded.cfbd_id, sideline.teams.cfbd_id)
        """,
        rows,
    )
    cur.execute(
        "select school, id from sideline.teams where school = any(%s)",
        ([r[0] for r in rows],),
    )
    return dict(cur.fetchall())


def upsert_games(cur, games: list[tuple]) -> int:
    """Rows: (id, season, week, season_type, start_date, home_team_id,
    away_team_id, home_points, away_points, neutral_site)."""
    execute_values(
        cur,
        """
        insert into sideline.games (id, season, week, season_type, start_date,
                                    home_team_id, away_team_id, home_points,
                                    away_points, neutral_site)
        values %s
        on conflict (id) do update
          set home_points = excluded.home_points,
              away_points = excluded.away_points
        """,
        games,
    )
    return len(games)


def insert_plays(cur, plays: list[tuple]) -> int:
    """Rows match sideline.plays column order. Idempotent on play id."""
    execute_values(
        cur,
        """
        insert into sideline.plays (id, game_id, drive_id, season, week,
                                    offense_team_id, defense_team_id, period,
                                    clock_seconds, down, distance, yardline,
                                    yards_to_goal, yards_gained, play_type,
                                    play_text, offense_score, defense_score,
                                    ppa, scoring, drive_number, play_number)
        values %s
        on conflict (id) do nothing
        """,
        plays,
        page_size=500,
    )
    return len(plays)
