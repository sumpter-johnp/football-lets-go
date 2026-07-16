#!/bin/zsh
# Ingest queue from docs/play_caller_checklist.md — run on/after Aug 1 when
# the CFBD monthly quota (1,000 calls) resets. ~670 calls total; each line is
# idempotent and resumable (cache-first), so re-running after a failure is safe.
set -e
cd "$(dirname "$0")/.."

python3 ingest/ingest_team_season.py Marshall 2024
python3 ingest/ingest_team_season.py UConn 2024 2025
python3 ingest/ingest_team_season.py "Utah State" 2025
python3 ingest/ingest_team_season.py "Oregon State" 2016 2017
python3 ingest/ingest_team_season.py "Penn State" 2024 2025
python3 ingest/ingest_team_season.py Kansas 2021 2022 2023 2025
# CFBD spells it with the accented é — verbatim per the checklist
python3 ingest/ingest_team_season.py "San José State" 2018 2019 2020 2021 2022 2023

cat <<'EOF'

DONE — one manual follow-up before Phase 2 touches Kansas 2023:
The 2023 Guaranteed Rate Bowl was called by interim Jim Zebrowski, not
Kotelnicki. Insert a sideline.game_play_callers override for that game
(offense -> Jim Zebrowski) or play_attribution will silently credit
Kotelnicki via the season-stint fallback. See migration 0002 header.
EOF
