"""Command Center — the dashboard."""
import streamlit as st
from datetime import datetime
from cloud_storage import load_data
from weekly_summary import get_summary
from insights import (
    stroke_saver_plan,
    total_strokes_to_save,
    gap_to_break_80,
    practice_streak,
)
from achievements import all_with_status

CLUBS = [
    {"label": "D",  "name": "Mizuno ST-Z 230 Driver",       "color": "#00D4AA", "carry": 221, "speed": 97, "ball": 138, "smash": 1.42, "apex": 68, "path": -3.7},
    {"label": "3W", "name": "Callaway Rogue ST 3-Wood",     "color": "#4A9EFF", "carry": 195, "speed": 87, "ball": 120, "smash": 1.38, "apex": 55, "path": -2.5},
    {"label": "5H", "name": "Callaway Edge 5-Hybrid",       "color": "#9B59B6", "carry": 175, "speed": 82, "ball": 112, "smash": 1.37, "apex": 58, "path": -2.1},
    {"label": "5i", "name": "Mizuno JPX925 HM 5-Iron",      "color": "#E67E22", "carry": 178, "speed": 81, "ball": 114, "smash": 1.40, "apex": 60, "path": -3.6},
    {"label": "6i", "name": "Mizuno JPX925 HM 6-Iron",      "color": "#D35400", "carry": 167, "speed": 79, "ball": 111, "smash": 1.40, "apex": 61, "path": -3.9},
    {"label": "7i", "name": "Mizuno JPX925 HM 7-Iron",      "color": "#F39C12", "carry": 155, "speed": 78, "ball": 108, "smash": 1.38, "apex": 62, "path": -5.1},
    {"label": "8i", "name": "Mizuno JPX925 HM 8-Iron",      "color": "#E22E2E", "carry": 142, "speed": 77, "ball": 104, "smash": 1.35, "apex": 64, "path": -4.9},
    {"label": "9i", "name": "Mizuno JPX925 HM 9-Iron",      "color": "#E74C3C", "carry": 130, "speed": 76, "ball": 100, "smash": 1.32, "apex": 65, "path": -4.8},
    {"label": "PW", "name": "Mizuno JPX925 HM Pitching Wedge", "color": "#1ABC9C", "carry": 110, "speed": 74, "ball": 94,  "smash": 1.27, "apex": 60, "path": -4.5},
    {"label": "GW", "name": "Kirkland 52° Gap Wedge",       "color": "#3498DB", "carry": 95,  "speed": 70, "ball": 85,  "smash": 1.21, "apex": 55, "path": -1.2},
    {"label": "SW", "name": "Kirkland 56° Sand Wedge",      "color": "#95A5A6", "carry": 80,  "speed": 66, "ball": 76,  "smash": 1.15, "apex": 50, "path": -0.8},
    {"label": "LW", "name": "Kirkland 60° Lob Wedge",       "color": "#BDC3C7", "carry": 60,  "speed": 60, "ball": 65,  "smash": 1.08, "apex": 42, "path": -0.5},
    {"label": "PT", "name": "TaylorMade Spider Putter",     "color": "#C0392B", "carry": 0,   "speed": 0,  "ball": 0,   "smash": 0,    "apex": 0,  "path": 0},
]


