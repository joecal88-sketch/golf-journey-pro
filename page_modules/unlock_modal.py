"""Confetti unlock overlay — fires when new achievements are earned.

Shows a full-screen glass overlay with a centered tile per new achievement,
tier-colored ring pulse, confetti via tsparticles-confetti CDN.
"""
import streamlit as st
from styles import COLORS
from achievements import TIER_INFO


def render_if_pending():
    """Call this from Home.py AFTER evaluate_all().

    Expects st.session_state['pending_unlocks'] to be a list of dicts
    each with keys: id, icon, name, desc, tier.
    """
    pending = st.session_state.get("pending_unlocks") or []
    if not pending:
        return

    # Build tile HTML for the (up to 3) most recent unlocks
    show = pending[:3]
    tiles_html = ""
    for ach in show:
        info = TIER_INFO.get(ach.get("tier", "easy"), TIER_INFO["easy"])
        color = info["color"]
        tiles_html += f"""
        <div class="unlock-tile" style="--tier-color:{color};">
            <div class="ring-pulse"></div>
            <div class="tier-stripe">{info['label']} · +{info['points']} pts</div>
            <div class="hero-icon">{ach.get('icon','🏆')}</div>
            <div class="ach-name">{ach.get('name','Achievement')}</div>
            <div class="ach-desc">{ach.get('desc','')}</div>
            <div class="unlocked-stamp">✓ UNLOCKED</div>
        </div>
        """

    extra = len(pending) - len(show)
    extra_label = f"<div class='extra-label'>+ {extra} more unlocked</div>" if extra > 0 else ""

    st.markdown(f"""
    <style>
      @keyframes uo-fade-in {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
      @keyframes uo-rise {{
        from {{ opacity: 0; transform: translateY(40px) scale(0.85); }}
        to   {{ opacity: 1; transform: translateY(0) scale(1); }}
      }}
      @keyframes uo-ring-pulse {{
        0%   {{ transform: scale(0.8); opacity: 0.8; }}
        100% {{ transform: scale(1.5); opacity: 0; }}
      }}
      @keyframes uo-shine {{
        0%   {{ background-position: -200% 0; }}
        100% {{ background-position: 200% 0; }}
      }}
      .unlock-overlay {{
        position: fixed; inset: 0;
        background: radial-gradient(ellipse at center, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.92) 100%);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        z-index: 99999;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        gap: 20px;
        animation: uo-fade-in 0.4s ease-out;
        padding: 40px 20px;
      }}
      .unlock-banner {{
        font-family: 'Fraunces', serif;
        font-size: 14px; letter-spacing: 0.4em;
        text-transform: uppercase;
        background: linear-gradient(90deg, #fff, #d4a24c, #fff);
        background-size: 200% 100%;
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        animation: uo-shine 2.4s linear infinite;
        font-weight: 800;
      }}
      .unlock-headline {{
        font-family: 'Fraunces', serif;
        font-size: 48px; color: #fff; font-weight: 700;
        text-align: center; line-height: 1.1;
        text-shadow: 0 4px 30px rgba(212,162,76,0.6);
        animation: uo-rise 0.5s cubic-bezier(.2,.8,.2,1);
      }}
      .unlock-tile {{
        position: relative;
        background: linear-gradient(160deg, rgba(20, 28, 24, 0.92), rgba(8, 12, 10, 0.88));
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1.5px solid var(--tier-color);
        border-radius: 22px;
        padding: 28px 36px;
        min-width: 380px; max-width: 480px;
        text-align: center;
        box-shadow: 0 16px 70px rgba(0,0,0,0.8), 0 0 80px var(--tier-color);
        animation: uo-rise 0.6s cubic-bezier(.2,.8,.2,1);
        overflow: hidden;
      }}
      .unlock-tile .ring-pulse {{
        position: absolute; left: 50%; top: 80px;
        transform: translate(-50%, -50%) scale(0.8);
        width: 110px; height: 110px;
        border: 3px solid var(--tier-color); border-radius: 50%;
        animation: uo-ring-pulse 1.6s ease-out infinite;
        pointer-events: none;
      }}
      .unlock-tile .tier-stripe {{
        font-size: 11px; letter-spacing: 0.25em;
        text-transform: uppercase; font-weight: 800;
        color: var(--tier-color);
      }}
      .unlock-tile .hero-icon {{
        font-size: 84px; line-height: 1; margin: 14px 0 10px;
        filter: drop-shadow(0 8px 24px var(--tier-color));
      }}
      .unlock-tile .ach-name {{
        font-family: 'Fraunces', serif;
        font-size: 26px; font-weight: 700; color: #fff;
        margin: 6px 0 6px;
      }}
      .unlock-tile .ach-desc {{
        font-size: 13px; color: rgba(255,255,255,0.72); line-height: 1.5;
        max-width: 360px; margin: 0 auto;
      }}
      .unlock-tile .unlocked-stamp {{
        margin-top: 16px;
        display: inline-block;
        padding: 6px 16px; border-radius: 999px;
        background: var(--tier-color); color: #0a0e0c;
        font-size: 11px; letter-spacing: 0.25em;
        text-transform: uppercase; font-weight: 800;
      }}
      .extra-label {{
        font-size: 13px; color: rgba(255,255,255,0.7);
        font-style: italic;
      }}
      .unlock-overlay .stButton {{ margin-top: 8px; }}
      .unlock-overlay .stButton button {{
        background: linear-gradient(90deg, #d4a24c, #b8852a) !important;
        color: #0a0e0c !important;
        border: none !important;
        padding: 14px 36px !important;
        font-size: 14px !important;
        font-weight: 800 !important;
        letter-spacing: 0.2em !important;
        text-transform: uppercase !important;
        border-radius: 999px !important;
        box-shadow: 0 8px 30px rgba(212,162,76,0.6) !important;
        transition: transform 0.2s ease !important;
      }}
      .unlock-overlay .stButton button:hover {{
        transform: translateY(-2px) scale(1.05) !important;
        box-shadow: 0 12px 40px rgba(212,162,76,0.8) !important;
      }}
    </style>

    <div class="unlock-overlay" id="gj-unlock-overlay">
      <div class="unlock-banner">★ ACHIEVEMENT UNLOCKED ★</div>
      <div class="unlock-headline">Awesome work, Joel.</div>
      <div style="display:flex;gap:20px;flex-wrap:wrap;justify-content:center;align-items:stretch;">
        {tiles_html}
      </div>
      {extra_label}
    </div>

    <!-- Confetti -->
    <script type="module">
      import confetti from "https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.3/+esm";
      function fire() {{
        confetti({{
          particleCount: 220,
          spread: 100,
          origin: {{ y: 0.5 }},
          colors: ['#d4a24c', '#7FB069', '#4A90E2', '#fff', '#C04A4A'],
          startVelocity: 50,
          scalar: 1.2,
          zIndex: 100000,
        }});
        confetti({{
          particleCount: 80,
          spread: 60,
          angle: 60,
          origin: {{ x: 0, y: 0.6 }},
          colors: ['#d4a24c', '#7FB069', '#fff'],
          zIndex: 100000,
        }});
        confetti({{
          particleCount: 80,
          spread: 60,
          angle: 120,
          origin: {{ x: 1, y: 0.6 }},
          colors: ['#d4a24c', '#4A90E2', '#fff'],
          zIndex: 100000,
        }});
      }}
      // Fire immediately and again after 0.4s for a layered effect
      fire();
      setTimeout(fire, 400);
      setTimeout(fire, 900);
    </script>
    """, unsafe_allow_html=True)

    # Dismiss button
    cols = st.columns([1, 1, 1])
    with cols[1]:
        if st.button("AWESOME!", key="dismiss_unlock", use_container_width=True):
            st.session_state["pending_unlocks"] = []
            st.rerun()
