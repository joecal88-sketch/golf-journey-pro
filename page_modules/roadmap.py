"""Roadmap & Drills — AI-generated drill cards with diagrams + voice narration."""
import streamlit as st
import streamlit.components.v1 as components
import json
import requests
from drills import DRILLS, find_drills_for
from insights import stroke_saver_plan, total_strokes_to_save, miss_pattern, gap_to_break_80
from achievements import all_with_status
from cloud_storage import load_data


CATEGORIES = ["All", "Driver", "Driver / Irons", "Wedges", "Putting", "Speed", "Full Swing", "Short Game", "Warm-Up"]


def render():
    st.markdown(
        """
        <div class="page-header">
            <div>
                <div class="page-eyebrow">PERSONALIZED PLAN · DRILL LIBRARY</div>
                <div class="page-title">Roadmap & Drills</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Your Roadmap", "📚 Drill Library", "✨ AI Drill Generator", "🏆 Achievements"])

    with tab1:
        _render_roadmap()
    with tab2:
        _render_drills()
    with tab3:
        _render_ai_drill_gen()
    with tab4:
        _render_achievements()


# ──────────────────────────────────────────────────────────────────────
def _render_roadmap():
    plan = stroke_saver_plan()
    total = total_strokes_to_save()
    gap = gap_to_break_80()
    mp = miss_pattern()

    if gap.get("avg") is not None:
        avg5 = gap["avg"]
        gap_val = gap["gap"]
        under = gap["under_80_count"]
        of_last = gap["of_last"]
        color = "#00D4AA" if gap_val <= 0 else ("#FFB800" if gap_val < 3 else "#FF6B35")
        label = "GOAL ACHIEVED" if gap_val <= 0 else f"{abs(gap_val)} STROKES TO GO"

        # Build hero card piece by piece with st.markdown to avoid nested-quote rendering bugs
        with st.container():
            st.markdown(
                f"""
                <div style="background:linear-gradient(135deg,#0F0F0F 0%,#0a0a0a 100%);border:1px solid #1A1A1A;border-top:3px solid {color};border-radius:16px;padding:24px 28px;">
                  <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:14px;">
                    <div style="flex:1;min-width:240px;">
                      <div style="font-size:11px;color:#888;letter-spacing:2px;text-transform:uppercase;font-weight:700;">YOUR PRIMARY GOAL</div>
                      <div style="font-size:28px;font-weight:900;margin-top:8px;letter-spacing:-0.5px;">Break 80 Consistently</div>
                      <div style="font-size:14px;color:{color};margin-top:6px;font-weight:700;">{label}</div>
                      <div style="font-size:13px;color:#999;margin-top:12px;line-height:1.6;">
                        Last 5 rounds avg: <strong style="color:#fff;">{avg5}</strong>. {under} of {of_last} were under 80.<br>
                        Total stroke-savers identified: <strong style="color:#00D4AA;">{total} strokes</strong> across {len(plan)} areas.
                      </div>
                    </div>
                    <div style="text-align:center;background:#0a0a0a;padding:16px 20px;border-radius:14px;border:1px solid #222;">
                      <div style="font-size:11px;color:#888;letter-spacing:2px;text-transform:uppercase;font-weight:700;">LAST 5 AVG</div>
                      <div style="font-size:54px;font-weight:900;color:{color};line-height:1;margin-top:6px;letter-spacing:-2px;">{avg5}</div>
                    </div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Miss pattern callout
    if mp.get("bias") and mp["bias"] != "balanced":
        st.markdown(
            f"""
            <div style="background:#0F0F0F;border:1px solid #1A1A1A;border-left:3px solid #FFB800;border-radius:14px;padding:18px 22px;margin-top:14px;">
              <div style="font-size:11px;color:#FFB800;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;">MISS PATTERN</div>
              <div style="font-size:14px;color:#DDD;margin-top:8px;line-height:1.7;">{mp['summary']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not plan:
        st.info("Log rounds and practice shots to build your personalized roadmap.")
        return

    st.markdown('<div class="section-label" style="margin-top:24px;">RANKED STROKE-SAVERS</div>', unsafe_allow_html=True)

    for i, item in enumerate(plan, 1):
        related = find_drills_for([item["area"], item["icon"]])
        rel_chips = ""
        for d in related[:2]:
            rel_chips += (
                f'<span style="display:inline-block;background:#161616;border:1px solid #2A2A2A;'
                f'border-radius:10px;padding:8px 14px;margin:4px 6px 4px 0;font-size:12px;'
                f'color:#00D4AA;font-weight:600;">📚 {d["title"]} · {d["duration"]}</span>'
            )

        st.markdown(
            f"""
            <div style="background:#0F0F0F;border:1px solid #1A1A1A;border-left:3px solid {item['color']};border-radius:14px;padding:18px 22px;margin-bottom:12px;">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:14px;">
                <div style="flex:1;min-width:260px;">
                  <div style="display:flex;align-items:center;gap:10px;">
                    <div style="background:{item['color']}25;color:{item['color']};border-radius:50%;width:36px;height:36px;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:14px;">#{i}</div>
                    <div style="font-size:14px;color:{item['color']};font-weight:800;letter-spacing:0.5px;text-transform:uppercase;">{item['icon']} {item['area']}</div>
                  </div>
                  <div style="font-size:13px;color:#DDD;margin-top:12px;line-height:1.7;">{item['why']}</div>
                  <div style="font-size:12px;color:#888;margin-top:10px;line-height:1.6;"><strong style="color:#00D4AA;">Drill plan:</strong> {item['drill']}</div>
                  <div style="font-size:11px;color:#888;margin-top:8px;">Current: <strong style="color:#fff;">{item['current']}</strong> → Target: <strong style="color:{item['color']};">{item['target']}</strong></div>
                  <div style="margin-top:14px;">{rel_chips}</div>
                </div>
                <div style="text-align:right;">
                  <div style="font-size:42px;font-weight:900;color:{item['color']};line-height:1;letter-spacing:-1px;">{item['strokes_saved']}</div>
                  <div style="font-size:10px;color:#888;letter-spacing:1.5px;text-transform:uppercase;font-weight:700;margin-top:4px;">strokes saved</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────────────
def _render_drills():
    st.markdown('<div class="section-label">FILTER</div>', unsafe_allow_html=True)
    cat = st.selectbox("Category", CATEGORIES, label_visibility="collapsed")

    filtered = DRILLS if cat == "All" else [d for d in DRILLS if d["category"].lower() == cat.lower()]
    st.markdown(f'<div style="font-size:12px;color:#888;margin-bottom:14px;">{len(filtered)} drills · tap any drill for an AI-generated coaching breakdown</div>', unsafe_allow_html=True)

    # Init session state for selected drill
    if "selected_drill_id" not in st.session_state:
        st.session_state["selected_drill_id"] = None

    for d in filtered:
        # Use button for selection
        cA, cB = st.columns([5, 1])
        with cA:
            st.markdown(
                f"""
                <div style="background:#0F0F0F;border:1px solid #1A1A1A;border-left:3px solid #00D4AA;border-radius:14px;padding:18px 22px;margin-bottom:8px;">
                  <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                    <span style="background:rgba(0,212,170,0.15);color:#00D4AA;padding:4px 10px;border-radius:8px;font-size:11px;font-weight:700;letter-spacing:0.5px;">{d['category']}</span>
                    <span style="background:rgba(74,158,255,0.15);color:#4A9EFF;padding:4px 10px;border-radius:8px;font-size:11px;font-weight:700;letter-spacing:0.5px;">{d['level']}</span>
                    <span style="background:rgba(255,184,0,0.15);color:#FFB800;padding:4px 10px;border-radius:8px;font-size:11px;font-weight:700;letter-spacing:0.5px;">⏱ {d['duration']}</span>
                  </div>
                  <div style="font-size:18px;font-weight:800;margin-top:12px;color:#fff;">{d['title']}</div>
                  <div style="font-size:13px;color:#CCC;margin-top:8px;line-height:1.7;">{d['description']}</div>
                  <div style="font-size:11px;color:#888;margin-top:8px;"><strong style="color:#00D4AA;">Reps:</strong> {d['reps']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with cB:
            if st.button("Open card", key=f"drill_open_{d['id']}", use_container_width=True):
                st.session_state["selected_drill_id"] = d["id"]
                st.session_state["selected_drill_obj"] = d
                st.rerun()

    # If a drill is selected, render its AI card
    if st.session_state.get("selected_drill_id"):
        drill_obj = st.session_state.get("selected_drill_obj")
        if drill_obj:
            st.markdown('<div class="section-label" style="margin-top:24px;">⛳ AI COACHING CARD</div>', unsafe_allow_html=True)
            _render_drill_card(drill_obj)


# ──────────────────────────────────────────────────────────────────────
def _render_drill_card(drill: dict):
    """Renders an AI-generated coaching breakdown for a drill, with voice narration option."""
    settings = load_data().get("settings", {})
    api_key = settings.get("gemini_key", "")

    # Cache breakdown in session state (key = drill id)
    cache_key = f"drillcard_{drill['id']}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = None

    if st.session_state[cache_key] is None:
        if api_key:
            try:
                with st.spinner("Generating coaching card..."):
                    prompt = (
                        f"You are an elite PGA-level golf coach creating a coaching card for the drill: {drill['title']}.\n"
                        f"Description: {drill['description']}\n"
                        f"Category: {drill['category']} · Level: {drill['level']} · Duration: {drill['duration']} · Reps: {drill['reps']}\n\n"
                        "Reply in this EXACT format:\n\n"
                        "**🎯 What it fixes:** (one sentence)\n\n"
                        "**🛠 Setup:** (3-5 short bullets — exactly what to put down on the range/practice green)\n\n"
                        "**✅ Step-by-step:** (5-7 numbered steps, second-person, very specific)\n\n"
                        "**👀 What to feel:** (2-3 short bullets — body cues)\n\n"
                        "**🚫 Common mistakes:** (2-3 bullets)\n\n"
                        "**🏆 Success metric:** (one line — how you know you've nailed it)\n\n"
                        "**🎙 Audio script (60 sec):** (a written 60-second voice-over your phone can read aloud while you do the drill)\n\n"
                        "Be specific. Reference Joel's miss bias (right miss, slice tendency, 31.3 GHIN) where relevant."
                    )
                    answer = _call_gemini(api_key, prompt)
                    st.session_state[cache_key] = answer
            except Exception as e:
                st.session_state[cache_key] = f"*(Couldn't generate AI card: {e})*\n\n{drill['description']}"
        else:
            st.session_state[cache_key] = (
                f"_(No Gemini key — showing standard description)_\n\n"
                f"**Setup:** {drill['description']}\n\n"
                f"**Reps:** {drill['reps']}"
            )

    answer = st.session_state[cache_key]

    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,#0F0F0F,#0a0a0a);border:1px solid #1A1A1A;border-top:3px solid #00D4AA;border-radius:16px;padding:24px 28px;">
          <div style="font-size:11px;color:#00D4AA;letter-spacing:2px;text-transform:uppercase;font-weight:700;">DRILL · {drill['category'].upper()}</div>
          <div style="font-size:24px;font-weight:900;margin-top:6px;color:#fff;">{drill['title']}</div>
          <div style="font-size:12px;color:#888;margin-top:4px;">⏱ {drill['duration']} · {drill['reps']} · {drill['level']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Visual diagram (SVG)
    diagram_svg = _drill_diagram(drill["category"])
    if diagram_svg:
        st.markdown(f'<div style="background:#0F0F0F;border:1px solid #1A1A1A;border-radius:14px;padding:20px;margin-top:12px;text-align:center;">{diagram_svg}</div>', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="background:#0F0F0F;border:1px solid #1A1A1A;border-radius:14px;padding:20px 24px;margin-top:12px;">
          <div style="font-size:14px;color:#DDD;line-height:1.8;white-space:pre-wrap;">{answer}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cA, cB = st.columns(2)
    if cA.button("🔊 Read aloud", use_container_width=True, key=f"read_{drill['id']}"):
        components.html(_speak_widget(answer), height=60)
    if cB.button("✕ Close card", use_container_width=True, key=f"close_{drill['id']}"):
        st.session_state["selected_drill_id"] = None
        st.session_state[cache_key] = None
        st.rerun()


def _drill_diagram(category: str) -> str:
    """Return a small inline SVG diagram for the drill category."""
    cat = category.lower()
    if "putt" in cat:
        # Putting gate diagram
        return """
        <svg viewBox="0 0 320 140" width="100%" style="max-width:420px;">
          <rect x="0" y="0" width="320" height="140" fill="#0E2A1B" rx="10"/>
          <line x1="40" y1="70" x2="280" y2="70" stroke="#FFB800" stroke-width="2" stroke-dasharray="6 6"/>
          <circle cx="60" cy="70" r="8" fill="#fff" stroke="#00D4AA" stroke-width="2"/>
          <line x1="100" y1="55" x2="100" y2="85" stroke="#FFB800" stroke-width="3"/>
          <line x1="120" y1="55" x2="120" y2="85" stroke="#FFB800" stroke-width="3"/>
          <text x="110" y="48" fill="#FFB800" text-anchor="middle" font-size="9" font-family="Inter">GATE</text>
          <circle cx="270" cy="70" r="10" fill="#000" stroke="#fff" stroke-width="2"/>
          <text x="270" y="74" fill="#fff" text-anchor="middle" font-size="11" font-family="Inter">⛳</text>
          <text x="160" y="125" fill="#999" text-anchor="middle" font-size="11" font-family="Inter">Two tees barely wider than ball · 4 ft from cup</text>
        </svg>
        """
    if "wedge" in cat or "short" in cat:
        # Wedge ladder
        return """
        <svg viewBox="0 0 320 140" width="100%" style="max-width:420px;">
          <rect x="0" y="0" width="320" height="140" fill="#0E2A1B" rx="10"/>
          <circle cx="40" cy="100" r="6" fill="#fff"/>
          <text x="40" y="124" fill="#999" text-anchor="middle" font-size="10" font-family="Inter">YOU</text>
          <circle cx="100" cy="60" r="8" fill="#FFB800" opacity="0.3"/>
          <text x="100" y="48" fill="#FFB800" text-anchor="middle" font-size="10" font-family="Inter">75</text>
          <circle cx="160" cy="60" r="8" fill="#FFB800" opacity="0.5"/>
          <text x="160" y="48" fill="#FFB800" text-anchor="middle" font-size="10" font-family="Inter">85</text>
          <circle cx="220" cy="60" r="8" fill="#FFB800" opacity="0.7"/>
          <text x="220" y="48" fill="#FFB800" text-anchor="middle" font-size="10" font-family="Inter">95</text>
          <circle cx="280" cy="60" r="8" fill="#FFB800"/>
          <text x="280" y="48" fill="#FFB800" text-anchor="middle" font-size="10" font-family="Inter">105</text>
          <text x="160" y="118" fill="#999" text-anchor="middle" font-size="11" font-family="Inter">5 wedges at each yardage · land within 10 ft</text>
        </svg>
        """
    if "driver" in cat or "iron" in cat:
        # Gate drill
        return """
        <svg viewBox="0 0 320 140" width="100%" style="max-width:420px;">
          <rect x="0" y="0" width="320" height="140" fill="#0E2A1B" rx="10"/>
          <line x1="160" y1="20" x2="160" y2="120" stroke="rgba(255,255,255,0.2)" stroke-dasharray="4 4"/>
          <circle cx="160" cy="80" r="7" fill="#fff" stroke="#000" stroke-width="1"/>
          <line x1="135" y1="85" x2="135" y2="105" stroke="#FFB800" stroke-width="3"/>
          <line x1="185" y1="85" x2="185" y2="105" stroke="#FFB800" stroke-width="3"/>
          <text x="135" y="120" fill="#FFB800" text-anchor="middle" font-size="9" font-family="Inter">tee</text>
          <text x="185" y="120" fill="#FFB800" text-anchor="middle" font-size="9" font-family="Inter">tee</text>
          <path d="M160 70 L 160 30" stroke="#00D4AA" stroke-width="2" fill="none"/>
          <polygon points="160,28 156,38 164,38" fill="#00D4AA"/>
          <text x="160" y="20" fill="#00D4AA" text-anchor="middle" font-size="11" font-family="Inter">target line</text>
        </svg>
        """
    if "speed" in cat:
        # Stack overspeed
        return """
        <svg viewBox="0 0 320 140" width="100%" style="max-width:420px;">
          <rect x="0" y="0" width="320" height="140" fill="#0E2A1B" rx="10"/>
          <rect x="50" y="40" width="20" height="60" fill="#00D4AA" rx="3"/>
          <text x="60" y="118" fill="#00D4AA" text-anchor="middle" font-size="10" font-family="Inter">20g</text>
          <rect x="100" y="50" width="20" height="50" fill="#4A9EFF" rx="3"/>
          <text x="110" y="118" fill="#4A9EFF" text-anchor="middle" font-size="10" font-family="Inter">45g</text>
          <rect x="150" y="55" width="20" height="45" fill="#FFB800" rx="3"/>
          <text x="160" y="118" fill="#FFB800" text-anchor="middle" font-size="10" font-family="Inter">60g</text>
          <rect x="200" y="60" width="20" height="40" fill="#FF6B35" rx="3"/>
          <text x="210" y="118" fill="#FF6B35" text-anchor="middle" font-size="10" font-family="Inter">75g</text>
          <rect x="250" y="65" width="20" height="35" fill="#9B59B6" rx="3"/>
          <text x="260" y="118" fill="#9B59B6" text-anchor="middle" font-size="10" font-family="Inter">100g</text>
          <text x="160" y="25" fill="#fff" text-anchor="middle" font-size="11" font-family="Inter">TheStack — light to heavy, max effort</text>
        </svg>
        """
    if "warm" in cat:
        return """
        <svg viewBox="0 0 320 100" width="100%" style="max-width:420px;">
          <rect x="0" y="0" width="320" height="100" fill="#0E2A1B" rx="10"/>
          <text x="50" y="55" fill="#fff" text-anchor="middle" font-size="22" font-family="Inter">🥄</text>
          <text x="50" y="80" fill="#999" text-anchor="middle" font-size="9" font-family="Inter">putts</text>
          <text x="110" y="55" fill="#fff" text-anchor="middle" font-size="22" font-family="Inter">⛳</text>
          <text x="110" y="80" fill="#999" text-anchor="middle" font-size="9" font-family="Inter">wedge</text>
          <text x="170" y="55" fill="#fff" text-anchor="middle" font-size="22" font-family="Inter">🏌️</text>
          <text x="170" y="80" fill="#999" text-anchor="middle" font-size="9" font-family="Inter">iron</text>
          <text x="230" y="55" fill="#fff" text-anchor="middle" font-size="22" font-family="Inter">🏌️‍♂️</text>
          <text x="230" y="80" fill="#999" text-anchor="middle" font-size="9" font-family="Inter">hybrid</text>
          <text x="290" y="55" fill="#fff" text-anchor="middle" font-size="22" font-family="Inter">💥</text>
          <text x="290" y="80" fill="#999" text-anchor="middle" font-size="9" font-family="Inter">driver</text>
        </svg>
        """
    return ""


# ──────────────────────────────────────────────────────────────────────
def _render_ai_drill_gen():
    st.markdown('<div class="section-label">GENERATE A CUSTOM DRILL · AI-POWERED</div>', unsafe_allow_html=True)
    st.caption("Tell me your specific issue. I'll generate a custom drill with setup, steps, success metric, and a 60-sec voice script.")

    issue = st.text_area(
        "What's your issue?",
        placeholder="e.g. I keep blocking my driver right; my chip shots from tight lies fly long; my putting distance control is awful from 25-40 ft.",
        height=100,
    )

    cA, cB = st.columns(2)
    duration = cA.selectbox("How long do you have?", ["5 min", "10 min", "15 min", "20 min", "30 min"])
    setting = cB.selectbox("Where will you practice?", ["Driving range", "Putting green", "Chipping green", "Backyard / mat at home", "Course / play"])

    if st.button("✨ Generate drill", use_container_width=True):
        if not issue.strip():
            st.warning("Describe your issue first.")
            return
        api_key = load_data().get("settings", {}).get("gemini_key", "")
        if not api_key:
            st.error("Need a Gemini API key. Add one on the AI Coach page.")
            return
        with st.spinner("Coach is designing your drill..."):
            try:
                prompt = (
                    "You are an elite PGA golf coach. Design a custom drill for Joel C. (GHIN 31.3, "
                    "right miss bias, goal: break 80, 300yd driver, 20 hcp).\n"
                    f"Issue: {issue}\n"
                    f"Available time: {duration}\n"
                    f"Setting: {setting}\n\n"
                    "Reply in this exact format:\n\n"
                    "**🎯 Drill Name:** (catchy, 4-6 words)\n\n"
                    "**🩹 What it fixes:** (one sentence)\n\n"
                    "**🛠 Setup:** (3-5 bullets)\n\n"
                    "**✅ Step-by-step:** (5-7 numbered steps)\n\n"
                    "**🏆 Success metric:** (one specific number — e.g., 'land 6 of 10 within 10 ft')\n\n"
                    "**🎙 60-sec voice script:** (a written voice-over)"
                )
                answer = _call_gemini(api_key, prompt)
                st.session_state["last_generated_drill"] = answer
            except Exception as e:
                st.error(f"AI generation failed: {e}")
                return

    if "last_generated_drill" in st.session_state:
        st.markdown(
            f"""
            <div style="background:linear-gradient(135deg,#0F0F0F,#0a0a0a);border:1px solid #1A1A1A;border-top:3px solid #00D4AA;border-radius:16px;padding:24px 28px;margin-top:14px;">
              <div style="font-size:11px;color:#00D4AA;letter-spacing:2px;text-transform:uppercase;font-weight:700;margin-bottom:10px;">⛳ YOUR CUSTOM DRILL</div>
              <div style="font-size:14px;color:#DDD;line-height:1.8;white-space:pre-wrap;">{st.session_state['last_generated_drill']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🔊 Read drill aloud", use_container_width=True):
            components.html(_speak_widget(st.session_state["last_generated_drill"]), height=60)


# ──────────────────────────────────────────────────────────────────────
def _render_achievements():
    all_ach = all_with_status()
    unlocked = [a for a in all_ach if a["unlocked"]]
    locked = [a for a in all_ach if not a["unlocked"]]

    c1, c2 = st.columns(2)
    c1.metric("Unlocked", f"{len(unlocked)} of {len(all_ach)}")
    c2.metric("Progress", f"{len(unlocked) / len(all_ach) * 100:.0f}%")

    st.markdown('<div class="section-label" style="margin-top:18px;">UNLOCKED</div>', unsafe_allow_html=True)
    if not unlocked:
        st.markdown('<div style="font-size:13px;color:#888;">No achievements unlocked yet — keep playing.</div>', unsafe_allow_html=True)
    for a in unlocked:
        st.markdown(
            f"""
            <div style="background:#0F0F0F;border:1px solid #1A1A1A;border-left:3px solid #FFB800;border-radius:14px;padding:16px 20px;margin-bottom:8px;">
              <div style="display:flex;align-items:center;gap:14px;">
                <div style="font-size:32px;">{a['icon']}</div>
                <div style="flex:1;">
                  <div style="font-size:15px;font-weight:800;color:#FFB800;">{a['label']}</div>
                  <div style="font-size:12px;color:#999;margin-top:3px;">{a['desc']}</div>
                </div>
                <span style="background:rgba(255,184,0,0.15);color:#FFB800;padding:4px 10px;border-radius:8px;font-size:10px;font-weight:700;letter-spacing:0.5px;">UNLOCKED</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-label" style="margin-top:18px;">LOCKED · KEEP GOING</div>', unsafe_allow_html=True)
    for a in locked:
        st.markdown(
            f"""
            <div style="background:#0F0F0F;border:1px solid #1A1A1A;border-radius:14px;padding:16px 20px;margin-bottom:8px;opacity:0.6;">
              <div style="display:flex;align-items:center;gap:14px;">
                <div style="font-size:28px;filter:grayscale(1);">{a['icon']}</div>
                <div style="flex:1;">
                  <div style="font-size:15px;font-weight:700;color:#888;">{a['label']}</div>
                  <div style="font-size:12px;color:#666;margin-top:3px;">{a['desc']}</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ──────────────────────────────────────────────────────────────────────
def _call_gemini(api_key: str, prompt: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.6, "maxOutputTokens": 900},
    }
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    r.raise_for_status()
    j = r.json()
    return j["candidates"][0]["content"]["parts"][0]["text"]


def _speak_widget(text: str) -> str:
    safe = (text or "").replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    return f"""
    <div style="font-family:Inter;color:#999;font-size:11px;">🔊 Reading aloud...</div>
    <script>
    (function(){{
      const txt = `{safe}`;
      if (!('speechSynthesis' in window)) return;
      const clean = txt.replace(/\\*\\*/g, '').replace(/\\*/g, '').replace(/\\#/g, '');
      const u = new SpeechSynthesisUtterance(clean);
      u.rate = 1.05; u.pitch = 1.0;
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(u);
    }})();
    </script>
    """
