"""Local rule-based caddy intelligence.

Used as primary brain when Gemini is rate-limited. Fast, deterministic,
no API quota burn. Knows Joel's bag and typical carries.
"""
from cloud_storage import load_data

# Joel's bag with realistic carry distances (yards) — derived from MLM2PRO ranges
DEFAULT_CARRIES = {
    "Driver": 245,
    "3W": 215,
    "5H": 195,
    "5i": 175,
    "6i": 165,
    "7i": 156,
    "8i": 145,
    "9i": 135,
    "PW": 120,
    "GW": 105,
    "SW": 85,
    "LW": 65,
    "Putter": 0,
}

# Club shape tendencies (rough rules of thumb)
CLUB_SHAPES = {
    "Driver": "lowest spin, longest carry, highest dispersion",
    "3W": "long off the tee or off the deck on a flat lie",
    "5H": "easier to launch than a long iron, great on uneven lies",
    "5i": "long iron — needs clean contact",
    "6i": "mid iron, moderate trajectory",
    "7i": "your scoring iron — most reliable",
    "8i": "high mid iron, easy to spin",
    "9i": "approach iron — full swing carries 135",
    "PW": "full pitch club for 110-125y",
    "GW": "gap wedge — fills the 100-110 hole",
    "SW": "sand wedge — bunkers and 80y full",
    "LW": "lob wedge for short flop / tight pins",
}


def get_user_carries() -> dict:
    """Pull actual carries from logged practice shots if available; else defaults."""
    try:
        d = load_data() or {}
        shots = d.get("practice_shots") or []
        if not shots:
            return dict(DEFAULT_CARRIES)
        by_club = {}
        for s in shots:
            club = s.get("club")
            carry = s.get("carry")
            if club and isinstance(carry, (int, float)) and carry > 0:
                by_club.setdefault(club, []).append(float(carry))
        carries = dict(DEFAULT_CARRIES)
        for club, vals in by_club.items():
            if len(vals) >= 3:  # need decent sample
                carries[club] = round(sum(vals) / len(vals))
        return carries
    except Exception:
        return dict(DEFAULT_CARRIES)


def _wind_dir_to_label(wind_dir) -> str:
    """Convert numeric degrees or string into a coarse compass label."""
    if wind_dir is None or wind_dir == "":
        return ""
    if isinstance(wind_dir, (int, float)):
        deg = float(wind_dir) % 360
        if deg < 22.5 or deg >= 337.5:
            return "N"
        if deg < 67.5: return "NE"
        if deg < 112.5: return "E"
        if deg < 157.5: return "SE"
        if deg < 202.5: return "S"
        if deg < 247.5: return "SW"
        if deg < 292.5: return "W"
        return "NW"
    return str(wind_dir)


def wind_adjustment_yards(distance: int, wind_mph: float, wind_dir="") -> tuple:
    """Returns (adjusted_distance, explanation). Accepts wind_dir as str OR degrees (int/float)."""
    try:
        wind_mph = float(wind_mph or 0)
    except (TypeError, ValueError):
        wind_mph = 0.0
    if wind_mph <= 3:
        return distance, "Calm — play the number."
    # Crude wind rule: 1% per mph headwind, 0.5% per mph tail, half effect on cross
    wind_dir_label = _wind_dir_to_label(wind_dir).upper()
    is_into = any(d in wind_dir_label for d in ["INTO", "HEAD", "N", "NE", "NW"])  # heuristic
    is_with = any(d in wind_dir_label for d in ["TAIL", "WITH", "S", "SE", "SW"])
    if is_into:
        adj = round(distance * (1 + wind_mph * 0.01))
        return adj, f"Into {wind_mph} mph — play {adj}y (+{adj - distance})."
    if is_with:
        adj = round(distance * (1 - wind_mph * 0.005))
        return adj, f"Helping {wind_mph} mph — play {adj}y ({adj - distance:+}y)."
    return distance, f"Cross-wind {wind_mph} mph — aim {1 + int(wind_mph/4)} ball into wind."


