"""Golf Journey Pro v5.2 — Premium Edition · Entry."""
import streamlit as st
import streamlit.components.v1 as components
from styles import CSS, COLORS
from cloud_storage import seed_demo_if_empty, load_data
from achievements import evaluate_all, stats as ach_stats
from insights import practice_streak

st.set_page_config(
    page_title="Golf Journey Pro",
    page_icon="⛳",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)

# PWA tags
components.html(
    """
    <script>
    (function() {
        if (window.parent.document.getElementById('pwa-tags-injected')) return;
        const head = window.parent.document.head;
        const tags = [
            '<link id="pwa-tags-injected" rel="manifest" href="./app/static/manifest.json">',
            '<meta name="apple-mobile-web-app-capable" content="yes">',
            '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">',
            '<meta name="apple-mobile-web-app-title" content="Golf Journey">',
            '<meta name="theme-color" content="#0B1410">',
            '<link rel="apple-touch-icon" href="./app/static/icon-192.png">',
        ];
        head.insertAdjacentHTML('beforeend', tags.join(''));
    })();
    </script>
    """,
    height=0,
)

seed_demo_if_empty()
newly = evaluate_all()
if newly:
    # Queue for confetti overlay; deduped against any already pending
    existing_ids = {a.get("id") for a in st.session_state.get("pending_unlocks", [])}
    for a in newly:
        if a.get("id") not in existing_ids:
            st.session_state.setdefault("pending_unlocks", []).append(a)

from page_modules import dashboard, practice, live_round, coach, performance, roadmap, achievements_page, unlock_modal

# Render confetti overlay before any page if there are pending unlocks
unlock_modal.render_if_pending()

PAGES = [
    ("home",     "🏠", "Command",       dashboard.render),
    ("practice", "🏌️", "Practice",      practice.render),
    ("live",     "📍", "Live Round",    live_round.render),
    ("plan",     "🎯", "Plan",          roadmap.render),
    ("coach",    "🎓", "Coach",         coach.render),
    ("stats",    "📈", "Stats",         performance.render),
    ("trophy",   "🏆", "Achievements",  achievements_page.render),
]

if "active_page" not in st.session_state:
    st.session_state["active_page"] = PAGES[0][0]


def _go(page_id: str):
    st.session_state["active_page"] = page_id


# ── Sidebar nav ──
with st.sidebar:
    st.markdown(
        f"""
        <div style="padding:24px 16px 22px;text-align:center;border-bottom:1px solid {COLORS['border']};margin-bottom:18px;">
            <div style="font-size:42px;line-height:1;">⛳</div>
            <div style="font-family:'Fraunces',serif;font-size:22px;font-weight:700;color:{COLORS['cream']};margin-top:6px;letter-spacing:-0.02em;">Golf Journey</div>
            <div style="font-size:10px;color:{COLORS['flag']};letter-spacing:0.25em;text-transform:uppercase;margin-top:6px;font-weight:800;">PRO · V5.2</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for pid, icon, name, _ in PAGES:
        active = pid == st.session_state["active_page"]
        st.button(
            f"{icon}  {name}",
            key=f"side_{pid}",
            use_container_width=True,
            type="primary" if active else "secondary",
            on_click=_go, args=(pid,),
        )

    streak = practice_streak()
    profile = load_data().get("profile", {})
    a_stats = ach_stats()

    st.markdown(
        f"""
        <div style="margin-top:22px;padding:18px;background:linear-gradient(160deg,{COLORS['bg_3']},{COLORS['bg_2']});border-radius:16px;border:1px solid {COLORS['border']};">
            <div style="font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.18em;text-transform:uppercase;margin-bottom:10px;font-weight:700;">PLAYER</div>
            <div style="font-family:'Fraunces',serif;font-size:18px;font-weight:700;color:{COLORS['cream']};">{profile.get('name', 'Joel C.')}</div>
            <div style="font-size:12px;color:{COLORS['flag']};font-weight:700;margin-top:3px;letter-spacing:0.05em;">GHIN {profile.get('ghin', 31.3)}</div>
            <div style="font-size:11px;color:{COLORS['cream_dim']};margin-top:10px;line-height:1.5;">El Cariso · Scholl Canyon<br>Van Nuys Par 3</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if streak > 0:
        st.markdown(
            f"""
            <div class="streak-card" style="margin-top:14px;">
                <span style="font-size:24px;">🔥</span>
                <div>
                    <div style="font-size:10px;letter-spacing:0.18em;text-transform:uppercase;opacity:0.85;font-weight:700;">Day Streak</div>
                    <div style="font-family:'Fraunces',serif;font-size:24px;font-weight:700;line-height:1;">{streak}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="margin-top:14px;padding:14px;background:linear-gradient(135deg,rgba(212,162,76,0.10),{COLORS['bg_2']});border:1px solid {COLORS['border']};border-radius:14px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.18em;text-transform:uppercase;font-weight:700;">Achievements</div>
                    <div style="font-family:'Fraunces',serif;font-size:22px;font-weight:700;color:{COLORS['flag']};line-height:1;margin-top:4px;">{a_stats['unlocked']}<span style="color:{COLORS['cream_dim']};font-size:14px;"> / {a_stats['total']}</span></div>
                    <div style="font-size:10px;color:{COLORS['flag']};margin-top:3px;font-weight:700;letter-spacing:0.05em;">{a_stats['points']:,} pts</div>
                </div>
                <div style="font-size:30px;">🏆</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.button("View all 100 →", key="side_view_ach", use_container_width=True, on_click=_go, args=("trophy",))

    if newly:
        st.markdown(
            f"""
            <div style="margin-top:14px;padding:12px 14px;background:linear-gradient(135deg,rgba(212,162,76,0.18),rgba(212,162,76,0.05));border:1px solid {COLORS['flag']};border-radius:12px;">
                <div style="font-size:10px;color:{COLORS['flag']};font-weight:800;letter-spacing:0.18em;text-transform:uppercase;">🎉 Unlocked</div>
                <div style="font-size:13px;color:{COLORS['cream']};margin-top:4px;font-weight:600;">{newly[0]['name']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.caption("📱 Add to Home Screen on iPhone Safari for the full app experience.")


# ── Top nav (visible always — works whether sidebar open or collapsed) ──
nav_cols = st.columns(len(PAGES))
for i, (pid, icon, name, _) in enumerate(PAGES):
    with nav_cols[i]:
        active = pid == st.session_state["active_page"]
        st.button(
            f"{icon} {name}",
            key=f"top_{pid}",
            use_container_width=True,
            type="primary" if active else "secondary",
            on_click=_go, args=(pid,),
        )

st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

# ── Route ──
for pid, icon, name, fn in PAGES:
    if pid == st.session_state["active_page"]:
        fn()
        break
