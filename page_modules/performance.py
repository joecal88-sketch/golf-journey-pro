"""Performance Stats — score trends + course breakdown + strengths/weaknesses."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from cloud_storage import load_data
from styles import COLORS
from insights import par_type_weakness, course_history, hole_weakness, TOUR_BENCH


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
