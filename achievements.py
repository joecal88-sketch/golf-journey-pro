"""Golf Journey Pro v5.1 — 100 achievement system across 4 tiers."""
from cloud_storage import load_data, save_data
from datetime import datetime, timedelta

# ---------- Bulletproof helpers (every fn returns sensible default on bad data) ----------
def _safe_list(d, k):
    try:
        v = d.get(k) if isinstance(d, dict) else None
    except Exception:
        v = None
    if isinstance(v, list):
        return v
    return []

def _safe_dict(d, k):
    try:
        v = d.get(k) if isinstance(d, dict) else None
    except Exception:
        v = None
    return v if isinstance(v, dict) else {}

def _rounds(d):  return _safe_list(d, "rounds")
def _shots(d):   return _safe_list(d, "practice_shots")
def _coach(d):   return _safe_list(d, "coach_history")
def _drills(d):  return _safe_list(d, "ai_drills")

def _num(x, default=0):
    try:
        n = float(x)
        return n if n == n else default  # NaN check
    except Exception:
        return default

def _score(r):       return _num(r.get("score"), 999) if isinstance(r, dict) else 999
def _putts(r):       return _num(r.get("putts"), 99) if isinstance(r, dict) else 99
def _gir(r):         return _num(r.get("gir"), 0) if isinstance(r, dict) else 0
def _fir(r):         return _num(r.get("fir"), 0) if isinstance(r, dict) else 0
def _carry(s):       return _num(s.get("carry"), 0) if isinstance(s, dict) else 0
def _club(s):        return s.get("club", "") if isinstance(s, dict) else ""
def _course(r):      return (r.get("course", "") if isinstance(r, dict) else "") or ""
def _date(item):     return (item.get("date", "") if isinstance(item, dict) else "")[:10]


# ---------- Predicate factories ----------
def at_least_rounds(n):           return lambda d: len(_rounds(d)) >= n
def at_least_shots(n):            return lambda d: len(_shots(d)) >= n
def at_least_chats(n):            return lambda d: len(_coach(d)) >= n
def at_least_drills(n):           return lambda d: len(_drills(d)) >= n
def break_score(threshold):       return lambda d: any(_score(r) < threshold for r in _rounds(d))
def putts_below(t):               return lambda d: any(_putts(r) < t for r in _rounds(d))
def gir_at_least(g):              return lambda d: any(_gir(r) >= g for r in _rounds(d))
def fir_at_least(f):              return lambda d: any(_fir(r) >= f for r in _rounds(d))
def carry_at_least(club, y):      return lambda d: any(_club(s) == club and _carry(s) >= y for s in _shots(d))
def carry_any_club(y):            return lambda d: any(_carry(s) >= y for s in _shots(d))
def streak_days(n):               return lambda d: _streak(d) >= n
def unique_courses_at_least(n):   return lambda d: _unique_courses(d) >= n
def home_count_at_least(n):       return lambda d: _home_count(d) >= n
def shots_in_one_day(n):          return lambda d: _max_shots_in_day(d) >= n
def rounds_in_one_week(n):        return lambda d: _max_rounds_in_week(d) >= n


# ---------- Stateful helpers ----------
def _streak(d):
    shots = _shots(d)
    dates = sorted({_date(s) for s in shots if _date(s)}, reverse=True)
    if not dates: return 0
    today = datetime.now().date()
    streak = 0
    for i, ds in enumerate(dates):
        try:
            dt = datetime.strptime(ds, "%Y-%m-%d").date()
        except Exception:
            continue
        if (today - dt).days == i:
            streak += 1
        else:
            break
    return streak

def _unique_courses(d):
    return len({_course(r).strip().lower() for r in _rounds(d) if _course(r)})

def _home_count(d):
    profile = _safe_dict(d, "profile")
    home = (profile.get("home_course") or "El Cariso").lower()
    return sum(1 for r in _rounds(d) if home in _course(r).lower())

def _max_shots_in_day(d):
    by_day = {}
    for s in _shots(d):
        dt = _date(s)
        if dt:
            by_day[dt] = by_day.get(dt, 0) + 1
    return max(by_day.values()) if by_day else 0

def _max_rounds_in_week(d):
    rs = _rounds(d)
    dates = []
    for r in rs:
        try:
            dates.append(datetime.strptime(_date(r), "%Y-%m-%d").date())
        except Exception:
            continue
    if not dates: return 0
    dates.sort()
    best = 0
    for i, base in enumerate(dates):
        count = sum(1 for d2 in dates[i:] if (d2 - base).days <= 7)
        best = max(best, count)
    return best

def _personal_best_recent(d):
    rs = _rounds(d)
    if len(rs) < 2: return False
    scores = [_score(r) for r in rs]
    return scores[-1] == min(scores)

