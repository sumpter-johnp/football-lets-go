"""Play classification + the situation-neutral filter, shared by the Phase 2
tendency engine.

Ported from sideline-phase0/src/metrics.py so Phase 2 uses the exact
definitions Phase 0 validated — the only change is the input shape: these
operate on sideline.plays DB rows (flat columns, clock_seconds precomputed)
instead of raw CFBD payloads.
"""

from __future__ import annotations

PASS_TYPES = {
    "Pass Reception", "Pass Incompletion", "Passing Touchdown", "Sack",
    "Pass Interception Return", "Interception", "Interception Return Touchdown",
    "Pass Interception", "Pass Completion", "Pass",
}
RUSH_TYPES = {"Rush", "Rushing Touchdown"}
PUNT_TYPES = {"Punt", "Blocked Punt", "Punt Return Touchdown", "Blocked Punt Touchdown"}
FG_TYPES = {
    "Field Goal Good", "Field Goal Missed", "Blocked Field Goal",
    "Missed Field Goal Return", "Missed Field Goal Return Touchdown",
    "Blocked Field Goal Touchdown",
}
SCRIMMAGE_TYPES = PASS_TYPES | RUSH_TYPES

TD_TYPES = {"Passing Touchdown", "Rushing Touchdown"}


def is_pass(p: dict) -> bool:
    return p["play_type"] in PASS_TYPES


def is_scrimmage(p: dict) -> bool:
    return p["play_type"] in SCRIMMAGE_TYPES


def is_neutral(p: dict) -> bool:
    """One-score game, quarters 1-3, excluding the Q2 two-minute drill —
    strips scoreboard-driven behavior (a team down 21 passes because of the
    score, not the coach)."""
    period = p.get("period")
    if period is None or period > 3:
        return False
    off, deff = p.get("offense_score"), p.get("defense_score")
    if off is None or deff is None:
        return False
    if abs(off - deff) > 8:
        return False
    secs = p.get("clock_seconds")
    if period == 2 and secs is not None and secs <= 120:
        return False
    return True


def score_state(p: dict) -> str | None:
    off, deff = p.get("offense_score"), p.get("defense_score")
    if off is None or deff is None:
        return None
    diff = off - deff
    if diff > 8:
        return "leading"
    if diff < -8:
        return "trailing"
    return "neutral"


def dist_class(distance: int | None) -> str | None:
    if distance is None:
        return None
    if distance <= 3:
        return "short"
    if distance <= 6:
        return "medium"
    if distance <= 10:
        return "long"
    return "xlong"


def field_zone(yards_to_goal: int | None) -> str | None:
    if yards_to_goal is None:
        return None
    if yards_to_goal >= 80:
        return "backed_up"
    if yards_to_goal >= 60:
        return "own_side"
    if yards_to_goal >= 40:
        return "midfield"
    if yards_to_goal >= 21:
        return "fringe"
    return "red_zone"


def snap_order(p: dict) -> tuple:
    """Sort key for true snap order within a game: drive_number is per-game,
    play_number is per-drive."""
    return (p.get("drive_number") or 0, p.get("play_number") or 0)
