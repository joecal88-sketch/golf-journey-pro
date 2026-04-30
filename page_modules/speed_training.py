"""Speed Training — TheStack-style protocols, dot UI, phase progress."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date as _date
from cloud_storage import append_speed, load_data

# Stack weight set
WEIGHTS = [
    {"name": "Green", "g": 20, "color": "#2ECC71"},
    {"name": "Blue",  "g": 45, "color": "#4A9EFF"},
    {"name": "Yellow","g": 60, "color": "#F1C40F"},
    {"name": "Red",   "g": 75, "color": "#E74C3C"},
    {"name": "Purple","g": 100,"color": "#9B59B6"},
]

# 4 protocols based on TheStack methodology
PROTOCOLS = {
    "Foundation L1": {
        "phase": "Phase 1 — Foundation",
        "desc": "Baseline speed development. Build neuromuscular pathways with progressive load.",
        "stations": [
            {"weight": "20g (Green)", "swings": 6, "rest": 30, "intensity": "Submax"},
            {"weight": "45g (Blue)",  "swings": 6, "rest": 30, "intensity": "Submax"},
            {"weight": "60g (Yellow)","swings": 6, "rest": 45, "intensity": "Max"},
            {"weight": "Driver",      "swings": 6, "rest": 45, "intensity": "Max"},
        ],
    },
    "Build L2": {
        "phase": "Phase 2 — Build",
        "desc": "Increase volume and adaptation. More max-effort swings.",
        "stations": [
            {"weight": "45g (Blue)",   "swings": 8, "rest": 30, "intensity": "Submax"},
            {"weight": "60g (Yellow)", "swings": 8, "rest": 45, "intensity": "Max"},
            {"weight": "75g (Red)",    "swings": 6, "rest": 60, "intensity": "Max"},
            {"weight": "Driver",       "swings": 8, "rest": 45, "intensity": "Max"},
        ],
    },
    "Peak L3": {
        "phase": "Phase 3 — Peak",
        "desc": "Max effort with overload weights. Build top-end speed ceiling.",
        "stations": [
            {"weight": "60g (Yellow)", "swings": 10, "rest": 45, "intensity": "Max"},
            {"weight": "75g (Red)",    "swings": 8,  "rest": 60, "intensity": "Max"},
            {"weight": "100g (Purple)","swings": 6,  "rest": 90, "intensity": "Max"},
            {"weight": "Driver",       "swings": 10, "rest": 60, "intensity": "Max"},
        ],
    },
    "Overload L4": {
        "phase": "Phase 4 — Overload-Underload",
        "desc": "Heavy weight followed by light weight. Trains the contrast effect for explosive speed.",
        "stations": [
            {"weight": "100g (Purple)","swings": 5, "rest": 60, "intensity": "Max"},
            {"weight": "20g (Green)",  "swings": 8, "rest": 30, "intensity": "Max"},
            {"weight": "75g (Red)",    "swings": 5, "rest": 60, "intensity": "Max"},
            {"weight": "20g (Green)",  "swings": 8, "rest": 30, "intensity": "Max"},
            {"weight": "Driver",       "swings": 8, "rest": 60, "intensity": "Max"},
        ],
    },
}


def render():
    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="page-eyebrow" style="color:#FFB800;">⚡ THESTACK SPEED PROTOCOL</div>
                <div class="page-title">Speed Training</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Foundation phase progress ──
    speed_sessions = load_data().get("speed", [])
    foundation_done = sum(1 for s in speed_sessions if "Foundation" in str(s.get("protocol", "")))
    target = 18
    pct = min(100, int(foundation_done / target * 100))

    st.markdown(
        f"""
        <div class="data-card" style="border-top:3px solid #FFB800;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:14px;margin-bottom:14px;">
                <div>
                    <div style="font-size:11px;color:#FFB800;font-weight:700;letter-spacing:2px;text-transform:uppercase;">PHASE 1 · FOUNDATION</div>
                    <div style="font-size:22px;font-weight:900;margin-top:6px;">Session {foundation_done} of {target}</div>
                    <div style="font-size:13px;color:#888;margin-top:4px;">{target - foundation_done} sessions to unlock Phase 2</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:36px;font-weight:900;color:#FFB800;line-height:1;">{pct}%</div>
                </div>
            </div>
            <div class="prog-track">
                <div class="prog-fill" style="width:{pct}%;--c1:#FFB800;--c2:#FF8C00;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["🏋️ Today's Session", "📈 Speed Logger", "📊 Progress", "📚 All Combos"])

    with tab1:
        _render_session()
    with tab2:
        _render_logger()
    with tab3:
        _render_progress()
    with tab4:
        _render_all_combos()


