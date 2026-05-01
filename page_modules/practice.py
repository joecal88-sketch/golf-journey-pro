"""Practice Hub — digital driving range with shot pattern visualization."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from cloud_storage import load_data, append_practice, update_metric
from styles import COLORS
from insights import TOUR_CARRY, carry_vs_tour
import io


CLUBS_ORDER = ["Driver", "3W", "5H", "5i", "6i", "7i", "8i", "9i", "PW", "GW", "SW", "LW"]


# --- Club name normalizer (handles Rapsodo / GCQuad / FlightScope / SkyTrak exports) ---
_CLUB_ALIASES = {
    # Driver
    "driver": "Driver", "dr": "Driver", "d": "Driver", "1w": "Driver", "1 wood": "Driver",
    # Woods
    "3w": "3W", "3 wood": "3W", "three wood": "3W", "fairway": "3W", "fairway wood": "3W",
    "5w": "3W", "5 wood": "3W",  # treat 5W under 3W bucket if needed
    # Hybrids
    "5h": "5H", "5 hybrid": "5H", "hybrid": "5H", "4h": "5H", "4 hybrid": "5H",
    # Irons
    "5i": "5i", "5 iron": "5i", "iron 5": "5i",
    "6i": "6i", "6 iron": "6i", "iron 6": "6i",
    "7i": "7i", "7 iron": "7i", "iron 7": "7i",
    "8i": "8i", "8 iron": "8i", "iron 8": "8i",
    "9i": "9i", "9 iron": "9i", "iron 9": "9i",
    # Wedges
    "pw": "PW", "p": "PW", "pitching wedge": "PW", "pitch": "PW",
    "gw": "GW", "aw": "GW", "gap wedge": "GW", "approach wedge": "GW", "52": "GW",
    "sw": "SW", "sand wedge": "SW", "56": "SW",
    "lw": "LW", "lob wedge": "LW", "60": "LW", "58": "LW",
}


def normalize_club(raw) -> str:
    """Map any vendor's club label to our canonical name. Returns original (titled) if unknown."""
    if raw is None:
        return ""
    s = str(raw).strip().lower()
    if not s or s in {"nan", "none"}:
        return ""
    # Direct alias hit
    if s in _CLUB_ALIASES:
        return _CLUB_ALIASES[s]
    # Stripped variants (remove punctuation/extra spaces)
    compact = "".join(ch for ch in s if ch.isalnum())
    if compact in _CLUB_ALIASES:
        return _CLUB_ALIASES[compact]
    # Pattern: e.g. "7-iron", "7iron"
    import re
    m = re.match(r"^(\d{1,2})\s*[\-_ ]?\s*(iron|i)$", s)
    if m:
        n = m.group(1)
        return f"{n}i" if n in {"3", "4", "5", "6", "7", "8", "9"} else s
    m = re.match(r"^iron\s*(\d{1,2})$", s)
    if m:
        n = m.group(1)
        return f"{n}i" if n in {"3", "4", "5", "6", "7", "8", "9"} else s
    m = re.match(r"^(\d{1,2})\s*(wood|w)$", s)
    if m:
        n = m.group(1)
        if n == "1":
            return "Driver"
        return f"{n}W" if n in {"3", "5", "7"} else s
    # Loft-only wedges (e.g. "52°", "56 deg")
    m = re.match(r"^(\d{2})\s*[°o]?\s*(deg|degrees|wedge)?$", s)
    if m:
        loft = int(m.group(1))
        if loft in (50, 52): return "GW"
        if loft in (54, 56): return "SW"
        if loft in (58, 60, 62): return "LW"
    return str(raw).strip()  # leave as-is so the user still sees their custom club
CLUB_ICONS = {
    "Driver": "🏌️", "3W": "🏌️", "5H": "🪵",
    "5i": "🎯", "6i": "🎯", "7i": "🎯", "8i": "🎯", "9i": "🎯",
    "PW": "⛳", "GW": "⛳", "SW": "⛳", "LW": "⛳",
}


