"""Golf Journey Pro v5.0 — 40+ achievement system."""
from cloud_storage import load_data, save_data
from datetime import datetime, timedelta

# Each: (id, icon, name, description, criteria_fn)
def _rounds(d):  return d.get("rounds", []) or []
def _shots(d):   return d.get("practice_shots", []) or []
def _coach(d):   return d.get("coach_history", []) or []

ACHIEVEMENTS = [
    # === Scoring milestones ===
    ("first_round",    "⛳", "First Round",          "Log your first round",                    lambda d: len(_rounds(d)) >= 1),
    ("five_rounds",    "🎯", "Five Down",            "Log 5 rounds",                            lambda d: len(_rounds(d)) >= 5),
    ("ten_rounds",     "🏌️", "Ten Strong",           "Log 10 rounds",                           lambda d: len(_rounds(d)) >= 10),
    ("twenty_rounds",  "👑", "Twenty Club",          "Log 20 rounds",                           lambda d: len(_rounds(d)) >= 20),
    ("fifty_rounds",   "💎", "Half Century",         "Log 50 rounds",                           lambda d: len(_rounds(d)) >= 50),
    ("break_90",       "🎉", "Break 90",             "Score under 90",                          lambda d: any(r.get("score", 999) < 90 for r in _rounds(d))),
    ("break_85",       "🔥", "Break 85",             "Score under 85",                          lambda d: any(r.get("score", 999) < 85 for r in _rounds(d))),
    ("break_80",       "🏆", "Break 80",             "Score under 80 — career goal",            lambda d: any(r.get("score", 999) < 80 for r in _rounds(d))),
    ("break_75",       "🌟", "Break 75",             "Score under 75 — elite",                  lambda d: any(r.get("score", 999) < 75 for r in _rounds(d))),
    ("personal_best",  "📈", "Personal Best",        "Log a new low score",                     lambda d: _has_pb(d)),
    ("sub_par_9",      "🦅", "Sub-Par Nine",         "Play 9 holes under par",                  lambda d: any(r.get("front_9", 99) < 36 or r.get("back_9", 99) < 36 for r in _rounds(d))),

    # === Practice ===
    ("first_shot",     "🎯", "First Shot",           "Log your first practice shot",            lambda d: len(_shots(d)) >= 1),
    ("100_shots",      "💯", "Century Practice",     "Log 100 practice shots",                  lambda d: len(_shots(d)) >= 100),
    ("500_shots",      "🚀", "500 Club",             "Log 500 practice shots",                  lambda d: len(_shots(d)) >= 500),
    ("1000_shots",     "🏔️", "Grinder",              "Log 1,000 practice shots",                lambda d: len(_shots(d)) >= 1000),
    ("all_clubs",      "🎒", "Full Bag Day",         "Practice with 5+ different clubs in one session", lambda d: _all_clubs(d)),

    # === Streaks ===
    ("streak_3",       "🔥", "On Fire",              "3-day practice streak",                   lambda d: _streak(d) >= 3),
    ("streak_7",       "🔥", "Week Warrior",         "7-day practice streak",                   lambda d: _streak(d) >= 7),
    ("streak_14",      "🔥", "Two-Week Grind",       "14-day practice streak",                  lambda d: _streak(d) >= 14),
    ("streak_30",      "👹", "Monthly Beast",        "30-day practice streak",                  lambda d: _streak(d) >= 30),

    # === Distance / Speed ===
    ("driver_250",     "💪", "Quarter K",            "Driver carry 250+ yards",                 lambda d: _has_carry(d, "Driver", 250)),
    ("driver_270",     "⚡", "Bomber",               "Driver carry 270+ yards",                 lambda d: _has_carry(d, "Driver", 270)),
    ("driver_290",     "🚀", "Deep Drive",           "Driver carry 290+ yards",                 lambda d: _has_carry(d, "Driver", 290)),
    ("driver_300",     "🏆", "300 Club",             "Driver carry 300+ yards — career goal",   lambda d: _has_carry(d, "Driver", 300)),
    ("iron_pure",      "🎯", "Pure Strike",          "7i carry within 5 yds of avg target",     lambda d: _pure_iron(d)),

    # === Course mastery ===
    ("home_5",         "🏡", "Home Course Hero",     "Play home course 5 times",                lambda d: _home_count(d) >= 5),
    ("home_10",        "🏠", "Local Legend",         "Play home course 10 times",               lambda d: _home_count(d) >= 10),
    ("three_courses",  "🗺️", "Course Hopper",        "Play 3 different courses",                lambda d: _unique_courses(d) >= 3),
    ("five_courses",   "✈️", "Travelin' Golfer",     "Play 5 different courses",                lambda d: _unique_courses(d) >= 5),

    # === Stats: short game ===
    ("putts_under_30", "⛳", "Putt Wizard",          "Sub-30 putts in a round",                 lambda d: any(r.get("putts", 99) < 30 for r in _rounds(d))),
    ("putts_under_28", "🪄", "Putt Master",          "Sub-28 putts in a round",                 lambda d: any(r.get("putts", 99) < 28 for r in _rounds(d))),
    ("gir_50",         "📍", "GIR Climber",          "Hit 50%+ greens in a round",              lambda d: any((r.get("gir", 0) / 18) >= 0.5 for r in _rounds(d) if r.get("gir") is not None)),
    ("gir_67",         "🎯", "GIR Sniper",           "Hit 12+ greens in a round",               lambda d: any(r.get("gir", 0) >= 12 for r in _rounds(d))),

    # === Coach / engagement ===
    ("first_chat",     "💬", "First Lesson",         "Chat with AI Coach",                      lambda d: len(_coach(d)) >= 1),
    ("ten_chats",      "🎓", "Student of the Game",  "10 conversations with Coach",             lambda d: len(_coach(d)) >= 10),
    ("photo_swing",    "📸", "Show Me",              "Submit a swing photo for analysis",       lambda d: any("photo" in c.get("type", "") for c in _coach(d))),
    ("voice_caddy",    "🎤", "Talk to Me",           "Use voice input with Coach",              lambda d: any(c.get("voice") for c in _coach(d))),

    # === Special / consistency ===
    ("week_active",    "📅", "Active Week",          "Practice 4+ days in a week",              lambda d: _active_week(d)),
    ("consistent_5",   "📊", "Consistent",           "5 rounds within 5 strokes of avg",        lambda d: _consistent(d, 5)),
    ("under_handicap", "📉", "Below The Number",     "Score below your handicap",               lambda d: _under_handicap(d)),
    ("dispersion_70",  "🎯", "Tight Dispersion",     "Achieve dispersion index of 70+",         lambda d: _dispersion(d) >= 70),
    ("ten_drills",     "💡", "Drill Sergeant",       "Generate 10 AI drills",                   lambda d: len(d.get("ai_drills", [])) >= 10),
    ("first_drill",    "📚", "Coachable",            "Generate your first AI drill",            lambda d: len(d.get("ai_drills", [])) >= 1),
]


