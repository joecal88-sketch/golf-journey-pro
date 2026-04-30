"""Live Round — auto-GPS caddy with weather and one-tap club rec."""
import streamlit as st
import streamlit.components.v1 as components
import requests
from datetime import datetime
from cloud_storage import load_data, append_round, save_aim_point, get_aim_point
from styles import COLORS
from insights import suggested_club, plays_like

# Pre-loaded LA-area courses with lat/lon
COURSES = {
    "El Cariso GC": {
        "lat": 34.2947, "lon": -118.4839, "par": 71,
        "pars": [4, 4, 3, 5, 4, 4, 3, 4, 5, 4, 4, 3, 4, 5, 4, 3, 4, 4],
    },
    "Scholl Canyon GC": {
        "lat": 34.1572, "lon": -118.2270, "par": 60,
        "pars": [4, 3, 4, 3, 4, 3, 3, 3, 4, 4, 3, 4, 3, 4, 3, 3, 3, 4],
    },
    "Van Nuys Par 3": {
        "lat": 34.2106, "lon": -118.4811, "par": 27,
        "pars": [3] * 9, "is_9_hole": True,
    },
    "DeBell GC": {
        "lat": 34.2017, "lon": -118.2937, "par": 71,
        "pars": [4, 4, 3, 5, 4, 4, 3, 4, 5, 4, 4, 3, 4, 5, 4, 3, 4, 4],
    },
    "Brookside #1": {
        "lat": 34.1641, "lon": -118.1660, "par": 72,
        "pars": [4, 4, 4, 3, 5, 4, 4, 3, 5, 4, 4, 3, 4, 4, 5, 3, 4, 4],
    },
    "Griffith Wilson": {
        "lat": 34.1473, "lon": -118.2845, "par": 72,
        "pars": [4, 4, 4, 5, 3, 4, 4, 3, 5, 4, 4, 3, 4, 4, 5, 3, 4, 4],
    },
    "Griffith Harding": {
        "lat": 34.1414, "lon": -118.2860, "par": 72,
        "pars": [5, 4, 4, 3, 4, 4, 5, 3, 4, 4, 4, 3, 5, 4, 4, 3, 4, 4],
    },
    "Rancho Park GC": {
        "lat": 34.0420, "lon": -118.4151, "par": 71,
        "pars": [4, 5, 4, 3, 4, 4, 5, 3, 4, 4, 4, 3, 5, 4, 4, 3, 4, 4],
    },
}


@st.cache_data(ttl=900)  # 15-minute cache
def fetch_weather(lat, lon):
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,wind_speed_10m,wind_direction_10m,"
            f"relative_humidity_2m,apparent_temperature,is_day"
            f"&temperature_unit=fahrenheit&wind_speed_unit=mph"
        )
        r = requests.get(url, timeout=4)
        if r.status_code == 200:
            return r.json().get("current", {})
    except Exception:
        return None
    return None


def _gps_button():
    """Inject a GPS button that writes location to a hidden iframe message."""
    components.html(
        """
        <button id="gps-btn" style="
            background: linear-gradient(135deg, #0E5C3A, #137A4D);
            color: #F5EFE0; border: 1px solid #137A4D; border-radius: 12px;
            padding: 14px 22px; font-weight: 700; font-size: 14px;
            cursor: pointer; width: 100%;
            box-shadow: 0 8px 24px rgba(19,122,77,0.35);
            font-family: 'Inter', sans-serif; letter-spacing: 0.02em;
        ">📍 Use My Current Location</button>
        <div id="gps-out" style="margin-top:10px;color:#F5EFE0;font-family:Inter,sans-serif;font-size:12px;"></div>
        <script>
        document.getElementById('gps-btn').onclick = function() {
            const out = document.getElementById('gps-out');
            out.innerText = "Locating…";
            if (!navigator.geolocation) { out.innerText = "GPS not supported in this browser."; return; }
            navigator.geolocation.getCurrentPosition(
                p => {
                    out.innerHTML = "📍 <b>Lat:</b> " + p.coords.latitude.toFixed(5) +
                                    " · <b>Lon:</b> " + p.coords.longitude.toFixed(5) +
                                    "<br><span style='color:#D4A24C;'>Copy → paste below to lock to course.</span>";
                },
                e => { out.innerText = "GPS denied or unavailable."; },
                {enableHighAccuracy: true, timeout: 5000}
            );
        };
        </script>
        """,
        height=110,
    )