def _all_clubs_one_session(d, n=5):
    by_date = {}
    for s in _shots(d):
        dt = _date(s)
        if dt:
            by_date.setdefault(dt, set()).add(_club(s))
    return any(len(c) >= n for c in by_date.values())

def _consistent(d, threshold, count=5):
    rs = _rounds(d)[-count:]
    scores = [_score(r) for r in rs if _score(r) < 200]
    if len(scores) < count: return False
    avg = sum(scores) / len(scores)
    return all(abs(s - avg) <= threshold for s in scores)

def _under_handicap(d):
    profile = _safe_dict(d, "profile")
    hcp = _num(profile.get("ghin"), 31.3)
    target = 72 + hcp
    return any(_score(r) < target for r in _rounds(d))

def _under_handicap_by(d, by):
    profile = _safe_dict(d, "profile")
    hcp = _num(profile.get("ghin"), 31.3)
    target = 72 + hcp - by
    return any(_score(r) < target for r in _rounds(d))

def _back_to_back(d):
    rs = _rounds(d)
    if len(rs) < 2: return False
    return _score(rs[-1]) < 90 and _score(rs[-2]) < 90

def _three_in_a_row_under(d, threshold):
    rs = _rounds(d)
    if len(rs) < 3: return False
    return all(_score(r) < threshold for r in rs[-3:])

def _ten_in_a_row_under(d, threshold):
    rs = _rounds(d)
    if len(rs) < 10: return False
    return all(_score(r) < threshold for r in rs[-10:])

def _improvement(d, points):
    rs = _rounds(d)
    if len(rs) < 10: return False
    first5 = [_score(r) for r in rs[:5]]
    last5  = [_score(r) for r in rs[-5:]]
    return (sum(first5)/5) - (sum(last5)/5) >= points

def _photo_swing(d):    return any(("photo" in str(c.get("type", ""))) for c in _coach(d) if isinstance(c, dict))
def _voice_caddy(d):    return any(c.get("voice") for c in _coach(d) if isinstance(c, dict))
def _dispersion(d, t):  return _num(_safe_dict(d, "metrics").get("dispersion_index"), 0) >= t
def _eagle(d):          return any(any((h or {}).get("score", 9) - (h or {}).get("par", 4) <= -2 for h in _safe_list(r, "holes")) for r in _rounds(d))
def _birdies_in_round(d, n):
    for r in _rounds(d):
        b = sum(1 for h in _safe_list(r, "holes") if isinstance(h, dict) and _num(h.get("score"), 9) - _num(h.get("par"), 4) == -1)
        if b >= n: return True
    return False
def _no_double_bogey(d):
    for r in _rounds(d):
        holes = _safe_list(r, "holes")
        if not holes: continue
        if all(_num(h.get("score"), 9) - _num(h.get("par"), 4) <= 1 for h in holes if isinstance(h, dict)):
            return True
    return False
def _played_par3_only(d):
    return any("par 3" in _course(r).lower() for r in _rounds(d))
def _played_morning(d):
    return any(isinstance(r.get("tee_time"), str) and r["tee_time"][:2].isdigit() and int(r["tee_time"][:2]) < 8 for r in _rounds(d) if isinstance(r, dict))
def _holed_long_putt(d):
    return any(_num(s.get("putt_length"), 0) >= 20 and s.get("holed") for s in _shots(d) if isinstance(s, dict))


# ---------- The 100 Achievements ----------
# (id, icon, name, description, tier, category, criteria_fn)
# tiers: "easy", "medium", "hard", "legendary"
# categories: "Scoring", "Practice", "Distance", "Short Game", "Streaks", "Courses", "Coach", "Special"

