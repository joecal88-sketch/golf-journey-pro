"""Live Round — auto-GPS + weather plays-like caddy, voice scorecard, 8 LA courses."""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import date as _date
from cloud_storage import append_round, load_data

# ── 8 LA-area courses pre-loaded ──
COURSES = {
    "El Cariso (Sylmar)": {
        "rating": 68.8, "slope": 119, "par": 70,
        "lat": 34.3132, "lon": -118.4659,
        "holes": [4, 4, 3, 5, 4, 3, 4, 4, 4, 4, 4, 5, 4, 3, 4, 4, 3, 4],
    },
    "Scholl Canyon (Glendale)": {
        "rating": 64.5, "slope": 108, "par": 60,
        "lat": 34.1465, "lon": -118.2150,
        "holes": [3, 3, 4, 3, 3, 3, 4, 3, 3, 3, 3, 4, 3, 3, 3, 4, 3, 4],
    },
    "Van Nuys Par 3": {
        "rating": 54.0, "slope": 90, "par": 54,
        "lat": 34.2089, "lon": -118.4906,
        "holes": [3] * 18,
    },
    "DeBell (Burbank)": {
        "rating": 70.4, "slope": 124, "par": 71,
        "lat": 34.2069, "lon": -118.2786,
        "holes": [4, 4, 3, 5, 4, 3, 4, 5, 4, 4, 4, 3, 4, 4, 5, 3, 4, 4],
    },
    "Brookside #1 (Pasadena)": {
        "rating": 71.4, "slope": 124, "par": 72,
        "lat": 34.1611, "lon": -118.1690,
        "holes": [4, 4, 4, 3, 5, 4, 3, 4, 5, 4, 4, 3, 4, 4, 5, 3, 4, 4],
    },
    "Griffith Park · Wilson": {
        "rating": 71.7, "slope": 121, "par": 72,
        "lat": 34.1490, "lon": -118.2820,
        "holes": [4, 4, 5, 3, 4, 4, 5, 3, 4, 4, 4, 3, 4, 4, 5, 4, 3, 5],
    },
    "Griffith Park · Harding": {
        "rating": 71.5, "slope": 122, "par": 72,
        "lat": 34.1497, "lon": -118.2823,
        "holes": [4, 5, 4, 3, 4, 4, 4, 5, 3, 4, 5, 4, 3, 4, 4, 4, 3, 5],
    },
    "Rancho Park (Westside)": {
        "rating": 72.6, "slope": 124, "par": 71,
        "lat": 34.0451, "lon": -118.4115,
        "holes": [5, 4, 3, 4, 4, 4, 5, 3, 4, 4, 4, 3, 5, 4, 3, 4, 4, 4],
    },
}

# Joel's club distances for "plays-like" caddy (matches dashboard bag)
CLUB_CARRIES = [
    {"club": "LW", "carry": 60},
    {"club": "SW", "carry": 80},
    {"club": "GW", "carry": 95},
    {"club": "PW", "carry": 110},
    {"club": "9i", "carry": 130},
    {"club": "8i", "carry": 142},
    {"club": "7i", "carry": 155},
    {"club": "6i", "carry": 167},
    {"club": "5i", "carry": 178},
    {"club": "5H", "carry": 175},
    {"club": "3W", "carry": 195},
    {"club": "Driver", "carry": 221},
]


