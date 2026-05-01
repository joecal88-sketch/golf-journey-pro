"""Golf Journey Pro v5.1 — Dedicated Achievements Hub.

100 challenges across 4 tiers, 8 categories. Filterable, sortable,
with tier-colored progress bars and points system.
"""
import streamlit as st
from styles import COLORS
from achievements import get_all, stats, TIER_INFO, ACHIEVEMENTS


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
    if a["unlocked"]:
        return (
            f'<div style="background:linear-gradient(160deg,{color}1c,{COLORS["bg_3"]});'
            f'border:1.5px solid {color}88;border-radius:14px;padding:14px;display:flex;'
            f'gap:12px;align-items:center;min-height:84px;box-shadow:0 4px 18px {color}22;">'
            f'<div style="font-size:36px;line-height:1;flex-shrink:0;filter:drop-shadow(0 2px 6px {color}55);">{a["icon"]}</div>'
            f'<div style="flex:1;min-width:0;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;gap:6px;margin-bottom:3px;">'
            f'<div style="font-family:\'Fraunces\',serif;font-size:15px;font-weight:700;color:{COLORS["cream"]};">{a["name"]}</div>'
            f'{_tier_chip(a["tier"])}</div>'
            f'<div style="font-size:11.5px;color:{COLORS["cream_dim"]};line-height:1.4;">{a["desc"]}</div>'
            f'<div style="font-size:9px;color:{color};letter-spacing:0.2em;text-transform:uppercase;font-weight:800;margin-top:6px;">✓ Unlocked</div>'
            f'</div></div>'
        )
    # locked
    return (
        f'<div style="background:{COLORS["bg_2"]};border:1px solid {COLORS["border"]};'
        f'border-radius:14px;padding:14px;display:flex;gap:12px;align-items:center;'
        f'min-height:84px;opacity:0.6;">'
        f'<div style="font-size:36px;line-height:1;flex-shrink:0;filter:grayscale(1);">{a["icon"]}</div>'
        f'<div style="flex:1;min-width:0;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;gap:6px;margin-bottom:3px;">'
        f'<div style="font-family:\'Fraunces\',serif;font-size:15px;font-weight:700;color:{COLORS["text_dim"]};">{a["name"]}</div>'
        f'{_tier_chip(a["tier"])}</div>'
        f'<div style="font-size:11.5px;color:{COLORS["muted"]};line-height:1.4;">{a["desc"]}</div>'
        f'</div></div>'
    )


def render():
    s = stats()
    all_a = get_all()

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
            100 challenges. From easy wins to legendary feats. Unlock them all.
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
    """Render achievements in a 3-column responsive grid."""
    # Use 3 columns on wide; group items
    cols_per_row = 3
    for i in range(0, len(items), cols_per_row):
        chunk = items[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        for j, a in enumerate(chunk):
            with cols[j]:
                st.markdown(_ach_card(a), unsafe_allow_html=True)
        # vertical spacer
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
