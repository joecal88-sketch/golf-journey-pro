"""Achievement system — unlocks based on Joel's data."""
from cloud_storage import load_data, add_achievement


ACHIEVEMENTS = [
    {"key": "first_round",   "label": "First Round Logged",       "icon": "🏌️", "desc": "Log your first round."},
    {"key": "sub_85",        "label": "First Sub-85",             "icon": "✨", "desc": "Score under 85 on a regulation course."},
    {"key": "sub_80",        "label": "First Sub-80",             "icon": "🏆", "desc": "Score under 80 on a regulation course."},
    {"key": "sub_75",        "label": "Sub-75 Club",              "icon": "👑", "desc": "Score under 75."},
    {"key": "drive_240",     "label": "240+ Driver",              "icon": "💥", "desc": "Carry a drive 240 yards."},
    {"key": "drive_270",     "label": "270+ Driver",              "icon": "🚀", "desc": "Carry a drive 270 yards."},
    {"key": "drive_300",     "label": "300-Yard Club",            "icon": "💎", "desc": "Carry a drive 300 yards."},
    {"key": "speed_100",     "label": "100 mph Driver",           "icon": "⚡", "desc": "Reach 100 mph driver swing speed."},
    {"key": "speed_110",     "label": "110 mph Club",             "icon": "🔥", "desc": "Reach 110 mph driver swing speed."},
    {"key": "streak_3",      "label": "3-Day Streak",             "icon": "🔥", "desc": "Practice 3 days in a row."},
    {"key": "streak_7",      "label": "7-Day Streak",             "icon": "🔥", "desc": "Practice 7 days in a row."},
    {"key": "streak_30",     "label": "30-Day Streak",            "icon": "🌟", "desc": "Practice 30 days in a row."},
    {"key": "stack_10",      "label": "10 Stack Sessions",        "icon": "📚", "desc": "Complete 10 Stack sessions."},
    {"key": "rounds_10",     "label": "10 Rounds Logged",         "icon": "📋", "desc": "Log 10 rounds of golf."},
    {"key": "rounds_50",     "label": "50 Rounds Logged",         "icon": "📜", "desc": "Log 50 rounds of golf."},
    {"key": "gir_8",         "label": "8 GIR in a Round",         "icon": "🎯", "desc": "Hit 8 greens in regulation."},
    {"key": "putts_28",      "label": "28 or Fewer Putts",        "icon": "🎯", "desc": "Have 28 or fewer putts in a round."},
]


def evaluate_all() -> list:
    """Run all unlock checks. Returns list of newly unlocked achievement keys."""
    data = load_data()
    rounds = data.get("rounds", [])
    speed = data.get("speed", [])
    practice = data.get("practice", [])
    newly = []

    def _unlock(key, label):
        if add_achievement(key, label):
            newly.append(key)

    # Rounds
    if rounds:
        _unlock("first_round", "First Round Logged")
        if len(rounds) >= 10:
            _unlock("rounds_10", "10 Rounds Logged")
        if len(rounds) >= 50:
            _unlock("rounds_50", "50 Rounds Logged")

        for r in rounds:
            try:
                score = float(r.get("score", 999))
                par = float(r.get("par", 70))
                putts = float(r.get("putts", 999))
                gir = float(r.get("gir", 0))
            except Exception:
                continue
            if par >= 65:
                if score < 85: _unlock("sub_85", "First Sub-85")
                if score < 80: _unlock("sub_80", "First Sub-80")
                if score < 75: _unlock("sub_75", "Sub-75 Club")
            if gir >= 8: _unlock("gir_8", "8 GIR in a Round")
            if putts <= 28: _unlock("putts_28", "28 or Fewer Putts")

    # Speed
    if speed:
        if len(speed) >= 10: _unlock("stack_10", "10 Stack Sessions")
        for s in speed:
            try:
                sp = float(s.get("driver_speed", 0))
                if sp >= 100: _unlock("speed_100", "100 mph Driver")
                if sp >= 110: _unlock("speed_110", "110 mph Club")
            except Exception:
                continue

    # Driver carry
    for p in practice:
        if p.get("club") == "D":
            try:
                c = float(p.get("carry", 0))
                if c >= 240: _unlock("drive_240", "240+ Driver")
                if c >= 270: _unlock("drive_270", "270+ Driver")
                if c >= 300: _unlock("drive_300", "300-Yard Club")
            except Exception:
                continue

    # Streak
    from insights import practice_streak
    streak = practice_streak()
    if streak >= 3:  _unlock("streak_3", "3-Day Streak")
    if streak >= 7:  _unlock("streak_7", "7-Day Streak")
    if streak >= 30: _unlock("streak_30", "30-Day Streak")

    return newly


def all_with_status() -> list:
    """Return all achievements with locked/unlocked status."""
    data = load_data()
    unlocked = {a["key"] for a in data.get("achievements", [])}
    return [
        {**a, "unlocked": a["key"] in unlocked}
        for a in ACHIEVEMENTS
    ]
