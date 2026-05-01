"""Golf Journey Pro v5.2 — Dedicated Achievements Hub.

150+ challenges across 4 tiers, 8 categories. Filterable, sortable,
with hover glass FX, click-to-detail modals, and unlock timestamps.
"""
import streamlit as st
from styles import COLORS
from achievements import get_all, stats, TIER_INFO, ACHIEVEMENTS


def _inject_achievement_css():
    """One-time CSS injection for hover glass + tier glows."""
    if st.session_state.get("_ach_css_done"):
        return
    st.session_state["_ach_css_done"] = True
    st.markdown("""
    <style>
      .ach-card {
        position: relative;
        border-radius: 14px;
        padding: 14px;
        display: flex;
        gap: 12px;
        align-items: center;
        min-height: 90px;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: transform 0.25s cubic-bezier(.2,.8,.2,1), box-shadow 0.25s ease, border-color 0.25s ease;
        cursor: pointer;
        overflow: hidden;
      }
      .ach-card::before {
        content: "";
        position: absolute; inset: 0;
        background: radial-gradient(circle at 30% 0%, rgba(255,255,255,0.06), transparent 60%);
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s ease;
      }
      .ach-card:hover {
        transform: translateY(-3px) scale(1.025);
        box-shadow: 0 14px 38px rgba(0,0,0,0.45), 0 0 0 1px var(--tier-color, rgba(255,255,255,0.2));
      }
      .ach-card:hover::before { opacity: 1; }
      .ach-card .ach-icon {
        font-size: 36px;
        line-height: 1;
        flex-shrink: 0;
        transition: transform 0.3s ease, filter 0.3s ease;
      }
      .ach-card:hover .ach-icon {
        transform: scale(1.1) rotate(-4deg);
      }
      .ach-card.locked { opacity: 0.55; }
      .ach-card.locked .ach-icon { filter: grayscale(1); }
      .ach-card.locked:hover { opacity: 0.78; }
      .ach-glow-ring {
        position: absolute; inset: -1px;
        border-radius: 14px;
        pointer-events: none;
        opacity: 0; transition: opacity 0.3s ease;
      }
      .ach-card:hover .ach-glow-ring { opacity: 1; }
      /* Click overlay: target ONLY buttons with key prefix "ach_open_" by using
         Streamlit's stVerticalBlock containing both card markdown + button. The
         column wrapper becomes the positioning context; the button absolutely
         positions over the card markdown. */
      div[data-testid="column"]:has(.ach-card),
      div[data-testid="stColumn"]:has(.ach-card) {
        position: relative;
      }
      div[data-testid="column"]:has(.ach-card) div[data-testid="stButton"],
      div[data-testid="stColumn"]:has(.ach-card) div[data-testid="stButton"] {
        position: absolute !important;
        top: 0; left: 0; right: 0; bottom: 0;
        margin: 0 !important;
        z-index: 5;
        height: 100%;
      }
      div[data-testid="column"]:has(.ach-card) div[data-testid="stButton"] > button,
      div[data-testid="stColumn"]:has(.ach-card) div[data-testid="stButton"] > button {
        width: 100%;
        height: 100%;
        min-height: 90px;
        background: transparent !important;
        border: none !important;
        color: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
        cursor: pointer;
      }
      div[data-testid="column"]:has(.ach-card) div[data-testid="stButton"] > button:focus,
      div[data-testid="column"]:has(.ach-card) div[data-testid="stButton"] > button:active,
      div[data-testid="column"]:has(.ach-card) div[data-testid="stButton"] > button:hover,
      div[data-testid="stColumn"]:has(.ach-card) div[data-testid="stButton"] > button:focus,
      div[data-testid="stColumn"]:has(.ach-card) div[data-testid="stButton"] > button:active,
      div[data-testid="stColumn"]:has(.ach-card) div[data-testid="stButton"] > button:hover {
        outline: none !important;
        box-shadow: none !important;
        background: transparent !important;
        color: transparent !important;
      }
      .ach-modal {
        background: rgba(20, 28, 24, 0.90); backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border: 1.5px solid var(--tier-color);
        border-radius: 18px;
        padding: 32px 34px;
        margin: 16px 0 20px;
        box-shadow: 0 16px 70px rgba(0,0,0,0.6), 0 0 60px var(--tier-color);
        animation: ach-rise 0.4s cubic-bezier(.2,.8,.2,1);
      }
      @keyframes ach-rise {
        from { opacity: 0; transform: translateY(20px) scale(0.96); }
        to   { opacity: 1; transform: translateY(0) scale(1); }
      }
      .ach-modal h2 { margin: 0 0 4px; font-size: 28px; color: #fff; }
      .ach-modal .ach-cat { font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase; color: var(--tier-color); font-weight: 800; }
      .ach-modal .ach-desc { color: rgba(255,255,255,0.78); font-size: 15px; margin: 14px 0; line-height: 1.55; }
      .ach-modal .ach-meta-row { display: flex; gap: 14px; flex-wrap: wrap; margin-top: 18px; }
      .ach-modal .ach-meta-tile {
        flex: 1; min-width: 130px;
        background: rgba(0,0,0,0.3); padding: 12px 14px; border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.08);
      }
      .ach-modal .ach-meta-label { font-size: 10px; letter-spacing: 0.18em; text-transform: uppercase; color: rgba(255,255,255,0.55); font-weight: 700; }
      .ach-modal .ach-meta-val { font-family: 'Fraunces', serif; font-size: 22px; color: #fff; margin-top: 4px; }
      .ach-modal .ach-hero-icon { font-size: 72px; line-height: 1; }
    </style>
    """, unsafe_allow_html=True)