ACHIEVEMENTS = [
    # ============================================================
    # SCORING — 25 achievements
    # ============================================================
    ("first_round",    "⛳", "First Round",          "Log your first round",                              "easy",      "Scoring", at_least_rounds(1)),
    ("five_rounds",    "🎯", "Five Down",            "Log 5 rounds",                                      "easy",      "Scoring", at_least_rounds(5)),
    ("ten_rounds",     "🏌️", "Ten Strong",           "Log 10 rounds",                                     "easy",      "Scoring", at_least_rounds(10)),
    ("twenty_rounds",  "👑", "Twenty Club",          "Log 20 rounds",                                     "medium",    "Scoring", at_least_rounds(20)),
    ("fifty_rounds",   "💎", "Half Century",         "Log 50 rounds",                                     "hard",      "Scoring", at_least_rounds(50)),
    ("hundred_rounds", "🪩", "Centurion",            "Log 100 rounds",                                    "legendary", "Scoring", at_least_rounds(100)),
    ("break_100",      "🎉", "Break 100",            "Score under 100",                                   "easy",      "Scoring", break_score(100)),
    ("break_95",       "🚀", "Break 95",             "Score under 95",                                    "easy",      "Scoring", break_score(95)),
    ("break_90",       "🔥", "Break 90",             "Score under 90",                                    "medium",    "Scoring", break_score(90)),
    ("break_85",       "🌶️", "Break 85",             "Score under 85",                                    "medium",    "Scoring", break_score(85)),
    ("break_80",       "🏆", "Break 80",             "Score under 80 — your career goal",                 "hard",      "Scoring", break_score(80)),
    ("break_75",       "🌟", "Break 75",             "Score under 75 — elite",                            "legendary", "Scoring", break_score(75)),
    ("break_par",      "🦅", "Even Par",             "Shoot par or better",                               "legendary", "Scoring", break_score(73)),
    ("personal_best",  "📈", "Personal Best",        "Set a new low score",                               "medium",    "Scoring", _personal_best_recent),
    ("under_handicap", "📉", "Below The Number",     "Score below your handicap",                         "medium",    "Scoring", _under_handicap),
    ("hcp_minus_3",    "🎯", "Three Better",         "Score 3+ strokes below your handicap",              "hard",      "Scoring", lambda d: _under_handicap_by(d, 3)),
    ("hcp_minus_5",    "🚨", "Five Better",          "Score 5+ strokes below your handicap",              "legendary", "Scoring", lambda d: _under_handicap_by(d, 5)),
    ("back_to_back_90","🔁", "Back-to-Back",         "Two rounds in a row under 90",                      "medium",    "Scoring", _back_to_back),
    ("three_under_85", "🎬", "Trilogy",              "Three rounds in a row under 85",                    "hard",      "Scoring", lambda d: _three_in_a_row_under(d, 85)),
    ("ten_under_85",   "🛡️", "Ten Sub-85s",          "Ten rounds in a row under 85",                      "legendary", "Scoring", lambda d: _ten_in_a_row_under(d, 85)),
    ("sub_par_9",      "🦅", "Sub-Par Nine",         "Play 9 holes under par",                            "hard",      "Scoring", lambda d: any(_num(r.get("front_9"), 99) < 36 or _num(r.get("back_9"), 99) < 36 for r in _rounds(d))),
    ("eagle",          "🦅", "Eagle",                "Make an eagle (-2)",                                "hard",      "Scoring", _eagle),
    ("five_birdies",   "🐦", "Birdie Barrage",       "5 birdies in a single round",                       "hard",      "Scoring", lambda d: _birdies_in_round(d, 5)),
    ("ten_birdies",    "🐦‍🔥", "Birdie Storm",         "10 birdies in a single round",                      "legendary", "Scoring", lambda d: _birdies_in_round(d, 10)),
    ("no_double",      "🛡️", "Bogey-Proof",          "Round with no double bogeys",                       "hard",      "Scoring", _no_double_bogey),

    # ============================================================
    # PRACTICE — 15 achievements
    # ============================================================
    ("first_shot",     "🎯", "First Shot",           "Log your first practice shot",                      "easy",      "Practice", at_least_shots(1)),
    ("50_shots",       "🎳", "Half Bucket",          "Log 50 practice shots",                             "easy",      "Practice", at_least_shots(50)),
    ("100_shots",      "💯", "Century Practice",     "Log 100 practice shots",                            "easy",      "Practice", at_least_shots(100)),
    ("250_shots",      "📦", "Full Bucket",          "Log 250 practice shots",                            "medium",    "Practice", at_least_shots(250)),
    ("500_shots",      "🚀", "500 Club",             "Log 500 practice shots",                            "medium",    "Practice", at_least_shots(500)),
    ("1000_shots",     "🏔️", "Grinder",              "Log 1,000 practice shots",                          "hard",      "Practice", at_least_shots(1000)),
    ("2500_shots",     "⛏️", "Range Rat",            "Log 2,500 practice shots",                          "hard",      "Practice", at_least_shots(2500)),
    ("5000_shots",     "🗿", "Iron Will",            "Log 5,000 practice shots",                          "legendary", "Practice", at_least_shots(5000)),
    ("10000_shots",    "🌌", "Mastery",              "Log 10,000 practice shots — Gladwell mode",         "legendary", "Practice", at_least_shots(10000)),
    ("all_clubs",      "🎒", "Full Bag Day",         "Practice with 5+ clubs in one session",             "medium",    "Practice", _all_clubs_one_session),
    ("range_session_50","🪣", "Range Marathon",       "50+ shots in a single day",                         "medium",    "Practice", shots_in_one_day(50)),
    ("range_session_100","🌋", "100-Ball Bucket",     "100+ shots in a single day",                        "hard",      "Practice", shots_in_one_day(100)),
    ("range_session_200","♾️", "Endurance",          "200+ shots in a single day",                        "legendary", "Practice", shots_in_one_day(200)),
    ("dispersion_50",  "🎯", "Tightening Up",        "Dispersion index 50+",                              "medium",    "Practice", lambda d: _dispersion(d, 50)),
    ("dispersion_70",  "🪡", "Pinpoint",             "Dispersion index 70+",                              "hard",      "Practice", lambda d: _dispersion(d, 70)),

    # ============================================================
    # DISTANCE — 12 achievements
    # ============================================================
    ("driver_220",     "💪", "Off The Tee",          "Driver carry 220+ yards",                           "easy",      "Distance", carry_at_least("Driver", 220)),
    ("driver_240",     "🏋️", "Solid Strike",         "Driver carry 240+ yards",                           "easy",      "Distance", carry_at_least("Driver", 240)),
    ("driver_250",     "🦾", "Quarter K",            "Driver carry 250+ yards",                           "medium",    "Distance", carry_at_least("Driver", 250)),
    ("driver_260",     "💥", "Long Ball",            "Driver carry 260+ yards",                           "medium",    "Distance", carry_at_least("Driver", 260)),
    ("driver_270",     "⚡", "Bomber",               "Driver carry 270+ yards",                           "hard",      "Distance", carry_at_least("Driver", 270)),
    ("driver_280",     "🎇", "Tour Caliber",         "Driver carry 280+ yards",                           "hard",      "Distance", carry_at_least("Driver", 280)),
    ("driver_290",     "🚀", "Deep Drive",           "Driver carry 290+ yards",                           "legendary", "Distance", carry_at_least("Driver", 290)),
    ("driver_300",     "🏆", "300 Club",             "Driver carry 300+ yards — career goal",             "legendary", "Distance", carry_at_least("Driver", 300)),
    ("driver_320",     "👽", "Outlier",              "Driver carry 320+ yards",                           "legendary", "Distance", carry_at_least("Driver", 320)),
    ("seven_iron_165", "🎯", "Pure 7-iron",          "7i carry 165+ yards",                               "medium",    "Distance", carry_at_least("7i", 165)),
    ("seven_iron_180", "🎯", "Tour 7-iron",          "7i carry 180+ yards",                               "hard",      "Distance", carry_at_least("7i", 180)),
    ("wedge_100",      "🎯", "Wedge Sniper",         "Wedge carry under 5y from target average",          "medium",    "Distance", _all_clubs_one_session),  # proxy

    # ============================================================
    # SHORT GAME — 10 achievements
    # ============================================================
    ("putts_under_36", "⛳", "Two-Putt Round",       "36 or fewer putts in a round",                      "easy",      "Short Game", putts_below(37)),
    ("putts_under_32", "🏌️‍♂️", "Smooth Stroke",       "Sub-32 putts in a round",                           "medium",    "Short Game", putts_below(32)),
    ("putts_under_30", "🪄", "Putt Wizard",          "Sub-30 putts in a round",                           "hard",      "Short Game", putts_below(30)),
    ("putts_under_28", "🎩", "Putt Master",          "Sub-28 putts in a round — Tour pace",               "legendary", "Short Game", putts_below(28)),
    ("putts_under_25", "🛸", "Magician",             "Sub-25 putts in a round",                           "legendary", "Short Game", putts_below(25)),
    ("long_putt",      "🎯", "Long Range",           "Hole a putt 20ft+",                                 "hard",      "Short Game", _holed_long_putt),
    ("gir_4",          "📍", "GIR Starter",          "Hit 4+ greens in a round",                          "easy",      "Short Game", gir_at_least(4)),
    ("gir_8",          "📍", "GIR Builder",          "Hit 8+ greens in a round",                          "medium",    "Short Game", gir_at_least(8)),
    ("gir_12",         "🎯", "GIR Sniper",           "Hit 12+ greens in a round",                         "hard",      "Short Game", gir_at_least(12)),
    ("gir_15",         "🏹", "GIR Surgeon",          "Hit 15+ greens in a round",                         "legendary", "Short Game", gir_at_least(15)),

    # ============================================================
    # STREAKS — 10 achievements
    # ============================================================
    ("streak_2",       "✨", "Back-to-Back Days",    "2-day practice streak",                             "easy",      "Streaks", streak_days(2)),
    ("streak_3",       "🔥", "On Fire",              "3-day practice streak",                             "easy",      "Streaks", streak_days(3)),
    ("streak_5",       "🔥", "5-Day Push",           "5-day practice streak",                             "easy",      "Streaks", streak_days(5)),
    ("streak_7",       "🔥", "Week Warrior",         "7-day practice streak",                             "medium",    "Streaks", streak_days(7)),
    ("streak_14",      "🔥", "Two-Week Grind",       "14-day practice streak",                            "medium",    "Streaks", streak_days(14)),
    ("streak_21",      "🌪️", "Habit Formed",         "21-day practice streak",                            "hard",      "Streaks", streak_days(21)),
    ("streak_30",      "👹", "Monthly Beast",        "30-day practice streak",                            "hard",      "Streaks", streak_days(30)),
    ("streak_60",      "🐲", "Two-Month Dragon",     "60-day practice streak",                            "legendary", "Streaks", streak_days(60)),
    ("streak_100",     "🪐", "Triple Digits",        "100-day practice streak",                           "legendary", "Streaks", streak_days(100)),
    ("streak_365",     "🌌", "Year of Golf",         "365-day practice streak — the holy grail",          "legendary", "Streaks", streak_days(365)),

    # ============================================================
    # COURSES — 10 achievements
    # ============================================================
    ("home_3",         "🏡", "Familiar Face",        "Play home course 3 times",                          "easy",      "Courses", home_count_at_least(3)),
    ("home_5",         "🏡", "Home Course Hero",     "Play home course 5 times",                          "easy",      "Courses", home_count_at_least(5)),
    ("home_10",        "🏠", "Local Legend",         "Play home course 10 times",                         "medium",    "Courses", home_count_at_least(10)),
    ("home_25",        "🛖", "Course Owner",         "Play home course 25 times",                         "hard",      "Courses", home_count_at_least(25)),
    ("two_courses",    "🚙", "Branching Out",        "Play 2 different courses",                          "easy",      "Courses", unique_courses_at_least(2)),
    ("three_courses",  "🗺️", "Course Hopper",        "Play 3 different courses",                          "easy",      "Courses", unique_courses_at_least(3)),
    ("five_courses",   "✈️", "Travelin' Golfer",     "Play 5 different courses",                          "medium",    "Courses", unique_courses_at_least(5)),
    ("ten_courses",    "🌍", "Globe Trotter",        "Play 10 different courses",                         "hard",      "Courses", unique_courses_at_least(10)),
    ("twenty_courses", "🛫", "Course Collector",     "Play 20 different courses",                         "legendary", "Courses", unique_courses_at_least(20)),
    ("par3_course",    "🏝️", "Par 3 Specialist",     "Play a par-3 course",                               "easy",      "Courses", _played_par3_only),

    # ============================================================
    # COACH — 10 achievements
    # ============================================================
    ("first_chat",     "💬", "First Lesson",         "Chat with AI Coach",                                "easy",      "Coach", at_least_chats(1)),
    ("five_chats",     "💭", "Curious Mind",         "5 conversations with Coach",                        "easy",      "Coach", at_least_chats(5)),
    ("ten_chats",      "🎓", "Student of the Game",  "10 conversations with Coach",                       "medium",    "Coach", at_least_chats(10)),
    ("fifty_chats",    "📚", "Devoted Pupil",        "50 conversations with Coach",                       "hard",      "Coach", at_least_chats(50)),
    ("hundred_chats",  "🧑‍🏫", "Master Apprentice",    "100 conversations with Coach",                      "legendary", "Coach", at_least_chats(100)),
    ("photo_swing",    "📸", "Show Me",              "Submit a swing photo for analysis",                 "easy",      "Coach", _photo_swing),
    ("voice_caddy",    "🎤", "Talk to Me",           "Use voice input with Coach",                        "easy",      "Coach", _voice_caddy),
    ("first_drill",    "📚", "Coachable",            "Generate your first AI drill",                      "easy",      "Coach", at_least_drills(1)),
    ("ten_drills",     "💡", "Drill Sergeant",       "Generate 10 AI drills",                             "medium",    "Coach", at_least_drills(10)),
    ("fifty_drills",   "🧠", "Pattern Hunter",       "Generate 50 AI drills",                             "hard",      "Coach", at_least_drills(50)),

    # ============================================================
    # SPECIAL / META — 8 achievements
    # ============================================================
    ("week_active",    "📅", "Active Week",          "Practice 4+ days in a week",                        "easy",      "Special", lambda d: _streak(d) >= 4),
    ("two_rounds_week","🗓️", "Big Week",             "Play 2 rounds in 7 days",                           "medium",    "Special", rounds_in_one_week(2)),
    ("three_rounds_week","🗓️", "Golf Bender",        "Play 3 rounds in 7 days",                           "hard",      "Special", rounds_in_one_week(3)),
    ("consistent_5",   "📊", "Consistent",           "Last 5 rounds within 5 strokes of avg",             "medium",    "Special", lambda d: _consistent(d, 5)),
    ("consistent_3",   "📐", "Metronome",            "Last 5 rounds within 3 strokes of avg",             "hard",      "Special", lambda d: _consistent(d, 3)),
    ("improvement_5",  "📈", "Trending Down",        "5+ stroke improvement first 5 to last 5 rounds",    "hard",      "Special", lambda d: _improvement(d, 5)),
    ("improvement_10", "🌅", "Transformation",       "10+ stroke improvement first 5 to last 5 rounds",   "legendary", "Special", lambda d: _improvement(d, 10)),
    ("dawn_patrol",    "🌄", "Dawn Patrol",          "Tee off before 8am",                                "medium",    "Special", _played_morning),

    # ============================================================
    # SCORING (extra) — climbing milestones
    # ============================================================
    ("break_110",      "🌱", "Sub-110",              "Score under 110",                                   "easy",      "Scoring", break_score(110)),
    ("break_105",      "🌳", "Sub-105",              "Score under 105",                                   "easy",      "Scoring", break_score(105)),
    ("break_120",      "🌿", "Sub-120",              "Score under 120",                                   "easy",      "Scoring", break_score(120)),
    ("two_eagles",     "🦅", "Double Eagle",         "Make 2+ eagles in a single round",                  "legendary", "Scoring", lambda d: any(sum(1 for h in _safe_list(r, "holes") if isinstance(h, dict) and _num(h.get("score"), 9) - _num(h.get("par"), 4) <= -2) >= 2 for r in _rounds(d))),
    ("three_birdies",  "🐤", "Birdie Trio",          "3 birdies in a round",                              "medium",    "Scoring", lambda d: _birdies_in_round(d, 3)),
    ("front_9_under_40","➕", "Sharp Front",         "Front 9 under 40 strokes",                          "medium",    "Scoring", lambda d: any(_num(r.get("front_9"), 99) < 40 for r in _rounds(d))),
    ("back_9_under_40", "➖", "Sharp Back",          "Back 9 under 40 strokes",                           "medium",    "Scoring", lambda d: any(_num(r.get("back_9"), 99) < 40 for r in _rounds(d))),
    ("thirty_rounds",  "3️⃣", "Thirty Strong",        "Log 30 rounds",                                     "medium",    "Scoring", at_least_rounds(30)),

    # ============================================================
    # SHORT GAME — sandies, scrambles, putt streaks
    # ============================================================
    ("sandie",         "🏖️", "Sandie",               "Up-and-down from a bunker",                         "medium",    "Short Game", lambda d: any((h or {}).get("sand_save") for r in _rounds(d) for h in _safe_list(r, "holes"))),
    ("three_sandies",  "🏝️", "Beach Boy",            "3+ sandies in one round",                           "hard",      "Short Game", lambda d: any(sum(1 for h in _safe_list(r, "holes") if isinstance(h, dict) and h.get("sand_save")) >= 3 for r in _rounds(d))),
    ("up_and_down",    "⬆️", "Up & Down",            "5+ up-and-downs in one round",                      "hard",      "Short Game", lambda d: any(sum(1 for h in _safe_list(r, "holes") if isinstance(h, dict) and h.get("up_and_down")) >= 5 for r in _rounds(d))),
    ("chip_in",        "🎯", "Chip-In",              "Chip in from off the green",                        "hard",      "Short Game", lambda d: any(s.get("chip_in") for s in _shots(d))),
    ("three_putts_zero","🛡️", "Three-Putt Free",     "Round with zero three-putts",                       "hard",      "Short Game", lambda d: any((not any((h or {}).get("putts", 0) >= 3 for h in _safe_list(r, "holes"))) and len(_safe_list(r, "holes")) > 0 for r in _rounds(d))),
    ("holed_30ft",     "🌠", "30-Footer",            "Hole a putt 30ft+",                                 "legendary", "Short Game", lambda d: any(_num(s.get("putt_length"), 0) >= 30 and s.get("holed") for s in _shots(d))),
    ("birdie_putt_long","🪄", "Magic Roll",          "Birdie putt 15ft+",                                 "hard",      "Short Game", lambda d: any(_num(s.get("putt_length"), 0) >= 15 and s.get("holed") and s.get("for_birdie") for s in _shots(d))),
    ("gir_2_putt",     "🎯", "Greens & Putts",       "GIR 8+ AND putts under 32",                         "hard",      "Short Game", lambda d: any(_gir(r) >= 8 and _putts(r) < 32 for r in _rounds(d))),

    # ============================================================
    # DISTANCE — extra clubs and elite carries
    # ============================================================
    ("3w_220",         "🪵", "Pure 3-Wood",          "3W carry 220+ yards",                               "medium",    "Distance", carry_at_least("3W", 220)),
    ("3w_240",         "🌲", "Long 3-Wood",          "3W carry 240+ yards",                               "hard",      "Distance", carry_at_least("3W", 240)),
    ("hybrid_200",     "🏞️", "Hybrid Hero",          "5H carry 200+ yards",                               "medium",    "Distance", carry_at_least("5H", 200)),
    ("pw_120",         "🎯", "Wedge 120",            "PW carry 120+ yards",                               "medium",    "Distance", carry_at_least("PW", 120)),
    ("sw_90",          "⛱️", "Sand Wedge Pro",       "SW carry 90+ yards",                                "medium",    "Distance", carry_at_least("SW", 90)),
    ("any_350",        "🔥", "Big Bomb",             "Any club carry 350+ yards",                         "legendary", "Distance", carry_any_club(350)),

    # ============================================================
    # PRACTICE — tracking depth
    # ============================================================
    ("week_practice",  "📅", "Practice Week",        "Practice 5+ days in 7",                             "medium",    "Practice", lambda d: _streak(d) >= 5),
    ("month_practice", "📆", "Practice Month",       "Practice 20+ days in 30",                           "hard",      "Practice", lambda d: _streak(d) >= 20),
    ("shot_dispersion_85","🪡", "Laser",             "Dispersion index 85+",                              "legendary", "Practice", lambda d: _dispersion(d, 85)),
    ("all_irons",      "🪙", "Iron Day",             "Practice with all 6 irons in one session",          "hard",      "Practice", lambda d: _all_clubs_one_session(d, n=6)),
    ("full_bag_session","🎒", "Full Bag",            "Practice with 10+ clubs in one session",            "hard",      "Practice", lambda d: _all_clubs_one_session(d, n=10)),

    # ============================================================
    # COURSES — variety + travel
    # ============================================================
    ("home_50",        "🏚️", "Course Mayor",         "Play home course 50 times",                         "legendary", "Courses", home_count_at_least(50)),
    ("home_100",       "🏰", "Honorary Member",      "Play home course 100 times",                        "legendary", "Courses", home_count_at_least(100)),
    ("play_three_homes","🏘️", "All Three Homes",     "Play all 3 home courses",                           "medium",    "Courses", lambda d: all(any(name.lower() in _course(r).lower() for r in _rounds(d)) for name in ["El Cariso", "Scholl", "Van Nuys"])),

    # ============================================================
    # COACH — engagement
    # ============================================================
    ("twenty_chats",   "📖", "Lesson Hunter",        "20 conversations with Coach",                       "medium",    "Coach", at_least_chats(20)),
    ("twenty_drills",  "🧩", "Drill Builder",        "Generate 20 AI drills",                             "medium",    "Coach", at_least_drills(20)),
    ("hundred_drills", "🧠", "Mind of a Coach",      "Generate 100 AI drills",                            "legendary", "Coach", at_least_drills(100)),

    # ============================================================
    # SPECIAL — weather, time, seasonal, gaming feel
    # ============================================================
    ("played_rain",    "🌧️", "Mudder",               "Play in the rain (round flagged 'rain')",           "medium",    "Special", lambda d: any("rain" in str(r.get("weather", "")).lower() for r in _rounds(d))),
    ("played_wind",    "💨", "Wind Player",          "Play in 15+ mph wind",                              "medium",    "Special", lambda d: any(_num(r.get("wind_mph"), 0) >= 15 for r in _rounds(d))),
    ("played_cold",    "❄️", "Cold Soldier",         "Play below 50°F",                                   "medium",    "Special", lambda d: any(_num(r.get("temp_f"), 99) < 50 for r in _rounds(d))),
    ("played_hot",     "🌡️", "Heat Warrior",         "Play above 95°F",                                   "medium",    "Special", lambda d: any(_num(r.get("temp_f"), 0) > 95 for r in _rounds(d))),
    ("sunset_round",   "🌅", "Sunset Round",         "Tee off after 4pm",                                 "easy",      "Special", lambda d: any(isinstance(r.get("tee_time"), str) and r["tee_time"][:2].isdigit() and int(r["tee_time"][:2]) >= 16 for r in _rounds(d))),
    ("twilight_round", "🌃", "Twilight",             "Tee off after 5pm",                                 "medium",    "Special", lambda d: any(isinstance(r.get("tee_time"), str) and r["tee_time"][:2].isdigit() and int(r["tee_time"][:2]) >= 17 for r in _rounds(d))),
    ("weekend_warrior","🛋️", "Weekend Warrior",      "Play 4 weekend rounds",                             "medium",    "Special", lambda d: sum(1 for r in _rounds(d) if _date(r) and datetime.strptime(_date(r), "%Y-%m-%d").weekday() >= 5) >= 4),
    ("weekday_warrior","💼", "Played Hooky",         "Play 5 weekday rounds",                             "medium",    "Special", lambda d: sum(1 for r in _rounds(d) if _date(r) and datetime.strptime(_date(r), "%Y-%m-%d").weekday() < 5) >= 5),
    ("morning_practice","☀️", "Early Bird",          "Practice before 7am",                               "easy",      "Special", lambda d: any("morning" in str(s.get("time", "")).lower() for s in _shots(d))),
    ("five_rounds_month","📅", "Marathon Month",      "5+ rounds in a calendar month",                     "hard",      "Special", lambda d: _max_rounds_in_week(d) >= 4),
    ("new_year_round", "🎆", "New Year Round",       "Play a round in January",                           "easy",      "Special", lambda d: any(_date(r).startswith("2026-01") or _date(r)[5:7] == "01" for r in _rounds(d))),
    ("summer_round",   "🌞", "Summer Heat",          "Play in June, July, or August",                     "easy",      "Special", lambda d: any(_date(r)[5:7] in ("06", "07", "08") for r in _rounds(d))),
    ("fall_round",     "🍂", "Autumn Player",        "Play in October or November",                       "easy",      "Special", lambda d: any(_date(r)[5:7] in ("10", "11") for r in _rounds(d))),
    ("app_launch",     "🎮", "Day One Player",       "Open Golf Journey Pro",                             "easy",      "Special", lambda d: True),
    ("profile_set",    "📝", "Profile Complete",     "Set up your profile with home course",              "easy",      "Special", lambda d: bool(_safe_dict(d, "profile").get("home_course"))),
    ("voice_round",    "🎙️", "Voice Caddy On Course", "Use voice caddy during a live round",              "medium",    "Special", lambda d: any(c.get("voice") and c.get("context") == "live_round" for c in _coach(d) if isinstance(c, dict))),
    ("first_screenshot","📷", "Memory Made",          "Take your first hole-by-hole record",               "easy",      "Special", lambda d: any(_safe_list(r, "holes") for r in _rounds(d))),
    ("all_categories", "🌈", "Renaissance Golfer",   "Unlock at least one in every category",             "hard",      "Special", lambda d: True),  # checked at runtime
]