def _calc_handicap(rounds_df: pd.DataFrame):
    if len(rounds_df) < 3:
        return None
    diffs = []
    for _, r in rounds_df.iterrows():
        try:
            score = float(r.get("score", 0))
            rating = float(r.get("rating", 72))
            slope = float(r.get("slope", 113))
            diffs.append((score - rating) * 113.0 / slope)
        except Exception:
            continue
    if not diffs:
        return None
    diffs = sorted(diffs)
    n = len(diffs)
    take = max(1, min(8, n // 2))
    return round(sum(diffs[:take]) / take * 0.96, 1)


def _plays_like(distance: int, wind: int, wind_dir: str, elevation: int) -> dict:
    wind_factor = wind * 0.01 if wind_dir == "Headwind" else (
        -wind * 0.005 if wind_dir == "Tailwind" else 0
    )
    elev_yds = (elevation / 10.0) * 2.0 if elevation > 0 else (elevation / 10.0) * 1.5
    plays_like = round(distance * (1 + wind_factor) + elev_yds)
    best = min(CLUB_CARRIES, key=lambda c: abs(c["carry"] - plays_like))
    return {
        "distance": distance,
        "plays_like": plays_like,
        "club": best["club"],
        "club_carry": best["carry"],
        "delta": plays_like - best["carry"],
    }


@st.cache_data(ttl=900)
def _fetch_weather(lat: float, lon: float):
    """Open-Meteo free API — current temperature + wind + direction."""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,wind_speed_10m,wind_direction_10m"
            "&wind_speed_unit=mph&temperature_unit=fahrenheit"
        )
        r = requests.get(url, timeout=10)
        j = r.json()
        cur = j.get("current", {})
        return {
            "temp": cur.get("temperature_2m"),
            "wind_mph": cur.get("wind_speed_10m"),
            "wind_dir_deg": cur.get("wind_direction_10m"),
        }
    except Exception as e:
        return {"error": str(e)}


def _wind_to_compass(deg):
    if deg is None:
        return "—"
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    ix = int((deg + 22.5) % 360 / 45)
    return dirs[ix]


# ──────────────────────────────────────────────────────────────────────
def render():
    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="page-eyebrow">USGA · ROUND TRACKER</div>
                <div class="page-title">Live Round</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["📍 Smart Caddy", "📝 Hole-by-Hole", "📊 Trends", "🎯 Handicap"])

    with tab1:
        _render_caddy()
    with tab2:
        _render_hole_by_hole()
    with tab3:
        _render_trends()
    with tab4:
        _render_handicap()


