"""Sticky-metric computation from CFBD play-by-play.

Four metrics, chosen because they are plausibly coach-driven rather than
personnel-hostage (per the project outline):

  1. neutral_pass_rate   — pass share on 1st/2nd down, situation-neutral
  2. sec_per_play        — median seconds between consecutive snaps in a drive
  3. fourth_down_go_rate — go rate on 4th-and-<=3 in the decision zone
  4. explosive_pass_rate — dropbacks gaining 20+ yds / dropbacks (SHOT-RATE PROXY;
                           outcome-contaminated, interpret with care)

Situation-neutral filter applied everywhere:
  * one-score game (|score diff| <= 8)
  * quarters 1-3
  * excludes final 2:00 of Q2 (two-minute drill)

Known limitations, stated so the verdict stays honest:
  * QB scrambles are logged as rushes in PBP -> pass rate slightly understated
    for scramble-heavy QBs. Affects (a) and (b) equally, so the comparison holds.
  * Explosive pass rate depends on completions, i.e. on receivers -> weakest of
    the four as a pure "coach dial."
"""

from __future__ import annotations

from statistics import median

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

MIN_SAMPLES = {
    "neutral_pass_rate": 150,
    "sec_per_play": 150,
    "fourth_down_go_rate": 12,
    "explosive_pass_rate": 80,
}


def _clock_seconds(play: dict) -> int | None:
    clock = play.get("clock") or {}
    m, s = clock.get("minutes"), clock.get("seconds")
    if m is None or s is None:
        return None
    return m * 60 + s


def _is_neutral(play: dict) -> bool:
    period = play.get("period")
    if period is None or period > 3:
        return False
    off, deff = play.get("offense_score"), play.get("defense_score")
    if off is None or deff is None:
        return False
    if abs(off - deff) > 8:
        return False
    secs = _clock_seconds(play)
    if period == 2 and secs is not None and secs <= 120:
        return False  # two-minute drill
    return True


def compute_metrics(plays: list[dict]) -> dict:
    """Returns {metric: {"value": float|None, "n": int}} for one set of offensive plays."""
    neutral = [p for p in plays if _is_neutral(p)]

    # 1. Early-down neutral pass rate
    early = [
        p for p in neutral
        if p.get("down") in (1, 2)
        and p.get("play_type") in PASS_TYPES | RUSH_TYPES
    ]
    n_early = len(early)
    pass_rate = (
        sum(p["play_type"] in PASS_TYPES for p in early) / n_early
        if n_early else None
    )

    # 2. Pace: clock delta between consecutive plays in the same drive/period
    deltas = []
    by_drive: dict = {}
    for p in neutral:
        key = (p.get("drive_id"), p.get("period"))
        if key[0] is not None:
            by_drive.setdefault(key, []).append(p)
    for drive_plays in by_drive.values():
        drive_plays.sort(key=lambda p: -(_clock_seconds(p) or 0))  # clock counts down
        for a, b in zip(drive_plays, drive_plays[1:]):
            ca, cb = _clock_seconds(a), _clock_seconds(b)
            if ca is None or cb is None:
                continue
            d = ca - cb
            if 5 <= d <= 60:  # drop timeouts, reviews, clock glitches
                deltas.append(d)
    pace = median(deltas) if deltas else None

    # 3. 4th-down go rate: 4th-and-<=3, decision zone (not pinned, not chip-shot FG range... 
    #    zone = 34-70 yards to goal excluded low end so FG isn't automatic)
    fourth = [
        p for p in neutral
        if p.get("down") == 4
        and (p.get("distance") or 99) <= 3
        and p.get("yards_to_goal") is not None
        and 34 <= p["yards_to_goal"] <= 70
        and p.get("play_type") in PASS_TYPES | RUSH_TYPES | PUNT_TYPES | FG_TYPES
    ]
    n_fourth = len(fourth)
    go_rate = (
        sum(p["play_type"] in PASS_TYPES | RUSH_TYPES for p in fourth) / n_fourth
        if n_fourth else None
    )

    # 4. Explosive pass rate (shot proxy)
    dropbacks = [p for p in neutral if p.get("play_type") in PASS_TYPES]
    n_db = len(dropbacks)
    explosive = (
        sum((p.get("yards_gained") or 0) >= 20 for p in dropbacks) / n_db
        if n_db else None
    )

    return {
        "neutral_pass_rate": {"value": pass_rate, "n": n_early},
        "sec_per_play": {"value": pace, "n": len(deltas)},
        "fourth_down_go_rate": {"value": go_rate, "n": n_fourth},
        "explosive_pass_rate": {"value": explosive, "n": n_db},
    }


def pool_metrics(metric_sets: list[dict]) -> dict:
    """Sample-size-weighted pool of several seasons' metrics into one profile."""
    pooled = {}
    for name in MIN_SAMPLES:
        pairs = [
            (m[name]["value"], m[name]["n"])
            for m in metric_sets
            if m[name]["value"] is not None and m[name]["n"] > 0
        ]
        total_n = sum(n for _, n in pairs)
        pooled[name] = {
            "value": (sum(v * n for v, n in pairs) / total_n) if total_n else None,
            "n": total_n,
        }
    return pooled
