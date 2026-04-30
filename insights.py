"""Stroke-Saver Engine — analyzes Joel's data and ranks fixes by stroke impact."""
import pandas as pd
import numpy as np
from cloud_storage import load_data

# PGA Tour benchmarks (avg amateur 15 hcp comparisons)
TOUR_BENCHMARKS = {
    "D":  {"carry": 296, "ball": 167, "smash": 1.49},
    "3W": {"carry": 243, "ball": 158, "smash": 1.48},
    "5W": {"carry": 230, "ball": 153, "smash": 1.47},
    "5H": {"carry": 215, "ball": 146, "smash": 1.45},
    "7i": {"carry": 172, "ball": 130, "smash": 1.33},
    "9i": {"carry": 148, "ball": 119, "smash": 1.28},
    "PW": {"carry": 136, "ball": 112, "smash": 1.23},
    "GW": {"carry": 110, "ball": 102, "smash": 1.18},
    "SW": {"carry": 92,  "ball": 92,  "smash": 1.13},
    "LW": {"carry": 70,  "ball": 80,  "smash": 1.05},
}


def stroke_saver_plan() -> list:
    """Returns ranked list of stroke-saving recommendations.

    Each item: {area, strokes_saved, current, target, drill, why}
    """
    data = load_data()
    rounds = data.get("rounds", [])
    plan = []

    if not rounds:
        return plan

    df = pd.DataFrame(rounds)
    for col in ["score", "putts", "gir", "fir", "par"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Use only par-70+ rounds for fair comparison (skip par-3 courses)
    full = df[df.get("par", 70) >= 65].copy()
    if len(full) == 0:
        full = df.copy()

    avg_score = full["score"].mean() if "score" in full else None
    avg_putts = full["putts"].mean() if "putts" in full else None
    avg_gir = full["gir"].mean() if "gir" in full else None
    avg_fir = full["fir"].mean() if "fir" in full else None

    # 1. Putting
    if avg_putts and avg_putts > 30:
        save = round((avg_putts - 30) * 0.8, 1)
        plan.append({
            "area": "Putting",
            "strokes_saved": save,
            "current": f"{avg_putts:.1f} putts/round",
            "target": "30 putts/round",
            "drill": "Lag drill — 3 balls from 30/40/50 ft, twice per practice. Gate drill at 4 ft.",
            "why": f"You average {avg_putts:.1f} putts. Tour avg is 29; bogey golfers cluster at 32+. Each putt saved is a stroke.",
            "icon": "🎯",
            "color": "#4A9EFF",
        })

    # 2. GIR (approach shots)
    if avg_gir is not None and avg_gir < 7:
        # full course = 18 greens
        gap = max(0, 7 - avg_gir)
        save = round(gap * 0.6, 1)
        plan.append({
            "area": "Approach Shots (GIR)",
            "strokes_saved": save,
            "current": f"{avg_gir:.1f} of 18 greens",
            "target": "7 GIR/round",
            "drill": "100-shot wedge ladder — 75/85/95/105 yds, 25 each. Track make %.",
            "why": f"You hit {avg_gir:.1f} GIR/round. Players who break 80 average 7+. More GIR = fewer up-and-downs needed.",
            "icon": "🎯",
            "color": "#00D4AA",
        })

    # 3. Fairways / Driver accuracy
    if avg_fir is not None and avg_fir < 7:
        gap = max(0, 7 - avg_fir)
        save = round(gap * 0.4, 1)
        plan.append({
            "area": "Driver Accuracy",
            "strokes_saved": save,
            "current": f"{avg_fir:.1f} fairways hit",
            "target": "7+ FIR/round",
            "drill": "Headcover under right armpit — 20 half-swings. Gate drill with two tees outside the clubhead.",
            "why": f"You hit {avg_fir:.1f} fairways. Each missed fairway costs ~0.3 strokes on average.",
            "icon": "🏌️",
            "color": "#FFB800",
        })

    # 4. Speed gain → distance
    speed = data.get("speed", [])
    if speed:
        latest = speed[-1].get("driver_speed", 97)
        if latest < 105:
            gap = 105 - latest
            save = round(gap * 0.08, 1)  # ~0.5 stroke per 6 mph gain
            plan.append({
                "area": "Driver Speed",
                "strokes_saved": save,
                "current": f"{latest} mph",
                "target": "105 mph",
                "drill": "TheStack Foundation L1 → Build L2, 3x/week. Overspeed sets with 20g club.",
                "why": f"You're at {latest} mph. Each +1 mph = ~2.5 yds carry. 8 mph more puts you in 270+ range consistently.",
                "icon": "⚡",
                "color": "#FF6B35",
            })

    plan.sort(key=lambda x: x["strokes_saved"], reverse=True)
    return plan


def total_strokes_to_save() -> float:
    return round(sum(p["strokes_saved"] for p in stroke_saver_plan()), 1)


def gap_to_break_80() -> dict:
    """How close are we to breaking 80 consistently?"""
    data = load_data()
    rounds = [r for r in data.get("rounds", []) if r.get("par", 70) >= 65]
    if len(rounds) < 3:
        return {"avg": None, "gap": None, "trend": None, "recent": []}
    df = pd.DataFrame(rounds)
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["score", "date"]).sort_values("date")
    recent5 = df.tail(5)
    avg5 = recent5["score"].mean()
    under_80 = (recent5["score"] < 80).sum()
    return {
        "avg": round(avg5, 1),
        "gap": round(avg5 - 80, 1),
        "under_80_count": int(under_80),
        "of_last": len(recent5),
        "recent": recent5["score"].tolist(),
    }


