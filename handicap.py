"""WHS handicap calculator — replicates the official USGA / R&A formula.

This is what GHIN does behind the scenes. We can't auto-pull from GHIN
(no public API), but we can compute the player's "Computed Handicap Index"
from logged rounds using the exact same math.

Formula:
- Differential per round = (Adjusted Gross Score - Course Rating) * 113 / Slope
- Take the player's logged differentials
- Use lowest 8 of last 20 (with adjustments for fewer rounds)
- Average those 8, multiply by 0.96 (the WHS bonus for excellence)
- Cap at 54.0
"""
from typing import Optional


def differential(score: float, course_rating: float, slope: int) -> float:
    """Compute a single round's score differential."""
    if slope <= 0:
        slope = 113
    return ((score - course_rating) * 113.0) / slope


# Number-of-rounds adjustment table (per USGA/R&A WHS)
# (rounds_in_pool, rounds_to_use, adjustment_strokes)
_TABLE = [
    (3,  1, -2.0),
    (4,  1, -1.0),
    (5,  1,  0.0),
    (6,  2, -1.0),
    (7,  2,  0.0),
    (8,  2,  0.0),
    (9,  3,  0.0),
    (10, 3,  0.0),
    (11, 3,  0.0),
    (12, 4,  0.0),
    (13, 4,  0.0),
    (14, 4,  0.0),
    (15, 5,  0.0),
    (16, 5,  0.0),
    (17, 6,  0.0),
    (18, 6,  0.0),
    (19, 7,  0.0),
    (20, 8,  0.0),
]


def compute_index(rounds: list, default_rating: float = 72.0, default_slope: int = 113) -> Optional[dict]:
    """
    Given a list of round dicts, return the WHS-style handicap index.

    Each round dict should have:
      score (required)
      course_rating (optional, defaults to 72.0)
      slope (optional, defaults to 113)
    """
    if not rounds:
        return None

    # Use the most recent 20 rounds
    pool = list(rounds)[-20:]
    diffs = []
    for r in pool:
        try:
            score = float(r.get("score", 0))
            if score <= 0:
                continue
            cr = float(r.get("course_rating", default_rating))
            sl = int(r.get("slope", default_slope))
            d = differential(score, cr, sl)
            diffs.append(d)
        except Exception:
            continue

    n = len(diffs)
    if n < 3:
        return {
            "index": None,
            "rounds_used": n,
            "rounds_needed": 3 - n,
            "message": f"Need at least 3 rounds to compute. ({n}/3)",
        }

    # Look up adjustment from table
    use_count = 1
    adj = 0.0
    for rows, take, a in _TABLE:
        if n <= rows:
            use_count = take
            adj = a
            break
    else:
        use_count = 8
        adj = 0.0

    sorted_diffs = sorted(diffs)
    used = sorted_diffs[:use_count]
    avg = sum(used) / use_count
    index = round((avg * 0.96) + adj, 1)
    index = max(-10.0, min(54.0, index))

    return {
        "index": index,
        "rounds_used": use_count,
        "rounds_in_pool": n,
        "differentials": [round(d, 1) for d in sorted(diffs)],
        "differentials_used": [round(d, 1) for d in used],
        "adjustment": adj,
        "average_used": round(avg, 2),
        "raw_index_pre_cap": round(avg * 0.96, 2),
    }


def update_profile_handicap(d: dict) -> Optional[float]:
    """Compute and write back the handicap on the profile dict.
    Returns the new index, or None if not enough data."""
    rounds = d.get("rounds") or []
    result = compute_index(rounds)
    if result and result.get("index") is not None:
        d.setdefault("profile", {})["computed_handicap"] = result["index"]
        d["profile"]["handicap_breakdown"] = result
        return result["index"]
    return None