def _tier_chip(tier: str) -> str:
    info = TIER_INFO.get(tier, TIER_INFO["easy"])
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;'
        f'background:{info["color"]}22;color:{info["color"]};border:1px solid {info["color"]}55;'
        f'font-size:9px;letter-spacing:0.18em;text-transform:uppercase;font-weight:800;">'
        f'{info["label"]} · {info["points"]}pt</span>'
    )


def _progress_bar(pct: float, color: str, height: int = 8) -> str:
    return (
        f'<div style="width:100%;height:{height}px;background:{COLORS["bg"]};'
        f'border-radius:999px;overflow:hidden;border:1px solid {COLORS["border"]};">'
        f'<div style="width:{max(0,min(100,pct)):.1f}%;height:100%;'
        f'background:linear-gradient(90deg,{color},{color}cc);border-radius:999px;'
        f'transition:width 0.6s ease;"></div></div>'
    )


def _ach_card(a: dict) -> str:
    info = TIER_INFO.get(a["tier"], TIER_INFO["easy"])
    color = info["color"]
    locked_class = "" if a["unlocked"] else "locked"
    bg = (
        f'linear-gradient(160deg,{color}1c,{COLORS["bg_3"]})'
        if a["unlocked"] else COLORS["bg_2"]
    )
    border = f'1.5px solid {color}88' if a["unlocked"] else f'1px solid {COLORS["border"]}'
    shadow = f'0 4px 18px {color}22' if a["unlocked"] else "none"
    text_color = COLORS["cream"] if a["unlocked"] else COLORS["text_dim"]
    desc_color = COLORS["cream_dim"] if a["unlocked"] else COLORS["muted"]
    status_html = (
        f'<div style="font-size:9px;color:{color};letter-spacing:0.2em;text-transform:uppercase;font-weight:800;margin-top:6px;">✓ Unlocked'
        + (f' · {a.get("unlocked_at","")[:10]}' if a.get("unlocked_at") else "")
        + '</div>'
    ) if a["unlocked"] else (
        f'<div style="font-size:9px;color:{COLORS["muted"]};letter-spacing:0.2em;text-transform:uppercase;font-weight:800;margin-top:6px;">🔒 Locked</div>'
    )
    return (
        f'<div class="ach-card {locked_class}" '
        f'style="--tier-color:{color}; background:{bg}; border:{border}; box-shadow:{shadow};">'
        f'  <div class="ach-glow-ring" style="box-shadow:inset 0 0 0 2px {color}66, 0 0 24px {color}44;"></div>'
        f'  <div class="ach-icon" style="filter:drop-shadow(0 2px 6px {color}55);">{a["icon"]}</div>'
        f'  <div style="flex:1;min-width:0;">'
        f'    <div style="display:flex;justify-content:space-between;align-items:center;gap:6px;margin-bottom:3px;">'
        f'      <div style="font-family:\'Fraunces\',serif;font-size:15px;font-weight:700;color:{text_color};">{a["name"]}</div>'
        f'      {_tier_chip(a["tier"])}</div>'
        f'    <div style="font-size:11.5px;color:{desc_color};line-height:1.4;">{a["desc"]}</div>'
        f'    {status_html}'
        f'  </div>'
        f'</div>'
    )