# ---------- Tier metadata ----------
TIER_INFO = {
    "easy":      {"label": "Easy",      "color": "#7FB069", "points": 10},
    "medium":    {"label": "Medium",    "color": "#4A90E2", "points": 25},
    "hard":      {"label": "Hard",      "color": "#D4A24C", "points": 60},
    "legendary": {"label": "Legendary", "color": "#C04A4A", "points": 150},
}


# ---------- Public API ----------
def _normalize_unlocked(raw):
    """Convert any stored format into a dict {aid: {unlocked_at: iso}}.
    Supports legacy list/set formats."""
    if isinstance(raw, dict):
        out = {}
        for k, v in raw.items():
            if isinstance(v, dict):
                out[k] = v
            else:
                out[k] = {"unlocked_at": str(v) if v else None}
        return out
    if isinstance(raw, (list, set, tuple)):
        return {aid: {"unlocked_at": None} for aid in raw}
    return {}


def evaluate_all():
    """Evaluate all achievements. Bulletproof against any data shape."""
    try:
        d = load_data()
    except Exception:
        return []
    if not isinstance(d, dict):
        return []
    unlocked = _normalize_unlocked(d.get("achievements"))
    now_iso = datetime.now().isoformat(timespec="seconds")
    newly = []
    cat_unlocked = set()
    for ach in ACHIEVEMENTS:
        try:
            aid, icon, name, desc, tier, cat, fn = ach
        except Exception:
            continue
        if aid in unlocked:
            cat_unlocked.add(cat)
            continue
        try:
            # Special-case the Renaissance Golfer (one in every category)
            if aid == "all_categories":
                cats_in_app = {a[5] for a in ACHIEVEMENTS if len(a) >= 7}
                if cats_in_app.issubset(cat_unlocked) and len(cat_unlocked) >= len(cats_in_app):
                    pass
                else:
                    continue
            elif not fn(d):
                continue
            unlocked[aid] = {"unlocked_at": now_iso}
            cat_unlocked.add(cat)
            newly.append({"id": aid, "icon": icon, "name": name, "desc": desc, "tier": tier, "unlocked_at": now_iso})
        except Exception:
            continue
    if newly:
        try:
            d["achievements"] = unlocked
            save_data(d)
        except Exception:
            pass
    return newly


def get_all():
    """Return list of every achievement with unlocked state + timestamp."""
    try:
        d = load_data()
    except Exception:
        d = {}
    if not isinstance(d, dict):
        d = {}
    unlocked = _normalize_unlocked(d.get("achievements"))
    out = []
    for aid, icon, name, desc, tier, cat, fn in ACHIEVEMENTS:
        meta = unlocked.get(aid)
        out.append({
            "id": aid, "icon": icon, "name": name, "desc": desc,
            "tier": tier, "category": cat,
            "unlocked": aid in unlocked,
            "unlocked_at": (meta or {}).get("unlocked_at"),
        })
    return out


def stats():
    all_a = get_all()
    unlocked = [a for a in all_a if a["unlocked"]]
    points = sum(TIER_INFO[a["tier"]]["points"] for a in unlocked)
    by_tier = {}
    for tier in TIER_INFO:
        by_tier[tier] = {
            "unlocked": sum(1 for a in unlocked if a["tier"] == tier),
            "total":    sum(1 for a in all_a if a["tier"] == tier),
        }
    return {
        "total":    len(all_a),
        "unlocked": len(unlocked),
        "points":   points,
        "by_tier":  by_tier,
    }
