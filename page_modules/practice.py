"""Practice Hub — clickable club picker, range-style dispersion, Dispersion Index vs Pro."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from cloud_storage import append_practice, load_data
from insights import club_vs_tour, miss_pattern

# Mirrors the dashboard bag (full Mizuno set 5i-PW)
CLUBS_LIST = [
    {"label": "D",  "name": "Driver",        "color": "#00D4AA", "tour_carry": 290, "tour_disp": 28},
    {"label": "3W", "name": "3-Wood",        "color": "#4A9EFF", "tour_carry": 245, "tour_disp": 24},
    {"label": "5H", "name": "5-Hybrid",      "color": "#9B59B6", "tour_carry": 225, "tour_disp": 20},
    {"label": "5i", "name": "5-Iron",        "color": "#E67E22", "tour_carry": 209, "tour_disp": 18},
    {"label": "6i", "name": "6-Iron",        "color": "#D35400", "tour_carry": 198, "tour_disp": 17},
    {"label": "7i", "name": "7-Iron",        "color": "#F39C12", "tour_carry": 184, "tour_disp": 15},
    {"label": "8i", "name": "8-Iron",        "color": "#E22E2E", "tour_carry": 172, "tour_disp": 14},
    {"label": "9i", "name": "9-Iron",        "color": "#E74C3C", "tour_carry": 160, "tour_disp": 13},
    {"label": "PW", "name": "Pitching Wedge","color": "#1ABC9C", "tour_carry": 142, "tour_disp": 11},
    {"label": "GW", "name": "Gap Wedge",     "color": "#3498DB", "tour_carry": 122, "tour_disp": 10},
    {"label": "SW", "name": "Sand Wedge",    "color": "#95A5A6", "tour_carry": 100, "tour_disp": 9},
    {"label": "LW", "name": "Lob Wedge",     "color": "#BDC3C7", "tour_carry": 80,  "tour_disp": 8},
]

CLUB_COLORS = {c["label"]: c["color"] for c in CLUBS_LIST}


def render():
    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="page-eyebrow">RAPSODO MLM2PRO · ANALYSIS</div>
                <div class="page-title">Practice Hub</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["🏌️ My Bag", "📊 Session", "➕ Quick Log", "📜 History"])

    with tab1:
        _render_clubcards()

    with tab2:
        _render_session_tab()

    with tab3:
        _render_quick_log()

    with tab4:
        data = load_data().get("practice", [])
        if not data:
            st.info("No practice shots logged yet.")
        else:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)


# ──────────────────────────────────────────────────────────────────────
# CLUB-CARD BROWSER (Command Center style on Practice page)
# ──────────────────────────────────────────────────────────────────────
def _render_clubcards():
    data = load_data().get("practice", [])
    df = pd.DataFrame(data) if data else pd.DataFrame()

    if "practice_selected_club" not in st.session_state:
        st.session_state["practice_selected_club"] = "D"

    st.markdown('<div class="section-label">PICK A CLUB · SEE PER-CLUB STATS</div>', unsafe_allow_html=True)

    # Render in rows of 6 buttons
    rows = [CLUBS_LIST[i:i + 6] for i in range(0, len(CLUBS_LIST), 6)]
    for row in rows:
        cols = st.columns(len(row))
        for col, club in zip(cols, row):
            with col:
                is_sel = st.session_state.get("practice_selected_club") == club["label"]
                btn_label = f"●  {club['label']}" if is_sel else club["label"]
                if st.button(btn_label, key=f"prac_clb_{club['label']}", use_container_width=True):
                    st.session_state["practice_selected_club"] = club["label"]
                    st.rerun()

    selected = st.session_state.get("practice_selected_club", "D")
    club = next((c for c in CLUBS_LIST if c["label"] == selected), CLUBS_LIST[0])

    # Filter shots for selected club
    if not df.empty and "club" in df.columns:
        sub = df[df["club"] == selected].copy()
        sub["carry"] = pd.to_numeric(sub.get("carry"), errors="coerce")
        sub["side"] = pd.to_numeric(sub.get("side"), errors="coerce")
    else:
        sub = pd.DataFrame()

    # Stats
    if len(sub) > 0:
        avg_carry = sub["carry"].mean()
        max_carry = sub["carry"].max()
        avg_apex = pd.to_numeric(sub.get("apex"), errors="coerce").mean() if "apex" in sub.columns else None
        # Dispersion = ~2σ of side offset (yds)
        if "side" in sub.columns and sub["side"].notna().sum() >= 3:
            disp = 2 * sub["side"].std()
        else:
            disp = None
        shots_n = len(sub)
        # Dispersion index vs pro
        tour_disp = club["tour_disp"]
        if disp is not None and disp > 0:
            disp_idx = round(tour_disp / disp * 100)
        else:
            disp_idx = None
    else:
        avg_carry = max_carry = avg_apex = disp = disp_idx = None
        shots_n = 0

    # Header card
    st.markdown(
        f"""
        <div class="data-card" style="margin-top:14px;border-top:3px solid {club['color']};">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:14px;">
                <div>
                    <div style="font-size:11px;color:{club['color']};font-weight:700;letter-spacing:2px;text-transform:uppercase;">SELECTED · {club['label']}</div>
                    <div style="font-size:22px;font-weight:800;color:#fff;margin-top:4px;">{club['name']}</div>
                    <div style="font-size:12px;color:#888;margin-top:4px;">{shots_n} practice shots logged</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:10px;color:#888;letter-spacing:2px;text-transform:uppercase;font-weight:700;">DISPERSION INDEX</div>
                    <div style="font-size:42px;font-weight:900;color:{_disp_color(disp_idx)};line-height:1;margin-top:4px;letter-spacing:-1px;">
                        {f"{disp_idx}" if disp_idx is not None else "—"}
                    </div>
                    <div style="font-size:11px;color:#888;margin-top:4px;">{_disp_label(disp_idx)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Per-club KPIs
    cA, cB, cC, cD = st.columns(4)
    cA.metric("Avg Carry", f"{avg_carry:.0f} yds" if avg_carry is not None else "—")
    cB.metric("Max Carry", f"{max_carry:.0f} yds" if max_carry is not None else "—")
    cC.metric("Apex", f"{avg_apex:.0f} ft" if avg_apex is not None and not np.isnan(avg_apex) else "—")
    cD.metric("Dispersion", f"{disp:.0f} yds" if disp is not None else "—",
              delta=f"Tour {club['tour_disp']} yds")

    st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

    # ── Driving-range style dispersion plot for SELECTED club ──
    st.markdown('<div class="section-label">DRIVING-RANGE DISPERSION MAP</div>', unsafe_allow_html=True)

    # Data points: real (if available) else simulated
    if len(sub) > 0 and sub["side"].notna().sum() >= 3 and sub["carry"].notna().sum() >= 3:
        xs = sub["side"].dropna().values
        ys = sub["carry"].dropna().values[: len(xs)]
        source = f"{len(xs)} real shots"
    else:
        # Simulated cone using estimated carry from CLUBS_LIST
        np.random.seed(hash(selected) % (2**31))
        target = avg_carry if avg_carry else _est_avg_carry(selected)
        n = 12
        xs = np.random.normal(0, max(target * 0.04, 4), n)
        ys = np.random.normal(target, max(target * 0.04, 5), n)
        source = "simulated · log shots to see real data"

    target_carry = avg_carry if avg_carry else _est_avg_carry(selected)

    fig = _range_figure(xs, ys, target_carry, club["color"], club["tour_disp"])
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.caption(f"📍 {source}. Red = your scatter ellipse · Yellow = tour-pro ellipse. Smaller = more accurate.")


def _disp_color(idx):
    if idx is None:
        return "#888"
    if idx >= 90:
        return "#00D4AA"
    if idx >= 70:
        return "#FFB800"
    return "#FF6B35"


def _disp_label(idx):
    if idx is None:
        return "Log 3+ shots"
    if idx >= 90:
        return "Tour-level accuracy"
    if idx >= 75:
        return "Strong amateur"
    if idx >= 50:
        return "Mid-handicap"
    return "Tighten it up"


def _est_avg_carry(label):
    # Reasonable defaults if no shots logged yet
    defaults = {
        "D": 221, "3W": 195, "5H": 175, "5i": 178, "6i": 167,
        "7i": 155, "8i": 142, "9i": 130, "PW": 110,
        "GW": 95, "SW": 80, "LW": 60,
    }
    return defaults.get(label, 130)


def _range_figure(xs, ys, target_carry, color, tour_disp):
    """Build a driving-range visual: green grass, target line, dispersion scatter, tour ellipse."""
    fig = go.Figure()

    # X range: ±40 yds, Y range: 0 to 1.2 * target
    x_min, x_max = -50, 50
    y_max = float(target_carry) * 1.15 + 20

    # Grass background — solid teal-green via shape
    fig.add_shape(
        type="rect", x0=x_min, x1=x_max, y0=0, y1=y_max,
        line=dict(color="rgba(0,0,0,0)"),
        fillcolor="#0E2A1B",
        layer="below",
    )

    # Range alignment yardage lines (every 25 yds)
    for y in range(0, int(y_max), 25):
        fig.add_shape(
            type="line", x0=x_min, x1=x_max, y0=y, y1=y,
            line=dict(color="rgba(255,255,255,0.06)", width=1, dash="dot"),
            layer="below",
        )
        if y > 0 and y % 50 == 0:
            fig.add_annotation(
                x=x_min + 4, y=y, text=f"{y}", showarrow=False,
                font=dict(color="rgba(255,255,255,0.35)", size=10, family="Inter"),
                xanchor="left",
            )

    # Center alignment line (the tee → target)
    fig.add_shape(
        type="line", x0=0, x1=0, y0=0, y1=y_max,
        line=dict(color="rgba(255,255,255,0.18)", width=1, dash="dash"),
        layer="below",
    )

    # Target circle (where you're aiming, at target_carry)
    target_r = 6  # yds
    fig.add_shape(
        type="circle",
        x0=-target_r, y0=target_carry - target_r,
        x1=target_r,  y1=target_carry + target_r,
        line=dict(color="#FFB800", width=2),
        fillcolor="rgba(255,184,0,0.18)",
        layer="below",
    )
    fig.add_annotation(
        x=0, y=target_carry + target_r + 6,
        text=f"🎯 Target {int(target_carry)} yds",
        showarrow=False,
        font=dict(color="#FFB800", size=11, family="Inter"),
    )

    # Tour ellipse (yellow)
    fig.add_shape(
        type="circle",
        x0=-tour_disp, y0=target_carry - tour_disp * 0.8,
        x1=tour_disp,  y1=target_carry + tour_disp * 0.8,
        line=dict(color="rgba(255,184,0,0.6)", width=2, dash="dot"),
        fillcolor="rgba(0,0,0,0)",
    )

    # Player dispersion ellipse (computed from std of points)
    if len(xs) >= 3:
        sx = float(np.std(xs)) * 1.96  # 95% lateral
        sy = float(np.std(ys)) * 1.96
        cy = float(np.mean(ys))
        fig.add_shape(
            type="circle",
            x0=-sx, y0=cy - sy,
            x1=sx,  y1=cy + sy,
            line=dict(color=color, width=2),
            fillcolor=f"rgba(0,212,170,0.10)",
        )

    # Shot scatter
    fig.add_trace(go.Scatter(
        x=xs, y=ys,
        mode="markers",
        marker=dict(color=color, size=10, line=dict(color="#000", width=1), opacity=0.9),
        name="Shots",
        hovertemplate="Side %{x:.1f} yd · Carry %{y:.0f} yd<extra></extra>",
    ))

    fig.update_layout(
        plot_bgcolor="#0E2A1B",
        paper_bgcolor="#0A0A0A",
        font=dict(family="Inter", color="#CCC"),
        height=520,
        margin=dict(t=20, b=30, l=30, r=30),
        xaxis=dict(
            title="← Left  ·  yards offline  ·  Right →",
            range=[x_min, x_max],
            zeroline=False,
            showgrid=False,
            color="#999",
        ),
        yaxis=dict(
            title="Carry (yds)",
            range=[0, y_max],
            zeroline=False,
            showgrid=False,
            color="#999",
        ),
        showlegend=False,
    )
    return fig


# ──────────────────────────────────────────────────────────────────────
# SESSION TAB (CSV + summary chart, ALL clubs)
# ──────────────────────────────────────────────────────────────────────
def _render_session_tab():
    upload = st.file_uploader(
        "Upload Rapsodo CSV (or use your seeded session)",
        type=["csv"],
        help="Drop your Rapsodo MLM2PRO CSV. The app auto-maps club, carry, ball speed, and apex columns.",
    )
    if upload is not None:
        try:
            df = _smart_parse_csv(upload)
            st.success(f"✓ Loaded {len(df)} shots")
            _render_session(df)
        except Exception as e:
            st.error(f"Could not parse CSV: {e}")
    else:
        data = load_data().get("practice", [])
        if data:
            df = pd.DataFrame(data)
            st.markdown(
                f'<span class="pill pill-green">SESSION LOADED</span> '
                f'<span style="color:#888;font-size:13px;margin-left:8px;">{len(df)} shots from your most recent practice</span>',
                unsafe_allow_html=True,
            )
            _render_session(df)
        else:
            st.info("Upload a Rapsodo CSV or use Quick Log to add your first shots.")


def _smart_parse_csv(upload) -> pd.DataFrame:
    df = pd.read_csv(upload)
    rename_map = {}
    for c in df.columns:
        cl = c.lower()
        if "club" in cl and "speed" not in cl and "club" not in rename_map.values():
            rename_map[c] = "club"
        elif "carry" in cl:
            rename_map[c] = "carry"
        elif "ball" in cl and "speed" in cl:
            rename_map[c] = "ball_speed"
        elif "club" in cl and "speed" in cl:
            rename_map[c] = "club_speed"
        elif "apex" in cl or "height" in cl:
            rename_map[c] = "apex"
        elif "side" in cl or "offline" in cl:
            rename_map[c] = "side"
        elif "smash" in cl:
            rename_map[c] = "smash"
    return df.rename(columns=rename_map)


def _render_session(df: pd.DataFrame):
    if "club" not in df.columns or "carry" not in df.columns:
        st.warning("CSV needs at least 'club' and 'carry' columns.")
        return
    df["carry"] = pd.to_numeric(df["carry"], errors="coerce")
    df = df.dropna(subset=["carry"])

    # Top KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Shots", len(df))
    c2.metric("Avg Carry", f"{df['carry'].mean():.0f} yds")
    c3.metric("Max Carry", f"{df['carry'].max():.0f} yds")
    c4.metric("Clubs Used", df["club"].nunique())

    # Miss pattern callout
    mp = miss_pattern()
    if mp.get("bias") and mp["bias"] != "balanced":
        bias_color = "#FF3B30" if mp["bias"] == "right" else "#FFB800"
        st.markdown(
            f"""
            <div class="data-card" style="border-left:3px solid {bias_color};margin-top:12px;">
                <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
                    <div style="font-size:32px;">🎯</div>
                    <div style="flex:1;min-width:240px;">
                        <div style="font-size:11px;color:{bias_color};font-weight:700;letter-spacing:1.5px;text-transform:uppercase;">MISS PATTERN DETECTED</div>
                        <div style="font-size:14px;color:#DDD;margin-top:6px;line-height:1.6;">{mp['summary']}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # All-clubs carry chart
    st.markdown('<div class="section-label" style="margin-top:18px;">CARRY BY CLUB</div>', unsafe_allow_html=True)
    summary = df.groupby("club").agg(
        carry_mean=("carry", "mean"),
        carry_max=("carry", "max"),
        shots=("carry", "count"),
    ).reset_index()
    summary["color"] = summary["club"].map(lambda c: CLUB_COLORS.get(c, "#888"))
    summary = summary.sort_values("carry_mean", ascending=False)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=summary["club"], y=summary["carry_mean"],
        marker=dict(color=summary["color"], line=dict(width=0)),
        text=summary["carry_mean"].round(0),
        textposition="outside",
        textfont=dict(color="#fff", size=12, family="Inter"),
    ))
    fig.update_layout(
        plot_bgcolor="#0A0A0A", paper_bgcolor="#0A0A0A",
        font=dict(family="Inter", color="#CCC", size=12),
        height=380, margin=dict(t=30, b=30, l=30, r=30),
        yaxis=dict(title="Carry (yds)", gridcolor="#1A1A1A"),
        xaxis=dict(showgrid=False),
        showlegend=False, bargap=0.4,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Stats table
    st.markdown('<div class="section-label">SESSION TABLE</div>', unsafe_allow_html=True)
    table = summary.copy()
    table["carry_mean"] = table["carry_mean"].round(1)
    table["carry_max"] = table["carry_max"].round(1)
    table = table.rename(columns={
        "club": "Club", "shots": "Shots",
        "carry_mean": "Avg Carry", "carry_max": "Max Carry",
    })[["Club", "Shots", "Avg Carry", "Max Carry"]]
    st.dataframe(table, use_container_width=True, hide_index=True)


def _render_quick_log():
    st.markdown('<div class="section-label">QUICK SHOT LOG</div>', unsafe_allow_html=True)
    st.caption("Faster than typing — also try voice on your phone (browser mic).")

    with st.form("shot_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        club = c1.selectbox("Club", [c["label"] for c in CLUBS_LIST])
        carry = c2.number_input("Carry (yds)", 0, 350, 150)
        ball_speed = c3.number_input("Ball Speed (mph)", 0, 200, 100)
        c4, c5, c6 = st.columns(3)
        club_speed = c4.number_input("Club Speed (mph)", 0, 150, 80)
        apex = c5.number_input("Apex (ft)", 0, 200, 60)
        side = c6.number_input("Side (− left / + right, yds)", -50, 50, 0)
        notes = st.text_input("Notes (optional)", "")

        submitted = st.form_submit_button("Log Shot", use_container_width=True)
        if submitted:
            append_practice({
                "date": str(datetime.now())[:10],
                "club": club, "carry": carry,
                "ball_speed": ball_speed, "club_speed": club_speed,
                "apex": apex, "side": side, "notes": notes,
            })
            st.success(f"✓ {club} · {carry} yds logged")
