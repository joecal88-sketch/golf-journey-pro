"""Performance Stats — score trends + course breakdown + strengths/weaknesses."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from cloud_storage import load_data
from styles import COLORS
from insights import par_type_weakness, course_history, hole_weakness, TOUR_BENCH, TOUR_CARRY


def render():
    st.markdown(
        f"""
        <div style="margin:8px 0 22px;">
            <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.25em;text-transform:uppercase;font-weight:800;">📈 PERFORMANCE</div>
            <h1 style="margin:6px 0 4px;font-size:42px;">Your Numbers</h1>
            <div style="color:{COLORS['cream_dim']};font-size:15px;">Trends, courses, strengths and weaknesses — all in one view.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    data = load_data()
    rounds = data.get("rounds", []) or []
    if not rounds:
        st.info("No rounds yet. Log one in Live Round to populate stats.")
        return

    df = pd.DataFrame(rounds)

    # === Score trend ===
    st.markdown(
        f"""
        <div class="section-header">
            <span class="eyebrow">Trend</span>
            <h2>Score over time</h2>
            <span class="accent"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    df["over_par"] = df["score"] - df["par"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["over_par"], mode="lines+markers",
        line=dict(color=COLORS["fairway_2"], width=3),
        marker=dict(size=10, color=COLORS["flag"], line=dict(color=COLORS["fairway_2"], width=2)),
        text=[f"{r['course']}: {r['score']} (+{r['score'] - r['par']})" for _, r in df.iterrows()],
        hoverinfo="text",
        name="Over par",
    ))
    # Zero line
    fig.add_shape(type="line", x0=df["date"].min(), x1=df["date"].max(), y0=0, y1=0,
                  line=dict(color=COLORS["cream_dim"], width=1, dash="dash"))
    fig.update_layout(
        plot_bgcolor=COLORS["bg_2"],
        paper_bgcolor=COLORS["bg_2"],
        font=dict(color=COLORS["cream"], family="Inter"),
        xaxis=dict(showgrid=False, title=""),
        yaxis=dict(gridcolor=COLORS["border"], title="Strokes over par"),
        margin=dict(l=10, r=10, t=10, b=10),
        height=320, showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # === BIG You vs Tour Hub ===
    _render_you_vs_tour_hub(rounds, data.get("practice_shots", []) or [])

    # === By Course ===
    st.markdown(
        f"""
        <div class="section-header">
            <span class="eyebrow">Courses</span>
            <h2>Performance by course</h2>
            <span class="accent"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    courses = df["course"].unique()
    for c in courses:
        sub = df[df["course"] == c]
        scores = sub["score"].tolist()
        best = min(scores)
        avg = round(sum(scores) / len(scores), 1)
        last = scores[-1]
        plays = len(scores)
        weak_par = par_type_weakness(c)
        weak_str = ""
        if weak_par:
            worst_par, worst_diff = max(weak_par.items(), key=lambda x: x[1])
            if worst_diff > 0.4:
                weak_str = f"Weakness: <b>Par {worst_par}s</b> (avg +{worst_diff} vs par)"

        st.markdown(
            f"""
            <div class="gj-card-flush" style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;">
                    <div>
                        <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.18em;text-transform:uppercase;font-weight:700;">{plays} plays</div>
                        <div style="font-family:Fraunces,serif;font-size:22px;font-weight:700;color:{COLORS['cream']};margin-top:4px;">{c}</div>
                        <div style="font-size:13px;color:{COLORS['cream_dim']};margin-top:6px;">{weak_str}</div>
                    </div>
                    <div style="display:flex;gap:18px;">
                        <div style="text-align:center;">
                            <div style="font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.15em;font-weight:700;">BEST</div>
                            <div style="font-family:Fraunces,serif;font-size:26px;color:{COLORS['fairway_2']};font-weight:700;">{best}</div>
                        </div>
                        <div style="text-align:center;">
                            <div style="font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.15em;font-weight:700;">AVG</div>
                            <div style="font-family:Fraunces,serif;font-size:26px;color:{COLORS['cream']};font-weight:700;">{avg}</div>
                        </div>
                        <div style="text-align:center;">
                            <div style="font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.15em;font-weight:700;">LAST</div>
                            <div style="font-family:Fraunces,serif;font-size:26px;color:{COLORS['cream']};font-weight:700;">{last}</div>
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # === Putts/GIR/FIR averages with Tour comparison ===
    st.markdown(
        f"""
        <div class="section-header">
            <span class="eyebrow">Stats</span>
            <h2>Round averages</h2>
            <span class="accent"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    putts_avg = round(df["putts"].mean(), 1) if "putts" in df else None
    gir_avg = round(df["gir"].mean(), 1) if "gir" in df else None
    fir_avg = round(df["fir"].mean(), 1) if "fir" in df else None

    c1, c2, c3 = st.columns(3)
    if putts_avg is not None:
        with c1:
            delta = putts_avg - TOUR_BENCH["putts_per_round"]
            color = COLORS["fairway_2"] if delta <= 1 else COLORS["flag"]
            st.markdown(
                f"""
                <div class="gj-card-flush" style="text-align:center;">
                    <div class="hero-stat-label">PUTTS / ROUND</div>
                    <div style="font-family:Fraunces,serif;font-size:48px;font-weight:700;color:{COLORS['cream']};line-height:1;">{putts_avg}</div>
                    <div style="font-size:12px;color:{color};margin-top:6px;font-weight:700;">{delta:+.1f} vs Tour ({TOUR_BENCH['putts_per_round']})</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    if gir_avg is not None:
        with c2:
            gir_pct = round(gir_avg / 18 * 100)
            delta = gir_pct - TOUR_BENCH["gir_pct"]
            color = COLORS["fairway_2"] if delta >= -10 else COLORS["flag"]
            st.markdown(
                f"""
                <div class="gj-card-flush" style="text-align:center;">
                    <div class="hero-stat-label">GIR / ROUND</div>
                    <div style="font-family:Fraunces,serif;font-size:48px;font-weight:700;color:{COLORS['cream']};line-height:1;">{gir_avg}<span style='font-size:18px;color:{COLORS['cream_dim']};'>/18</span></div>
                    <div style="font-size:12px;color:{color};margin-top:6px;font-weight:700;">{gir_pct}% vs Tour {TOUR_BENCH['gir_pct']}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    if fir_avg is not None:
        with c3:
            fir_pct = round(fir_avg / 14 * 100)
            delta = fir_pct - TOUR_BENCH["fairway_pct"]
            color = COLORS["fairway_2"] if delta >= -10 else COLORS["flag"]
            st.markdown(
                f"""
                <div class="gj-card-flush" style="text-align:center;">
                    <div class="hero-stat-label">FAIRWAYS / ROUND</div>
                    <div style="font-family:Fraunces,serif;font-size:48px;font-weight:700;color:{COLORS['cream']};line-height:1;">{fir_avg}<span style='font-size:18px;color:{COLORS['cream_dim']};'>/14</span></div>
                    <div style="font-size:12px;color:{color};margin-top:6px;font-weight:700;">{fir_pct}% vs Tour {TOUR_BENCH['fairway_pct']}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # === Hole-by-hole heatmap if data ===
    has_holes = any(r.get("holes") for r in rounds)
    if has_holes:
        st.markdown(
            f"""
            <div class="section-header">
                <span class="eyebrow">Holes</span>
                <h2>Where you struggle</h2>
                <span class="accent"></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for c in courses:
            weak = hole_weakness(c)
            if not weak: continue
            st.markdown(f"<div style='font-size:13px;color:{COLORS['flag']};letter-spacing:0.15em;text-transform:uppercase;font-weight:700;margin:14px 0 8px;'>{c}</div>", unsafe_allow_html=True)
            for w in weak:
                width = min(100, int(w["avg_over_par"] * 30))
                st.markdown(
                    f"""
                    <div class="gauge-row">
                        <div class="gauge-label">
                            <span class="name">Hole {w['hole']}</span>
                            <span class="vals"><span class="you">+{w['avg_over_par']} avg</span> · <span class="pro">{w['plays']} plays</span></span>
                        </div>
                        <div class="gauge-track">
                            <div class="gauge-fill danger" style="width:{width}%;"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _big_gauge(name, you, pro, lower_is_better=False, unit="", emoji="📊"):
    """A larger, tier-colored gauge for the You vs Tour hub."""
    if you is None or pro is None or pro == 0:
        return ""
    pct = (pro / you) * 100 if lower_is_better else (you / pro) * 100
    pct = max(0, min(115, pct))
    if pct >= 90:
        tier_color, tier_label = COLORS["fairway_2"], "TOUR LEVEL"
    elif pct >= 75:
        tier_color, tier_label = COLORS["flag"], "STRONG"
    elif pct >= 55:
        tier_color, tier_label = "#d4a24c", "DEVELOPING"
    else:
        tier_color, tier_label = COLORS["danger"], "GROW HERE"

    delta_str = ""
    if isinstance(you, (int, float)) and isinstance(pro, (int, float)):
        diff = (you - pro) if not lower_is_better else (pro - you)
        sign = "+" if diff >= 0 else ""
        delta_str = f"{sign}{round(diff, 1)}{unit}"

    return (
        f'<div class="big-gauge">'
        f'  <div class="bg-head">'
        f'    <span class="bg-emoji">{emoji}</span>'
        f'    <span class="bg-name">{name}</span>'
        f'    <span class="bg-tier" style="background:{tier_color}25;color:{tier_color};border-color:{tier_color}80;">{tier_label}</span>'
        f'  </div>'
        f'  <div class="bg-vals">'
        f'    <span class="bg-you" style="color:{tier_color};">{you}{unit}</span>'
        f'    <span class="bg-pro">vs Tour {pro}{unit}</span>'
        f'    <span class="bg-delta" style="color:{tier_color};">{delta_str}</span>'
        f'  </div>'
        f'  <div class="bg-track"><div class="bg-fill" style="width:{pct}%;background:linear-gradient(90deg,{tier_color}80,{tier_color});"></div></div>'
        f'</div>'
    )


def _render_you_vs_tour_hub(rounds, shots):
    """Beefy hub with 12+ comparison metrics."""
    st.markdown(
        f"""
        <div class="section-header">
            <span class="eyebrow">Benchmark</span>
            <h2>You vs the Tour</h2>
            <span class="accent"></span>
        </div>
        <div style="color:{COLORS['cream_dim']};font-size:13px;margin:-10px 0 14px;">
          12+ live comparisons against PGA Tour averages. Tier-colored: Tour-level → Strong → Developing → Grow here.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"""
    <style>
      .big-gauge {{
        background: linear-gradient(160deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
        border: 1px solid {COLORS['border']};
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 12px;
        backdrop-filter: blur(10px);
      }}
      .bg-head {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
      .bg-emoji {{ font-size:20px; }}
      .bg-name {{ flex:1; font-weight:700; color:{COLORS['cream']}; font-size:14px; }}
      .bg-tier {{
        font-size:9px; font-weight:800; letter-spacing:0.18em; padding:3px 8px;
        border-radius:999px; border:1px solid;
      }}
      .bg-vals {{ display:flex; align-items:baseline; gap:10px; margin:10px 0 8px; flex-wrap:wrap; }}
      .bg-you {{ font-family:'Fraunces',serif; font-size:28px; font-weight:700; line-height:1; }}
      .bg-pro {{ font-size:12px; color:{COLORS['cream_dim']}; }}
      .bg-delta {{ margin-left:auto; font-size:12px; font-weight:700; }}
      .bg-track {{ height:8px; background:rgba(255,255,255,0.06); border-radius:999px; overflow:hidden; }}
      .bg-fill {{ height:100%; border-radius:999px; transition:width 0.6s ease-out; }}
    </style>
    """, unsafe_allow_html=True)

    # Compute all user metrics
    putts = [r.get("putts") for r in rounds if r.get("putts")]
    gir = [r.get("gir") for r in rounds if r.get("gir") is not None]
    fir = [r.get("fir") for r in rounds if r.get("fir") is not None]
    scores = [r.get("score") for r in rounds if r.get("score")]
    pars = [r.get("par", 72) for r in rounds]

    user_putts = round(sum(putts) / len(putts), 1) if putts else None
    user_gir = round(sum(gir) / len(gir) / 18 * 100, 1) if gir else None
    user_fir = round(sum(fir) / len(fir) / 14 * 100, 1) if fir else None
    user_score = round(sum(scores) / len(scores), 1) if scores else None

    # 3-putt %, birdies, bogey-avoidance from holes
    n_holes = 0; three_putts = 0; birdies = 0; bogey_or_worse = 0; total_under = 0
    for r in rounds:
        for h in r.get("holes", []) or []:
            n_holes += 1
            sc = h.get("score"); pr = h.get("par", 4)
            if sc is None: continue
            if sc - pr <= -1: birdies += 1
            if sc - pr >= 1: bogey_or_worse += 1
    user_birdies = round(birdies / len(rounds), 1) if rounds else None
    user_bogey_avoid = round((1 - bogey_or_worse / n_holes) * 100, 1) if n_holes else None

    # Practice shot metrics
    drivers = [s for s in shots if s.get("club") == "Driver"]
    user_drv_carry = round(sum(s["carry"] for s in drivers) / len(drivers)) if drivers else None
    user_drv_speed = round(sum(s.get("ball_speed", 0) for s in drivers if s.get("ball_speed")) / max(1, len([s for s in drivers if s.get("ball_speed")])), 1) if drivers else None
    user_drv_clubspeed = round(sum(s.get("club_speed", 0) for s in drivers if s.get("club_speed")) / max(1, len([s for s in drivers if s.get("club_speed")])), 1) if drivers else None
    user_drv_apex = round(sum(s.get("apex_ft", 0) for s in drivers if s.get("apex_ft")) / max(1, len([s for s in drivers if s.get("apex_ft")])), 1) if drivers else None

    sevens = [s for s in shots if s.get("club") == "7i"]
    user_7i = round(sum(s["carry"] for s in sevens) / len(sevens)) if sevens else None
    irons = [s for s in shots if s.get("club") in ("5i", "6i", "7i", "8i", "9i", "PW")]
    user_iron_disp = round(sum(abs(s.get("offline_y", 0)) for s in irons) / max(1, len(irons)), 1) if irons else None

    # Render in 2-column grid
    metrics = [
        _big_gauge("Score per round", user_score, TOUR_BENCH["score_avg"], lower_is_better=True, emoji="🎯"),
        _big_gauge("Putts per round", user_putts, TOUR_BENCH["putts_per_round"], lower_is_better=True, emoji="🥅"),
        _big_gauge("Greens in regulation", user_gir, TOUR_BENCH["gir_pct"], unit="%", emoji="🌱"),
        _big_gauge("Fairways hit", user_fir, TOUR_BENCH["fairway_pct"], unit="%", emoji="🛣️"),
        _big_gauge("Birdies per round", user_birdies, TOUR_BENCH["birdies_per_round"], emoji="🐦"),
        _big_gauge("Bogey avoidance", user_bogey_avoid, TOUR_BENCH["bogey_avoidance_pct"], unit="%", emoji="🛡️"),
        _big_gauge("Driver carry", user_drv_carry, TOUR_CARRY["Driver"], unit="y", emoji="🚀"),
        _big_gauge("Driver ball speed", user_drv_speed, TOUR_BENCH["driver_speed_mph"], unit=" mph", emoji="⚡"),
        _big_gauge("Driver club speed", user_drv_clubspeed, TOUR_BENCH["club_speed_mph"], unit=" mph", emoji="💨"),
        _big_gauge("Driver apex", user_drv_apex, TOUR_BENCH["apex_ft"], unit=" ft", emoji="📈"),
        _big_gauge("7-iron carry", user_7i, TOUR_CARRY["7i"], unit="y", emoji="🎳"),
        _big_gauge("Iron dispersion (lower=better)", user_iron_disp, 5.0, lower_is_better=True, unit="y", emoji="🎯"),
    ]
    metrics = [m for m in metrics if m]

    # Two columns for grid layout
    half = (len(metrics) + 1) // 2
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("".join(metrics[:half]), unsafe_allow_html=True)
    with col_r:
        st.markdown("".join(metrics[half:]), unsafe_allow_html=True)
