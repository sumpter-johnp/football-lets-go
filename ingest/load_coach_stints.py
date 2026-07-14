"""Load Wikipedia-scraped staff data into sideline.{coaches,coach_stints}.

Input: the CSV produced by sideline-phase0/src/wiki_staff.py
(team,year,head_coach,offensive_coordinator,defensive_coordinator,source).

Consecutive years for the same (coach, team, role) collapse into one stint.
play_caller stays NULL — Wikipedia records title holders, not play-callers;
that flag is only set true/false after checking a school announcement
(the Phase 0 lesson). Multiple names in one field (co-coordinators,
mid-season changes) each get their own stint row.

Usage:
    python3 ingest/load_coach_stints.py data/stints_raw.csv
    python3 ingest/load_coach_stints.py data/stints_raw.csv --dry-run
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict

# Wikipedia team name -> CFBD school name (sideline.teams.school)
WIKI_TO_CFBD = {
    "BYU Cougars": "BYU",
    "Arizona Wildcats": "Arizona",
    "TCU Horned Frogs": "TCU",
    "Iowa State Cyclones": "Iowa State",
    "Notre Dame Fighting Irish": "Notre Dame",
    "UCF Knights": "UCF",
    "Arizona State Sun Devils": "Arizona State",
    "Utah Utes": "Utah",
    "Baylor Bears": "Baylor",
    "Kansas Jayhawks": "Kansas",
    "Cincinnati Bearcats": "Cincinnati",
    "Colorado State Rams": "Colorado State",
}

ROLE_COLUMNS = [
    ("head_coach", "HC", None),
    ("offensive_coordinator", "OC", "offense"),
    ("defensive_coordinator", "DC", "defense"),
]


def _split_outside_parens(field: str) -> list[str]:
    """Split on ';' only at paren depth 0 — 'A (interim; wk 1-7); B' -> ['A (interim; wk 1-7)', ' B']"""
    parts, depth, start = [], 0, 0
    for i, ch in enumerate(field):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            parts.append(field[start:i])
            start = i + 1
    parts.append(field[start:])
    return parts


def split_names(field: str) -> list[tuple[str, str | None]]:
    """'Seth Doege; M. Adkins (interim)' -> [('Seth Doege', None), ('M. Adkins', 'interim')]"""
    out = []
    for raw in _split_outside_parens(field):
        raw = raw.strip()
        if not raw:
            continue
        m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", raw)
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
        else:
            out.append((raw, None))
    return out


def build_stints(rows: list[dict]) -> list[dict]:
    """(coach, team, role) year sets -> stints with consecutive years collapsed."""
    years = defaultdict(set)   # (coach, school, role, unit) -> {years}
    meta = {}                  # same key + year -> (source, note)
    for r in rows:
        school = WIKI_TO_CFBD.get(r["team"])
        if school is None:
            continue
        year = int(r["year"])
        for col, role, unit in ROLE_COLUMNS:
            for name, note in split_names(r.get(col) or ""):
                key = (name, school, role, unit)
                years[key].add(year)
                meta[key + (year,)] = (r.get("source"), note)

    stints = []
    for (name, school, role, unit), ys in sorted(years.items()):
        run = []
        for y in sorted(ys) + [None]:
            if run and (y is None or y != run[-1] + 1):
                start, end = run[0], run[-1]
                source, note = meta[(name, school, role, unit, end)]
                stints.append({
                    "coach": name, "school": school, "role": role, "unit": unit,
                    "start_year": start, "end_year": end,
                    "source": source,
                    "notes": note or None,
                })
                run = []
            if y is not None:
                run.append(y)
    return stints


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv_path")
    ap.add_argument("--dry-run", action="store_true", help="print stints, skip DB")
    args = ap.parse_args()

    with open(args.csv_path) as f:
        rows = list(csv.DictReader(f))
    stints = build_stints(rows)
    print(f"{len(rows)} team-year rows -> {len(stints)} stints, "
          f"{len({s['coach'] for s in stints})} coaches")

    if args.dry_run:
        for s in stints:
            span = (f"{s['start_year']}" if s["start_year"] == s["end_year"]
                    else f"{s['start_year']}-{s['end_year']}")
            note = f"  [{s['notes']}]" if s["notes"] else ""
            print(f"  {s['school']:15} {s['role']:3} {span:9} {s['coach']}{note}")
        return

    from db import connect
    from psycopg2.extras import execute_values

    conn = connect()
    try:
        with conn, conn.cursor() as cur:
            execute_values(
                cur,
                "insert into sideline.coaches (name) values %s on conflict (name) do nothing",
                [(c,) for c in sorted({s["coach"] for s in stints})],
            )
            cur.execute("select name, id from sideline.coaches")
            coach_ids = dict(cur.fetchall())
            cur.execute("select school, id from sideline.teams")
            team_ids = dict(cur.fetchall())

            missing = {s["school"] for s in stints} - set(team_ids)
            if missing:
                raise RuntimeError(f"schools not in sideline.teams: {missing}")

            execute_values(
                cur,
                """
                insert into sideline.coach_stints
                  (coach_id, team_id, role, unit, start_year, end_year, source, notes)
                values %s
                on conflict (coach_id, team_id, role, start_year) do update
                  set end_year = excluded.end_year,
                      source   = excluded.source,
                      notes    = excluded.notes
                """,
                [
                    (coach_ids[s["coach"]], team_ids[s["school"]], s["role"], s["unit"],
                     s["start_year"], s["end_year"], s["source"], s["notes"])
                    for s in stints
                ],
            )
            cur.execute("select count(*) from sideline.coach_stints")
            total = cur.fetchone()[0]
        print(f"db: {total} rows now in sideline.coach_stints")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
