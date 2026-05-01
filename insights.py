"""Intelligent insights — specific, voice-matched to user examples."""
from cloud_storage import load_data
from datetime import datetime, timedelta
from collections import Counter, defaultdict

# PGA Tour benchmarks (2024 season averages)
TOUR_CARRY = {
    "Driver": 296, "3W": 264, "5H": 235, "5i": 200, "6i": 188, "7i": 176,
    "8i": 164, "9i": 152, "PW": 138, "GW": 124, "SW": 105, "LW": 85,
}
TOUR_BENCH = {
    "putts_per_round": 28.7, "gir_pct": 65, "fairway_pct": 60,
    "scrambling_pct": 60, "score_avg": 71.2,
    "three_putt_pct": 2.8,        # % of holes
    "sand_save_pct": 51,           # % up-and-downs from sand
    "birdies_per_round": 3.6,
    "bogey_avoidance_pct": 86,    # 1 - bogey or worse
    "driver_speed_mph": 116,       # ball speed
    "club_speed_mph": 113,         # tour avg driver club head speed
    "apex_ft": 102,                # tour driver apex
    "strokes_gained_putt": 0.0,
}


def practice_streak():
    d = load_data()
    shots = d.get("practice_shots", []) or []
    if not shots: return 0
    dates = sorted({s.get("date", "")[:10] for s in shots if s.get("date")}, reverse=True)
    today = datetime.now().date()
    streak = 0
    for i, ds in enumerate(dates):
        try:
            dt = datetime.strptime(ds, "%Y-%m-%d").date()
        except:
            continue
        if (today - dt).days == i:
            streak += 1
        else:
            break
    return streak


def carry_vs_tour(club, your_carry):
    """Compare your carry to PGA Tour avg. Returns dict with delta + verdict."""
    tour = TOUR_CARRY.get(club)
    if not tour or not your_carry:
        return None
    delta = your_carry - tour
    pct = (your_carry / tour) * 100
    if delta >= -5:
        verdict = "Pro level"
    elif delta >= -20:
        verdict = "Above amateur"
    elif delta >= -40:
        verdict = "Typical amateur"
    else:
        verdict = "Room to grow"
    return {"tour": tour, "you": your_carry, "delta": delta, "pct": pct, "verdict": verdict}


def miss_pattern(club="7i"):
    """Returns user's miss tendency for a club: 'right' / 'left' / 'short' / 'long' / None."""
    d = load_data()
    shots = [s for s in (d.get("practice_shots", []) or []) if s.get("club") == club]
    shots = [s for s in shots if s.get("offline_y") is not None]
    if len(shots) < 5:
        return None
    rights = sum(1 for s in shots if s.get("offline_y", 0) > 5)
    lefts = sum(1 for s in shots if s.get("offline_y", 0) < -5)
    total = len(shots)
    if rights / total >= 0.6:
        return {"side": "right", "pct": int(100 * rights / total), "n": total}
    if lefts / total >= 0.6:
        return {"side": "left", "pct": int(100 * lefts / total), "n": total}
    return None


def course_history(course_name):
    """Stats on user's history at a course."""
    d = load_data()
    rounds = [r for r in (d.get("rounds", []) or []) if course_name.lower() in (r.get("course", "").lower())]
    if not rounds:
        return None
    scores = [r.get("score") for r in rounds if r.get("score")]
    return {
        "plays": len(rounds),
        "best": min(scores) if scores else None,
        "avg": round(sum(scores) / len(scores), 1) if scores else None,
        "last": scores[-1] if scores else None,
    }


def hole_weakness(course_name):
    """Find the hole(s) where user struggles most. Returns top 1-3 weak holes."""
    d = load_data()
    rounds = [r for r in (d.get("rounds", []) or []) if course_name.lower() in (r.get("course", "").lower())]
    hole_diffs = defaultdict(list)
    for r in rounds:
        for hole in (r.get("holes", []) or []):
            par = hole.get("par")
            score = hole.get("score")
            num = hole.get("num")
            if par and score and num:
                hole_diffs[num].append(score - par)
    if not hole_diffs:
        return []
    weak = []
    for num, diffs in hole_diffs.items():
        if len(diffs) >= 2:  # need 2+ plays to be meaningful
            weak.append({"hole": num, "avg_over_par": round(sum(diffs) / len(diffs), 1), "plays": len(diffs)})
    weak.sort(key=lambda x: -x["avg_over_par"])
    return weak[:3]


