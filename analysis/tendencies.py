"""Phase 2 tendency engine: one offensive profile from one set of plays.

The profile covers what the project outline scopes for Phase 2, offense only
(the DNA layer claims nothing on defense yet):

  * the four Phase 0 sticky dials (definitions identical to Phase 0)
  * run/pass mix by down x distance class and by field zone (neutral filter)
  * pace by game state
  * red-zone / short-yardage / opening-script identity
  * sample size (n) attached to every number — no n, no claim

Explicitly NOT computed: 2-point behavior (a season yields <10 decisions —
too thin to claim anything) and any defensive metric.

Every rate carries {"value", "n"}; buckets add mean PPA (CFBD's EPA-like
metric) for the Phase 3 matchup layer. Values are None when n == 0.
"""

from __future__ import annotations

from statistics import median

from playtypes import (
    FG_TYPES,
    PASS_TYPES,
    PUNT_TYPES,
    RUSH_TYPES,
    SCRIMMAGE_TYPES,
    TD_TYPES,
    dist_class,
    field_zone,
    is_neutral,
    is_pass,
    is_scrimmage,
    score_state,
    snap_order,
)

MIN_SAMPLES = {
    "neutral_pass_rate": 150,
    "sec_per_play": 150,
    "fourth_down_go_rate": 12,
    "explosive_pass_rate": 80,
}


def _rate(plays: list[dict], pred) -> dict:
    n = len(plays)
    ppa = [float(p["ppa"]) for p in plays if p.get("ppa") is not None]
    return {
        "value": (sum(pred(p) for p in plays) / n) if n else None,
        "n": n,
        "ppa_mean": (sum(ppa) / len(ppa)) if ppa else None,
    }


def _pace(plays: list[dict]) -> dict:
    """Median clock delta between consecutive snaps of the same drive/period.
    5-60s window drops timeouts, reviews, and clock glitches."""
    deltas = []
    by_drive: dict = {}
    for p in plays:
        key = (p.get("game_id"), p.get("drive_id"), p.get("period"))
        if key[1] is not None:
            by_drive.setdefault(key, []).append(p)
    for drive_plays in by_drive.values():
        drive_plays.sort(key=lambda p: -(p.get("clock_seconds") or 0))
        for a, b in zip(drive_plays, drive_plays[1:]):
            ca, cb = a.get("clock_seconds"), b.get("clock_seconds")
            if ca is None or cb is None:
                continue
            d = ca - cb
            if 5 <= d <= 60:
                deltas.append(d)
    return {"value": median(deltas) if deltas else None, "n": len(deltas)}


def sticky_metrics(plays: list[dict]) -> dict:
    """The four Phase 0 dials, definitions unchanged."""
    neutral = [p for p in plays if is_neutral(p)]

    early = [p for p in neutral if p.get("down") in (1, 2) and is_scrimmage(p)]
    pass_rate = (sum(is_pass(p) for p in early) / len(early)) if early else None

    pace = _pace(neutral)

    fourth = [
        p for p in neutral
        if p.get("down") == 4
        and (p.get("distance") or 99) <= 3
        and p.get("yards_to_goal") is not None
        and 34 <= p["yards_to_goal"] <= 70
        and p["play_type"] in SCRIMMAGE_TYPES | PUNT_TYPES | FG_TYPES
    ]
    go_rate = (
        sum(p["play_type"] in SCRIMMAGE_TYPES for p in fourth) / len(fourth)
        if fourth else None
    )

    dropbacks = [p for p in neutral if is_pass(p)]
    explosive = (
        sum((p.get("yards_gained") or 0) >= 20 for p in dropbacks) / len(dropbacks)
        if dropbacks else None
    )

    return {
        "neutral_pass_rate": {"value": pass_rate, "n": len(early)},
        "sec_per_play": pace,
        "fourth_down_go_rate": {"value": go_rate, "n": len(fourth)},
        "explosive_pass_rate": {"value": explosive, "n": len(dropbacks)},
    }


def pool_sticky(metric_sets: list[dict]) -> dict:
    """Sample-size-weighted pool of several seasons' sticky dials (Phase 0's
    pool_metrics, unchanged)."""
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


