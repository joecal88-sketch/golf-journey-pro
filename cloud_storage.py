"""Local persistent storage for Golf Journey Pro v4.0."""
import json
import os
from datetime import datetime, date

DATA_FILE = "golf_data.json"

DEFAULT_DATA = {
    "profile": {
        "name": "Joel C.",
        "ghin": 31.3,
        "home_courses": ["El Cariso", "Scholl Canyon", "Van Nuys Par 3"],
        "goals": {
            "break_80": {"label": "Break 80 Consistently", "target": 80, "current_avg": 79.8},
            "driver_300": {"label": "300-Yard Driver", "target": 300, "current": 270},
            "handicap_20": {"label": "Reach 20 Handicap", "target": 20, "current": 31.3},
        },
    },
    "rounds": [],
    "practice": [],
    "speed": [],
    "notes": [],
    "achievements": [],
    "challenges": [],
    "settings": {
        "gemini_key": "AIzaSyD2osEMCaQagKBaPZqfq_jMDU-cS4HCjCw",
        "weight_unit": "yds",
    },
}


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                d = json.load(f)
            # Ensure all top-level keys exist
            for k, v in DEFAULT_DATA.items():
                if k not in d:
                    d[k] = v
            # Ensure baked-in Gemini key is present (heal old saves)
            if not d.get("settings", {}).get("gemini_key"):
                d.setdefault("settings", {})["gemini_key"] = DEFAULT_DATA["settings"]["gemini_key"]
                save_data(d)
            return d
        except Exception:
            pass
    save_data(DEFAULT_DATA)
    return DEFAULT_DATA.copy()


def save_data(data: dict) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def append_round(row: dict) -> None:
    data = load_data()
    row.setdefault("logged_at", str(datetime.now()))
    data["rounds"].append(row)
    save_data(data)


def append_practice(rows) -> None:
    data = load_data()
    if isinstance(rows, list):
        data["practice"].extend(rows)
    else:
        data["practice"].append(rows)
    save_data(data)


def append_speed(row: dict) -> None:
    data = load_data()
    row.setdefault("date", str(date.today()))
    data["speed"].append(row)
    save_data(data)


def append_note(text: str, kind: str = "general") -> None:
    data = load_data()
    data["notes"].append(
        {"text": text, "kind": kind, "date": str(datetime.now())}
    )
    save_data(data)


def update_settings(updates: dict) -> None:
    data = load_data()
    data["settings"].update(updates)
    save_data(data)


def add_achievement(key: str, label: str) -> bool:
    """Returns True if newly added (was not already unlocked)."""
    data = load_data()
    existing = {a["key"] for a in data.get("achievements", [])}
    if key in existing:
        return False
    data["achievements"].append(
        {"key": key, "label": label, "date": str(datetime.now())}
    )
    save_data(data)
    return True


def seed_demo_if_empty() -> None:
    """Seed Joel's profile data so the app feels alive on first launch."""
    data = load_data()
    if data.get("rounds") or data.get("practice") or data.get("speed"):
        return  # already has data

    # Seed rounds
    sample_rounds = [
        {"date": "2026-03-10", "course": "Scholl Canyon", "rating": 64.5, "slope": 108, "par": 60, "score": 71, "putts": 32, "gir": 4, "fir": 5, "notes": "Solid front nine"},
        {"date": "2026-03-18", "course": "El Cariso",     "rating": 68.8, "slope": 119, "par": 70, "score": 88, "putts": 34, "gir": 3, "fir": 6, "notes": "Drives off line"},
        {"date": "2026-03-25", "course": "El Cariso",     "rating": 68.8, "slope": 119, "par": 70, "score": 79, "putts": 31, "gir": 6, "fir": 7, "notes": "Best round in months"},
        {"date": "2026-04-02", "course": "Van Nuys Par 3","rating": 54.0, "slope": 90,  "par": 54, "score": 67, "putts": 28, "gir": 8, "fir": 0, "notes": "Wedges dialed"},
        {"date": "2026-04-09", "course": "Scholl Canyon", "rating": 64.5, "slope": 108, "par": 60, "score": 75, "putts": 33, "gir": 5, "fir": 4, "notes": "Lag putting needs work"},
        {"date": "2026-04-16", "course": "El Cariso",     "rating": 68.8, "slope": 119, "par": 70, "score": 84, "putts": 32, "gir": 4, "fir": 5, "notes": "Two-way miss off tee"},
        {"date": "2026-04-23", "course": "El Cariso",     "rating": 68.8, "slope": 119, "par": 70, "score": 79, "putts": 30, "gir": 7, "fir": 7, "notes": "Stack speed paying off"},
    ]
    for r in sample_rounds:
        r["logged_at"] = r["date"]
    data["rounds"] = sample_rounds

    # Seed speed sessions
    sample_speed = [
        {"date": "2026-03-15", "protocol": "Foundation L1", "green_speed": 102, "blue_speed": 96,  "yellow_speed": 91,  "red_speed": 86, "purple_speed": 80, "driver_speed": 92},
        {"date": "2026-03-22", "protocol": "Foundation L1", "green_speed": 103, "blue_speed": 97,  "yellow_speed": 92,  "red_speed": 87, "purple_speed": 81, "driver_speed": 93},
        {"date": "2026-03-29", "protocol": "Foundation L1", "green_speed": 104, "blue_speed": 98,  "yellow_speed": 93,  "red_speed": 88, "purple_speed": 82, "driver_speed": 94},
        {"date": "2026-04-05", "protocol": "Build L2",       "green_speed": 105, "blue_speed": 99,  "yellow_speed": 94,  "red_speed": 89, "purple_speed": 83, "driver_speed": 95},
        {"date": "2026-04-12", "protocol": "Build L2",       "green_speed": 106, "blue_speed": 100, "yellow_speed": 95,  "red_speed": 89, "purple_speed": 84, "driver_speed": 96},
        {"date": "2026-04-19", "protocol": "Build L2",       "green_speed": 107, "blue_speed": 100, "yellow_speed": 95,  "red_speed": 90, "purple_speed": 84, "driver_speed": 97},
    ]
    data["speed"] = sample_speed

    # Seed practice shots (Rapsodo-style)
    base = {"D": 221, "3W": 195, "5W": 185, "5H": 175, "7i": 155, "9i": 130, "PW": 110, "GW": 95, "SW": 80, "LW": 60}
    practice = []
    import random
    random.seed(42)
    for club, avg in base.items():
        for _ in range(8):
            practice.append({
                "date": "2026-04-20",
                "club": club,
                "carry": round(random.gauss(avg, avg * 0.05), 1),
                "ball_speed": round(random.gauss(100 + avg / 4, 4), 1),
                "club_speed": round(random.gauss(70 + avg / 8, 3), 1),
                "apex": round(random.gauss(60, 8), 1),
                "side": round(random.gauss(-2 if club != "D" else -4, max(avg * 0.04, 3)), 1),
                "notes": "",
            })
    data["practice"] = practice

    save_data(data)
