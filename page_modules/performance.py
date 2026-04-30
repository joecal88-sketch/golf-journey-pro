"""Performance — score trend, by-course, putts vs GIR, USGA handicap."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from cloud_storage import load_data
from weekly_summary import get_summary


def render():
    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="page-eyebrow">ALL-TIME · TRENDS</div>
                <div class="page-title">Performance</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    summary = get_summary()
    rounds = load_data().get("rounds", [])
    practice = load_data().get("practice", [])
    speed = load_data().get("speed", [])

    # ── Top KPIs ──
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rounds", summary.get("rounds_count", 0))
    c2.metric("Best Score", summary.get("best_score") or "—")
    c3.metric("Practice Shots", len(practice))
    c4.metric("Speed Sessions", len(speed))

    if not rounds:
        st.info("Log rounds to unlock trend analysis.")
        return

    df = pd.DataFrame(rounds)
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df["par"] = pd.to_numeric(df.get("par", 70), errors="coerce")
    df["putts"] = pd.to_numeric(df.get("putts", 0), errors="coerce")
    df["gir"] = pd.to_numeric(df.get("gir", 0), errors="coerce")
    df["fir"] = pd.to_numeric(df.get("fir", 0), errors="coerce")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["score", "date"]).sort_values("date")

    full = df[df["par"] >= 65].copy()  # regulation rounds only

    # ── Score trend with break-80 line ──
    st.markdown('<div class="section-label" style="margin-top:24px;">SCORE TREND · REGULATION COURSES</div>', unsafe_allow_html=True)

    if len(full) > 0:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=full["date"], y=full["score"], mode="lines+markers",
            line=dict(color="#00D4AA", width=3),
            marker=dict(size=12, color="#00D4AA", line=dict(color="#000", width=1)),
            name="Score",
            hovertemplate="<b>%{x|%b %d}</b><br>Score: %{y}<extra></extra>",
        ))
        if len(full) >= 3:
            rolling = full["score"].rolling(window=3, min_periods=1).mean()
            fig.add_trace(go.Scatter(
                x=full["date"], y=rolling, mode="lines",
                line=dict(color="#FFB800", width=2, dash="dash"),
                name="3-Round Avg",
            ))
        fig.add_hline(
            y=80, line=dict(color="#FF6B35", width=2, dash="dot"),
            annotation_text="Break 80", annotation_position="top right",
            annotation_font_color="#FF6B35", annotation_font_size=12,
        )
        fig.update_layout(
            plot_bgcolor="#0A0A0A", paper_bgcolor="#0A0A0A",
            font=dict(family="Inter", color="#CCC"),
            height=420, margin=dict(t=30, b=30, l=30, r=30),
            xaxis=dict(gridcolor="#1A1A1A"),
            yaxis=dict(title="Score", gridcolor="#1A1A1A"),
            legend=dict(bgcolor="rgba(0,0,0,0)", x=0, y=1.1, orientation="h"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── By-course breakdown ──
    if "course" in df.columns:
        st.markdown('<div class="section-label">BY COURSE</div>', unsafe_allow_html=True)
        by_course = df.groupby("course").agg(
            Rounds=("score", "count"),
            Avg=("score", "mean"),
            Best=("score", "min"),
            AvgPar=("par", "mean"),
        ).reset_index()
        by_course["Avg"] = by_course["Avg"].round(1)
        by_course["AvgPar"] = by_course["AvgPar"].round(0).astype(int)
        by_course["vs Par"] = (by_course["Avg"] - by_course["AvgPar"]).round(1)
        by_course = by_course.rename(columns={"course": "Course", "AvgPar": "Par"})
        st.dataframe(
            by_course[["Course", "Rounds", "Avg", "Best", "Par", "vs Par"]],
            use_container_width=True, hide_index=True,
        )

    # ── Putts vs GIR dual chart ──
    st.markdown('<div class="section-label">PUTTS · GIR · FAIRWAYS</div>', unsafe_allow_html=True)
    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(
        go.Bar(
            x=full["date"], y=full["putts"], name="Putts",
            marker=dict(color="#4A9EFF", opacity=0.85),
        ),
        secondary_y=False,
    )
    fig2.add_trace(
        go.Scatter(
            x=full["date"], y=full["gir"], mode="lines+markers", name="GIR",
            line=dict(color="#00D4AA", width=3),
            marker=dict(size=10, color="#00D4AA", line=dict(color="#000", width=1)),
        ),
        secondary_y=True,
    )
    fig2.add_trace(
        go.Scatter(
            x=full["date"], y=full["fir"], mode="lines+markers", name="Fairways",
            line=dict(color="#FFB800", width=3),
            marker=dict(size=10, color="#FFB800", line=dict(color="#000", width=1)),
        ),
        secondary_y=True,
    )
    fig2.update_layout(
        plot_bgcolor="#0A0A0A", paper_bgcolor="#0A0A0A",
        font=dict(family="Inter", color="#CCC"),
        height=400, margin=dict(t=30, b=30, l=30, r=30),
        legend=dict(bgcolor="rgba(0,0,0,0)", x=0, y=1.15, orientation="h"),
        xaxis=dict(gridcolor="#1A1A1A"),
    )
    fig2.update_yaxes(title_text="Putts", gridcolor="#1A1A1A", secondary_y=False)
    fig2.update_yaxes(title_text="GIR / Fairways (of 18)", gridcolor="rgba(0,0,0,0)", secondary_y=True, range=[0, 18])
    st.plotly_chart(fig2, use_container_width=True)

    # ── Stats summary cards ──
    cs1, cs2, cs3 = st.columns(3)
    if len(full) > 0:
        cs1.metric("Avg Putts", f"{full['putts'].mean():.1f}", help="Tour avg ~29")
        cs2.metric("Avg GIR", f"{full['gir'].mean():.1f} / 18", help="Break-80 target: 7+")
        cs3.metric("Avg Fairways", f"{full['fir'].mean():.1f} / 18", help="Solid: 8+")
