"""Command Center — hero stats, smart insights, pro comparison, stroke-saver."""
import streamlit as st
from cloud_storage import load_data
from styles import COLORS
from insights import smart_insights, TOUR_BENCH, TOUR_CARRY
from drills import get_by_id
from handicap import compute_index


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


def _render_explainer_modal(rounds, hcp_result, best, last, avg):
    """Show a glassmorphic dismissable modal explaining a stat's calculation."""
    import streamlit as st
    modal = st.session_state.get("explain_modal")
    if not modal:
        return

    title = ""
    body_html = ""

    if modal == "handicap":
        title = "🎯 Handicap Index — WHS Formula"
        if hcp_result and hcp_result.get("index") is not None:
            diffs = hcp_result.get("differentials", [])
            used = hcp_result.get("differentials_used", [])
            n_used = hcp_result.get("rounds_used", 0)
            n_pool = hcp_result.get("rounds_in_pool", 0)
            avg_used = hcp_result.get("average_used", 0)
            adj = hcp_result.get("adjustment", 0)
            idx = hcp_result.get("index")
            diffs_html = "".join([f"<span class='diff-pill {'used' if d in used else ''}'>{d}</span>" for d in diffs])
            body_html = (
                f"<p>Computed from <b>{n_pool} round{'s' if n_pool != 1 else ''}</b> using the official USGA / R&amp;A WHS formula:</p>"
                f"<pre class='formula'>Differential = (Score - Course Rating) × 113 / Slope</pre>"
                f"<p>We then take the lowest <b>{n_used}</b> differential{'s' if n_used != 1 else ''} from your last 20 rounds, average them, multiply by 0.96.</p>"
                f"<div class='diff-list'>{diffs_html}</div>"
                f"<p style='margin-top:14px;'>Math: avg of best {n_used} = <b>{avg_used}</b> × 0.96 = <b>{round(avg_used*0.96,2)}</b>{f' + {adj} adj' if adj else ''} = <b>{idx}</b></p>"
            )
        else:
            body_html = "<p>Need at least 3 logged rounds to compute. Log more rounds and your handicap will recalculate automatically.</p>"

    elif modal == "best":
        scores = [r.get("score") for r in rounds if r.get("score")]
        if scores:
            best_round = min(rounds, key=lambda r: r.get("score", 999))
            title = "🏆 Best Round — Career Low"
            body_html = (
                f"<p>Your lowest score across <b>{len(rounds)}</b> logged rounds.</p>"
                f"<div class='stat-row'>Score: <b>{best_round.get('score')}</b> on {best_round.get('course')} ({best_round.get('date')})</div>"
                f"<div class='stat-row'>Par: {best_round.get('par')} — finished <b>{best_round.get('score') - best_round.get('par'):+}</b></div>"
                f"<div class='stat-row'>Putts: {best_round.get('putts', '—')} · GIR: {best_round.get('gir', '—')} · FIR: {best_round.get('fir', '—')}</div>"
            )
        else:
            body_html = "<p>Log a round to start tracking your best.</p>"

    elif modal == "last":
        if rounds:
            r = rounds[-1]
            title = "⛳ Last Round"
            body_html = (
                f"<div class='stat-row'>Course: <b>{r.get('course')}</b></div>"
                f"<div class='stat-row'>Date: {r.get('date')}</div>"
                f"<div class='stat-row'>Score: <b>{r.get('score')}</b> (par {r.get('par')})</div>"
                f"<div class='stat-row'>Putts: {r.get('putts', '—')} · GIR: {r.get('gir', '—')}/18 · FIR: {r.get('fir', '—')}/14</div>"
                f"<div class='stat-row'>Course rating/slope: {r.get('course_rating', '—')} / {r.get('slope', '—')}</div>"
            )
        else:
            body_html = "<p>No rounds logged yet.</p>"

    elif modal == "avg":
        scores = [r.get("score") for r in rounds if r.get("score")]
        if scores:
            title = "📊 Round Average"
            recent = scores[-5:]
            body_html = (
                f"<p>Mean score across <b>{len(scores)}</b> logged rounds.</p>"
                f"<pre class='formula'>{' + '.join(str(s) for s in scores[:8])}{' + ...' if len(scores)>8 else ''} ÷ {len(scores)} = {round(sum(scores)/len(scores),1)}</pre>"
                f"<p>Last 5 rounds: {', '.join(str(s) for s in recent)} — trend avg <b>{round(sum(recent)/len(recent),1)}</b></p>"
            )
        else:
            body_html = "<p>Log rounds to see your average.</p>"

    # Render glassmorphic modal (single-line HTML to avoid Streamlit markdown indent issues)
    css = (
        "<style>"
        f".gj-explainer{{background:rgba(20,28,24,0.85);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border:1px solid {COLORS['flag']}50;border-radius:16px;padding:28px 30px;margin:14px 0 18px;box-shadow:0 12px 60px rgba(0,0,0,0.4),0 0 0 1px {COLORS['flag']}20;animation:fadeInUp 0.35s ease-out;}}"
        "@keyframes fadeInUp{from{opacity:0;transform:translateY(12px);}to{opacity:1;transform:translateY(0);}}"
        f".gj-explainer h3{{margin:0 0 14px;font-size:22px;color:{COLORS['cream']};}}"
        f".gj-explainer p{{color:{COLORS['cream_dim']};line-height:1.6;margin:8px 0;}}"
        f".gj-explainer .formula{{background:rgba(0,0,0,0.4);padding:10px 14px;border-radius:8px;color:{COLORS['flag']};font-family:'JetBrains Mono',monospace;font-size:13px;margin:10px 0;white-space:pre-wrap;border-left:2px solid {COLORS['flag']};}}"
        f".gj-explainer .stat-row{{color:{COLORS['cream']};padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:14px;}}"
        ".gj-explainer .diff-list{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}"
        f".gj-explainer .diff-pill{{background:rgba(255,255,255,0.06);padding:4px 10px;border-radius:999px;font-size:12px;color:{COLORS['cream_dim']};font-family:'JetBrains Mono',monospace;}}"
        f".gj-explainer .diff-pill.used{{background:{COLORS['flag']}30;color:{COLORS['flag']};font-weight:700;border:1px solid {COLORS['flag']}80;}}"
        "</style>"
    )
    html = f'{css}<div class="gj-explainer"><h3>{title}</h3>{body_html}</div>'
    st.markdown(html, unsafe_allow_html=True)

    if st.button("✕ Close", key=f"close_{modal}", use_container_width=False):
        st.session_state["explain_modal"] = None
        st.rerun()


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

    # Compute live WHS handicap from rounds
    hcp_result = compute_index(rounds) if rounds else None
    computed_hcp = hcp_result.get("index") if hcp_result and hcp_result.get("index") is not None else profile.get("ghin", "—")
    ghin_display = profile.get("ghin", "—")

    # === Direct-click hero stats (v5.3) ===
    # Pattern: render visual card with markdown + Streamlit button overlaid using
    # CSS that targets columns containing .hero-stat-card (works without :has on root).
    st.markdown(
        f"""
        <style>
        /* Column containing a hero-stat-card becomes the positioning context */
        div[data-testid="column"]:has(.hero-stat-card),
        div[data-testid="stColumn"]:has(.hero-stat-card) {{
            position: relative;
        }}
        /* The visual card */
        .hero-stat-card {{
            background: linear-gradient(160deg, {COLORS['bg_3']}, {COLORS['bg_2']});
            border: 1px solid {COLORS['border']};
            border-radius: 18px;
            padding: 30px 20px;
            min-height: 168px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            gap: 6px;
        }}
        div[data-testid="column"]:has(.hero-stat-card):hover .hero-stat-card,
        div[data-testid="stColumn"]:has(.hero-stat-card):hover .hero-stat-card {{
            transform: translateY(-3px);
            border-color: {COLORS['flag']}80;
            box-shadow: 0 18px 50px rgba(212,162,76,0.18);
        }}
        .hero-stat-card .hsc-label {{
            font-size: 11px; letter-spacing: 0.28em; text-transform: uppercase;
            color: {COLORS['flag']}; font-weight: 800;
        }}
        .hero-stat-card .hsc-value {{
            font-family: 'Fraunces', serif; font-size: 56px;
            color: {COLORS['cream']}; line-height: 1; font-weight: 600;
            text-shadow: 0 4px 18px rgba(212,162,76,0.18);
        }}
        .hero-stat-card .hsc-sub {{
            font-size: 12px; color: {COLORS['cream_dim']}; margin-top: 2px;
        }}
        .hero-stat-card .hsc-hint {{
            font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase;
            color: {COLORS['flag']}80; font-weight: 700; margin-top: 6px;
            opacity: 0; transition: opacity 0.25s ease;
        }}
        div[data-testid="column"]:has(.hero-stat-card):hover .hero-stat-card .hsc-hint,
        div[data-testid="stColumn"]:has(.hero-stat-card):hover .hero-stat-card .hsc-hint {{
            opacity: 1;
        }}
        /* Overlay the Streamlit button on top of the entire column area */
        div[data-testid="column"]:has(.hero-stat-card) div[data-testid="stButton"],
        div[data-testid="stColumn"]:has(.hero-stat-card) div[data-testid="stButton"] {{
            position: absolute !important;
            top: 0; left: 0; right: 0; bottom: 0;
            margin: 0 !important;
            z-index: 5;
            height: 100%;
        }}
        div[data-testid="column"]:has(.hero-stat-card) div[data-testid="stButton"] > button,
        div[data-testid="stColumn"]:has(.hero-stat-card) div[data-testid="stButton"] > button {{
            width: 100%;
            height: 100%;
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
            cursor: pointer;
            min-height: 168px;
        }}
        div[data-testid="column"]:has(.hero-stat-card) div[data-testid="stButton"] > button:focus,
        div[data-testid="column"]:has(.hero-stat-card) div[data-testid="stButton"] > button:hover,
        div[data-testid="column"]:has(.hero-stat-card) div[data-testid="stButton"] > button:active,
        div[data-testid="stColumn"]:has(.hero-stat-card) div[data-testid="stButton"] > button:focus,
        div[data-testid="stColumn"]:has(.hero-stat-card) div[data-testid="stButton"] > button:hover,
        div[data-testid="stColumn"]:has(.hero-stat-card) div[data-testid="stButton"] > button:active {{
            outline: none !important;
            box-shadow: none !important;
            background: transparent !important;
            color: transparent !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    last_course = (rounds[-1].get('course', '')[:14] if rounds else "—")
    hero_specs = [
        ("HANDICAP", computed_hcp, f"GHIN: {ghin_display}", "handicap", "hero_hcp"),
        ("BEST", best, "career low", "best", "hero_best"),
        ("LAST ROUND", last, last_course, "last", "hero_last"),
        ("ROUND AVG", avg, f"over {len(rounds)} rounds", "avg", "hero_avg"),
    ]
    hero_cols = st.columns(4)
    for col, (lbl, val, sub, modal_key, btn_key) in zip(hero_cols, hero_specs):
        with col:
            st.markdown(
                f'<div class="hero-stat-card">'
                f'<div class="hsc-label">{lbl}</div>'
                f'<div class="hsc-value">{val}</div>'
                f'<div class="hsc-sub">{sub}</div>'
                f'<div class="hsc-hint">tap for breakdown</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(" ", key=btn_key, use_container_width=True):
                st.session_state["explain_modal"] = modal_key
                st.rerun()

    # Render explainer modal if active
    _render_explainer_modal(rounds, hcp_result, best, last, avg)

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
