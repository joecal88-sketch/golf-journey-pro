"""Golf Journey Pro v4.1 — Seamless Edition · Entry point."""
import streamlit as st
import streamlit.components.v1 as components
from styles import CSS
from cloud_storage import seed_demo_if_empty, load_data
from achievements import evaluate_all
from insights import practice_streak

st.set_page_config(
    page_title="Golf Journey Pro",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)

# ── PWA + iOS install meta tags ──
PWA_HEAD = """
<script>
(function() {
  if (window.parent.document.getElementById('pwa-tags-injected')) return;
  const head = window.parent.document.head;
  const tags = [
    '<link id="pwa-tags-injected" rel="manifest" href="./app/static/manifest.json">',
    '<meta name="apple-mobile-web-app-capable" content="yes">',
    '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">',
    '<meta name="apple-mobile-web-app-title" content="Golf Journey">',
    '<meta name="theme-color" content="#0A0A0A">',
    '<link rel="apple-touch-icon" href="./app/static/icon-192.png">',
  ];
  head.insertAdjacentHTML('beforeend', tags.join(''));
})();
</script>
"""
components.html(PWA_HEAD, height=0)

# Sidebar collapse-button polish
st.markdown(
    """
    <style>
    [data-testid="stSidebarCollapseButton"] {
        opacity: 1 !important;
        visibility: visible !important;
        background: #00D4AA !important;
        border-radius: 8px !important;
        z-index: 999999 !important;
    }
    [data-testid="stSidebarCollapseButton"] svg { color: #000 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# Seed Joel's data so the app feels alive on first launch
seed_demo_if_empty()

# Run achievement check on every load (safe — duplicates ignored)
newly_unlocked = evaluate_all()

from page_modules import (
    dashboard,
    practice,
    live_round,
    speed_training,
    coach,
    performance,
    roadmap,
)

PAGES = [
    "🏠  Command Center",
    "🏌️  Practice Hub",
    "📍  Live Round",
    "⚡  Speed Training",
    "🎯  Roadmap & Drills",
    "🎓  AI Coach",
    "📈  Performance",
]
SHORT = ["🏠 Home", "🏌️ Practice", "📍 Live", "⚡ Speed", "🎯 Plan", "🎓 Coach", "📈 Stats"]

# Initialize active page state
if "active_page" not in st.session_state:
    st.session_state["active_page"] = PAGES[0]


def _set_page(page_name: str):
    """Callback: switch active page (runs before widgets re-render)."""
    st.session_state["active_page"] = page_name


# ── Sidebar (primary nav) ────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div style="padding:24px 16px 20px;text-align:center;border-bottom:1px solid #1A1A1A;margin-bottom:20px;">
            <div style="font-size:36px;line-height:1;">⛳</div>
            <div style="font-size:18px;font-weight:900;color:#fff;margin-top:8px;letter-spacing:-0.3px;">Golf Journey</div>
            <div style="font-size:10px;color:#00D4AA;letter-spacing:3px;text-transform:uppercase;margin-top:4px;font-weight:700;">PRO v4.1</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar nav as buttons (not radio) — avoids the widget-state-overwrites-rerun bug
    for i, p in enumerate(PAGES):
        is_active = (p == st.session_state["active_page"])
        st.button(
            p,
            key=f"sidenav_{i}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            on_click=_set_page,
            args=(p,),
        )

    streak = practice_streak()
    profile = load_data().get("profile", {})

    st.markdown(
        f"""
        <div style="margin-top:24px;padding:16px;background:linear-gradient(135deg,#111,#0c0c0c);border-radius:14px;border:1px solid #1A1A1A;">
            <div style="font-size:10px;color:#888;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px;font-weight:700;">PLAYER</div>
            <div style="font-size:16px;font-weight:800;">{profile.get('name', 'Joel C.')}</div>
            <div style="font-size:12px;color:#00D4AA;font-weight:700;margin-top:3px;">GHIN {profile.get('ghin', 31.3)}</div>
            <div style="font-size:11px;color:#777;margin-top:4px;line-height:1.5;">El Cariso · Scholl Canyon<br>Van Nuys Par 3</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if streak > 0:
        st.markdown(
            f"""
            <div class="streak-card" style="margin-top:14px;">
                <span style="font-size:22px;">🔥</span>
                <div>
                    <div style="font-size:11px;letter-spacing:1px;text-transform:uppercase;opacity:0.85;">Day Streak</div>
                    <div style="font-size:22px;font-weight:900;line-height:1;">{streak}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if newly_unlocked:
        st.markdown(
            """
            <div style="margin-top:14px;padding:12px 14px;background:rgba(255,184,0,0.1);border:1px solid rgba(255,184,0,0.3);border-radius:12px;">
                <div style="font-size:11px;color:#FFB800;font-weight:700;letter-spacing:1px;text-transform:uppercase;">🎉 New Achievement</div>
                <div style="font-size:12px;color:#FFB800;margin-top:4px;">Check the Command Center</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)
    st.caption("📱 Add to Home Screen on iPhone for the full-screen app experience.")


# ── Backup top-of-page navigation (visible when sidebar is collapsed) ──────────
nav_cols = st.columns(len(PAGES))
for i, p in enumerate(PAGES):
    with nav_cols[i]:
        is_active = (p == st.session_state["active_page"])
        st.button(
            SHORT[i],
            key=f"topnav_{i}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
            on_click=_set_page,
            args=(p,),
        )

st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)


# ── Route ──────────────────────────────────────────────
active = st.session_state["active_page"]
if "Command" in active:
    dashboard.render()
elif "Practice" in active:
    practice.render()
elif "Round" in active:
    live_round.render()
elif "Speed" in active:
    speed_training.render()
elif "Roadmap" in active:
    roadmap.render()
elif "Coach" in active:
    coach.render()
elif "Perform" in active:
    performance.render()