def _render_ach_modal(all_a):
    """Render glass modal for the currently-selected achievement."""
    aid = st.session_state.get("ach_modal_id")
    if not aid:
        return
    a = next((x for x in all_a if x["id"] == aid), None)
    if not a:
        return
    info = TIER_INFO.get(a["tier"], TIER_INFO["easy"])
    color = info["color"]

    # Find related "next" achievements in same category (locked)
    related = [x for x in all_a if x["category"] == a["category"] and not x["unlocked"] and x["id"] != aid][:3]
    related_html = ""
    if related:
        rels = "".join(
            f'<div style="display:flex;gap:10px;align-items:center;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.06);">'
            f'<span style="font-size:20px;">{r["icon"]}</span>'
            f'<span style="flex:1;font-size:13px;color:rgba(255,255,255,0.85);">{r["name"]}</span>'
            f'<span style="font-size:9px;color:{TIER_INFO[r["tier"]]["color"]};letter-spacing:0.18em;font-weight:800;text-transform:uppercase;">{r["tier"]}</span>'
            f'</div>' for r in related
        )
        related_html = f'<div style="margin-top:18px;"><div style="font-size:10px;letter-spacing:0.2em;text-transform:uppercase;color:rgba(255,255,255,0.55);font-weight:700;margin-bottom:6px;">What’s next in {a["category"]}</div>{rels}</div>'

    unlocked_at = a.get("unlocked_at")
    when_str = unlocked_at[:19].replace("T", " ") if unlocked_at else "—"
    status_pill = (
        f'<span style="display:inline-block;padding:4px 12px;border-radius:999px;background:{color}30;color:{color};border:1px solid {color}80;font-size:10px;font-weight:800;letter-spacing:0.2em;text-transform:uppercase;">✓ Unlocked</span>'
        if a["unlocked"] else
        f'<span style="display:inline-block;padding:4px 12px;border-radius:999px;background:rgba(255,255,255,0.08);color:rgba(255,255,255,0.6);border:1px solid rgba(255,255,255,0.15);font-size:10px;font-weight:800;letter-spacing:0.2em;text-transform:uppercase;">🔒 Locked</span>'
    )

    icon_filter = f"filter:drop-shadow(0 6px 20px {color});" if a['unlocked'] else f"filter:drop-shadow(0 6px 20px {color}) grayscale(0.5);"
    modal_html = (
        f'<div class="ach-modal" style="--tier-color:{color}50;">'
        f'<div style="display:flex;gap:24px;align-items:center;">'
        f'<div class="ach-hero-icon" style="{icon_filter}">{a["icon"]}</div>'
        f'<div style="flex:1;"><div class="ach-cat">{a["category"]} · {info["label"]}</div>'
        f'<h2 style="margin:6px 0 0;color:#FAF7F2;font-family:Georgia,serif;font-size:28px;">{a["name"]}</h2>'
        f'<div style="margin-top:10px;">{status_pill}</div></div></div>'
        f'<div class="ach-desc" style="margin-top:18px;font-size:15px;color:rgba(255,255,255,0.78);line-height:1.6;">{a["desc"]}</div>'
        f'<div class="ach-meta-row" style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px;">'
        f'<div class="ach-meta-tile"><div class="ach-meta-label">Points</div><div class="ach-meta-val" style="color:{color};">{info["points"]}</div></div>'
        f'<div class="ach-meta-tile"><div class="ach-meta-label">Tier</div><div class="ach-meta-val">{info["label"]}</div></div>'
        f'<div class="ach-meta-tile"><div class="ach-meta-label">Unlocked</div><div class="ach-meta-val" style="font-size:14px;">{when_str}</div></div>'
        f'</div>'
        f'{related_html}'
        f'</div>'
    )
    st.markdown(modal_html, unsafe_allow_html=True)
    if st.button("✕ Close", key=f"close_ach_modal"):
        st.session_state["ach_modal_id"] = None
        st.rerun()


