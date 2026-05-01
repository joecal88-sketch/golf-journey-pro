"""AI Caddy — voice-first, Base44-inspired flow.

Design:
1) BIG search bar → look up any golf course on Earth via OpenStreetMap Overpass API
2) Course card shows par/rating/slope (from seed data or Gemini), plus a Tee Off button
3) Per-hole view: weather (Open-Meteo, no key), distance, par, big mic button
4) Mic captures voice → Gemini caddy responds → optional TTS playback
5) Hole-by-hole list to skip around; End Round saves the round
"""
import streamlit as st
import requests
import json
import time
from styles import COLORS
from cloud_storage import load_data, append_round
from gemini_client import chat as gemini_chat, generate_text, GeminiUnavailable, is_available as gemini_available
from caddy_brain import answer_caddy_question, recommend_club


# -------------------- Helpers --------------------
def _osm_search(query: str, limit: int = 8) -> list:
    """Search OpenStreetMap for golf courses. Returns list of {name, lat, lon, address}."""
    if not query or len(query) < 3:
        return []
    try:
        # Nominatim: free, no key. Filter to golf courses.
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": f"{query} golf",
                "format": "json",
                "limit": limit,
                "addressdetails": 1,
            },
            headers={"User-Agent": "GolfJourneyPro/5.2"},
            timeout=8,
        )
        if r.status_code != 200:
            return []
        results = r.json()
        out = []
        for x in results:
            name = x.get("display_name", "").split(",")[0]
            if not name:
                continue
            addr = x.get("address", {}) or {}
            city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("suburb") or ""
            state = addr.get("state", "")
            short = ", ".join(p for p in [city, state] if p)
            out.append({
                "name": name,
                "address": short or x.get("display_name", "")[:80],
                "lat": float(x.get("lat", 0)),
                "lon": float(x.get("lon", 0)),
                "type": x.get("type", ""),
            })
        # De-dupe by (name, city)
        seen = set(); uniq = []
        for r2 in out:
            k = (r2["name"].lower(), r2["address"].lower())
            if k in seen: continue
            seen.add(k); uniq.append(r2)
        return uniq[:limit]
    except Exception:
        return []


def _course_info(course_name: str) -> dict:
    """Look up course rating/slope/par from local seed; otherwise sensible defaults."""
    seed = {
        "El Cariso":      {"par": 62, "rating": 61.1, "slope": 97, "holes": 18, "yardage": 4500},
        "Scholl Canyon":  {"par": 60, "rating": 56.5, "slope": 89, "holes": 18, "yardage": 4100},
        "Van Nuys Par 3": {"par": 27, "rating": 54.5, "slope": 80, "holes": 9,  "yardage": 1500},
    }
    for k, v in seed.items():
        if k.lower() in course_name.lower():
            return v
    return {"par": 72, "rating": 72.0, "slope": 113, "holes": 18, "yardage": 6500}


def _get_weather(lat: float, lon: float) -> dict:
    """Open-Meteo current conditions, no API key required."""
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "current": "temperature_2m,wind_speed_10m,wind_direction_10m,relative_humidity_2m",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
            },
            timeout=6,
        )
        if r.status_code != 200:
            return {}
        cur = r.json().get("current", {})
        return {
            "temp_f": round(cur.get("temperature_2m", 0)),
            "wind_mph": round(cur.get("wind_speed_10m", 0)),
            "wind_dir": int(cur.get("wind_direction_10m", 0)),
            "humidity": int(cur.get("relative_humidity_2m", 0)),
        }
    except Exception:
        return {}