def _voice_scorecard(course_name, n_holes):
    """Voice-input scorecard widget."""
    components.html(
        f"""
        <div style="background:{COLORS['bg_3']};border:1px solid {COLORS['border']};border-radius:14px;padding:16px;">
          <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.18em;text-transform:uppercase;font-weight:700;margin-bottom:8px;">🎤 Voice Scorecard</div>
          <button id="voice-mic" style="
              background: linear-gradient(135deg,#0E5C3A,#137A4D);
              color:#F5EFE0;border:none;border-radius:99px;
              padding:12px 22px;font-weight:700;cursor:pointer;
              font-family:Inter,sans-serif;font-size:13px;">
              🎙 Tap to speak scores
          </button>
          <div id="vs-status" style="margin-top:8px;font-size:12px;color:#A8A99F;"></div>
          <div id="vs-text" style="margin-top:10px;padding:10px;background:#0F1B16;border-radius:10px;color:#F5EFE0;font-family:Inter;font-size:13px;min-height:40px;"></div>
          <div style="margin-top:8px;font-size:11px;color:#8A8B83;">Say: "hole 1 four, hole 2 par, hole 3 bogey, hole 4 birdie..."</div>
        </div>
        <script>
        const btn = document.getElementById('voice-mic');
        const status = document.getElementById('vs-status');
        const text = document.getElementById('vs-text');
        btn.onclick = function() {{
            if (!('webkitSpeechRecognition' in window)) {{
                status.innerText = 'Voice not supported in this browser. Use Safari on iPhone or Chrome.'; return;
            }}
            const rec = new webkitSpeechRecognition();
            rec.continuous = true;
            rec.interimResults = true;
            rec.onresult = e => {{
                let s = '';
                for (let i = 0; i < e.results.length; i++) {{
                    s += e.results[i][0].transcript + ' ';
                }}
                text.innerText = s;
            }};
            rec.onstart = () => status.innerText = '🔴 Listening...';
            rec.onend = () => status.innerText = '✓ Stopped. Copy from above and paste in the scorecard.';
            rec.start();
            btn.disabled = true; btn.style.opacity = 0.5;
            setTimeout(() => {{ rec.stop(); btn.disabled = false; btn.style.opacity = 1; }}, 60000);
        }};
        </script>
        """,
        height=240,
    )