def _digital_range(shots, club_name, target_carry):
    """Top-down illustrated fairway with rough, sand traps, distance arcs, tee box.
    Layered: deep rough → light rough → fairway → sand → trees → arcs → markers → shots.
    """
    fig = go.Figure()

    max_y = max(int(target_carry * 1.25), 280)
    fairway_w = 36   # half-width of fairway
    rough_w = 78     # half-width of rough/playable area
    deep_w = 110     # half-width of deep rough boundary

    # 1) Deep rough background (entire panel)
    fig.add_shape(
        type="rect", x0=-deep_w, x1=deep_w, y0=-30, y1=max_y + 30,
        fillcolor="#1f3a23", line=dict(width=0), layer="below",
    )
    # 2) Light rough strip (between fairway and deep rough)
    fig.add_shape(
        type="rect", x0=-rough_w, x1=rough_w, y0=-15, y1=max_y + 10,
        fillcolor="#2f5a36", line=dict(width=0), layer="below",
    )
    # 3) Fairway (slight taper toward green)
    fig.add_trace(go.Scatter(
        x=[-fairway_w * 1.05, fairway_w * 1.05, fairway_w * 0.78, -fairway_w * 0.78, -fairway_w * 1.05],
        y=[-10, -10, max_y - 8, max_y - 8, -10],
        fill="toself",
        fillcolor="#4a8a52",
        line=dict(color="#5fa066", width=1.5),
        hoverinfo="skip", showlegend=False,
    ))
    # 4) Mowing-stripe overlay (alternating darker stripes for that PGA TV look)
    for i in range(0, max_y, 18):
        if (i // 18) % 2 == 0:
            continue
        fig.add_shape(
            type="rect",
            x0=-fairway_w, x1=fairway_w,
            y0=i, y1=i + 18,
            fillcolor="rgba(255,255,255,0.04)",
            line=dict(width=0), layer="below",
        )

    # 5) Dashed white center line (target line)
    fig.add_trace(go.Scatter(
        x=[0, 0], y=[0, max_y - 12],
        mode="lines",
        line=dict(color="rgba(255,255,255,0.45)", width=1.5, dash="dash"),
        hoverinfo="skip", showlegend=False,
    ))

    # 6) Distance arc lines + labels at 50-yd increments
    theta_arc = np.linspace(-np.pi / 2.6, np.pi / 2.6, 60)
    for d in range(50, max_y + 1, 50):
        # subtle arc across fairway
        arc_x = (rough_w * 0.95) * np.sin(theta_arc)
        arc_y = d + (rough_w * 0.95) * (np.cos(theta_arc) - 1) * 0.05  # nearly flat
        # Use a straight line across rough as the arc (visual reference)
        fig.add_trace(go.Scatter(
            x=[-rough_w * 0.96, rough_w * 0.96],
            y=[d, d],
            mode="lines",
            line=dict(color="rgba(255,255,255,0.32)", width=1, dash="dot"),
            hoverinfo="skip", showlegend=False,
        ))
        # Distance label badge on right side
        fig.add_annotation(
            x=rough_w * 0.96 + 6, y=d,
            text=f"<b>{d}</b>",
            showarrow=False,
            font=dict(color="#f5efe0", size=11, family="Inter"),
            xanchor="left",
            bgcolor="rgba(0,0,0,0.45)",
            borderpad=3,
            bordercolor="rgba(255,255,255,0.15)",
            borderwidth=1,
        )

    # 7) Sand traps (kidney-shaped) — placed strategically along the fairway
    def add_bunker(cx, cy, rx, ry, rotation_deg=0):
        """Add a kidney/oval sand trap."""
        t = np.linspace(0, 2 * np.pi, 60)
        # kidney shape: ellipse with a slight inward dimple
        x_local = rx * np.cos(t) - 0.18 * rx * np.cos(2 * t)
        y_local = ry * np.sin(t)
        rad = np.deg2rad(rotation_deg)
        x_rot = x_local * np.cos(rad) - y_local * np.sin(rad)
        y_rot = x_local * np.sin(rad) + y_local * np.cos(rad)
        fig.add_trace(go.Scatter(
            x=cx + x_rot, y=cy + y_rot,
            fill="toself",
            fillcolor="#e8d8a8",
            line=dict(color="#c9b884", width=1.5),
            hoverinfo="skip", showlegend=False,
        ))

    # Bunker positions scaled to target_carry so they always frame the landing zone
    bunker_specs = [
        (-fairway_w + 2, target_carry * 0.45, 9, 5, 25),
        (fairway_w - 4, target_carry * 0.62, 11, 6, -20),
        (-fairway_w * 0.4, target_carry * 0.92, 8, 5, 10),
        (fairway_w * 0.55, target_carry * 1.05, 10, 5, -30),
    ]
    for spec in bunker_specs:
        if spec[1] < max_y - 12:
            add_bunker(*spec)

    # 8) Tree clusters in deep rough (small dark green dots)
    rng = np.random.default_rng(42)
    n_trees = 28
    tree_x = np.concatenate([
        rng.uniform(-deep_w + 4, -rough_w - 6, n_trees // 2),
        rng.uniform(rough_w + 6, deep_w - 4, n_trees - n_trees // 2),
    ])
    tree_y = rng.uniform(0, max_y, n_trees)
    fig.add_trace(go.Scatter(
        x=tree_x, y=tree_y,
        mode="markers",
        marker=dict(size=14, color="#0e1f12",
                    line=dict(color="#1a3a22", width=1),
                    symbol="circle"),
        hoverinfo="skip", showlegend=False,
    ))
    # Tree highlights (lighter dots offset)
    fig.add_trace(go.Scatter(
        x=tree_x - 1.5, y=tree_y + 1.5,
        mode="markers",
        marker=dict(size=6, color="#2c5a36", symbol="circle"),
        hoverinfo="skip", showlegend=False,
    ))

    # 9) Green at target_carry (oval, more elegant)
    theta = np.linspace(0, 2 * np.pi, 60)
    gr_x = 14 * np.cos(theta)
    gr_y = target_carry + 9 * np.sin(theta) - 4
    fig.add_trace(go.Scatter(
        x=gr_x, y=gr_y,
        fill="toself",
        fillcolor="#7dc788",
        line=dict(color="#a8e0b0", width=2),
        hoverinfo="skip", showlegend=False,
    ))
    # Pin shadow + flag
    fig.add_trace(go.Scatter(
        x=[0, 0], y=[target_carry - 4, target_carry + 6],
        mode="lines", line=dict(color="#1a1a1a", width=2),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_annotation(
        x=0, y=target_carry + 6, text="🚩", showarrow=False, font=dict(size=20),
        xshift=6, yshift=4,
    )
    fig.add_annotation(
        x=0, y=target_carry - 16, text=f"<b>{target_carry}y</b>",
        showarrow=False,
        font=dict(color="#fff", size=12, family="Fraunces"),
        bgcolor="rgba(0,0,0,0.55)", borderpad=3,
        bordercolor=COLORS["flag"], borderwidth=1,
    )

    # 10) Tee box
    fig.add_shape(
        type="rect",
        x0=-12, x1=12, y0=-22, y1=-8,
        fillcolor="#d4a24c",
        line=dict(color="#a37c2c", width=2),
    )
    # Tee markers (two dots)
    fig.add_trace(go.Scatter(
        x=[-7, 7], y=[-15, -15],
        mode="markers",
        marker=dict(size=8, color="#fff", line=dict(color="#a37c2c", width=1)),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_annotation(
        x=0, y=-26, text="<b>TEE BOX</b>",
        showarrow=False,
        font=dict(color="#d4a24c", size=10, family="Inter"),
    )

    # 11) Plot user's actual shots (tracer lines + landing dots + mean)
    if shots:
        carries = [s.get("carry", 0) for s in shots]
        offlines = [s.get("offline_y", 0) for s in shots]
        # Tracer lines from tee to landing
        for c, o in zip(carries, offlines):
            fig.add_trace(go.Scatter(
                x=[0, o], y=[-8, c],
                mode="lines",
                line=dict(color="rgba(212,162,76,0.22)", width=1),
                hoverinfo="skip", showlegend=False,
            ))
        # Landing dots (with subtle glow ring)
        fig.add_trace(go.Scatter(
            x=offlines, y=carries,
            mode="markers",
            marker=dict(
                size=14, color=COLORS["flag"],
                line=dict(color="rgba(0,0,0,0.7)", width=2),
                symbol="circle",
                opacity=0.92,
            ),
            text=[f"Carry: {c:.0f}y<br>Offline: {o:+.0f}y" for c, o in zip(carries, offlines)],
            hoverinfo="text",
            showlegend=False,
        ))
        # Mean ball (cream halo)
        mean_c = float(np.mean(carries))
        mean_o = float(np.mean(offlines))
        fig.add_trace(go.Scatter(
            x=[mean_o], y=[mean_c],
            mode="markers",
            marker=dict(size=26, color=COLORS["cream"],
                        line=dict(color=COLORS["fairway_2"], width=3),
                        symbol="circle"),
            hovertext=f"Mean: {mean_c:.0f}y, {mean_o:+.0f}y",
            hoverinfo="text",
            showlegend=False,
        ))

    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False, range=[-deep_w, deep_w], scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False, range=[-30, max_y + 30]),
        plot_bgcolor="#0e1f12",
        paper_bgcolor=COLORS["bg_2"],
        margin=dict(l=0, r=0, t=10, b=0),
        height=620,
    )
    return fig


def _dispersion_index(shots):
    """0-100 vs Tour pro tightness. Tour 7i offline std ~6yds. Player 60ft -> ~20yds = score 30."""
    if len(shots) < 5:
        return None
    offlines = [s.get("offline_y", 0) for s in shots]
    carries = [s.get("carry", 0) for s in shots]
    if not carries:
        return None
    off_std = float(np.std(offlines))
    car_std = float(np.std(carries))
    # Tour: ~5y offline, ~3y carry std on 7i
    tour_off = 5
    tour_car = 4
    score = 100 - min(80, (off_std / tour_off - 1) * 30 + (car_std / tour_car - 1) * 20)
    return max(0, round(score))


def render():
    data = load_data()
    shots = data.get("practice_shots", []) or []

    st.markdown(
        f"""
        <div style="margin:8px 0 22px;">
            <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.25em;text-transform:uppercase;font-weight:800;">🏌️ PRACTICE HUB</div>
            <h1 style="margin:6px 0 4px;font-size:42px;">Digital Driving Range</h1>
            <div style="color:{COLORS['cream_dim']};font-size:15px;">Visualize your shot pattern. Compare to Tour. Find the leaks.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Range View", "📥 Quick Log", "📊 By Club", "📤 Import CSV"])

    # === RANGE VIEW ===
    with tab1:
        # Normalize club names on read so legacy / non-canonical entries still bucket correctly
        for s in shots:
            if s.get("club"):
                s["club"] = normalize_club(s["club"]) or s["club"]

        # Club picker - which clubs have data
        clubs_with_data = {s["club"] for s in shots if s.get("club")}
        # Show canonical clubs first (in order), then any custom labels at the end
        clubs_to_show = [c for c in CLUBS_ORDER if c in clubs_with_data]
        custom_clubs = sorted(clubs_with_data - set(CLUBS_ORDER) - {"Unknown"})
        clubs_to_show = clubs_to_show + custom_clubs

        if not clubs_to_show:
            st.info("Log shots in the Quick Log tab to see your dispersion pattern here.")
        else:
            _render_range_view(shots, clubs_to_show)

    # === QUICK LOG ===
    with tab2:
        _render_quick_log()

    # === BY CLUB ===
    with tab3:
        _render_by_club(shots)

    # === CSV IMPORT ===
    with tab4:
        _render_csv_import()


def _render_range_view(shots, clubs_to_show):
        # Club picker buttons
        if "selected_club" not in st.session_state:
            st.session_state["selected_club"] = "7i" if "7i" in clubs_to_show else clubs_to_show[0]

        st.markdown(f"<div style='font-size:11px;color:{COLORS['cream_dim']};letter-spacing:0.18em;text-transform:uppercase;font-weight:700;margin-bottom:10px;'>Select Club</div>", unsafe_allow_html=True)
        # Render club buttons in rows of 6
        for row_start in range(0, len(clubs_to_show), 6):
            row = clubs_to_show[row_start:row_start + 6]
            cols = st.columns(6)
            for i, c in enumerate(row):
                with cols[i]:
                    is_active = c == st.session_state["selected_club"]
                    if st.button(
                        f"{CLUB_ICONS.get(c, '⛳')} {c}",
                        key=f"clb_{c}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary",
                    ):
                        st.session_state["selected_club"] = c
                        st.rerun()
            # Pad row
            for j in range(len(row), 6):
                with cols[j]:
                    st.markdown("&nbsp;", unsafe_allow_html=True)

        st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

        # Get shots for selected club
        c = st.session_state["selected_club"]
        club_shots = [s for s in shots if s.get("club") == c]

        # Stats row
        carries = [s.get("carry", 0) for s in club_shots]
        offlines = [s.get("offline_y", 0) for s in club_shots]
        avg_carry = round(np.mean(carries)) if carries else 0
        max_carry = round(max(carries)) if carries else 0
        car_std = round(np.std(carries), 1) if len(carries) > 1 else 0
        off_std = round(np.std(offlines), 1) if len(offlines) > 1 else 0
        di = _dispersion_index(club_shots)
        tour_carry = TOUR_CARRY.get(c, avg_carry)

        s1, s2, s3, s4, s5 = st.columns(5)
        with s1: st.markdown(f"<div class='gj-card-flush' style='text-align:center;padding:16px 8px;'><div class='hero-stat-label'>AVG CARRY</div><div style='font-family:Fraunces,serif;font-size:32px;font-weight:700;color:{COLORS['cream']};'>{avg_carry}<span style='font-size:14px;color:{COLORS['cream_dim']};'>y</span></div></div>", unsafe_allow_html=True)
        with s2: st.markdown(f"<div class='gj-card-flush' style='text-align:center;padding:16px 8px;'><div class='hero-stat-label'>MAX CARRY</div><div style='font-family:Fraunces,serif;font-size:32px;font-weight:700;color:{COLORS['cream']};'>{max_carry}<span style='font-size:14px;color:{COLORS['cream_dim']};'>y</span></div></div>", unsafe_allow_html=True)
        with s3: st.markdown(f"<div class='gj-card-flush' style='text-align:center;padding:16px 8px;'><div class='hero-stat-label'>± CARRY</div><div style='font-family:Fraunces,serif;font-size:32px;font-weight:700;color:{COLORS['cream']};'>{car_std}<span style='font-size:14px;color:{COLORS['cream_dim']};'>y</span></div></div>", unsafe_allow_html=True)
        with s4: st.markdown(f"<div class='gj-card-flush' style='text-align:center;padding:16px 8px;'><div class='hero-stat-label'>± OFFLINE</div><div style='font-family:Fraunces,serif;font-size:32px;font-weight:700;color:{COLORS['cream']};'>{off_std}<span style='font-size:14px;color:{COLORS['cream_dim']};'>y</span></div></div>", unsafe_allow_html=True)
        with s5:
            color = COLORS["fairway_2"] if di and di >= 70 else (COLORS["flag"] if di and di >= 50 else COLORS["danger"])
            st.markdown(f"<div class='gj-card-flush' style='text-align:center;padding:16px 8px;'><div class='hero-stat-label'>DISPERSION INDEX</div><div style='font-family:Fraunces,serif;font-size:32px;font-weight:700;color:{color};'>{di if di is not None else '—'}<span style='font-size:14px;color:{COLORS['cream_dim']};'>/100</span></div></div>", unsafe_allow_html=True)

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

        # The range visualization
        fig = _digital_range(club_shots, c, tour_carry)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Vs Tour comparison
        cmp = carry_vs_tour(c, avg_carry)
        if cmp:
            delta_color = COLORS["fairway_2"] if cmp["delta"] >= -10 else COLORS["flag"]
            st.markdown(
                f"""
                <div class="gj-card-flush" style="margin-top:8px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div>
                            <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.18em;text-transform:uppercase;font-weight:700;">vs PGA Tour</div>
                            <div style="font-size:18px;color:{COLORS['cream']};font-weight:600;margin-top:4px;">Your {c}: <span style="color:{COLORS['flag']};font-family:Fraunces,serif;font-weight:700;">{avg_carry}y</span> · Tour avg: {cmp['tour']}y</div>
                            <div style="font-size:13px;color:{COLORS['cream_dim']};margin-top:4px;">{cmp['verdict']} — you're at {cmp['pct']:.0f}% of Tour avg distance.</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-family:Fraunces,serif;font-size:42px;font-weight:700;color:{delta_color};line-height:1;">{cmp['delta']:+}</div>
                            <div style="font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.15em;text-transform:uppercase;font-weight:700;">yards delta</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Update saved metric
        if di is not None:
            update_metric("dispersion_index", di)


def _render_quick_log():
        st.markdown(f"<div style='color:{COLORS['cream_dim']};font-size:14px;margin-bottom:14px;'>Log a quick shot — auto-saved.</div>", unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            club = st.selectbox("Club", CLUBS_ORDER, index=CLUBS_ORDER.index("7i"))
        with col2:
            carry = st.number_input("Carry (yds)", min_value=20, max_value=350, value=155, step=1)
        with col3:
            offline = st.number_input("Offline (yds, +R/-L)", min_value=-60, max_value=60, value=0, step=1)
        with col4:
            ball_speed = st.number_input("Ball speed (mph, opt)", min_value=0, max_value=200, value=0, step=1)

        if st.button("Log Shot", type="primary", use_container_width=True):
            row = {
                "date": datetime.now().date().isoformat(),
                "club": club,
                "carry": carry,
                "offline_y": offline,
            }
            if ball_speed > 0:
                row["ball_speed"] = ball_speed
            append_practice(row)
            st.success(f"Logged: {club} {carry}y, {offline:+}y offline")
            st.rerun()


def _render_by_club(shots):
        if not shots:
            st.info("No shots logged yet.")
        else:
            # Normalize club names so all of them surface (not just canonical irons)
            for s in shots:
                if s.get("club"):
                    s["club"] = normalize_club(s["club"]) or s["club"]
            df = pd.DataFrame(shots)
            present_canonical = [c for c in CLUBS_ORDER if c in df["club"].values]
            present_custom = sorted(set(df["club"].values) - set(CLUBS_ORDER))
            order = present_canonical + present_custom
            agg = df.groupby("club").agg(
                avg_carry=("carry", "mean"),
                max_carry=("carry", "max"),
                std_carry=("carry", "std"),
                shots=("carry", "count"),
            ).round(1).reindex(order)
            agg["tour_avg"] = [TOUR_CARRY.get(c, "—") for c in agg.index]
            agg["delta"] = agg.apply(lambda r: round(r["avg_carry"] - r["tour_avg"]) if isinstance(r["tour_avg"], (int, float)) else "—", axis=1)
            agg = agg.rename(columns={
                "avg_carry": "Avg Carry",
                "max_carry": "Max",
                "std_carry": "± StDev",
                "shots": "Shots",
                "tour_avg": "Tour Avg",
                "delta": "vs Tour",
            })
            st.dataframe(agg, use_container_width=True)


def _render_csv_import():
        st.markdown(
            f"""
            <div class="gj-card-flush">
                <h3 style='margin:0 0 8px;'>📤 Auto-import Rapsodo CSV</h3>
                <div style='color:{COLORS["cream_dim"]};font-size:13px;line-height:1.6;'>
                Drop your Rapsodo session export below. We auto-detect the columns — no mapping required.
                Supported: <b>Carry, Total, Ball Speed, Club Speed, Side / Offline, Apex, Club</b>.
                </div>
            </div>
            <div style='height:12px;'></div>
            """,
            unsafe_allow_html=True,
        )
        f = st.file_uploader("Drop CSV here", type=["csv"], label_visibility="collapsed")
        if f:
            try:
                df = pd.read_csv(f)
                # Auto-detect columns case-insensitively
                cols = {c.lower().strip(): c for c in df.columns}
                def find(*keys):
                    for k in keys:
                        for col_low, col_orig in cols.items():
                            if k in col_low:
                                return col_orig
                    return None

                club_col = find("club name", "club")
                carry_col = find("carry")
                ball_col = find("ball speed")
                club_speed_col = find("club speed", "head speed")
                side_col = find("side", "offline", "lateral")
                apex_col = find("apex", "height")

                preview_rows = []
                for _, r in df.iterrows():
                    row = {"date": datetime.now().date().isoformat()}
                    if club_col:
                        row["club"] = normalize_club(r[club_col])
                    if not row.get("club"):
                        # No club label → skip silently rather than dropping shot under "unknown"
                        row["club"] = "Unknown"
                    if carry_col and pd.notna(r[carry_col]):
                        try: row["carry"] = float(r[carry_col])
                        except: continue
                    if ball_col and pd.notna(r[ball_col]):
                        try: row["ball_speed"] = float(r[ball_col])
                        except: pass
                    if club_speed_col and pd.notna(r[club_speed_col]):
                        try: row["club_speed"] = float(r[club_speed_col])
                        except: pass
                    if side_col and pd.notna(r[side_col]):
                        try: row["offline_y"] = float(r[side_col])
                        except: pass
                    if apex_col and pd.notna(r[apex_col]):
                        try: row["apex_ft"] = float(r[apex_col])
                        except: pass
                    if "carry" in row:
                        preview_rows.append(row)

                st.success(f"Detected {len(preview_rows)} valid shots. Preview:")
                st.dataframe(pd.DataFrame(preview_rows[:10]), use_container_width=True)
                if st.button(f"Import all {len(preview_rows)} shots", type="primary", use_container_width=True):
                    append_practice(preview_rows)
                    st.success(f"✅ Imported {len(preview_rows)} shots.")
                    st.rerun()
            except Exception as e:
                st.error(f"Could not parse CSV: {e}")
