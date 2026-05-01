"""Plan & Drills — drill library with working open buttons, AI cards, achievements."""
import streamlit as st
from cloud_storage import load_data, append_ai_drill
from drills import DRILLS, by_category, get_by_id
from achievements import get_all, stats as ach_stats
from styles import COLORS

try:
    import google.generativeai as genai
    HAS_GENAI = True
except Exception:
    HAS_GENAI = False


def _drill_detail(drill):
    """Render full drill detail with YouTube embed + AI breakdown."""
    st.markdown(
        f"""
        <div class="gj-card-flush">
            <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.18em;text-transform:uppercase;font-weight:700;">{drill['category']}</div>
            <h2 style="margin:6px 0 10px;font-size:30px;">{drill['icon']} {drill['title']}</h2>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <span class="gj-pill">{drill['duration']}</span>
                <span class="gj-pill gj-pill-gold">FIX: {drill['issue']}</span>
            </div>
            <div style="color:{COLORS['cream_dim']};margin-top:14px;font-size:14px;line-height:1.6;">{drill['summary']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # YouTube embed
    yt_id = drill.get("youtube_id")
    if yt_id:
        st.markdown(f"<div style='margin-top:14px;font-size:11px;color:{COLORS['flag']};letter-spacing:0.18em;text-transform:uppercase;font-weight:700;'>📺 WATCH: {drill.get('youtube_title', '')}</div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div style="margin-top:8px;border-radius:14px;overflow:hidden;border:1px solid {COLORS['border']};">
            <iframe width="100%" height="380"
                src="https://www.youtube.com/embed/{yt_id}"
                title="{drill.get('youtube_title', '')}"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen>
            </iframe>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Steps
    st.markdown(f"<div style='margin-top:18px;font-size:11px;color:{COLORS['flag']};letter-spacing:0.18em;text-transform:uppercase;font-weight:700;'>STEP-BY-STEP</div>", unsafe_allow_html=True)
    for i, step in enumerate(drill["steps"], 1):
        st.markdown(
            f"""
            <div style="display:flex;gap:14px;align-items:flex-start;padding:12px 14px;background:{COLORS['bg_2']};border-radius:12px;margin-top:8px;border:1px solid {COLORS['border']};">
                <div style="background:{COLORS['fairway']};color:{COLORS['cream']};border-radius:99px;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0;">{i}</div>
                <div style="font-size:14px;color:{COLORS['cream']};line-height:1.5;">{step}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # AI personalization
    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
    if st.button("✨ Get AI personalized breakdown for this drill", use_container_width=True, key=f"ai_{drill['id']}"):
        if not HAS_GENAI:
            st.error("Gemini library not installed.")
        else:
            try:
                d = load_data()
                key = d.get("settings", {}).get("gemini_key", "")
                genai.configure(api_key=key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                profile = d.get("profile", {})
                prompt = (
                    f"You are a PGA-level golf coach speaking to {profile.get('name', 'the player')}, "
                    f"GHIN handicap {profile.get('ghin', 31.3)}, working on the drill: '{drill['title']}'. "
                    f"The drill addresses: {drill['issue']}. "
                    f"Give a personalized 4-paragraph breakdown:\n"
                    f"1) Why this drill matters specifically for a {profile.get('ghin', 31)} handicap player\n"
                    f"2) The exact feel/sensation to chase during the drill\n"
                    f"3) Common mistakes to avoid\n"
                    f"4) How to know it's working — measurable outcome to look for\n"
                    f"Be direct, motivating, no fluff. Use 'you' throughout."
                )
                with st.spinner("Personalizing..."):
                    resp = model.generate_content(prompt)
                    text = resp.text
                append_ai_drill({"drill_id": drill["id"], "text": text})
                st.markdown(
                    f"""
                    <div class="insight-card gold" style="margin-top:14px;">
                        <div class="title">🎓 AI Coach — Personalized for you</div>
                        <div class="body" style="white-space:pre-line;">{text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            except Exception as e:
                st.error(f"AI breakdown unavailable: {e}")

    if st.button("← Back to drill library", key=f"back_{drill['id']}", use_container_width=True):
        st.session_state.pop("selected_drill", None)
        st.rerun()


def _render_drill_library():
    cats = by_category()
    for cat_name, drills in cats.items():
        st.markdown(
            f"""
            <div class="section-header">
                <span class="eyebrow">{cat_name}</span>
                <h2>{cat_name} drills</h2>
                <span class="accent"></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cols = st.columns(2)
        for i, d in enumerate(drills):
            with cols[i % 2]:
                st.markdown(
                    f"""
                    <div class="gj-card-flush" style="margin-bottom:12px;">
                        <div style="display:flex;align-items:flex-start;gap:14px;">
                            <div style="font-size:34px;">{d['icon']}</div>
                            <div style="flex:1;min-width:0;">
                                <div style="font-size:15px;font-weight:700;color:{COLORS['cream']};line-height:1.3;">{d['title']}</div>
                                <div style="font-size:12px;color:{COLORS['cream_dim']};margin-top:6px;line-height:1.5;">{d['summary']}</div>
                                <div style="display:flex;gap:6px;margin-top:10px;flex-wrap:wrap;">
                                    <span class="gj-pill">{d['duration']}</span>
                                    {'<span class="gj-pill gj-pill-gold">📺 Video</span>' if d.get('youtube_id') else ''}
                                </div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button(f"▶ Open drill", key=f"dl_{d['id']}", use_container_width=True, type="primary"):
                    st.session_state["selected_drill"] = d["id"]
                    st.rerun()


def _render_achievements():
    a_list = get_all()
    s = ach_stats()
    pct = round(s["unlocked"] / s["total"] * 100) if s["total"] else 0

    st.markdown(
        f"""
        <div class="gj-card-flush" style="background:linear-gradient(160deg,rgba(212,162,76,0.10),{COLORS['bg_3']});border-color:{COLORS['flag']}40;text-align:center;">
            <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.18em;text-transform:uppercase;font-weight:800;">ACHIEVEMENTS UNLOCKED</div>
            <div style="font-family:Fraunces,serif;font-size:64px;font-weight:700;color:{COLORS['flag']};line-height:1;margin:8px 0;">{s['unlocked']}<span style='color:{COLORS['cream_dim']};font-size:32px;'>/{s['total']}</span></div>
            <div style="color:{COLORS['cream_dim']};">Tier: {pct}% complete</div>
            <div class="gauge-track" style="margin-top:14px;">
                <div class="gauge-fill" style="width:{pct}%;background:linear-gradient(90deg,{COLORS['flag']},#E5B564);"></div>
            </div>
        </div>
        <div style="height:16px;"></div>
        """,
        unsafe_allow_html=True,
    )

    # Group by category prefix from id
    groups = {
        "🏆 Scoring": ["first_round", "five_rounds", "ten_rounds", "twenty_rounds", "fifty_rounds", "break_90", "break_85", "break_80", "break_75", "personal_best", "sub_par_9"],
        "🎯 Practice": ["first_shot", "100_shots", "500_shots", "1000_shots", "all_clubs"],
        "🔥 Streaks": ["streak_3", "streak_7", "streak_14", "streak_30"],
        "⚡ Distance": ["driver_250", "driver_270", "driver_290", "driver_300", "iron_pure"],
        "🗺️ Courses": ["home_5", "home_10", "three_courses", "five_courses"],
        "⛳ Short Game": ["putts_under_30", "putts_under_28", "gir_50", "gir_67"],
        "💬 Coach": ["first_chat", "ten_chats", "photo_swing", "voice_caddy"],
        "📊 Special": ["week_active", "consistent_5", "under_handicap", "dispersion_70", "ten_drills", "first_drill"],
    }

    by_id = {a["id"]: a for a in a_list}
    for group_name, ids in groups.items():
        st.markdown(
            f"""
            <div class="section-header">
                <h2 style="font-size:22px;">{group_name}</h2>
                <span class="accent"></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cols = st.columns(4)
        for i, aid in enumerate(ids):
            a = by_id.get(aid)
            if not a: continue
            with cols[i % 4]:
                cls = "ach-badge unlocked" if a["unlocked"] else "ach-badge locked"
                st.markdown(
                    f"""
                    <div class="{cls}">
                        <div class="icon">{a['icon']}</div>
                        <div class="name">{a['name']}</div>
                        <div class="desc">{a['desc']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _render_ai_drill_gen():
    st.markdown(f"<div style='color:{COLORS['cream_dim']};font-size:14px;margin-bottom:14px;'>Describe what you're working on and Gemini creates a custom drill on the spot.</div>", unsafe_allow_html=True)

    issue = st.text_input("What's giving you trouble?", placeholder="e.g. pulling my driver hard left", key="ai_issue")
    club = st.selectbox("With what club?", ["Driver", "Fairway/Hybrid", "Iron", "Wedge", "Putter"], key="ai_club")
    if st.button("✨ Generate Custom Drill", type="primary", use_container_width=True):
        if not issue.strip():
            st.warning("Tell me what to fix.")
            return
        if not HAS_GENAI:
            st.error("Gemini not available.")
            return
        try:
            d = load_data()
            key = d.get("settings", {}).get("gemini_key", "")
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            profile = d.get("profile", {})
            prompt = (
                f"Create a custom golf drill for a {profile.get('ghin', 31)} handicap player named "
                f"{profile.get('name', 'the player')}. They're struggling with: '{issue}' (with their {club}). "
                f"Output structure:\n"
                f"**THE DRILL:** [name]\n"
                f"**WHY THIS:** 2 sentences on root cause + why this drill targets it.\n"
                f"**SETUP:** What you need (be specific — alignment sticks, towel, tees, etc.)\n"
                f"**STEPS:** 4-5 numbered steps\n"
                f"**FEEL:** The exact sensation to chase\n"
                f"**SUCCESS METRIC:** How you know it's working\n"
                f"**TIME:** Duration estimate\n"
                f"Be direct, motivating, like a coach. No fluff."
            )
            with st.spinner("Drafting your drill..."):
                resp = model.generate_content(prompt)
                text = resp.text
            append_ai_drill({"issue": issue, "club": club, "text": text})
            st.markdown(
                f"""
                <div class="insight-card gold" style="margin-top:14px;">
                    <div class="title">🎓 Your Custom Drill</div>
                    <div class="body" style="white-space:pre-line;">{text}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.error(f"Could not generate: {e}")


def render():
    st.markdown(
        f"""
        <div style="margin:8px 0 22px;">
            <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.25em;text-transform:uppercase;font-weight:800;">🎯 PLAN & DRILLS</div>
            <h1 style="margin:6px 0 4px;font-size:42px;">Your Improvement Plan</h1>
            <div style="color:{COLORS['cream_dim']};font-size:15px;">Curated drills with real video. AI-generated drills tailored to your data.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # If a drill is selected, show its detail view
    if st.session_state.get("selected_drill"):
        drill = get_by_id(st.session_state["selected_drill"])
        if drill:
            _drill_detail(drill)
            return

    tab1, tab2 = st.tabs(["📚 Drill Library", "✨ AI Drill Generator"])
    with tab1: _render_drill_library()
    with tab2: _render_ai_drill_gen()