def recommend_club(distance: int, lie: str = "fairway", wind_mph: float = 0, wind_dir: str = "") -> dict:
    """Pick the right club for a target distance.

    Returns dict with: club, confidence, reason, adjusted_distance, alternatives
    """
    carries = get_user_carries()
    adj_dist, wind_note = wind_adjustment_yards(distance, wind_mph, wind_dir)

    # Lie penalty
    lie = (lie or "").lower()
    lie_factor = 1.0
    lie_note = ""
    if "rough" in lie:
        lie_factor = 1.05  # play 1 club up
        lie_note = "Rough — take one more club, expect flyer or short."
    elif "bunker" in lie or "sand" in lie:
        lie_factor = 1.10
        lie_note = "Bunker — open face, hit the sand 2\" behind."
    elif "uphill" in lie:
        lie_factor = 1.07
        lie_note = "Uphill — ball flies higher and shorter."
    elif "downhill" in lie:
        lie_factor = 0.93
        lie_note = "Downhill — ball flies lower and longer."

    target = adj_dist * lie_factor

    # Sort clubs by carry, find closest
    candidates = [(club, carry) for club, carry in carries.items() if carry > 0]
    candidates.sort(key=lambda x: x[1])
    best = None
    for club, carry in candidates:
        if carry >= target:
            best = (club, carry)
            break
    if not best:
        best = candidates[-1]  # longest club

    club, carry = best
    diff = carry - target
    if abs(diff) <= 3:
        confidence = "Perfect"
    elif abs(diff) <= 8:
        confidence = "Comfortable"
    else:
        confidence = "Stretch"

    # Alternatives: clubs ±1
    idx = next((i for i, (c, _) in enumerate(candidates) if c == club), 0)
    alts = []
    if idx > 0:
        c2, y2 = candidates[idx - 1]
        alts.append(f"{c2} — full swing ({y2}y)")
    if idx < len(candidates) - 1:
        c3, y3 = candidates[idx + 1]
        alts.append(f"{c3} — easy 3/4 swing ({y3}y)")

    parts = []
    parts.append(f"**{club}** — {confidence} number for {distance}y.")
    parts.append(f"Your typical {club} carries {carry}y.")
    if wind_note and wind_mph > 3:
        parts.append(wind_note)
    if lie_note:
        parts.append(lie_note)
    if alts:
        parts.append("Alternatives: " + " · ".join(alts))

    return {
        "club": club,
        "confidence": confidence,
        "adjusted_distance": adj_dist,
        "carry": carry,
        "reason": "\n\n".join(parts),
        "alternatives": alts,
    }


def answer_caddy_question(question: str, hole_info: dict = None, weather: dict = None) -> str:
    """Rule-based answers to common caddy questions. Returns markdown string."""
    q = (question or "").lower()
    hole_info = hole_info or {}
    weather = weather or {}
    distance = hole_info.get("distance") or hole_info.get("yardage") or 150
    par = hole_info.get("par", 4)
    wind_mph = float(weather.get("wind_mph", 0) or 0)
    wind_dir = weather.get("wind_dir", "")

    # Club recommendation
    if any(s in q for s in ["what club", "which club", "club here", "club for"]):
        rec = recommend_club(distance, wind_mph=wind_mph, wind_dir=wind_dir)
        return rec["reason"]

    # Distance / wind question
    if "wind" in q or "distance" in q or "play" in q:
        adj, note = wind_adjustment_yards(distance, wind_mph, wind_dir)
        return f"**{distance}y** to the pin. {note}\n\nPlay it as a **{adj}y** shot."

    # Strategy
    if "tee" in q or "off the tee" in q or "driver" in q:
        if par == 3:
            rec = recommend_club(distance, wind_mph=wind_mph, wind_dir=wind_dir)
            return f"Par 3, {distance}y — go with **{rec['club']}**.\n\n{rec['reason']}"
        if par == 5 and distance <= 480:
            return "Par 5 — driver is usually correct. If you're spraying it, hit 3W for the fairway and trust your wedge game on the third shot."
        if par == 4 and distance <= 320:
            return "Short par 4 — consider 3W or hybrid off the tee to leave a full wedge in. Avoid the half-shot you'll get with driver."
        return "Driver if the fairway is wide. If trouble lurks, take 3W or hybrid for fairway-first."

    # Layup
    if "layup" in q or "lay up" in q:
        return "Find your favorite full-swing wedge yardage (usually 100y for PW). Lay up to that number — full swings beat half-shots every time."

    # Bunker
    if "bunker" in q or "sand" in q:
        return "Open the SW face, dig your feet in for stability, hit ~2 inches behind the ball, accelerate through. Sand wedge with full follow-through."

    # Putting
    if "putt" in q or "green" in q:
        return "Read the slope from low side. Pace > line on long putts. Trust the read and roll it."

    # Default — give generic course-management advice
    rec = recommend_club(distance, wind_mph=wind_mph, wind_dir=wind_dir)
    return f"**{distance}y to pin.** {rec['reason']}"
