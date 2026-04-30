"""Command Center — hero stats, smart insights, pro comparison, stroke-saver."""
import streamlit as st
from cloud_storage import load_data
from styles import COLORS
from insights import smart_insights, TOUR_BENCH, TOUR_CARRY
from drills import get_by_id


def _gauge(name: str, you, pro, lower_is_better=False, unit=""):
    """Render a comparison gauge."""
    if you is None or pro is None:
        return ""
    pct = (pro / you) * 100 if lower_is_better else (you / pro) * 100
    pct = max(0, min(115, pct))
    color = "fairway" if pct >= 90 else ("gold" if pct >= 70 else "")
    fill_class = "" if pct >= 80 else "danger"
    return (
        f'<div class="gauge-row">'
        f'<div class="gauge-label">'
        f'<span class="name">{name}</span>'
        f'<span class="vals"><span class="you">{you}{unit}</span> · <span class="pro">Tour {pro}{unit}</span></span>'
        f'</div>'
        f'<div class="gauge-track">'
        f'<div class="gauge-fill {fill_class}" style="width:{pct}%"></div>'
        f'</div>'
        f'</div>'
    )


def _hero_block(label, value, unit="", sub=""):
    return f"""
    <div class="gj-card-flush" style="text-align:center;padding:30px 20px;">
        <div class="hero-stat-label">{label}</div>
        <div class="hero-stat">{value}<span style="font-size:32px;color:{COLORS['cream_dim']};">{unit}</span></div>
        <div style="color:{COLORS['cream_dim']};font-size:12px;margin-top:6px;">{sub}</div>
    </div>
    """