def par_type_weakness(course_name=None):
    """Identify if user struggles on par 3s, 4s, or 5s most."""
    d = load_data()
    rounds = d.get("rounds", []) or []
    if course_name:
        rounds = [r for r in rounds if course_name.lower() in (r.get("course", "").lower())]
    by_par = defaultdict(list)
    for r in rounds:
        for hole in (r.get("holes", []) or []):
            par = hole.get("par")
            score = hole.get("score")
            if par and score:
                by_par[par].append(score - par)
    return {p: round(sum(v) / len(v), 2) for p, v in by_par.items() if v}


def suggested_club(yards, plays_like=None):
    """Given target yards, suggest user's club using their actual carries."""
    d = load_data()
    shots = d.get("practice_shots", []) or []
    target = plays_like or yards
    by_club = defaultdict(list)
    for s in shots:
        if s.get("club") and s.get("carry"):
            by_club[s["club"]].append(s["carry"])
    avg_by_club = {c: sum(v) / len(v) for c, v in by_club.items() if len(v) >= 3}
    if not avg_by_club:
        # fallback to bag defaults
        avg_by_club = {
            "Driver": 240, "3W": 215, "5H": 195, "5i": 178, "6i": 167,
            "7i": 155, "8i": 142, "9i": 130, "PW": 110, "GW": 95, "SW": 80, "LW": 65,
        }
    # find club whose avg is closest but slightly over target (smooth swing)
    best = None
    best_diff = 9999
    for club, avg in avg_by_club.items():
        diff = avg - target  # positive = club goes longer than target
        if 0 <= diff < best_diff:
            best = (club, avg, diff)
            best_diff = diff
    if best is None:
        # all clubs short — pick longest
        club, avg = max(avg_by_club.items(), key=lambda x: x[1])
        return {"club": club, "your_carry": int(avg), "target": int(target), "warning": "longer than your bag"}
    return {"club": best[0], "your_carry": int(best[1]), "target": int(target), "warning": None}


def plays_like(yards, wind_mph=0, wind_dir="head", elevation_ft=0, temp_f=70):
    """Calculate playing yardage with wind, elevation, temp."""
    adj = yards
    # Wind: 1% per 1 mph head; 0.5% per 1 mph tail; 0.3% per 1 mph cross
    if wind_dir == "head":
        adj += yards * (wind_mph / 100)
    elif wind_dir == "tail":
        adj -= yards * (wind_mph / 200)
    # Elevation: 2 yards per 10 ft
    adj -= elevation_ft / 5
    # Temp: 2 yards per 10°F deviation from 70
    adj -= (temp_f - 70) / 5
    return round(adj)