def _wind_arrow(deg: int) -> str:
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int((deg + 22.5) // 45) % 8
    return dirs[idx]


# -------------------- CSS --------------------
def _inject_css():
    # Always re-inject — Streamlit reruns can drop styles, and this CSS
    # must apply on every sub-page render including the course detail view.
    st.markdown(f"""
    <style>
      .caddy-search-card {{
        background: linear-gradient(160deg, rgba(127,176,105,0.10), {COLORS['bg_2']});
        border: 1px solid {COLORS['fairway_2']}50;
        border-radius: 22px;
        padding: 32px 36px;
        margin-bottom: 18px;
        backdrop-filter: blur(14px);
        box-shadow: 0 12px 50px rgba(0,0,0,0.35);
      }}
      .caddy-eyebrow {{
        font-size: 11px; color: {COLORS['flag']};
        letter-spacing: 0.32em; text-transform: uppercase; font-weight: 800;
      }}
      .caddy-headline {{
        font-family: 'Fraunces', serif;
        font-size: 38px; line-height: 1.1; color: {COLORS['cream']};
        margin: 6px 0 4px;
      }}
      .caddy-sub {{ color: {COLORS['cream_dim']}; font-size: 14px; margin-bottom: 14px; }}

      .course-result {{
        background: rgba(255,255,255,0.04);
        border: 1px solid {COLORS['border']};
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 8px;
        display: flex; gap: 14px; align-items: center;
        cursor: pointer;
        transition: all 0.2s ease;
      }}
      .course-result:hover {{
        background: rgba(127,176,105,0.10);
        border-color: {COLORS['fairway_2']}80;
        transform: translateX(4px);
      }}
      .course-result .pin {{ font-size: 24px; }}
      .course-result .meta {{ flex: 1; }}
      .course-result .name {{ font-weight: 700; font-size: 16px; color: {COLORS['cream']}; }}
      .course-result .addr {{ font-size: 12px; color: {COLORS['cream_dim']}; margin-top: 2px; }}

      .selected-course-card {{
        background: linear-gradient(160deg, rgba(212,162,76,0.12), {COLORS['bg_3']});
        border: 1.5px solid {COLORS['flag']}80;
        border-radius: 22px;
        padding: 30px 34px;
        box-shadow: 0 16px 60px rgba(0,0,0,0.4), 0 0 80px {COLORS['flag']}20;
      }}
      .sc-header {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; flex-wrap: wrap; }}
      .sc-name {{ font-family: 'Fraunces', serif; font-size: 32px; color: {COLORS['cream']}; line-height: 1.1; }}
      .sc-addr {{ color: {COLORS['cream_dim']}; font-size: 13px; margin-top: 2px; }}

      .sc-stats {{ display: flex; gap: 12px; margin: 22px 0; flex-wrap: wrap; }}
      .sc-stat {{
        flex: 1; min-width: 110px;
        background: rgba(0,0,0,0.3); padding: 14px 16px;
        border-radius: 12px; border: 1px solid rgba(255,255,255,0.06);
        text-align: center;
      }}
      .sc-stat .label {{ font-size: 10px; letter-spacing: 0.2em; text-transform: uppercase; color: {COLORS['cream_dim']}; font-weight: 700; }}
      .sc-stat .val {{ font-family: 'Fraunces', serif; font-size: 28px; color: {COLORS['cream']}; margin-top: 4px; line-height: 1; }}

      .weather-strip {{
        display: flex; gap: 16px; padding: 12px 16px;
        background: rgba(74,144,226,0.08); border-radius: 12px;
        border: 1px solid rgba(74,144,226,0.25);
        flex-wrap: wrap; margin-bottom: 18px;
      }}
      .weather-strip .w-item {{ display: flex; gap: 6px; align-items: center; font-size: 13px; color: {COLORS['cream']}; }}

      /* Hole view */
      .hole-card {{
        background: linear-gradient(160deg, {COLORS['bg_3']}, {COLORS['bg_2']});
        border: 1px solid {COLORS['border']};
        border-radius: 22px;
        padding: 32px 38px; text-align: center;
      }}
      .hole-num {{
        font-size: 13px; letter-spacing: 0.3em; text-transform: uppercase;
        color: {COLORS['flag']}; font-weight: 800;
      }}
      .hole-big-num {{
        font-family: 'Fraunces', serif; font-size: 96px;
        color: {COLORS['cream']}; line-height: 1; margin: 6px 0 4px;
        text-shadow: 0 6px 24px rgba(212,162,76,0.3);
      }}
      .hole-par {{ font-size: 18px; color: {COLORS['cream_dim']}; }}
      .hole-distance {{
        font-family: 'Fraunces', serif; font-size: 42px;
        color: {COLORS['fairway_2']}; margin-top: 10px;
      }}
      .hole-distance .unit {{ font-size: 16px; color: {COLORS['cream_dim']}; }}

      /* Mic button */
      @keyframes mic-pulse {{
        0% {{ box-shadow: 0 0 0 0 rgba(212,162,76,0.7); }}
        70% {{ box-shadow: 0 0 0 24px rgba(212,162,76,0); }}
        100% {{ box-shadow: 0 0 0 0 rgba(212,162,76,0); }}
      }}
      .mic-button-wrap {{
        display: flex; flex-direction: column; align-items: center;
        gap: 10px; margin: 22px 0;
      }}
      .mic-button {{
        width: 96px; height: 96px; border-radius: 50%;
        background: radial-gradient(circle at 30% 30%, #f3c071, {COLORS['flag']});
        border: 4px solid rgba(255,255,255,0.15);
        display: flex; align-items: center; justify-content: center;
        font-size: 40px; color: #0a0e0c; cursor: pointer;
        animation: mic-pulse 2s infinite;
        box-shadow: 0 14px 40px rgba(212,162,76,0.4);
        transition: transform 0.2s ease;
      }}
      .mic-button:hover {{ transform: scale(1.06); }}
      .mic-label {{ font-size: 12px; color: {COLORS['cream_dim']}; letter-spacing: 0.18em; text-transform: uppercase; font-weight: 700; }}

      /* Caddy chat bubble */
      .caddy-bubble {{
        background: linear-gradient(135deg, rgba(212,162,76,0.16), rgba(127,176,105,0.08));
        border: 1px solid {COLORS['flag']}50;
        border-radius: 18px;
        padding: 18px 22px;
        margin: 14px 0;
        backdrop-filter: blur(10px);
      }}
      .caddy-bubble .label {{
        font-size: 10px; letter-spacing: 0.25em; text-transform: uppercase;
        color: {COLORS['flag']}; font-weight: 800; margin-bottom: 6px;
      }}
      .caddy-bubble .body {{ font-size: 15px; line-height: 1.5; color: {COLORS['cream']}; }}

      .you-bubble {{
        background: rgba(255,255,255,0.04);
        border: 1px solid {COLORS['border']};
        border-radius: 18px;
        padding: 14px 18px;
        margin: 10px 0;
        font-size: 14px; color: {COLORS['cream']};
      }}
      .you-bubble .label {{
        font-size: 10px; letter-spacing: 0.25em; text-transform: uppercase;
        color: {COLORS['cream_dim']}; font-weight: 800; margin-bottom: 4px;
      }}

      /* Premium course detail card additions (v5.3) */
      .sc-flag {{
        font-size: 42px;
        filter: drop-shadow(0 6px 18px rgba(212,162,76,0.45));
        line-height: 1;
        opacity: 0.95;
      }}
      .sc-divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, {COLORS['flag']}55, transparent);
        margin: 18px 0 4px;
      }}

      /* Live conditions weather card */
      .weather-card {{
        margin-top: 16px;
        padding: 22px 28px;
        border-radius: 22px;
        background: linear-gradient(160deg, rgba(74,144,226,0.10), rgba(20,40,60,0.55));
        border: 1px solid rgba(120,180,230,0.22);
        box-shadow: 0 14px 50px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.04);
        backdrop-filter: blur(14px);
      }}
      .wc-eyebrow {{
        font-size: 10px; letter-spacing: 0.36em; text-transform: uppercase;
        color: rgba(180,210,235,0.85); font-weight: 800;
        text-align: center; margin-bottom: 16px;
      }}
      .wc-row {{
        display: flex; gap: 14px; flex-wrap: wrap;
      }}
      .wc-block {{
        flex: 1; min-width: 130px;
        background: rgba(0,0,0,0.28);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 16px 14px;
        text-align: center;
        transition: transform 0.25s ease, border-color 0.25s ease;
      }}
      .wc-block:hover {{
        transform: translateY(-2px);
        border-color: rgba(120,180,230,0.35);
      }}
      .wc-icon {{
        font-size: 24px; line-height: 1; margin-bottom: 8px;
      }}
      .wc-num {{
        font-family: 'Fraunces', serif;
        font-size: 30px; line-height: 1;
        color: {COLORS['cream']}; font-weight: 600;
      }}
      .wc-unit {{
        font-family: 'Fraunces', serif;
        font-size: 14px; color: {COLORS['cream_dim']};
        font-weight: 400; margin-left: 2px;
      }}
      .wc-label {{
        font-size: 10px; letter-spacing: 0.22em; text-transform: uppercase;
        color: {COLORS['cream_dim']}; font-weight: 700;
        margin-top: 8px;
      }}
    </style>
    """, unsafe_allow_html=True)


# -------------------- Caddy AI prompt --------------------
def _caddy_system(course: dict, hole_info: dict, profile: dict, weather: dict) -> str:
    return f"""You are an elite PGA-Tour caddie giving advice to {profile.get('name', 'Joel')} (handicap {profile.get('ghin', 31.3)}).
You're walking the course with him. Be conversational, warm, brief (2-4 sentences max), and confident.

CURRENT CONTEXT:
- Course: {course.get('name', 'unknown')} (par {course.get('par', '?')}, rating {course.get('rating', '?')}/{course.get('slope', '?')})
- Hole: {hole_info.get('num', '?')} (par {hole_info.get('par', '?')}, ~{hole_info.get('distance', '?')} yards)
- Wind: {weather.get('wind_mph', '?')} mph from {_wind_arrow(weather.get('wind_dir', 0))}
- Temp: {weather.get('temp_f', '?')}°F
- Player's bag: Driver (Mizuno ST-Z 230), 3W (Callaway Rogue ST), 5H (Edge), Mizuno JPX925 5i-PW, Kirkland 52/56/60, Spider putter
- Player's typical carry: Driver 240y, 7i 155y (right-leaning miss), wedges 65-110y

Always tip your advice with exactly ONE recommendation: club + target line. Speak in second person ("you"). Don't ramble. Don't add disclaimers."""


# -------------------- Main render --------------------
def render():
    _inject_css()

    data = load_data()
    profile = data.get("profile", {})

    # ── Search header ──
    if not st.session_state.get("caddy_course"):
        _render_search()
        return

    # ── Tee'd off? Render hole view; else course detail ──
    if st.session_state.get("caddy_hole_idx") is None:
        _render_course_detail(profile)
    else:
        _render_hole_view(profile)


# -------------------- Search --------------------
def _render_search():
    st.markdown(f"""
    <div class="caddy-search-card">
      <div class="caddy-eyebrow">⛳ AI CADDY</div>
      <div class="caddy-headline">Where are you playing today?</div>
      <div class="caddy-sub">Search any course on Earth. Your caddy is ready with course knowledge, weather, and shot-by-shot advice.</div>
    </div>
    """, unsafe_allow_html=True)

    # Quick-pick home courses
    st.markdown(f"<div style='font-size:11px;color:{COLORS['cream_dim']};letter-spacing:0.2em;text-transform:uppercase;font-weight:700;margin:6px 0 8px;'>Your home courses</div>", unsafe_allow_html=True)
    qcols = st.columns(3)
    home_courses = [
        ("El Cariso", 34.2719, -118.4814),
        ("Scholl Canyon", 34.1525, -118.2098),
        ("Van Nuys Par 3", 34.2189, -118.4901),
    ]
    for i, (name, lat, lon) in enumerate(home_courses):
        with qcols[i]:
            if st.button(f"⛳ {name}", key=f"home_pick_{i}", use_container_width=True):
                st.session_state["caddy_course"] = {
                    "name": name, "address": "Los Angeles, CA",
                    "lat": lat, "lon": lon,
                    **_course_info(name),
                }
                st.rerun()

    st.markdown(f"<div style='font-size:11px;color:{COLORS['cream_dim']};letter-spacing:0.2em;text-transform:uppercase;font-weight:700;margin:18px 0 8px;'>Or search any course worldwide</div>", unsafe_allow_html=True)
    query = st.text_input(
        "Course search",
        placeholder="Pebble Beach, Augusta, Torrey Pines...",
        label_visibility="collapsed",
        key="caddy_search_q",
    )

    if query and len(query) >= 3:
        with st.spinner("Searching courses worldwide..."):
            results = _osm_search(query)
        if not results:
            st.info("No courses found. Try the full course name.")
            return
        for i, r in enumerate(results):
            cols = st.columns([5, 1])
            with cols[0]:
                st.markdown(f"""
                <div class="course-result">
                  <div class="pin">📍</div>
                  <div class="meta">
                    <div class="name">{r['name']}</div>
                    <div class="addr">{r['address']}</div>
                  </div>
                </div>
                """, unsafe_allow_html=True)
            with cols[1]:
                if st.button("Select →", key=f"sel_{i}", use_container_width=True):
                    st.session_state["caddy_course"] = {**r, **_course_info(r["name"])}
                    st.rerun()


# -------------------- Course detail --------------------
def _render_course_detail(profile):
    _inject_css()  # ensure CSS is present on this sub-page
    course = st.session_state["caddy_course"]

    cols = st.columns([5, 1])
    with cols[1]:
        if st.button("← Back", key="back_to_search", use_container_width=True):
            st.session_state["caddy_course"] = None
            st.rerun()

    with st.spinner("Pulling weather & course info..."):
        weather = _get_weather(course["lat"], course["lon"])

    # Premium course detail card — single-line HTML to avoid Streamlit markdown indent bugs
    course_card = (
        '<div class="selected-course-card">'
        '<div class="sc-header">'
        '<div style="flex:1;">'
        '<div class="caddy-eyebrow">✵ SELECTED COURSE</div>'
        f'<div class="sc-name">{course["name"]}</div>'
        f'<div class="sc-addr">{course.get("address", "")}</div>'
        '</div>'
        f'<div class="sc-flag">⛳</div>'
        '</div>'
        '<div class="sc-divider"></div>'
        '<div class="sc-stats">'
        f'<div class="sc-stat"><div class="label">Par</div><div class="val">{course.get("par", "—")}</div></div>'
        f'<div class="sc-stat"><div class="label">Rating</div><div class="val">{course.get("rating", "—")}</div></div>'
        f'<div class="sc-stat"><div class="label">Slope</div><div class="val">{course.get("slope", "—")}</div></div>'
        f'<div class="sc-stat"><div class="label">Holes</div><div class="val">{course.get("holes", 18)}</div></div>'
        f'<div class="sc-stat"><div class="label">Yardage</div><div class="val">{course.get("yardage", "—")}</div></div>'
        '</div>'
        '</div>'
    )
    st.markdown(course_card, unsafe_allow_html=True)

    if weather:
        wind_dir_str = _wind_arrow(weather.get("wind_dir", 0))
        weather_card = (
            '<div class="weather-card">'
            '<div class="wc-eyebrow">· LIVE CONDITIONS ·</div>'
            '<div class="wc-row">'
            f'<div class="wc-block"><div class="wc-icon">☀️</div><div class="wc-num">{weather.get("temp_f", "—")}<span class="wc-unit">°F</span></div><div class="wc-label">Temp</div></div>'
            f'<div class="wc-block"><div class="wc-icon">🌬️</div><div class="wc-num">{weather.get("wind_mph", "—")}<span class="wc-unit"> mph</span></div><div class="wc-label">Wind from {wind_dir_str}</div></div>'
            f'<div class="wc-block"><div class="wc-icon">💧</div><div class="wc-num">{weather.get("humidity", "—")}<span class="wc-unit">%</span></div><div class="wc-label">Humidity</div></div>'
            '</div>'
            '</div>'
        )
        st.markdown(weather_card, unsafe_allow_html=True)
        st.session_state["caddy_weather"] = weather

    # AI course preview
    if st.button("✨ Ask Gemini for course knowledge", key="ai_course_preview", use_container_width=True):
        with st.spinner("Getting course intel..."):
            try:
                preview = generate_text(
                    f"In 3 sentences, give me strategic notes on {course['name']} golf course "
                    f"({course.get('address','')}). Cover: hardest hole, signature feature, "
                    f"one piece of strategic advice for a {profile.get('ghin', 31.3)} handicap player.",
                )
                st.markdown(f'<div class="caddy-bubble"><div class="label">📚 Course Intel</div><div class="body">{preview}</div></div>', unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Couldn't fetch right now: {e}")

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    if st.button("⛳ TEE OFF", key="tee_off", use_container_width=True, type="primary"):
        st.session_state["caddy_hole_idx"] = 1
        st.session_state["caddy_chat"] = []
        st.session_state["caddy_holes_played"] = []
        st.rerun()


# -------------------- Hole view --------------------
def _render_hole_view(profile):
    course = st.session_state["caddy_course"]
    hole_idx = st.session_state["caddy_hole_idx"]
    weather = st.session_state.get("caddy_weather", {})
    n_holes = course.get("holes", 18)

    # Estimate hole distance & par based on simple defaults
    par = 4
    if course["name"] == "Van Nuys Par 3":
        par = 3
    elif course["name"] == "Scholl Canyon":
        par = 3 if hole_idx in (2, 4, 6, 7, 8) else 4
    distance = 380 if par == 4 else (520 if par == 5 else 145)

    cols = st.columns([1, 3, 1])
    with cols[0]:
        if st.button("← End Round", key="end_round", use_container_width=True):
            _save_round_and_exit(profile)
            return

    # Hole header card
    st.markdown(f"""
    <div class="hole-card">
      <div class="hole-num">{course['name']} · Hole {hole_idx} of {n_holes}</div>
      <div class="hole-big-num">{hole_idx}</div>
      <div class="hole-par">Par {par}</div>
      <div class="hole-distance">{distance}<span class="unit"> yards</span></div>
    </div>
    """, unsafe_allow_html=True)

    # Weather strip
    if weather:
        st.markdown(f"""
        <div class="weather-strip">
          <div class="w-item">🌡️ <b>{weather.get('temp_f', '—')}°F</b></div>
          <div class="w-item">💨 <b>{weather.get('wind_mph', '—')} mph</b> {_wind_arrow(weather.get('wind_dir', 0))}</div>
          <div class="w-item">💧 <b>{weather.get('humidity', '—')}%</b></div>
        </div>
        """, unsafe_allow_html=True)

    # Mic + text input row
    st.markdown(f"""
    <div class="mic-button-wrap">
      <div class="mic-button">🎤</div>
      <div class="mic-label">Ask your caddy</div>
    </div>
    """, unsafe_allow_html=True)

    # Voice + text input — Streamlit can't capture mic directly without extra components,
    # so we offer text + a "voice prompt" presets row.
    preset_prompts = [
        "What club here?",
        "How should I play the wind?",
        "Where's the safe miss?",
        "What's the smart play for my handicap?",
    ]
    pc = st.columns(len(preset_prompts))
    for i, p in enumerate(preset_prompts):
        with pc[i]:
            if st.button(p, key=f"preset_{i}_{hole_idx}", use_container_width=True):
                _ask_caddy(p, profile, course, {"num": hole_idx, "par": par, "distance": distance}, weather)

    user_q = st.text_input(
        "Or type a question for your caddy",
        placeholder="e.g. The pin is back-left, wind is right-to-left, what's my play?",
        key=f"caddy_typed_{hole_idx}",
        label_visibility="collapsed",
    )
    if user_q and st.session_state.get(f"_last_q_{hole_idx}") != user_q:
        st.session_state[f"_last_q_{hole_idx}"] = user_q
        _ask_caddy(user_q, profile, course, {"num": hole_idx, "par": par, "distance": distance}, weather)

    # Chat history
    chat = st.session_state.get("caddy_chat", [])
    for entry in chat[-6:]:
        if entry["role"] == "user":
            st.markdown(f'<div class="you-bubble"><div class="label">You</div>{entry["text"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="caddy-bubble"><div class="label">🎯 Caddy</div><div class="body">{entry["text"]}</div></div>', unsafe_allow_html=True)

    # Score input + nav
    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)
    score_cols = st.columns([2, 1, 1])
    with score_cols[0]:
        score = st.number_input(f"Your score on hole {hole_idx}", min_value=1, max_value=15, value=par, key=f"score_{hole_idx}")
    with score_cols[1]:
        if hole_idx > 1 and st.button("← Prev hole", key=f"prev_{hole_idx}", use_container_width=True):
            st.session_state["caddy_hole_idx"] = hole_idx - 1
            st.rerun()
    with score_cols[2]:
        if st.button("Next hole →", key=f"next_{hole_idx}", use_container_width=True, type="primary"):
            # Persist this hole's score
            holes_played = st.session_state.get("caddy_holes_played", [])
            holes_played = [h for h in holes_played if h["num"] != hole_idx]
            holes_played.append({"num": hole_idx, "par": par, "score": int(score)})
            st.session_state["caddy_holes_played"] = sorted(holes_played, key=lambda h: h["num"])
            if hole_idx >= n_holes:
                _save_round_and_exit(profile)
                return
            st.session_state["caddy_hole_idx"] = hole_idx + 1
            st.rerun()


def _ask_caddy(prompt: str, profile, course, hole_info, weather):
    """Hybrid caddy: offline rule-based brain first (instant, no quota), Gemini for upgrade.

    The local brain is always-on and gives a real answer using the player's bag,
    distance, wind, and lie. If Gemini is available we layer its richer phrasing on top,
    but the user never sees an error — they always get useful advice.
    """
    chat = st.session_state.get("caddy_chat", [])
    chat.append({"role": "user", "text": prompt})

    # 1) ALWAYS compute a local answer first — fast, deterministic, no quota burn
    local_answer = answer_caddy_question(
        prompt,
        hole_info={"distance": hole_info.get("distance"), "par": hole_info.get("par")},
        weather={"wind_mph": weather.get("wind_mph", 0), "wind_dir": _wind_arrow(weather.get("wind_dir", 0))},
    )
    answer = local_answer
    source = "local"

    # 2) Try Gemini for richer voice — but only if quota isn't blocked
    if gemini_available():
        try:
            history = [(c["role"], c["text"]) for c in chat[:-1]]
            history = [("user" if r == "user" else "model", t) for r, t in history]
            with st.spinner("Caddy thinking..."):
                ai_answer = gemini_chat(
                    history=history,
                    user_msg=prompt,
                    system=_caddy_system(course, hole_info, profile, weather),
                )
            if ai_answer and len(ai_answer) > 20:
                answer = ai_answer
                source = "gemini"
        except GeminiUnavailable:
            pass  # silently fall back to local
        except Exception:
            pass

    # Tag local answers so user knows it's the rule-based brain
    if source == "local":
        answer = answer + "\n\n_— Local Caddy Brain_"

    chat.append({"role": "model", "text": answer})
    st.session_state["caddy_chat"] = chat
    st.rerun()


def _save_round_and_exit(profile):
    """Persist the round and reset the caddy state."""
    course = st.session_state.get("caddy_course") or {}
    holes = st.session_state.get("caddy_holes_played") or []
    if holes:
        total = sum(h["score"] for h in holes)
        par_total = sum(h["par"] for h in holes)
        try:
            append_round({
                "date": time.strftime("%Y-%m-%d"),
                "course": course.get("name", "Unknown"),
                "par": par_total,
                "score": total,
                "holes": holes,
                "course_rating": course.get("rating"),
                "slope": course.get("slope"),
                "weather": "live_caddy",
                "wind_mph": (st.session_state.get("caddy_weather") or {}).get("wind_mph"),
                "temp_f": (st.session_state.get("caddy_weather") or {}).get("temp_f"),
            })
            st.success(f"Round saved! {total} on par {par_total} ({total - par_total:+}).")
        except Exception as e:
            st.error(f"Could not save round: {e}")
    # Reset caddy state
    for k in ["caddy_course", "caddy_hole_idx", "caddy_chat", "caddy_holes_played", "caddy_weather"]:
        st.session_state[k] = None if k != "caddy_chat" else []
    time.sleep(1)
    st.rerun()
