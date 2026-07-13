"""Seed the movers list with HEAD COACH movers from the CFBD /coaches endpoint.

Important: CFBD's coaches endpoint only covers head coaches — there is no
coordinator data in the API. This script finds HCs at a different FBS school in
2025 than 2024. Many HC movers are their own play-callers, which makes them
valid test subjects; the printout is a candidate list to verify, not a final
answer. Coordinator movers get added to movers_2025.csv by hand from school
announcements.

Usage:
    export CFBD_API_KEY=...
    python src/find_hc_movers.py
"""

from cfbd import CFBDClient


def main():
    client = CFBDClient()
    fbs_2025 = client.fbs_teams(2025)

    def hc_school(year: int) -> dict[str, str]:
        out = {}
        for c in client.coaches(year):
            name = f"{c.get('first_name', c.get('firstName', ''))} {c.get('last_name', c.get('lastName', ''))}".strip()
            for s in c.get("seasons", []):
                if s.get("year") == year and s.get("games", 0) > 0:
                    out[name] = s.get("school")
        return out

    hc_2024, hc_2025 = hc_school(2024), hc_school(2025)

    movers = [
        (name, hc_2024[name], school)
        for name, school in hc_2025.items()
        if name in hc_2024 and hc_2024[name] != school and school in fbs_2025
    ]

    print(f"Head coaches at a different school in 2025 ({len(movers)} found):\n")
    print("coach,unit,new_team,prior_stops,notes")
    for name, old, new in sorted(movers):
        # prior_stops needs the actual play-calling years — verify and edit
        print(f'{name},offense,{new},"{old}:2022-2024",VERIFY: is this HC the play-caller?')
    print(
        "\nPaste verified rows into movers_2025.csv. Only keep coaches who call "
        "their own offensive plays, and fix prior_stops to their real play-calling years."
    )


if __name__ == "__main__":
    main()
