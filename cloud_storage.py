"""Local persistent storage for Golf Journey Pro v5.0."""
import json
import os
from datetime import datetime, date
import random

DATA_FILE = "golf_data.json"

DEFAULT_DATA = {
    "profile": {
        "name": "Joel C.",
        "ghin": 31.3,
        "home_course": "El Cariso",
        "home_courses": ["El Cariso", "Scholl Canyon", "Van Nuys Par 3"],
        "goals": {
            "break_80": {"label": "Break 80 Consistently", "target": 80, "current_avg": 79.8},
            "driver_300": {"label": "300-Yard Driver", "target": 300, "current": 270},
            "handicap_20": {"label": "Reach 20 Handicap", "target": 20, "current": 31.3},
        },
    },
    "rounds": [],
    "practice_shots": [],
    "coach_history": [],
    "ai_drills": [],
    "course_aim_points": {},  # {"El Cariso/hole_3": {"lat": x, "lon": y, "yards_to_pin": 145}}
    "metrics": {"dispersion_index": 0},
    "achievements": [],
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
            # Ensure all top-level keys exist (heal old saves)
            for k, v in DEFAULT_DATA.items():
                if k not in d:
                    d[k] = v if not isinstance(v, (list, dict)) else (v.copy() if isinstance(v, dict) else list(v))
            if not d.get("settings", {}).get("gemini_key"):
                d.setdefault("settings", {})["gemini_key"] = DEFAULT_DATA["settings"]["gemini_key"]
                save_data(d)
            return d
        except Exception:
            pass
    save_data(DEFAULT_DATA)
    return _deep_copy(DEFAULT_DATA)


def _deep_copy(obj):
    return json.loads(json.dumps(obj, default=str))


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
        data["practice_shots"].extend(rows)
    else:
        data["practice_shots"].append(rows)
    save_data(data)


def append_coach(entry: dict) -> None:
    data = load_data()
    entry.setdefault("date", str(datetime.now()))
    data["coach_history"].append(entry)
    save_data(data)


def append_ai_drill(entry: dict) -> None:
    data = load_data()
    entry.setdefault("date", str(datetime.now()))
    data["ai_drills"].append(entry)
    save_data(data)


def update_settings(updates: dict) -> None:
    data = load_data()
    data["settings"].update(updates)
    save_data(data)


def update_metric(key: str, value) -> None:
    data = load_data()
    data.setdefault("metrics", {})[key] = value
    save_data(data)


def save_aim_point(course: str, hole: int, lat: float, lon: float, yards_to_pin: int) -> None:
    data = load_data()
    key = f"{course}/hole_{hole}"
    data.setdefault("course_aim_points", {})[key] = {
        "lat": lat, "lon": lon, "yards_to_pin": yards_to_pin,
    }
    save_data(data)


def get_aim_point(course: str, hole: int):
    data = load_data()
    return data.get("course_aim_points", {}).get(f"{course}/hole_{hole}")


def seed_demo_if_empty() -> None:
    """Seed Joel's profile with realistic data so app feels alive."""
    data = load_data()
    if data.get("rounds") or data.get("practice_shots"):
        return

    # Realistic round seeding with hole-by-hole detail
    el_cariso_pars = [4, 4, 3, 5, 4, 4, 3, 4, 5, 4, 4, 3, 4, 5, 4, 3, 4, 4]  # par 71-ish
    scholl_pars = [4, 3, 4, 3, 4, 3, 3, 3, 4]  # 9-hole par 60-ish exec
    par3_pars = [3] * 9

    def gen_holes(pars, score, hcp_factor):
        """Distribute over/under-par across holes realistically."""
        n = len(pars)
        target = score - sum(pars)  # net over par to spread
        out = []
        random.seed(hash(str(pars) + str(score)) & 0xFFFFFFFF)
        # Probabilities by hole difficulty
        for p in pars:
            # 30% par, 50% bogey, 15% double, 5% birdie for a 30+ handicap
            r = random.random()
            if r < 0.10: bonus = -1  # birdie
            elif r < 0.40: bonus = 0  # par
            elif r < 0.75: bonus = 1  # bogey
            elif r < 0.92: bonus = 2  # double
            else: bonus = 3
            out.append({"num": len(out) + 1, "par": p, "score": p + bonus})
        # Adjust to hit target score
        diff = score - sum(h["score"] for h in out)
        i = 0
        while diff != 0 and i < 50:
            idx = random.randint(0, n - 1)
            if diff > 0 and out[idx]["score"] < out[idx]["par"] + 4:
                out[idx]["score"] += 1
                diff -= 1
            elif diff < 0 and out[idx]["score"] > max(2, out[idx]["par"] - 1):
                out[idx]["score"] -= 1
                diff += 1
            i += 1
        return out

    sample_rounds = [
        {"date": "2026-02-08", "course": "El Cariso", "par": 71, "score": 93, "putts": 36, "gir": 2, "fir": 4},
        {"date": "2026-02-22", "course": "El Cariso", "par": 71, "score": 88, "putts": 34, "gir": 3, "fir": 5},
        {"date": "2026-03-08", "course": "Scholl Canyon", "par": 60, "score": 71, "putts": 32, "gir": 4, "fir": 5, "pars": scholl_pars*0+scholl_pars+[4,3,4,3,4,3,3,3,4]},  # 18-hole
        {"date": "2026-03-15", "course": "Van Nuys Par 3", "par": 27, "score": 33, "putts": 18, "gir": 5, "fir": 0, "is_9_hole": True, "pars": par3_pars},
        {"date": "2026-03-22", "course": "El Cariso", "par": 71, "score": 86, "putts": 33, "gir": 4, "fir": 6},
        {"date": "2026-04-02", "course": "El Cariso", "par": 71, "score": 84, "putts": 32, "gir": 5, "fir": 7},
        {"date": "2026-04-09", "course": "Scholl Canyon", "par": 60, "score": 70, "putts": 31, "gir": 5, "fir": 4},
        {"date": "2026-04-16", "course": "El Cariso", "par": 71, "score": 81, "putts": 30, "gir": 6, "fir": 7},
        {"date": "2026-04-23", "course": "El Cariso", "par": 71, "score": 79, "putts": 30, "gir": 7, "fir": 7, "notes": "Stack speed paying off"},
    ]
    for r in sample_rounds:
        if "El Cariso" in r["course"]:
            r["holes"] = gen_holes(el_cariso_pars, r["score"], r["score"])
        elif "Scholl" in r["course"]:
            pars18 = scholl_pars + [4, 3, 4, 3, 4, 3, 3, 3, 4]
            r["holes"] = gen_holes(pars18, r["score"], r["score"])
        elif "Van Nuys" in r["course"]:
            r["holes"] = gen_holes(par3_pars, r["score"], r["score"])
        r["logged_at"] = r["date"]
    data["rounds"] = sample_rounds

    # Practice shots — full bag with realistic carry/dispersion
    base = {
        "Driver": (240, 14, -8, 18),  # avg, std_dev, mean_offline, offline_std
        "3W":     (215, 11, -4, 14),
        "5H":     (195, 10, -2, 12),
        "5i":     (178, 9, -2, 11),
        "6i":     (167, 8, -1, 10),
        "7i":     (155, 7, 8, 12),    # right-leaning miss (matches insight)
        "8i":     (142, 6, 5, 10),
        "9i":     (130, 6, 3, 9),
        "PW":     (110, 5, 0, 7),
        "GW":     (95, 4, 0, 6),
        "SW":     (80, 4, 0, 6),
        "LW":     (65, 3, 0, 5),
    }
    practice = []
    random.seed(42)
    dates = ["2026-04-15", "2026-04-18", "2026-04-22", "2026-04-25", "2026-04-28"]
    for d in dates:
        for club, (avg, sd, off_m, off_sd) in base.items():
            n = random.randint(4, 8)
            for _ in range(n):
                carry = round(random.gauss(avg, sd), 1)
                offline = round(random.gauss(off_m, off_sd), 1)
                practice.append({
                    "date": d,
                    "club": club,
                    "carry": carry,
                    "offline_y": offline,
                    "ball_speed": round(carry / 1.6 + random.gauss(0, 2), 1),
                    "club_speed": round(carry / 2.4 + random.gauss(0, 1.5), 1),
                    "apex_ft": round(random.gauss(min(95, avg * 0.4), 8), 1),
                })
    data["practice_shots"] = practice
    data["metrics"] = {"dispersion_index": 58}

    save_data(data)