def _render_caddy():
    st.markdown('<div class="section-label">SMART PLAYS-LIKE CADDY · AUTO WEATHER</div>', unsafe_allow_html=True)
    st.caption("Pick the course you're at — wind & temp pull from the live forecast. Tweak distance and elevation only.")

    # Course selector
    course = st.selectbox("📍 Course (auto-loads location)", list(COURSES.keys()), key="caddy_course")
    info = COURSES[course]
    lat, lon = info["lat"], info["lon"]

    # Fetch weather
    wx = _fetch_weather(lat, lon)
    if wx and "error" not in wx and wx.get("wind_mph") is not None:
        wind = int(round(wx["wind_mph"]))
        temp = int(round(wx["temp"])) if wx.get("temp") is not None else None
        compass = _wind_to_compass(wx.get("wind_dir_deg"))
        wx_status_html = f"""
        <div class="data-card" style="border-left:3px solid #00D4AA;margin-top:8px;">
            <div style="display:flex;gap:24px;flex-wrap:wrap;align-items:center;">
                <div>
                    <div style="font-size:10px;color:#888;letter-spacing:2px;text-transform:uppercase;font-weight:700;">LIVE FORECAST · {course.split('(')[0].strip().upper()}</div>
                    <div style="font-size:13px;color:#DDD;margin-top:6px;">
                        🌤 <strong>{temp if temp else "—"}°F</strong>
                        &nbsp;·&nbsp;💨 <strong>{wind} mph from {compass}</strong>
                    </div>
                </div>
            </div>
        </div>
        """
    else:
        wind = 0
        temp = None
        compass = "—"
        wx_status_html = """
        <div class="data-card" style="border-left:3px solid #FFB800;margin-top:8px;">
            <div style="font-size:13px;color:#DDD;">⚠️ Couldn't fetch live weather — using neutral conditions. Override below.</div>
        </div>
        """
    st.markdown(wx_status_html, unsafe_allow_html=True)

    # Optional GPS via browser (informational — gives current location, not pin distance)
    with st.expander("📡 Use my phone GPS (optional)"):
        st.caption(
            "Tap below to grab your current GPS coordinates. Useful for verifying you're at the right course. "
            "Pin distance still needs a number — there's no public GPS-to-pin API for free."
        )
        gps_html = """
        <div style="padding:12px;background:#111;border-radius:10px;border:1px solid #222;">
            <button onclick="getGPS()" style="background:#00D4AA;color:#000;border:none;border-radius:8px;padding:10px 18px;font-weight:700;font-size:13px;cursor:pointer;">📍 Get My Location</button>
            <div id="gps-out" style="margin-top:10px;color:#DDD;font-size:13px;font-family:monospace;"></div>
        </div>
        <script>
        function getGPS() {
          const out = document.getElementById('gps-out');
          out.textContent = 'Getting location...';
          if (!navigator.geolocation) { out.textContent = 'GPS not supported'; return; }
          navigator.geolocation.getCurrentPosition(
            (pos) => {
              out.innerHTML = '✅ Lat: ' + pos.coords.latitude.toFixed(5) +
                              ' · Lon: ' + pos.coords.longitude.toFixed(5) +
                              ' · Accuracy: ±' + Math.round(pos.coords.accuracy) + ' m';
            },
            (err) => { out.textContent = '❌ ' + err.message; }
          );
        }
        </script>
        """
        components.html(gps_html, height=100)

    st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

    # Inputs (just distance + elevation + wind orientation relative to your shot)
    cA, cB = st.columns(2)
    distance = cA.number_input("Pin Distance (yds)", 30, 350, 150)
    elevation = cB.number_input("Elevation (+ uphill / − downhill, ft)", -100, 100, 0)
    cC, cD = st.columns(2)
    wind_override = cC.slider("Override Wind (mph) — auto from weather", 0, 30, int(wind))
    wind_dir = cD.selectbox("Wind direction relative to your shot", ["None", "Headwind", "Tailwind", "Crosswind"])

    result = _plays_like(distance, wind_override, wind_dir, elevation)

    # Result cards
    cE, cF = st.columns(2)
    with cE:
        st.markdown(
            f"""
            <div class="data-card" style="border-top:3px solid #00D4AA;">
                <div style="font-size:10px;color:#888;letter-spacing:2px;text-transform:uppercase;font-weight:700;">PLAYS LIKE</div>
                <div style="font-size:64px;font-weight:900;color:#00D4AA;line-height:1;margin-top:6px;letter-spacing:-2px;">{result['plays_like']}</div>
                <div style="font-size:13px;color:#999;margin-top:6px;">Pin: {distance} yds · Adj: {result['plays_like'] - distance:+d} yds</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with cF:
        delta = result["delta"]
        delta_color = "#00D4AA" if abs(delta) <= 5 else "#FFB800"
        st.markdown(
            f"""
            <div class="data-card" style="border-top:3px solid {delta_color};">
                <div style="font-size:10px;color:#888;letter-spacing:2px;text-transform:uppercase;font-weight:700;">RECOMMENDED CLUB</div>
                <div style="font-size:48px;font-weight:900;color:#fff;line-height:1;margin-top:6px;">{result['club']}</div>
                <div style="font-size:13px;color:#999;margin-top:6px;">Carries {result['club_carry']} yds · {delta:+d} from plays-like</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if wind_dir == "Crosswind" and wind_override >= 8:
        st.markdown(
            f"""
            <div class="data-card" style="border-left:3px solid #FFB800;margin-top:14px;">
                <div style="font-size:13px;color:#DDD;line-height:1.6;">
                    <strong style="color:#FFB800;">⚠️ Crosswind {wind_override} mph:</strong> aim {round(wind_override / 3)} yds upwind. Take an extra club for stability.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────────────
def _render_hole_by_hole():
    st.markdown('<div class="section-label">ROUND DETAILS</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    round_date = c1.date_input("Date", _date.today())
    course = c2.selectbox("Course", list(COURSES.keys()) + ["Other"])

    if course == "Other":
        course_name = st.text_input("Course name", "")
        c3, c4, c5 = st.columns(3)
        rating = c3.number_input("Course rating", 50.0, 80.0, 70.0, 0.1)
        slope = c4.number_input("Slope rating", 55, 155, 113)
        par = c5.number_input("Par", 50, 80, 72)
        holes = [4] * 18
    else:
        info = COURSES[course]
        rating, slope, par = info["rating"], info["slope"], info["par"]
        holes = info["holes"]
        course_name = course

    st.markdown(
        f'<div style="font-size:13px;color:#888;margin:8px 0 16px;">Rating <strong style="color:#fff;">{rating}</strong> · Slope <strong style="color:#fff;">{slope}</strong> · Par <strong style="color:#fff;">{par}</strong></div>',
        unsafe_allow_html=True,
    )

    # ── Voice scorecard widget ──
    with st.expander("🎙 Voice scorecard (try on your phone)"):
        st.caption("Tap, say things like 'hole 1, four', 'hole 2, par', 'hole 3, six'. Then paste below.")
        components.html(_voice_widget_html(), height=240)
        voice_paste = st.text_area("Voice transcript", placeholder="hole 1 four, hole 2 par, hole 3 bogey...", height=80, key="voice_paste")
        if st.button("📥 Apply voice scores", use_container_width=True):
            scores_from_voice = _parse_voice_scores(voice_paste, holes)
            if scores_from_voice:
                if "round_scores" not in st.session_state:
                    st.session_state["round_scores"] = [None] * 18
                for i, s in enumerate(scores_from_voice):
                    if s is not None:
                        st.session_state["round_scores"][i] = s
                st.success(f"✓ Applied {sum(1 for s in scores_from_voice if s is not None)} hole scores")
                st.rerun()
            else:
                st.warning("Couldn't parse any holes — try 'hole 1 four' style phrasing.")

    # Hole-by-hole entry
    st.markdown('<div class="section-label">HOLE-BY-HOLE SCORECARD</div>', unsafe_allow_html=True)

    if "round_scores" not in st.session_state or st.session_state.get("round_course") != course_name:
        st.session_state["round_scores"] = [None] * 18
        st.session_state["round_course"] = course_name

    # Front 9
    st.markdown("<div style='font-size:11px;color:#FFB800;font-weight:700;letter-spacing:2px;margin-bottom:8px;'>FRONT NINE</div>", unsafe_allow_html=True)
    cols = st.columns(9)
    for i in range(9):
        with cols[i]:
            st.markdown(
                f"<div style='text-align:center;font-size:10px;color:#888;font-weight:700;letter-spacing:1px;'>HOLE {i+1}</div>"
                f"<div style='text-align:center;font-size:11px;color:#00D4AA;font-weight:700;margin-bottom:4px;'>PAR {holes[i]}</div>",
                unsafe_allow_html=True,
            )
            v = st.number_input(
                f"h{i+1}", 1, 12,
                value=st.session_state["round_scores"][i] or holes[i],
                key=f"score_{i}", label_visibility="collapsed",
            )
            st.session_state["round_scores"][i] = v

    # Back 9
    st.markdown("<div style='font-size:11px;color:#FFB800;font-weight:700;letter-spacing:2px;margin:14px 0 8px;'>BACK NINE</div>", unsafe_allow_html=True)
    cols = st.columns(9)
    for i in range(9, 18):
        with cols[i - 9]:
            st.markdown(
                f"<div style='text-align:center;font-size:10px;color:#888;font-weight:700;letter-spacing:1px;'>HOLE {i+1}</div>"
                f"<div style='text-align:center;font-size:11px;color:#00D4AA;font-weight:700;margin-bottom:4px;'>PAR {holes[i]}</div>",
                unsafe_allow_html=True,
            )
            v = st.number_input(
                f"h{i+1}", 1, 12,
                value=st.session_state["round_scores"][i] or holes[i],
                key=f"score_{i}", label_visibility="collapsed",
            )
            st.session_state["round_scores"][i] = v

    # Running total
    scores = [s for s in st.session_state["round_scores"] if s]
    front = sum(st.session_state["round_scores"][:9]) if all(st.session_state["round_scores"][:9]) else None
    back = sum(st.session_state["round_scores"][9:]) if all(st.session_state["round_scores"][9:]) else None
    total = sum(scores)
    par_so_far = sum(holes[:len(scores)])
    diff = total - par_so_far if scores else 0

    cT1, cT2, cT3, cT4 = st.columns(4)
    cT1.metric("Front 9", front if front else "—", delta=f"{front - sum(holes[:9]):+d}" if front else None)
    cT2.metric("Back 9", back if back else "—", delta=f"{back - sum(holes[9:]):+d}" if back else None)
    cT3.metric("Total", total, delta=f"{diff:+d}")
    cT4.metric("vs Par", f"{diff:+d}")

    # Round summary
    st.markdown('<div class="section-label" style="margin-top:18px;">ROUND SUMMARY</div>', unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    putts = c5.number_input("Putts", 0, 60, 32)
    gir = c6.number_input("GIR", 0, 18, 5)
    fir = c7.number_input("Fairways Hit", 0, 18, 6)
    notes = c8.text_input("Notes", "")

    if st.button("💾 Save Round", use_container_width=True):
        append_round({
            "date": str(round_date),
            "course": course_name,
            "rating": rating, "slope": slope, "par": par,
            "score": total,
            "putts": putts, "gir": gir, "fir": fir,
            "notes": notes,
            "hole_scores": st.session_state["round_scores"],
        })
        st.success(f"✓ {total} ({diff:+d}) saved at {course_name}")
        st.session_state["round_scores"] = [None] * 18
        st.balloons()


def _voice_widget_html():
    return """
    <div style="font-family:Inter,sans-serif;background:#0F0F0F;border:1px solid #222;border-radius:14px;padding:16px;">
      <button id="micBtn" style="background:linear-gradient(135deg,#00D4AA,#00B894);color:#000;border:none;border-radius:50%;width:64px;height:64px;font-size:26px;cursor:pointer;box-shadow:0 4px 16px rgba(0,212,170,.3);">🎙</button>
      <div id="micStatus" style="color:#999;font-size:12px;margin-top:10px;">Tap mic, say: "hole 1 four, hole 2 par, hole 3 bogey"</div>
      <div id="micOutput" style="margin-top:10px;color:#00D4AA;font-size:14px;font-weight:600;font-family:monospace;min-height:24px;"></div>
      <button id="copyBtn" style="background:#222;color:#fff;border:none;border-radius:8px;padding:6px 14px;margin-top:10px;font-size:12px;cursor:pointer;">📋 Copy transcript</button>
    </div>
    <script>
    (function(){
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      const btn = document.getElementById('micBtn');
      const out = document.getElementById('micOutput');
      const status = document.getElementById('micStatus');
      const copyBtn = document.getElementById('copyBtn');
      if (!SR) {
        status.textContent = "Voice recognition not supported in this browser. Try Safari on iPhone or Chrome on Android.";
        btn.disabled = true; btn.style.opacity = .5;
        return;
      }
      const rec = new SR();
      rec.continuous = true;
      rec.interimResults = false;
      rec.lang = 'en-US';
      let listening = false;
      let transcript = '';
      btn.onclick = () => {
        if (!listening) { rec.start(); listening = true; status.textContent="Listening… tap again to stop."; btn.style.background="linear-gradient(135deg,#FF3B30,#CC2A20)"; }
        else { rec.stop(); listening = false; status.textContent="Stopped. Copy or paste the transcript above."; btn.style.background="linear-gradient(135deg,#00D4AA,#00B894)"; }
      };
      rec.onresult = (e) => {
        for (let i = e.resultIndex; i < e.results.length; i++) {
          if (e.results[i].isFinal) transcript += ' ' + e.results[i][0].transcript;
        }
        out.textContent = transcript.trim();
      };
      copyBtn.onclick = () => {
        navigator.clipboard.writeText(transcript.trim());
        copyBtn.textContent = '✓ Copied';
        setTimeout(() => copyBtn.textContent = '📋 Copy transcript', 1500);
      };
    })();
    </script>
    """


def _parse_voice_scores(text: str, holes_par):
    """Parse 'hole 1 four, hole 2 par, hole 3 birdie' → list of 18 ints (or None)."""
    if not text:
        return None
    import re
    text = text.lower()

    word_to_num = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    }

    out = [None] * 18
    # Find each "hole N <score>" segment
    pattern = r"hole\s+(\d{1,2})\s+([a-z0-9\-]+)"
    for m in re.finditer(pattern, text):
        h = int(m.group(1))
        if not (1 <= h <= 18):
            continue
        token = m.group(2).strip()
        par = holes_par[h - 1]
        if token == "par":
            out[h - 1] = par
        elif token in ("birdie", "birdy"):
            out[h - 1] = par - 1
        elif token in ("eagle",):
            out[h - 1] = par - 2
        elif token in ("bogey", "bogie"):
            out[h - 1] = par + 1
        elif token in ("double", "double-bogey"):
            out[h - 1] = par + 2
        elif token in ("triple", "triple-bogey"):
            out[h - 1] = par + 3
        elif token in word_to_num:
            out[h - 1] = word_to_num[token]
        elif token.isdigit():
            out[h - 1] = int(token)
    return out


# ──────────────────────────────────────────────────────────────────────
def _render_trends():
    rounds = load_data().get("rounds", [])
    if not rounds:
        st.info("No rounds logged yet.")
        return
    df = pd.DataFrame(rounds)
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["par"] = pd.to_numeric(df.get("par", 70), errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["score", "date"]).sort_values("date")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rounds", len(df))
    c2.metric("Best", int(df["score"].min()))
    c3.metric("Avg", f"{df['score'].mean():.1f}")
    c4.metric("Latest", int(df["score"].iloc[-1]))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["score"], mode="lines+markers",
        line=dict(color="#00D4AA", width=3),
        marker=dict(size=12, color="#00D4AA", line=dict(color="#000", width=1)),
        name="Score",
    ))
    fig.add_hline(y=80, line=dict(color="#FFB800", width=2, dash="dash"),
                  annotation_text="Break 80", annotation_position="top right",
                  annotation_font_color="#FFB800")
    fig.update_layout(
        plot_bgcolor="#0A0A0A", paper_bgcolor="#0A0A0A",
        font=dict(family="Inter", color="#CCC"),
        height=420, margin=dict(t=30, b=30, l=30, r=30),
        xaxis=dict(gridcolor="#1A1A1A"),
        yaxis=dict(title="Score", gridcolor="#1A1A1A"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-label">ROUNDS LOG</div>', unsafe_allow_html=True)
    show = df.sort_values("date", ascending=False).copy()
    show["date"] = show["date"].dt.strftime("%Y-%m-%d")
    cols = [c for c in ["date", "course", "score", "par", "putts", "gir", "fir", "notes"] if c in show.columns]
    st.dataframe(show[cols], use_container_width=True, hide_index=True)


def _render_handicap():
    rounds = load_data().get("rounds", [])
    st.markdown('<div class="section-label">USGA HANDICAP INDEX</div>', unsafe_allow_html=True)
    if not rounds:
        st.info("Log at least 3 rounds to calculate handicap.")
        return
    df = pd.DataFrame(rounds)
    hcp = _calc_handicap(df)
    c1, c2 = st.columns([1, 2])
    if hcp is not None:
        c1.markdown(
            f"""
            <div class="data-card" style="text-align:center;">
                <div style="font-size:11px;color:#888;letter-spacing:2px;text-transform:uppercase;font-weight:700;">CALCULATED INDEX</div>
                <div style="font-size:60px;font-weight:900;color:#00D4AA;line-height:1;margin-top:10px;letter-spacing:-2px;">{hcp}</div>
                <div style="font-size:11px;color:#888;margin-top:8px;">From {len(df)} rounds</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    c2.markdown(
        """
        <div class="data-card">
            <div style="font-size:11px;color:#888;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;font-weight:700;">HOW IT WORKS</div>
            <div style="font-size:13px;color:#CCC;line-height:1.7;">
            Score Differential = (Score − Rating) × 113 / Slope.<br>
            Take the lowest 8 of your last 20 (proportional for fewer rounds), average them, multiply by 0.96.<br>
            Your GHIN of 31.3 is the official tracked number — this is your live calc as you log rounds.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
