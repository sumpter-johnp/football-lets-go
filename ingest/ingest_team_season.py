"""Ingest one or more team-seasons from CFBD into sideline.{teams,games,plays}.

Usage:
    python3 ingest/ingest_team_season.py BYU 2025
    python3 ingest/ingest_team_season.py "Texas Tech" 2023 2024 2025
    python3 ingest/ingest_team_season.py BYU 2025 --dry-run   # fetch + map, no DB

Idempotent: plays insert on-conflict-do-nothing, games update scores, teams
merge metadata. First run pulls & caches CFBD responses (~37 calls per
team-season); re-runs cost zero API calls.
"""

from __future__ import annotations

import argparse

from cfbd import CFBDClient


def clock_seconds(play: dict) -> int | None:
    clock = play.get("clock") or {}
    m, s = clock.get("minutes"), clock.get("seconds")
    if m is None or s is None:
        return None
    return m * 60 + s


def map_game(g: dict, team_ids: dict[str, int]) -> tuple:
    return (
        g["id"],
        g["season"],
        g.get("week"),
        g.get("season_type"),
        g.get("start_date"),
        team_ids.get(g.get("home_team")),
        team_ids.get(g.get("away_team")),
        g.get("home_points"),
        g.get("away_points"),
        g.get("neutral_site"),
    )


def map_play(p: dict, season: int, week: int | None, team_ids: dict[str, int]) -> tuple:
    return (
        str(p["id"]),
        p.get("game_id"),
        str(p["drive_id"]) if p.get("drive_id") is not None else None,
        season,
        week,
        team_ids.get(p.get("offense")),
        team_ids.get(p.get("defense")),
        p.get("period"),
        clock_seconds(p),
        p.get("down"),
        p.get("distance"),
        p.get("yardline"),
        p.get("yards_to_goal"),
        p.get("yards_gained"),
        p.get("play_type"),
        p.get("play_text"),
        p.get("offense_score"),
        p.get("defense_score"),
        p.get("ppa"),
        p.get("scoring"),
        p.get("drive_number"),
        p.get("play_number"),
    )


def ingest(team: str, years: list[int], dry_run: bool) -> None:
    client = CFBDClient()

    for year in years:
        print(f"=== {team} {year} ===")
        fbs = client.fbs_teams(year)
        games = client.games_for_team(team, year)
        plays = client.plays_for_team(team, year)

        # game id -> week lets each play carry its week; plays payload has no week
        game_week = {g["id"]: g.get("week") for g in games}

        # every school referenced anywhere gets a teams row (FCS opponents
        # arrive name-only; FBS rows carry conference/classification/cfbd_id)
        fbs_rows = [
            {
                "school": t["school"],
                "conference": t.get("conference"),
                "classification": t.get("classification") or "fbs",
                "cfbd_id": t.get("id"),
            }
            for t in fbs
        ]
        fbs_schools = {t["school"] for t in fbs}
        referenced = (
            {g.get("home_team") for g in games}
            | {g.get("away_team") for g in games}
            | {p.get("offense") for p in plays}
            | {p.get("defense") for p in plays}
        ) - {None}
        extra_rows = [{"school": s} for s in sorted(referenced - fbs_schools)]

        print(
            f"fetched: {len(games)} games, {len(plays)} plays, "
            f"{len(fbs_rows)} FBS teams, {len(extra_rows)} non-FBS schools"
        )

        if dry_run:
            sample = plays[len(plays) // 2] if plays else {}
            print("dry run — sample mapped play:")
            print(map_play(sample, year, game_week.get(sample.get("game_id")), {}))
            continue

        from db import connect, insert_plays, upsert_games, upsert_teams

        conn = connect()
        try:
            with conn, conn.cursor() as cur:
                team_ids = upsert_teams(cur, fbs_rows + extra_rows)

                game_rows = [map_game(g, team_ids) for g in games]
                # stub games for any play whose game we didn't fetch (FK safety)
                known = {g["id"] for g in games}
                stubs = sorted(
                    {p["game_id"] for p in plays if p.get("game_id") is not None}
                    - known
                )
                game_rows += [
                    (gid, year, None, None, None, None, None, None, None, None)
                    for gid in stubs
                ]
                if stubs:
                    print(f"note: {len(stubs)} stub game rows (plays without game data)")
                upsert_games(cur, game_rows)

                play_rows = [
                    map_play(p, year, game_week.get(p.get("game_id")), team_ids)
                    for p in plays
                ]
                insert_plays(cur, play_rows)

                cur.execute(
                    """
                    select count(*) from sideline.plays
                    where season = %s
                      and (offense_team_id = %s or defense_team_id = %s)
                    """,
                    (year, team_ids.get(team), team_ids.get(team)),
                )
                total = cur.fetchone()[0]
            print(f"db: {len(game_rows)} games upserted, {len(play_rows)} plays sent, "
                  f"{total} plays now in sideline.plays for {team} {year}")
        finally:
            conn.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("team", help="CFBD school name, e.g. BYU or 'Texas Tech'")
    ap.add_argument("years", nargs="+", type=int)
    ap.add_argument("--dry-run", action="store_true", help="fetch and map, skip DB")
    args = ap.parse_args()

    if not args.dry_run:
        # fail fast on missing DB URL before burning API calls
        from db import connect

        connect().close()

    ingest(args.team, args.years, args.dry_run)


if __name__ == "__main__":
    main()