def smart_insights():
    """Generate the rotating list of intelligent insights for the dashboard."""
    d = load_data()
    out = []
    profile = d.get("profile", {})
    rounds = d.get("rounds", []) or []
    shots = d.get("practice_shots", []) or []

    # === Carry vs Tour for 7i (most data usually) ===
    sevens = [s for s in shots if s.get("club") == "7i" and s.get("carry")]
    if sevens:
        avg7 = round(sum(s["carry"] for s in sevens[-20:]) / len(sevens[-20:]))
        cmp = carry_vs_tour("7i", avg7)
        if cmp:
            out.append({
                "icon": "🎯",
                "title": f"You hit 7i {avg7} yards",
                "body": f"PGA Tour avg with 7-iron: {cmp['tour']} yds. You're at {cmp['pct']:.0f}% of Tour. {cmp['verdict']}.",
                "tone": "fairway" if cmp["delta"] >= -20 else "gold",
            })

    # === Miss pattern ===
    miss = miss_pattern("7i")
    if miss:
        verb_drill = "Cure The Slice — In-To-Out Path" if miss["side"] == "right" else "Square Path — Hook Fix"
        out.append({
            "icon": "📐",
            "title": f"{miss['pct']}% of your 7i misses go {miss['side']}",
            "body": f"That's likely an out-to-in path. Recommended drill: {verb_drill}.",
            "tone": "danger",
            "drill_link": "driver_path" if miss["side"] == "right" else None,
        })

    # === Course mastery ===
    home = profile.get("home_course", "El Cariso")
    hist = course_history(home)
    if hist and hist["plays"] >= 3:
        weak_par = par_type_weakness(home)
        weakest = max(weak_par.items(), key=lambda x: x[1]) if weak_par else None
        weak_text = f"Weakness: Par {weakest[0]}s (avg +{weakest[1]} vs par)." if weakest and weakest[1] > 0.5 else "Solid all-around."
        out.append({
            "icon": "🏠",
            "title": f"You've played {home} {hist['plays']} times",
            "body": f"Best score: {hist['best']}. Average: {hist['avg']}. {weak_text}",
            "tone": "fairway",
        })
        # Hole-specific weakness
        weak = hole_weakness(home)
        if weak:
            top = weak[0]
            if top["avg_over_par"] >= 1:
                out.append({
                    "icon": "⚠️",
                    "title": f"You're struggling on hole {top['hole']} at {home}",
                    "body": f"Average +{top['avg_over_par']} vs par over {top['plays']} plays. Focus practice on the shot that hole demands.",
                    "tone": "danger",
                })

    # === Putting ===
    putts = [r.get("putts") for r in rounds if r.get("putts")]
    if putts:
        avg_putts = round(sum(putts[-5:]) / len(putts[-5:]), 1)
        if avg_putts > TOUR_BENCH["putts_per_round"]:
            extra = round(avg_putts - TOUR_BENCH["putts_per_round"], 1)
            out.append({
                "icon": "⛳",
                "title": f"You average {avg_putts} putts per round",
                "body": f"Tour avg: {TOUR_BENCH['putts_per_round']}. You're losing ~{extra} strokes/round on the green. Try the Gate Drill.",
                "tone": "gold",
                "drill_link": "putt_gate",
            })

    # === Streak / consistency ===
    streak = practice_streak()
    if streak >= 3:
        out.append({
            "icon": "🔥",
            "title": f"{streak}-day practice streak",
            "body": "Consistency builds skill. Keep the chain alive — even 10 minutes counts.",
            "tone": "gold",
        })

    # === Score trend ===
    if len(rounds) >= 3:
        recent = [r.get("score") for r in rounds[-3:] if r.get("score")]
        prev = [r.get("score") for r in rounds[-6:-3] if r.get("score")]
        if recent and prev:
            r_avg = sum(recent) / len(recent)
            p_avg = sum(prev) / len(prev)
            delta = r_avg - p_avg
            if delta < -1.5:
                out.append({
                    "icon": "📈",
                    "title": f"Trending down {abs(delta):.1f} strokes",
                    "body": f"Last 3 rounds avg {r_avg:.1f} vs prior 3 at {p_avg:.1f}. Whatever you're doing, keep doing it.",
                    "tone": "fairway",
                })
            elif delta > 1.5:
                out.append({
                    "icon": "📉",
                    "title": f"Trending up {delta:.1f} strokes",
                    "body": f"Last 3 rounds avg {r_avg:.1f} vs prior 3 at {p_avg:.1f}. Time for a coach session — what changed?",
                    "tone": "danger",
                })

    # === Goal: Break 80 ===
    if rounds:
        best = min(r.get("score", 999) for r in rounds)
        if best >= 80:
            gap = best - 79
            out.append({
                "icon": "🏆",
                "title": f"Break 80 goal — {gap} strokes to go",
                "body": f"Your best is {best}. Putting + scrambling are usually the fastest path. Audit short game next session.",
                "tone": "gold",
            })

    return out