def _render_session():
    protocol_name = st.selectbox("Choose Protocol", list(PROTOCOLS.keys()), index=0)
    protocol = PROTOCOLS[protocol_name]

    st.markdown(
        f"""
        <div class="stack-bar">
            ⚡ {protocol_name} · {protocol['phase']}
        </div>
        <div class="stack-card">
            <div style="font-size:13px;color:#CCC;line-height:1.6;">{protocol['desc']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-label" style="margin-top:18px;">SESSION STATIONS</div>', unsafe_allow_html=True)

    for i, step in enumerate(protocol["stations"], 1):
        # dot indicators
        dots_html = "".join(['<span class="dot done"></span>' if j <= 0 else '<span class="dot"></span>' for j in range(step["swings"])])

        intensity_color = "#FF3B30" if step["intensity"] == "Max" else "#FFB800"

        st.markdown(
            f"""
            <div class="data-card" style="border-left:3px solid #FFB800;">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:14px;">
                    <div>
                        <div style="font-size:10px;color:#FFB800;font-weight:700;letter-spacing:2px;text-transform:uppercase;">STATION {i}</div>
                        <div style="font-size:18px;font-weight:800;margin-top:4px;">{step['weight']}</div>
                        <div style="margin-top:8px;">{dots_html}</div>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:28px;font-weight:900;color:#00D4AA;line-height:1;">{step['swings']}</div>
                        <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">swings</div>
                        <div style="font-size:11px;color:#888;margin-top:6px;">{step['rest']}s rest · <span style="color:{intensity_color};font-weight:700;">{step['intensity']}</span></div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_logger():
    st.markdown('<div class="section-label">LOG TODAY\'S TOP SPEEDS</div>', unsafe_allow_html=True)
    st.caption("Enter the top recorded mph for each weight from today's session.")

    with st.form("speed_form", clear_on_submit=False):
        protocol = st.selectbox("Protocol Used", list(PROTOCOLS.keys()))

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        green = c1.number_input("🟢 20g Green (mph)", 0, 200, 105)
        blue = c2.number_input("🔵 45g Blue (mph)", 0, 200, 100)
        yellow = c3.number_input("🟡 60g Yellow (mph)", 0, 200, 95)
        c4, c5, c6 = c1, c2, c3
        c4, c5, c6 = st.columns(3)
        red = c4.number_input("🔴 75g Red (mph)", 0, 200, 90)
        purple = c5.number_input("🟣 100g Purple (mph)", 0, 200, 85)
        driver = c6.number_input("🏌️ Driver Swing (mph)", 0, 200, 97)

        notes = st.text_input("Notes", "")

        submitted = st.form_submit_button("💾 Save Speed Session", use_container_width=True)
        if submitted:
            append_speed({
                "date": str(_date.today()),
                "protocol": protocol,
                "green_speed": green, "blue_speed": blue, "yellow_speed": yellow,
                "red_speed": red, "purple_speed": purple,
                "driver_speed": driver,
                "notes": notes,
            })
            st.success(f"✓ Speed session logged · Driver {driver} mph")
            st.balloons()


def _render_progress():
    speed = load_data().get("speed", [])
    if not speed:
        st.info("Log a speed session to see progress charts.")
        return
    df = pd.DataFrame(speed)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sessions", len(df))
    if "driver_speed" in df.columns:
        vals = pd.to_numeric(df["driver_speed"], errors="coerce")
        c2.metric("Latest Driver", f"{vals.iloc[-1]:.0f} mph")
        c3.metric("Top Driver", f"{vals.max():.0f} mph")
        if len(vals) >= 2:
            gain = vals.iloc[-1] - vals.iloc[0]
            c4.metric("Total Gain", f"{gain:+.0f} mph")

    fig = go.Figure()
    color_map = [
        ("driver_speed", "Driver", "#00D4AA", 4),
        ("green_speed",  "20g Green", "#2ECC71", 2),
        ("blue_speed",   "45g Blue",  "#4A9EFF", 2),
        ("yellow_speed", "60g Yellow","#F1C40F", 2),
        ("red_speed",    "75g Red",   "#E74C3C", 2),
        ("purple_speed", "100g Purple","#9B59B6", 2),
    ]
    for col, name, color, width in color_map:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["date"], y=pd.to_numeric(df[col], errors="coerce"),
                mode="lines+markers", name=name,
                line=dict(color=color, width=width),
                marker=dict(size=8, color=color, line=dict(color="#000", width=1)),
            ))
    fig.update_layout(
        plot_bgcolor="#0A0A0A", paper_bgcolor="#0A0A0A",
        font=dict(family="Inter", color="#CCC"),
        height=480, margin=dict(t=30, b=30, l=30, r=30),
        xaxis=dict(gridcolor="#1A1A1A"),
        yaxis=dict(title="Speed (mph)", gridcolor="#1A1A1A"),
        legend=dict(bgcolor="rgba(0,0,0,0)", x=0, y=1.15, orientation="h"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_all_combos():
    st.markdown('<div class="section-label">30 WEIGHT COMBINATIONS</div>', unsafe_allow_html=True)
    st.caption("All possible 1- and 2-weight combos using your 20g/45g/60g/75g/100g set. Use these for custom protocols.")

    combos = []
    for w in WEIGHTS:
        combos.append({"name": w["name"], "weight_g": w["g"], "type": "Single", "color": w["color"]})
    for i, w1 in enumerate(WEIGHTS):
        for j, w2 in enumerate(WEIGHTS):
            if j > i:
                combos.append({
                    "name": f"{w1['name']} + {w2['name']}",
                    "weight_g": w1["g"] + w2["g"],
                    "type": "Stacked",
                    "color": w1["color"],
                })
    combos.sort(key=lambda x: x["weight_g"])

    cols = st.columns(3)
    for i, combo in enumerate(combos):
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="data-card" style="padding:12px 14px;border-left:3px solid {combo['color']};">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div style="font-size:13px;font-weight:700;color:#fff;">{combo['name']}</div>
                            <div style="font-size:10px;color:#888;letter-spacing:1px;text-transform:uppercase;margin-top:2px;">{combo['type']}</div>
                        </div>
                        <div style="font-size:18px;font-weight:900;color:{combo['color']};">{combo['weight_g']}g</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