def render():
    summary = get_summary()
    today_str = datetime.now().strftime("%A, %B %d")

    # ── Page Header ──
    st.markdown(
        f"""
        <div class="page-header">
            <div>
                <div class="page-eyebrow">{today_str} · BURBANK, CA</div>
                <div class="page-title">Command Center</div>
            </div>
            <div style="background:linear-gradient(135deg,#111,#0c0c0c);border:1px solid #1E1E1E;border-radius:16px;padding:14px 22px;text-align:right;min-width:160px;">
                <div style="font-size:9px;color:#888;letter-spacing:2.5px;text-transform:uppercase;font-weight:700;">GHIN HANDICAP</div>
                <div style="font-size:42px;font-weight:900;color:#00D4AA;line-height:1;margin-top:4px;letter-spacing:-1.5px;">31.3</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── KPI Row ──
    avg_score = summary.get("avg_score") or 79.8
    rounds_count = summary.get("rounds_count") or 0
    espeed = int(summary.get("latest_espeed") or 97)
    practice_count = summary.get("practice_count") or 0

    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        (c1, "AVG SCORE", str(avg_score), "", f"{rounds_count} regulation rounds", "#00D4AA"),
        (c2, "DRIVER eSPEED", str(espeed), "mph", "Goal: 105 mph (+8)", "#FFB800"),
        (c3, "DIST POTENTIAL", "270", "yds", "Goal: 300 yds (+30)", "#FF6B35"),
        (c4, "PRACTICE SHOTS", str(practice_count), "", "Logged via Rapsodo", "#4A9EFF"),
    ]
    for col, lbl, val, unit, sub, color in kpis:
        with col:
            st.markdown(
                f"""
                <div class="kpi-card" style="--accent:{color};">
                    <div class="kpi-label">{lbl}</div>
                    <div style="line-height:1;"><span class="kpi-value">{val}</span><span class="kpi-unit">{unit}</span></div>
                    <div class="kpi-sub" style="color:{color};">{sub}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)

    # ── Two-column layout ──
    left, right = st.columns([1.3, 1])

    with left:
        # GAP-TO-BREAK-80 card
        gap = gap_to_break_80()
        if gap.get("avg") is not None:
            avg5 = gap["avg"]
            gap_val = gap["gap"]
            under = gap["under_80_count"]
            of_last = gap["of_last"]
            color = "#00D4AA" if gap_val <= 0 else ("#FFB800" if gap_val < 3 else "#FF6B35")
            label = "ACHIEVED" if gap_val <= 0 else f"{abs(gap_val)} STROKES AWAY"
            st.markdown(
                f"""
                <div class="data-card" style="border-left:3px solid {color};">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
                        <div>
                            <div style="font-size:10px;color:#888;letter-spacing:2px;text-transform:uppercase;font-weight:700;">BREAK 80 GOAL</div>
                            <div style="font-size:24px;font-weight:900;margin-top:6px;">{label}</div>
                            <div style="font-size:13px;color:#999;margin-top:6px;">Last 5 rounds avg: <strong style="color:#fff;">{avg5}</strong> · {under} of {of_last} under 80</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:42px;font-weight:900;color:{color};line-height:1;">{avg5}</div>
                            <div style="font-size:11px;color:#888;margin-top:4px;">vs target 80</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Stroke-Saver Plan
        plan = stroke_saver_plan()
        total_save = total_strokes_to_save()
        if plan:
            st.markdown(
                f"""
                <div class="section-label" style="margin-top:20px;">
                    🎯 STROKE-SAVER PLAN · {total_save} STROKES TO UNLOCK
                </div>
                """,
                unsafe_allow_html=True,
            )
            for item in plan[:3]:
                st.markdown(
                    f"""
                    <div class="insight-card">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:14px;">
                            <div style="flex:1;min-width:240px;">
                                <div style="font-size:12px;color:{item['color']};font-weight:700;letter-spacing:1px;text-transform:uppercase;">{item['icon']} {item['area']}</div>
                                <div style="font-size:13px;color:#DDD;margin-top:8px;line-height:1.6;">{item['why']}</div>
                                <div style="font-size:12px;color:#888;margin-top:10px;line-height:1.5;"><strong style="color:#00D4AA;">Drill:</strong> {item['drill']}</div>
                            </div>
                            <div style="text-align:right;">
                                <div class="insight-strokes">{item['strokes_saved']}</div>
                                <div style="font-size:10px;color:#888;letter-spacing:1.5px;text-transform:uppercase;font-weight:700;margin-top:4px;">strokes</div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Goal progress
        st.markdown('<div class="section-label" style="margin-top:24px;">GOAL PROGRESS</div>', unsafe_allow_html=True)
        for name, pct, c1c, c2c, note in [
            ("Break 80 Consistently", 60, "#00D4AA", "#00B894", f"Avg {avg5 if gap.get('avg') else '—'} · {gap.get('under_80_count', 0)} of last {gap.get('of_last', 0)} under 80"),
            ("300-Yard Driver",       47, "#FFB800", "#FF8C00", "Current potential: 270 yds · need +30"),
            ("Reach 20 Handicap",     35, "#4A9EFF", "#2980F0", "From 31.3 → 20.0"),
        ]:
            st.markdown(
                f"""
                <div style="margin-bottom:18px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                        <span style="font-size:14px;font-weight:600;">{name}</span>
                        <span style="font-size:14px;font-weight:800;color:{c1c};">{pct}%</span>
                    </div>
                    <div class="prog-track">
                        <div class="prog-fill" style="width:{pct}%;--c1:{c1c};--c2:{c2c};"></div>
                    </div>
                    <div style="font-size:11px;color:#777;margin-top:6px;">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right:
        # MY BAG
        st.markdown('<div class="section-label">MY BAG · TAP A CLUB</div>', unsafe_allow_html=True)

        if "selected_club" not in st.session_state:
            st.session_state["selected_club"] = "D"

        # Render in rows of 7 buttons (handles 13 clubs cleanly: 7+6)
        rows = [CLUBS[i:i + 7] for i in range(0, len(CLUBS), 7)]
        for row in rows:
            cols = st.columns(len(row))
            for col, club in zip(cols, row):
                with col:
                    is_sel = st.session_state.get("selected_club") == club["label"]
                    btn_label = f"●  {club['label']}" if is_sel else club["label"]
                    if st.button(btn_label, key=f"clb_{club['label']}", use_container_width=True):
                        st.session_state["selected_club"] = club["label"]
                        st.rerun()

        selected = st.session_state.get("selected_club", "D")
        club = next((c for c in CLUBS if c["label"] == selected), CLUBS[0])

        if club["carry"] > 0:
            path_color = "#FF3B30" if club["path"] < -3 else "#00D4AA"
            st.markdown(
                f"""
                <div class="data-card" style="margin-top:12px;border-top:3px solid {club['color']};">
                    <div style="font-size:11px;color:{club['color']};font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;">SELECTED · {club['label']}</div>
                    <div style="font-size:16px;font-weight:800;color:#fff;margin-bottom:18px;">{club['name']}</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;">
                        <div>
                            <div style="font-size:9px;color:#777;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;">Avg Carry</div>
                            <div style="font-size:30px;font-weight:900;color:{club['color']};line-height:1.1;">{club['carry']}<span style="font-size:11px;color:#888;font-weight:400;"> yds</span></div>
                        </div>
                        <div>
                            <div style="font-size:9px;color:#777;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;">Club Speed</div>
                            <div style="font-size:30px;font-weight:900;line-height:1.1;">{club['speed']}<span style="font-size:11px;color:#888;font-weight:400;"> mph</span></div>
                        </div>
                        <div>
                            <div style="font-size:9px;color:#777;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;">Ball Speed</div>
                            <div style="font-size:30px;font-weight:900;line-height:1.1;">{club['ball']}<span style="font-size:11px;color:#888;font-weight:400;"> mph</span></div>
                        </div>
                        <div>
                            <div style="font-size:9px;color:#777;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;">Smash Factor</div>
                            <div style="font-size:30px;font-weight:900;line-height:1.1;">{club['smash']}</div>
                        </div>
                        <div>
                            <div style="font-size:9px;color:#777;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;">Apex</div>
                            <div style="font-size:30px;font-weight:900;line-height:1.1;">{club['apex']}<span style="font-size:11px;color:#888;font-weight:400;"> ft</span></div>
                        </div>
                        <div>
                            <div style="font-size:9px;color:#777;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;">Club Path</div>
                            <div style="font-size:30px;font-weight:900;color:{path_color};line-height:1.1;">{club['path']}°</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div class="data-card" style="margin-top:12px;border-top:3px solid {club['color']};">
                    <div style="font-size:11px;color:{club['color']};font-weight:700;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;">SELECTED · {club['label']}</div>
                    <div style="font-size:16px;font-weight:800;color:#fff;margin-bottom:8px;">{club['name']}</div>
                    <div style="font-size:13px;color:#999;line-height:1.6;">Track putts per round in <strong style="color:#00D4AA;">Live Round</strong>. Mid-stroke face balanced putter — best with arc-style stroke.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Achievements preview
        st.markdown('<div class="section-label" style="margin-top:24px;">🏆 ACHIEVEMENTS</div>', unsafe_allow_html=True)
        all_ach = all_with_status()
        unlocked_count = sum(1 for a in all_ach if a["unlocked"])
        total = len(all_ach)
        st.markdown(
            f"<div style='font-size:13px;color:#999;margin-bottom:10px;'>{unlocked_count} of {total} unlocked</div>",
            unsafe_allow_html=True,
        )
        chips_html = ""
        for a in all_ach[:8]:
            cls = "achievement" if a["unlocked"] else "achievement locked"
            chips_html += f'<span class="{cls}">{a["icon"]} {a["label"]}</span>'
        st.markdown(f"<div>{chips_html}</div>", unsafe_allow_html=True)

    # ── Bottom: Today's focus ──
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">TODAY\'S FOCUS</div>', unsafe_allow_html=True)
    focus = summary.get("focus_area", "Keep logging rounds for personalized recommendations.")
    st.markdown(
        f"""
        <div class="data-card" style="border-left:3px solid #00D4AA;">
            <div style="font-size:10px;color:#00D4AA;letter-spacing:2px;text-transform:uppercase;font-weight:700;margin-bottom:8px;">AI FOCUS RECOMMENDATION</div>
            <div style="font-size:14px;color:#DDD;line-height:1.7;">{focus}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
