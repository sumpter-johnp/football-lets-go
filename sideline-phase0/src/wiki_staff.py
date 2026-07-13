"""Pull OC/DC names from Wikipedia team-season pages via the MediaWiki API.

Every FBS season has a page like "2024 Arizona Wildcats football team" whose
infobox carries |off_coach= and |def_coach= fields. This script fetches the
wikitext and parses those fields — the seed of Phase 1's coach_stints table,
and a cross-check for movers_2025.csv.

Run locally (Wikipedia isn't reachable from every sandbox):
    python src/wiki_staff.py "Arizona Wildcats" 2022 2025
    python src/wiki_staff.py --teams-file big12.txt 2021 2025 > stints_raw.csv

Caveat that never goes away: Wikipedia records the TITLE holder, not the
play-caller. Treat output as candidates to verify, not truth.
"""

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "sideline-phase0/0.1 (personal research project)"}


def fetch_wikitext(page_title: str) -> str | None:
    params = urllib.parse.urlencode({
        "action": "parse", "page": page_title, "prop": "wikitext",
        "format": "json", "formatversion": "2", "redirects": "1",
    })
    req = urllib.request.Request(f"{API}?{params}", headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        return data["parse"]["wikitext"]
    except Exception:
        return None


def _clean_names(raw: str) -> list[str]:
    """'[[Seth Doege]]<br>[[Matt Adkins|M. Adkins]] (interim)' -> ['Seth Doege', 'M. Adkins (interim)']"""
    raw = raw.replace("<br />", "<br>").replace("<br/>", "<br>")
    parts = re.split(r"<br>|\n\*|&", raw)
    names = []
    for part in parts:
        part = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", part)  # unpipe links
        part = re.sub(r"\{\{[^}]*\}\}|<[^>]+>|''+", "", part).strip(" ,;\n\t")
        if part and not re.fullmatch(r"\([^)]*\)", part):  # drop '(1st season)' etc.
            names.append(part)
    return names


def parse_coordinators(wikitext: str) -> dict:
    """Extract off_coach / def_coach / head_coach from a season infobox."""
    out = {}
    for field, key in [("off_coach", "oc"), ("def_coach", "dc"), ("head_coach", "hc")]:
        m = re.search(
            rf"^\s*\|\s*{field}\s*=\s*(.+?)(?=^\s*\|[a-z_ ]+=|^\}}\}})",
            wikitext, re.MULTILINE | re.DOTALL | re.IGNORECASE,
        )
        out[key] = _clean_names(m.group(1)) if m else []
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("team", nargs="?", help='Full team name, e.g. "Arizona Wildcats"')
    ap.add_argument("start_year", type=int)
    ap.add_argument("end_year", type=int)
    ap.add_argument("--teams-file", help="File with one team name per line (overrides positional team)")
    args = ap.parse_args()

    teams = ([t.strip() for t in open(args.teams_file) if t.strip()]
             if args.teams_file else [args.team])
    if not teams or teams == [None]:
        ap.error("Provide a team name or --teams-file")

    print("team,year,head_coach,offensive_coordinator,defensive_coordinator,source")
    for team in teams:
        for year in range(args.start_year, args.end_year + 1):
            title = f"{year} {team} football team"
            wt = fetch_wikitext(title)
            if wt is None:
                print(f'"{team}",{year},,,,PAGE_NOT_FOUND', file=sys.stderr)
                continue
            c = parse_coordinators(wt)
            url = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
            print(f'"{team}",{year},"{"; ".join(c["hc"])}","{"; ".join(c["oc"])}","{"; ".join(c["dc"])}",{url}')
            time.sleep(0.5)  # be polite


if __name__ == "__main__":
    main()