def render():
    _inject_achievement_css()
    s = stats()
    all_a = get_all()

    # Render modal first so it appears at the top
    _render_ach_modal(all_a)

    # ── Hero header ──
    pct = (s["unlocked"] / s["total"] * 100) if s["total"] else 0
    st.markdown(
        f"""
        <div style="margin-bottom:8px;">
            <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.32em;text-transform:uppercase;font-weight:800;">🏆 ACHIEVEMENTS HUB</div>
        </div>
        <h1 style="font-family:'Fraunces',serif;font-size:46px;font-weight:700;letter-spacing:-0.025em;color:{COLORS['cream']};margin:0 0 4px 0;line-height:1.05;">
            Your Golf Journey, Tracked.
        </h1>
        <div style="font-size:15px;color:{COLORS['cream_dim']};margin-bottom:22px;">
            {s['total']} challenges. From easy wins to legendary feats. Tap any card to dive in.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Headline stats row ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div style="background:linear-gradient(160deg,{COLORS['bg_3']},{COLORS['bg_2']});border:1px solid {COLORS['border']};border-radius:18px;padding:20px;">
                <div style="font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.2em;text-transform:uppercase;font-weight:700;">Unlocked</div>
                <div style="font-family:'Fraunces',serif;font-size:48px;font-weight:700;color:{COLORS['flag']};line-height:1;margin-top:6px;">{s['unlocked']}<span style="color:{COLORS['cream_dim']};font-size:22px;"> / {s['total']}</span></div>
                <div style="margin-top:14px;">{_progress_bar(pct, COLORS['flag'])}</div>
                <div style="font-size:11px;color:{COLORS['cream_dim']};margin-top:8px;">{pct:.1f}% complete</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div style="background:linear-gradient(160deg,{COLORS['bg_3']},{COLORS['bg_2']});border:1px solid {COLORS['border']};border-radius:18px;padding:20px;">
                <div style="font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.2em;text-transform:uppercase;font-weight:700;">Achievement Points</div>
                <div style="font-family:'Fraunces',serif;font-size:48px;font-weight:700;color:{COLORS['cream']};line-height:1;margin-top:6px;">{s['points']:,}</div>
                <div style="font-size:11px;color:{COLORS['cream_dim']};margin-top:14px;">Easy 10 · Med 25 · Hard 60 · Legendary 150</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        # Next-up: 3 closest locked easy/medium ones
        locked = [a for a in all_a if not a["unlocked"]]
        easy_med = [a for a in locked if a["tier"] in ("easy", "medium")][:3]
        if easy_med:
            inner = "".join(
                f'<div style="display:flex;gap:8px;align-items:center;padding:6px 0;border-bottom:1px solid {COLORS["border"]};">'
                f'<span style="font-size:18px;">{a["icon"]}</span>'
                f'<span style="font-size:12px;color:{COLORS["cream"]};flex:1;">{a["name"]}</span>'
                f'<span style="font-size:9px;color:{TIER_INFO[a["tier"]]["color"]};letter-spacing:0.15em;text-transform:uppercase;font-weight:800;">{a["tier"]}</span>'
                f'</div>'
                for a in easy_med
            )
        else:
            inner = f'<div style="font-size:13px;color:{COLORS["cream_dim"]};">All easy/medium unlocked.</div>'
        st.markdown(
            f"""
            <div style="background:linear-gradient(160deg,{COLORS['bg_3']},{COLORS['bg_2']});border:1px solid {COLORS['border']};border-radius:18px;padding:20px;">
                <div style="font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.2em;text-transform:uppercase;font-weight:700;margin-bottom:8px;">Next Up</div>
                {inner}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c4:
        # Tier breakdown
        tier_rows = ""
        for tier_id, info in TIER_INFO.items():
            t = s["by_tier"][tier_id]
            tpct = (t["unlocked"] / t["total"] * 100) if t["total"] else 0
            tier_rows += (
                f'<div style="margin-bottom:8px;">'
                f'<div style="display:flex;justify-content:space-between;font-size:11px;color:{COLORS["cream"]};margin-bottom:3px;">'
                f'<span style="color:{info["color"]};font-weight:700;letter-spacing:0.1em;text-transform:uppercase;">{info["label"]}</span>'
                f'<span>{t["unlocked"]} / {t["total"]}</span></div>'
                f'{_progress_bar(tpct, info["color"], height=6)}'
                f'</div>'
            )
        st.markdown(
            f"""
            <div style="background:linear-gradient(160deg,{COLORS['bg_3']},{COLORS['bg_2']});border:1px solid {COLORS['border']};border-radius:18px;padding:20px;">
                <div style="font-size:10px;color:{COLORS['cream_dim']};letter-spacing:0.2em;text-transform:uppercase;font-weight:700;margin-bottom:10px;">By Tier</div>
                {tier_rows}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:18px;'></div>", unsafe_allow_html=True)

    # ── Dev controls: lock everything (for shipping a fresh app) ──
    with st.expander("⚙️ Developer · Reset all achievements", expanded=False):
        st.markdown(
            f"<div style='font-size:13px;color:{COLORS['cream_dim']};margin-bottom:10px;'>"
            "Wipes every unlocked achievement so you can re-earn them in the finished app. "
            "Your rounds, practice shots, and profile are <b>not</b> touched."
            "</div>",
            unsafe_allow_html=True,
        )
        confirm = st.checkbox("Yes, I want to lock all achievements", key="ach_reset_confirm")
        if st.button("🔒 Lock all 151 achievements", key="ach_reset_btn", disabled=not confirm):
            try:
                from cloud_storage import load_data, save_data
                d = load_data()
                d["achievements"] = {}
                save_data(d)
                st.session_state["pending_unlocks"] = []
                st.success("All achievements locked. They'll re-unlock as you play.")
                st.rerun()
            except Exception as e:
                st.error(f"Reset failed: {e}")

    # ── Filters ──
    st.markdown(
        f'<div style="font-size:10px;color:{COLORS["cream_dim"]};letter-spacing:0.25em;text-transform:uppercase;font-weight:700;margin-bottom:10px;">FILTER & SORT</div>',
        unsafe_allow_html=True,
    )
    f1, f2, f3, f4 = st.columns([2, 2, 2, 1.2])
    with f1:
        category = st.selectbox(
            "Category",
            options=["All", "Scoring", "Practice", "Distance", "Short Game", "Streaks", "Courses", "Coach", "Special"],
            key="ach_filter_cat",
        )
    with f2:
        tier_filter = st.selectbox(
            "Tier",
            options=["All", "Easy", "Medium", "Hard", "Legendary"],
            key="ach_filter_tier",
        )
    with f3:
        status = st.selectbox(
            "Status",
            options=["All", "Unlocked", "Locked"],
            key="ach_filter_status",
        )
    with f4:
        sort_by = st.selectbox(
            "Sort",
            options=["Default", "Tier", "Name"],
            key="ach_sort",
        )

    # Apply filters
    filtered = list(all_a)
    if category != "All":
        filtered = [a for a in filtered if a["category"] == category]
    if tier_filter != "All":
        filtered = [a for a in filtered if a["tier"].lower() == tier_filter.lower()]
    if status == "Unlocked":
        filtered = [a for a in filtered if a["unlocked"]]
    elif status == "Locked":
        filtered = [a for a in filtered if not a["unlocked"]]

    # Sort
    tier_order = {"easy": 0, "medium": 1, "hard": 2, "legendary": 3}
    if sort_by == "Tier":
        filtered.sort(key=lambda a: (tier_order[a["tier"]], not a["unlocked"], a["name"]))
    elif sort_by == "Name":
        filtered.sort(key=lambda a: a["name"])
    else:
        # Default: unlocked first within each tier
        filtered.sort(key=lambda a: (tier_order[a["tier"]], not a["unlocked"]))

    st.markdown(
        f'<div style="font-size:12px;color:{COLORS["cream_dim"]};margin:6px 0 12px;">Showing <b style="color:{COLORS["cream"]};">{len(filtered)}</b> of {s["total"]} achievements</div>',
        unsafe_allow_html=True,
    )

    # ── Grid ──
    if not filtered:
        st.markdown(
            f'<div style="text-align:center;padding:48px;color:{COLORS["cream_dim"]};">No achievements match your filters.</div>',
            unsafe_allow_html=True,
        )
        return

    # Group by category if "All"
    if category == "All" and sort_by == "Default":
        cats_order = ["Scoring", "Practice", "Distance", "Short Game", "Streaks", "Courses", "Coach", "Special"]
        for cat in cats_order:
            cat_items = [a for a in filtered if a["category"] == cat]
            if not cat_items:
                continue
            cat_unlocked = sum(1 for a in cat_items if a["unlocked"])
            st.markdown(
                f"""
                <div style="margin-top:22px;margin-bottom:10px;display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid {COLORS['border']};padding-bottom:6px;">
                    <div style="font-family:'Fraunces',serif;font-size:22px;font-weight:700;color:{COLORS['cream']};">{cat}</div>
                    <div style="font-size:11px;color:{COLORS['flag']};letter-spacing:0.15em;text-transform:uppercase;font-weight:700;">{cat_unlocked} / {len(cat_items)} Unlocked</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            _render_grid(cat_items)
    else:
        _render_grid(filtered)


def _render_grid(items):
    """Render achievements in a 3-column responsive grid with click-to-detail."""
    cols_per_row = 3
    for i in range(0, len(items), cols_per_row):
        chunk = items[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for j, a in enumerate(chunk):
            with cols[j]:
                st.markdown(_ach_card(a), unsafe_allow_html=True)
                # Invisible click overlay covering the entire tile (CSS handles positioning)
                if st.button(" ", key=f"ach_open_{a['id']}", use_container_width=True):
                    st.session_state["ach_modal_id"] = a["id"]
                    st.rerun()
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
