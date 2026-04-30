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
CLUB_ICONS = {
    "Driver": "🏌️", "3W": "🏌️", "5H": "🪵",
    "5i": "🎯", "6i": "🎯", "7i": "🎯", "8i": "🎯", "9i": "🎯",
    "PW": "⛳", "GW": "⛳", "SW": "⛳", "LW": "⛳",
}


def _digital_range(shots, club_name, target_carry):
    """Render a top-down driving-range view with shot landings."""
    fig = go.Figure()

    # Range background — fairway gradient with yard markers
    max_y = max(target_carry * 1.2, 280)
    width = max(80, target_carry * 0.4)

    # Fairway shape (slight perspective)
    fig.add_trace(go.Scatter(
        x=[-width/1.5, width/1.5, width, -width, -width/1.5],
        y=[0, 0, max_y, max_y, 0],
        fill="toself",
        fillcolor="rgba(20, 100, 50, 0.35)",
        line=dict(color=COLORS["fairway_2"], width=2),
        hoverinfo="skip", showlegend=False,
    ))

    # Distance markers / target greens at 50-yd increments
    for d in range(50, int(max_y), 50):
        fig.add_trace(go.Scatter(
            x=[-width * (d / max_y) * 1.05, width * (d / max_y) * 1.05],
            y=[d, d],
            mode="lines",
            line=dict(color="rgba(245,239,224,0.18)", width=1, dash="dash"),
            hoverinfo="skip", showlegend=False,
        ))
        fig.add_annotation(
            x=width * (d / max_y) * 1.05, y=d,
            text=f"{d}y", showarrow=False,
            font=dict(color="rgba(245,239,224,0.6)", size=10, family="Inter"),
            xanchor="left", xshift=8,
        )

    # Target green at target_carry
    theta = np.linspace(0, 2 * np.pi, 50)
    green_r = 12
    fig.add_trace(go.Scatter(
        x=green_r * np.cos(theta) * (width / max_y),
        y=target_carry + green_r * np.sin(theta) * 0.6,
        fill="toself",
        fillcolor="rgba(255, 215, 100, 0.25)",
        line=dict(color=COLORS["flag"], width=2),
        hoverinfo="skip", showlegend=False,
    ))
    # Pin/flag
    fig.add_trace(go.Scatter(
        x=[0, 0], y=[target_carry, target_carry + 8],
        mode="lines", line=dict(color=COLORS["flag"], width=2),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_annotation(
        x=0, y=target_carry + 8, text="🚩", showarrow=False, font=dict(size=18),
        xshift=8, yshift=4,
    )
    fig.add_annotation(
        x=0, y=target_carry - 18, text=f"<b>{target_carry}y</b>",
        showarrow=False, font=dict(color=COLORS["flag"], size=13, family="Fraunces"),
    )

    # Tee box
    fig.add_trace(go.Scatter(
        x=[-15, 15, 15, -15, -15], y=[-5, -5, 0, 0, -5],
        fill="toself", fillcolor="rgba(212,162,76,0.4)",
        line=dict(color=COLORS["flag"], width=1),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_annotation(x=0, y=-3, text="TEE", showarrow=False,
                       font=dict(color=COLORS["bg"], size=10, family="Inter"))

    # Plot user's actual shots
    if shots:
        carries = [s.get("carry", 0) for s in shots]
        offlines = [s.get("offline_y", 0) for s in shots]
        # Trail lines from tee to landing
        for c, o in zip(carries, offlines):
            fig.add_trace(go.Scatter(
                x=[0, o], y=[0, c],
                mode="lines",
                line=dict(color="rgba(212,162,76,0.18)", width=1),
                hoverinfo="skip", showlegend=False,
            ))
        # Landing dots
        fig.add_trace(go.Scatter(
            x=offlines, y=carries,
            mode="markers",
            marker=dict(
                size=11, color=COLORS["flag"],
                line=dict(color="rgba(0,0,0,0.6)", width=1),
                symbol="circle",
            ),
            text=[f"Carry: {c:.0f}y<br>Offline: {o:+.0f}y" for c, o in zip(carries, offlines)],
            hoverinfo="text",
            showlegend=False,
        ))
        # Mean ball
        mean_c = np.mean(carries)
        mean_o = np.mean(offlines)
        fig.add_trace(go.Scatter(
            x=[mean_o], y=[mean_c],
            mode="markers",
            marker=dict(size=22, color=COLORS["cream"],
                        line=dict(color=COLORS["fairway_2"], width=3),
                        symbol="circle"),
            hovertext=f"Mean: {mean_c:.0f}y, {mean_o:+.0f}y",
            hoverinfo="text",
            showlegend=False,
        ))

    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False, range=[-width * 1.3, width * 1.3], scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False, range=[-15, max_y + 30]),
        plot_bgcolor=COLORS["bg_2"],
        paper_bgcolor=COLORS["bg_2"],
        margin=dict(l=0, r=0, t=10, b=0),
        height=560,
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
        # Club picker - which clubs have data
        clubs_with_data = {s["club"] for s in shots if s.get("club")}
        clubs_to_show = [c for c in CLUBS_ORDER if c in clubs_with_data]

        if not clubs_to_show:
            st.info("Log shots in the Quick Log tab to see your dispersion pattern here.")
            return

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

    # === QUICK LOG ===
    with tab2:
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

    # === BY CLUB ===
    with tab3:
        if not shots:
            st.info("No shots logged yet.")
        else:
            df = pd.DataFrame(shots)
            agg = df.groupby("club").agg(
                avg_carry=("carry", "mean"),
                max_carry=("carry", "max"),
                std_carry=("carry", "std"),
                shots=("carry", "count"),
            ).round(1).reindex([c for c in CLUBS_ORDER if c in df["club"].values])
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

    # === CSV IMPORT ===
    with tab4:
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
                    if club_col: row["club"] = str(r[club_col])
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