# ---- Helpers ----
def _has_pb(d):
    rs = _rounds(d)
    if len(rs) < 2: return False
    scores = [r.get("score", 999) for r in rs]
    return scores[-1] == min(scores)


def _all_clubs(d):
    shots = _shots(d)
    by_date = {}
    for s in shots:
        date = s.get("date", "")[:10]
        by_date.setdefault(date, set()).add(s.get("club"))
    return any(len(c) >= 5 for c in by_date.values())


def _streak(d):
    shots = _shots(d)
    if not shots: return 0
    dates = sorted({s.get("date", "")[:10] for s in shots if s.get("date")}, reverse=True)
    if not dates: return 0
    today = datetime.now().date()
    streak = 0
    for i, ds in enumerate(dates):
        try:
            dt = datetime.strptime(ds, "%Y-%m-%d").date()
        except:
            continue
        expected = today - timedelta(days=i)
        if (today - dt).days <= 1 and dt == expected:
            streak += 1
        elif streak > 0:
            break
    return streak


def _has_carry(d, club, yards):
    for s in _shots(d):
        if s.get("club") == club and (s.get("carry") or 0) >= yards:
            return True
    return False


def _pure_iron(d):
    sevens = [s for s in _shots(d) if s.get("club") == "7i" and s.get("carry")]
    if len(sevens) < 5: return False
    avg = sum(s["carry"] for s in sevens) / len(sevens)
    return any(abs(s["carry"] - avg) < 5 for s in sevens[-5:])


def _home_count(d):
    home = (d.get("profile", {}).get("home_course") or "El Cariso").lower()
    return sum(1 for r in _rounds(d) if home in (r.get("course", "").lower()))


def _unique_courses(d):
    return len({r.get("course", "").strip() for r in _rounds(d) if r.get("course")})


def _active_week(d):
    shots = _shots(d)
    if not shots: return False
    today = datetime.now().date()
    week_dates = {(today - timedelta(days=i)).isoformat() for i in range(7)}
    practiced = {s.get("date", "")[:10] for s in shots if s.get("date", "")[:10] in week_dates}
    return len(practiced) >= 4


def _consistent(d, threshold):
    rs = _rounds(d)[-5:]
    if len(rs) < 5: return False
    scores = [r.get("score") for r in rs if r.get("score")]
    if len(scores) < 5: return False
    avg = sum(scores) / len(scores)
    return all(abs(s - avg) <= threshold for s in scores)


def _under_handicap(d):
    hcp = d.get("profile", {}).get("ghin", 31.3)
    par_avg = 72  # most courses
    target = par_avg + hcp
    return any(r.get("score", 999) < target for r in _rounds(d))


def _dispersion(d):
    return d.get("metrics", {}).get("dispersion_index", 0)


# ---- API ----
def evaluate_all():
    d = load_data()
    unlocked = set(d.get("achievements") or [])
    newly = []
    for ach in ACHIEVEMENTS:
        aid, icon, name, desc, fn = ach
        if aid in unlocked:
            continue
        try:
            if fn(d):
                unlocked.add(aid)
                newly.append({"id": aid, "icon": icon, "name": name, "desc": desc})
        except Exception:
            continue
    if newly:
        d["achievements"] = list(unlocked)
        save_data(d)
    return newly


def get_all():
    d = load_data()
    unlocked = set(d.get("achievements") or [])
    out = []
    for aid, icon, name, desc, fn in ACHIEVEMENTS:
        out.append({
            "id": aid, "icon": icon, "name": name, "desc": desc,
            "unlocked": aid in unlocked,
        })
    return out


def stats():
    all_a = get_all()
    return {
        "total": len(all_a),
        "unlocked": sum(1 for a in all_a if a["unlocked"]),
    }