def render():
    data = load_data()
    profile = data.get("profile", {})
    rounds = data.get("rounds", []) or []
    shots = data.get("practice_shots", []) or []

    # Hero header
    st.markdown(
        f"""
        <div style="margin:8px 0 24px;">
            <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.25em;text-transform:uppercase;font-weight:800;">⛳ COMMAND CENTER</div>
            <h1 style="margin:6px 0 4px;font-size:42px;">Welcome back, {profile.get('name', 'Joel').split()[0]}.</h1>
            <div style="color:{COLORS['cream_dim']};font-size:15px;">Your pursuit of breaking 80 — by the numbers.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # === Hero stats row ===
    if rounds:
        scores = [r.get("score") for r in rounds if r.get("score")]
        best = min(scores) if scores else "—"
        avg = round(sum(scores) / len(scores), 1) if scores else "—"
        last = scores[-1] if scores else "—"
    else:
        best = avg = last = "—"

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(_hero_block("HANDICAP", profile.get("ghin", "—"), "", "GHIN index"), unsafe_allow_html=True)
    with c2: st.markdown(_hero_block("BEST", best, "", "career low"), unsafe_allow_html=True)
    with c3: st.markdown(_hero_block("LAST ROUND", last, "", f"{rounds[-1].get('course', '')[:14]}" if rounds else ""), unsafe_allow_html=True)
    with c4: st.markdown(_hero_block("ROUND AVG", avg, "", f"over {len(rounds)} rounds"), unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # === Goal: Break 80 progress ===
    gap = (best - 79) if isinstance(best, (int, float)) else None
    progress = max(0, min(100, 100 - gap * 5)) if gap is not None and gap >= 0 else 100
    st.markdown(
        f"""
        <div class="gj-card-flush" style="background:linear-gradient(160deg,rgba(212,162,76,0.10),{COLORS['bg_3']});border-color:{COLORS['flag']}40;">
          <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px;">
            <div>
              <span class="gj-pill gj-pill-gold">🏆 PRIMARY GOAL</span>
              <h2 style="margin:8px 0 0;font-size:24px;">Break 80 Consistently</h2>
            </div>
            <div style="text-align:right;">
              <div style="font-family:'Fraunces',serif;font-size:36px;font-weight:700;color:{COLORS['flag']};line-height:1;">{gap if gap is not None and gap >= 0 else 0}</div>
              <div style="font-size:11px;color:{COLORS['cream_dim']};letter-spacing:0.15em;text-transform:uppercase;font-weight:700;">strokes to go</div>
            </div>
          </div>
          <div class="gauge-track" style="height:10px;">
            <div class="gauge-fill" style="width:{progress}%;"></div>
          </div>
          <div style="display:flex;justify-content:space-between;margin-top:8px;font-size:11px;color:{COLORS['cream_dim']};">
            <span>Best: {best}</span>
            <span>Target: 79</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # === Smart insights ===
    insights_list = smart_insights()
    if insights_list:
        st.markdown(
            f"""
            <div class="section-header">
                <span class="eyebrow">Intelligence</span>
                <h2>What your data is telling us</h2>
                <span class="accent"></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cols = st.columns(2)
        for i, ins in enumerate(insights_list[:6]):
            with cols[i % 2]:
                tone_class = ins.get("tone", "")
                tone_class = "danger" if tone_class == "danger" else ("gold" if tone_class == "gold" else "")
                st.markdown(
                    f"""
                    <div class="insight-card {tone_class}">
                        <div class="icon">{ins['icon']}</div>
                        <div class="title">{ins['title']}</div>
                        <div class="body">{ins['body']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Clickable drill link if present
                if ins.get("drill_link"):
                    drill = get_by_id(ins["drill_link"])
                    if drill:
                        if st.button(f"▶ Open: {drill['title']}", key=f"ins_drill_{i}", use_container_width=True):
                            st.session_state["active_page"] = "plan"
                            st.session_state["selected_drill"] = drill["id"]
                            st.rerun()

    # === Vs PGA Tour gauges ===
    st.markdown(
        f"""
        <div class="section-header">
            <span class="eyebrow">Benchmark</span>
            <h2>You vs the Tour</h2>
            <span class="accent"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Calculate user's stats
    putts = [r.get("putts") for r in rounds if r.get("putts")]
    gir = [r.get("gir") for r in rounds if r.get("gir") is not None]
    fir = [r.get("fir") for r in rounds if r.get("fir") is not None]
    user_putts = round(sum(putts) / len(putts), 1) if putts else None
    user_gir = round(sum(gir) / len(gir) / 18 * 100, 1) if gir else None
    user_fir = round(sum(fir) / len(fir) / 14 * 100, 1) if fir else None

    # Driver carry from practice
    drivers = [s["carry"] for s in shots if s.get("club") == "Driver" and s.get("carry")]
    user_drv = round(sum(drivers) / len(drivers)) if drivers else None
    sevens = [s["carry"] for s in shots if s.get("club") == "7i" and s.get("carry")]
    user_7i = round(sum(sevens) / len(sevens)) if sevens else None

    # Render all gauges in one card via a single-line HTML string (avoid Streamlit markdown indentation bugs)
    gauges = []
    gauges.append(_gauge("Putts per round", user_putts, TOUR_BENCH["putts_per_round"], lower_is_better=True))
    if user_gir is not None:
        gauges.append(_gauge("Greens in regulation", user_gir, TOUR_BENCH["gir_pct"], unit="%"))
    if user_fir is not None:
        gauges.append(_gauge("Fairways hit", user_fir, TOUR_BENCH["fairway_pct"], unit="%"))
    if user_drv:
        gauges.append(_gauge("Driver carry", user_drv, TOUR_CARRY["Driver"], unit="y"))
    if user_7i:
        gauges.append(_gauge("7-iron carry", user_7i, TOUR_CARRY["7i"], unit="y"))
    # Single line, no indentation
    block = '<div class="gj-card-flush">' + "".join(g for g in gauges if g) + '</div>'
    st.markdown(block, unsafe_allow_html=True)

    # === Stroke-Saver Plan (drills clickable) ===
    st.markdown(
        f"""
        <div class="section-header">
            <span class="eyebrow">Action Plan</span>
            <h2>Your stroke-saver drills</h2>
            <span class="accent"></span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f"<div style='color:{COLORS['cream_dim']};font-size:14px;margin:-8px 0 16px;'>Tap any drill to open the full breakdown with video and steps.</div>", unsafe_allow_html=True)

    # Pick top 4 most relevant drills based on user's weaknesses
    drill_ids = []
    if user_putts and user_putts > TOUR_BENCH["putts_per_round"] + 2:
        drill_ids.extend(["putt_gate", "putt_lag"])
    drill_ids.extend(["iron_compression", "wedge_ladder"])
    if user_drv and user_drv < 240:
        drill_ids.append("driver_speed")
    drill_ids = drill_ids[:4]

    cols = st.columns(2)
    for i, did in enumerate(drill_ids):
        d = get_by_id(did)
        if not d: continue
        with cols[i % 2]:
            st.markdown(
                f"""
                <div class="gj-card-flush" style="margin-bottom:12px;">
                    <div style="display:flex;align-items:flex-start;gap:14px;">
                        <div style="font-size:32px;">{d['icon']}</div>
                        <div style="flex:1;">
                            <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.18em;text-transform:uppercase;font-weight:700;">{d['category']}</div>
                            <div style="font-size:16px;font-weight:700;color:{COLORS['cream']};margin-top:3px;line-height:1.3;">{d['title']}</div>
                            <div style="font-size:12px;color:{COLORS['cream_dim']};margin-top:6px;">{d['summary']}</div>
                            <div style="display:flex;gap:8px;margin-top:10px;">
                                <span class="gj-pill">{d['duration']}</span>
                                <span class="gj-pill gj-pill-gold">📺 Video</span>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"▶ Open drill", key=f"ss_{did}", use_container_width=True, type="primary"):
                st.session_state["active_page"] = "plan"
                st.session_state["selected_drill"] = did
                st.rerun()

    # === Recent rounds quick view ===
    if rounds:
        st.markdown(
            f"""
            <div class="section-header">
                <span class="eyebrow">Recent</span>
                <h2>Last 5 rounds</h2>
                <span class="accent"></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for r in reversed(rounds[-5:]):
            score = r.get("score", "—")
            par = r.get("par", 72)
            diff = score - par if isinstance(score, (int, float)) else 0
            diff_str = f"+{diff}" if diff > 0 else (str(diff) if diff < 0 else "E")
            color = COLORS["fairway_2"] if diff <= 0 else (COLORS["flag"] if diff < 8 else COLORS["danger"])
            st.markdown(
                f"""
                <div class="gj-card-flush" style="display:flex;justify-content:space-between;align-items:center;padding:16px 22px;margin-bottom:8px;">
                    <div>
                        <div style="font-size:14px;font-weight:600;color:{COLORS['cream']};">{r.get('course', '—')}</div>
                        <div style="font-size:12px;color:{COLORS['cream_dim']};margin-top:2px;">{r.get('date', '—')} · Par {par}</div>
                    </div>
                    <div style="display:flex;align-items:center;gap:18px;">
                        <div style="text-align:right;">
                            <div style="font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.15em;text-transform:uppercase;font-weight:700;">Putts</div>
                            <div style="font-family:'Fraunces',serif;font-size:18px;color:{COLORS['cream']};">{r.get('putts', '—')}</div>
                        </div>
                        <div style="text-align:right;">
                            <div style="font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.15em;text-transform:uppercase;font-weight:700;">GIR</div>
                            <div style="font-family:'Fraunces',serif;font-size:18px;color:{COLORS['cream']};">{r.get('gir', '—')}</div>
                        </div>
                        <div style="text-align:right;min-width:70px;">
                            <div style="font-family:'Fraunces',serif;font-size:32px;font-weight:700;color:{COLORS['cream']};line-height:1;">{score}</div>
                            <div style="font-size:11px;color:{color};font-weight:700;letter-spacing:0.05em;">{diff_str}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