def down_distance_buckets(plays: list[dict]) -> dict:
    """Pass rate per down (1-3) x distance class, situation-neutral. 4th down
    is its own sticky dial. Keyed 'down:distclass', e.g. '3:medium'."""
    buckets: dict[str, list] = {}
    for p in plays:
        if not is_neutral(p) or not is_scrimmage(p):
            continue
        if p.get("down") not in (1, 2, 3):
            continue
        dc = dist_class(p.get("distance"))
        if dc is None:
            continue
        buckets.setdefault(f"{p['down']}:{dc}", []).append(p)
    return {k: _rate(v, is_pass) for k, v in sorted(buckets.items())}


def field_zone_buckets(plays: list[dict]) -> dict:
    """Early-down pass rate per field zone, situation-neutral."""
    buckets: dict[str, list] = {}
    for p in plays:
        if not is_neutral(p) or not is_scrimmage(p) or p.get("down") not in (1, 2):
            continue
        fz = field_zone(p.get("yards_to_goal"))
        if fz is None:
            continue
        buckets.setdefault(fz, []).append(p)
    return {k: _rate(v, is_pass) for k, v in sorted(buckets.items())}


def pace_by_game_state(plays: list[dict]) -> dict:
    """Median seconds per snap split by score state, quarters 1-4. Unlike the
    sticky pace dial this keeps non-neutral situations — that's the point."""
    groups: dict[str, list] = {"neutral": [], "leading": [], "trailing": []}
    for p in plays:
        s = score_state(p)
        if s:
            groups[s].append(p)
    return {k: _pace(v) for k, v in groups.items()}


def red_zone_identity(plays: list[dict]) -> dict:
    """Pass rate + TD-per-trip inside the 20. Personnel-hostage caveat: TD
    share measures finishing talent as much as the caller; report, don't
    over-claim."""
    rz = [p for p in plays if (p.get("yards_to_goal") or 99) <= 20 and is_scrimmage(p)]
    trips: dict = {}
    td_trips: set = set()
    for p in rz:
        key = (p.get("game_id"), p.get("drive_id"))
        trips[key] = True
        if p.get("scoring") and p["play_type"] in TD_TYPES:
            td_trips.add(key)
    out = _rate(rz, is_pass)
    out["trips"] = len(trips)
    out["td_per_trip"] = (len(td_trips) / len(trips)) if trips else None
    return out


def short_yardage_identity(plays: list[dict]) -> dict:
    """3rd/4th-and-<=2, situation-neutral: rush share + conversion rate."""
    sy = [
        p for p in plays
        if is_neutral(p) and is_scrimmage(p)
        and p.get("down") in (3, 4) and (p.get("distance") or 99) <= 2
    ]
    out = _rate(sy, lambda p: not is_pass(p))
    out = {"rush_rate": out["value"], "n": out["n"], "ppa_mean": out["ppa_mean"]}
    converted = [
        p for p in sy
        if p.get("yards_gained") is not None and p.get("distance") is not None
        and p["yards_gained"] >= p["distance"]
    ]
    out["conversion_rate"] = (len(converted) / len(sy)) if sy else None
    return out


def opening_script(plays: list[dict], overall_neutral_pass_rate: float | None) -> dict:
    """First 15 scrimmage plays of each game (snap order): early-down pass
    rate vs the overall neutral dial — does the script lean differently?"""
    by_game: dict = {}
    for p in plays:
        if p.get("game_id") is not None:
            by_game.setdefault(p["game_id"], []).append(p)
    script_plays = []
    for game_plays in by_game.values():
        game_plays.sort(key=snap_order)
        script_plays += [p for p in game_plays if is_scrimmage(p)][:15]
    early = [p for p in script_plays if p.get("down") in (1, 2)]
    rate = (sum(is_pass(p) for p in early) / len(early)) if early else None
    return {
        "pass_rate_early_downs": rate,
        "n": len(early),
        "delta_vs_neutral": (
            rate - overall_neutral_pass_rate
            if rate is not None and overall_neutral_pass_rate is not None else None
        ),
    }


def profile(plays: list[dict]) -> dict:
    """Full offensive tendency profile for one play set (a team-season, or a
    coach's attributed film)."""
    sticky = sticky_metrics(plays)
    return {
        "n_plays": len(plays),
        "n_games": len({p.get("game_id") for p in plays if p.get("game_id")}),
        "sticky": sticky,
        "run_pass_by_down_distance": down_distance_buckets(plays),
        "run_pass_by_field_zone": field_zone_buckets(plays),
        "pace_by_game_state": pace_by_game_state(plays),
        "red_zone": red_zone_identity(plays),
        "short_yardage": short_yardage_identity(plays),
        "opening_script": opening_script(plays, sticky["neutral_pass_rate"]["value"]),
    }