def render():
    st.markdown(
        f"""
        <div style="margin:8px 0 22px;">
            <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.25em;text-transform:uppercase;font-weight:800;">📍 LIVE ROUND <span class="live-dot"></span></div>
            <h1 style="margin:6px 0 4px;font-size:42px;">Smart Caddy</h1>
            <div style="color:{COLORS['cream_dim']};font-size:15px;">GPS, weather, plays-like math, club rec — one tap from yardage to swing.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # === Course picker ===
    if "active_course" not in st.session_state:
        st.session_state["active_course"] = "El Cariso GC"
    if "active_hole" not in st.session_state:
        st.session_state["active_hole"] = 1

    col1, col2 = st.columns([2, 1])
    with col1:
        course_name = st.selectbox(
            "Course",
            list(COURSES.keys()),
            index=list(COURSES.keys()).index(st.session_state["active_course"]),
        )
        st.session_state["active_course"] = course_name
    with col2:
        course = COURSES[course_name]
        n_holes = len(course["pars"])
        hole = st.selectbox("Hole", list(range(1, n_holes + 1)), index=st.session_state["active_hole"] - 1)
        st.session_state["active_hole"] = hole

    par = course["pars"][hole - 1]

    # === Auto-fetch weather based on course coords ===
    weather = fetch_weather(course["lat"], course["lon"])

    # Hero caddy card with weather
    if weather:
        temp = round(weather.get("temperature_2m", 70))
        wind = round(weather.get("wind_speed_10m", 0))
        wind_dir = weather.get("wind_direction_10m", 0)
        humidity = round(weather.get("relative_humidity_2m", 50))
    else:
        temp, wind, wind_dir, humidity = 70, 5, 180, 50

    # === Yardage + Caddy block ===
    col_caddy, col_weather = st.columns([2, 1])

    with col_caddy:
        st.markdown(f"<div style='font-size:11px;color:{COLORS['cream_dim']};letter-spacing:0.18em;text-transform:uppercase;font-weight:700;margin-bottom:6px;'>HOLE {hole} · PAR {par}</div>", unsafe_allow_html=True)

        yards = st.number_input(
            "Distance to pin (yards)",
            min_value=20, max_value=600, value=150, step=5,
            key=f"yards_{course_name}_{hole}",
        )

        wind_facing = st.radio(
            "Wind direction",
            ["Tail (helps)", "Cross", "Head (hurts)"],
            index=2 if wind > 8 else 1,
            horizontal=True,
            key=f"wind_dir_{course_name}_{hole}",
        )
        wind_dir_code = {"Tail (helps)": "tail", "Cross": "cross", "Head (hurts)": "head"}[wind_facing]

        # Plays-like calc
        plays = plays_like(yards, wind_mph=wind, wind_dir=wind_dir_code, temp_f=temp)
        adj_delta = plays - yards

        # Club recommendation using user's actual carries
        rec = suggested_club(yards, plays_like=plays)

        delta_str = f"+{adj_delta}" if adj_delta > 0 else (str(adj_delta) if adj_delta < 0 else "0")
        st.markdown(
            f"""
            <div class="caddy-card">
                <div style="display:flex;justify-content:space-between;align-items:flex-end;">
                    <div>
                        <div style="font-size:11px;letter-spacing:0.18em;text-transform:uppercase;font-weight:700;color:rgba(245,239,224,0.7);">PLAYS LIKE</div>
                        <div class="yard">{plays}<span class="yard-unit">yd</span></div>
                        <div style="margin-top:6px;font-size:13px;color:{COLORS['flag']};font-weight:700;">{delta_str}y from {yards} actual</div>
                    </div>
                    <div style="text-align:right;font-size:13px;color:rgba(245,239,224,0.8);">
                        <div>🌬 {wind} mph {wind_facing.split()[0].lower()}</div>
                        <div>🌡 {temp}°F</div>
                        <div>💧 {humidity}%</div>
                    </div>
                </div>
                <div class="rec">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div style="font-size:11px;letter-spacing:0.18em;text-transform:uppercase;font-weight:700;color:rgba(245,239,224,0.7);">RECOMMENDED</div>
                            <div class="club">{rec['club']}</div>
                            <div style="font-size:13px;color:rgba(245,239,224,0.85);">Your avg carry: {rec['your_carry']}y</div>
                        </div>
                        <div style="text-align:right;font-size:11px;color:{COLORS['flag']};letter-spacing:0.1em;">
                            {'⚠ longer than bag' if rec.get('warning') else '✓ smooth swing'}<br>
                            <span style="color:rgba(245,239,224,0.7);">aim center</span>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_weather:
        st.markdown(
            f"""
            <div class="gj-card-flush">
                <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.18em;text-transform:uppercase;font-weight:700;margin-bottom:10px;">📡 LIVE CONDITIONS <span class="live-dot"></span></div>
                <div style="font-size:13px;color:{COLORS['cream']};line-height:1.8;">
                    <div><b>{course_name}</b></div>
                    <div style="color:{COLORS['cream_dim']};font-size:11px;">{course['lat']:.3f}, {course['lon']:.3f}</div>
                </div>
                <div style="margin-top:14px;display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                    <div><div style='font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.15em;font-weight:700;'>TEMP</div><div style='font-family:Fraunces,serif;font-size:24px;color:{COLORS['cream']};'>{temp}°</div></div>
                    <div><div style='font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.15em;font-weight:700;'>WIND</div><div style='font-family:Fraunces,serif;font-size:24px;color:{COLORS['cream']};'>{wind}<span style='font-size:13px;'>mph</span></div></div>
                    <div><div style='font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.15em;font-weight:700;'>HUMIDITY</div><div style='font-family:Fraunces,serif;font-size:24px;color:{COLORS['cream']};'>{humidity}%</div></div>
                    <div><div style='font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.15em;font-weight:700;'>UPDATED</div><div style='font-size:12px;color:{COLORS['cream']};margin-top:4px;'>{datetime.now().strftime('%I:%M %p')}</div></div>
                </div>
                <div style="margin-top:14px;font-size:10px;color:{COLORS['cream_dim']};">Open-Meteo · auto-refresh 15min</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # === GPS button ===
    st.markdown(
        f"""
        <div class="section-header" style="margin-top:24px;">
            <span class="eyebrow">Locator</span>
            <h2>GPS check</h2>
            <span class="accent"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _gps_button()
    st.markdown(f"<div style='font-size:12px;color:{COLORS['cream_dim']};margin-top:8px;'>Live pin distances require licensed course-map data — we don't have that. But once you tap your aim point on a hole, we'll remember it for next time.</div>", unsafe_allow_html=True)

    # === Saved aim point for this hole ===
    aim = get_aim_point(course_name, hole)
    if aim:
        st.markdown(
            f"""
            <div class="gj-card-flush" style="margin-top:14px;">
                <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.18em;text-transform:uppercase;font-weight:700;">📌 Saved aim point — Hole {hole}</div>
                <div style="font-size:14px;color:{COLORS['cream']};margin-top:6px;">From tee to your aim: <b>{aim['yards_to_pin']}y</b> · ({aim['lat']:.5f}, {aim['lon']:.5f})</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # === Voice scorecard ===
    st.markdown(
        f"""
        <div class="section-header" style="margin-top:24px;">
            <span class="eyebrow">Scorecard</span>
            <h2>Hands-free entry</h2>
            <span class="accent"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _voice_scorecard(course_name, n_holes)

    # === Quick scorecard ===
    st.markdown(
        f"""
        <div class="section-header" style="margin-top:24px;">
            <span class="eyebrow">Manual</span>
            <h2>Round summary</h2>
            <span class="accent"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        score = st.number_input("Score", min_value=20, max_value=200, value=85, key="rs_score")
    with c2:
        putts = st.number_input("Putts", min_value=10, max_value=60, value=32, key="rs_putts")
    with c3:
        gir = st.number_input("GIR", min_value=0, max_value=18, value=4, key="rs_gir")
    with c4:
        fir = st.number_input("FIR", min_value=0, max_value=14, value=6, key="rs_fir")
    with c5:
        st.write("&nbsp;")
        if st.button("💾 Save Round", type="primary", use_container_width=True):
            row = {
                "date": datetime.now().date().isoformat(),
                "course": course_name,
                "par": course["par"],
                "score": score,
                "putts": putts,
                "gir": gir,
                "fir": fir,
            }
            append_round(row)
            st.success(f"✅ Round saved — {course_name} · {score}")
            st.balloons()
