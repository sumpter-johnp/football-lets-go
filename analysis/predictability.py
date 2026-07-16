"""Predictability scoring: how far an offense's situational mixing sits from
league-average mixing, per bucket and summarized.

High deviation = exploitable IF stable — the brief must pair every
predictability claim with sample size and (where multi-season data exists)
stability. Also honest: the "league" baseline is computed from whatever is in
sideline.plays, which today is ~80 team-seasons' worth of plays biased toward
games involving BYU/Arizona/TCU. The baseline JSON carries this caveat; it
firms up as the ingest queue lands.
"""

from __future__ import annotations

from playtypes import dist_class, is_neutral, is_pass, is_scrimmage

MIN_BUCKET_N = 20  # below this, a bucket contributes to nothing


def league_baseline(all_plays: list[dict]) -> dict:
    """League-average pass rate per down(1-3) x distance-class bucket,
    situation-neutral, across every offense in the DB."""
    buckets: dict[str, list] = {}
    for p in all_plays:
        if not is_neutral(p) or not is_scrimmage(p) or p.get("down") not in (1, 2, 3):
            continue
        dc = dist_class(p.get("distance"))
        if dc is None:
            continue
        buckets.setdefault(f"{p['down']}:{dc}", []).append(p)
    return {
        k: {"pass_rate": sum(is_pass(p) for p in v) / len(v), "n": len(v)}
        for k, v in sorted(buckets.items())
    }


def score(dd_buckets: dict, baseline: dict) -> dict:
    """Per-bucket deviation from league mixing + an n-weighted summary index.

    dd_buckets: tendencies.down_distance_buckets output ({bucket: {value, n}}).
    Positive deviation = passes more than league in that spot.
    """
    per_bucket = {}
    weighted, total_n = 0.0, 0
    for key, b in dd_buckets.items():
        base = baseline.get(key)
        if (
            b["value"] is None or base is None
            or b["n"] < MIN_BUCKET_N or base["n"] < MIN_BUCKET_N
        ):
            continue
        dev = b["value"] - base["pass_rate"]
        per_bucket[key] = {
            "pass_rate": b["value"],
            "league": base["pass_rate"],
            "deviation": dev,
            "n": b["n"],
        }
        weighted += abs(dev) * b["n"]
        total_n += b["n"]
    extremes = sorted(per_bucket, key=lambda k: -abs(per_bucket[k]["deviation"]))
    return {
        "index": (weighted / total_n) if total_n else None,  # mean |deviation|, n-weighted
        "n": total_n,
        "per_bucket": per_bucket,
        "most_predictable": extremes[:3],
    }