def miss_pattern() -> dict:
    """Analyze practice shots for left/right miss tendency."""
    data = load_data()
    practice = data.get("practice", [])
    if not practice:
        return {"bias": None, "magnitude": 0, "summary": "Log practice shots to detect miss patterns."}
    df = pd.DataFrame(practice)
    if "side" not in df.columns:
        return {"bias": None, "magnitude": 0, "summary": "Need shot side data."}
    df["side"] = pd.to_numeric(df["side"], errors="coerce")
    df = df.dropna(subset=["side"])
    if len(df) == 0:
        return {"bias": None, "magnitude": 0, "summary": "No side data yet."}
    avg = df["side"].mean()
    if abs(avg) < 1.5:
        return {"bias": "balanced", "magnitude": abs(avg), "summary": "Dispersion is balanced — no strong miss bias detected."}
    if avg > 0:
        return {"bias": "right",
                "magnitude": round(avg, 1),
                "summary": f"Average miss is {avg:.1f} yds RIGHT — likely an out-to-in path or open face. Try the gate drill and check grip strength."}
    return {"bias": "left",
            "magnitude": round(abs(avg), 1),
            "summary": f"Average miss is {abs(avg):.1f} yds LEFT — likely in-to-out with a closed face or release timing. Drill: feet-together half swings."}


def practice_streak() -> int:
    """Count consecutive days with logged practice / speed / round activity."""
    data = load_data()
    dates = set()
    for src in ["practice", "speed", "rounds"]:
        for item in data.get(src, []):
            d = str(item.get("date", ""))[:10]
            if d:
                dates.add(d)
    if not dates:
        return 0
    sorted_dates = sorted(dates, reverse=True)
    from datetime import datetime as _dt, timedelta
    today = _dt.now().date()
    streak = 0
    cursor = today
    sset = set(sorted_dates)
    while cursor.isoformat() in sset or (cursor == today):
        if cursor.isoformat() in sset:
            streak += 1
        elif cursor != today:
            break
        cursor -= timedelta(days=1)
        if streak > 365:
            break
    return streak


def club_vs_tour() -> list:
    """Compare practice carry distances vs tour benchmarks."""
    data = load_data()
    practice = data.get("practice", [])
    if not practice:
        return []
    df = pd.DataFrame(practice)
    if "club" not in df.columns or "carry" not in df.columns:
        return []
    df["carry"] = pd.to_numeric(df["carry"], errors="coerce")
    summary = df.groupby("club")["carry"].mean().round(1).reset_index()
    out = []
    for _, row in summary.iterrows():
        club = row["club"]
        bench = TOUR_BENCHMARKS.get(club, {}).get("carry")
        if bench:
            out.append({
                "club": club,
                "your_carry": row["carry"],
                "tour_carry": bench,
                "gap": round(row["carry"] - bench, 1),
                "pct_of_tour": round(row["carry"] / bench * 100, 0),
            })
    return out
