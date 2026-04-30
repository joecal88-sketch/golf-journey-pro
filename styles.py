"""Golf Journey Pro v5.0 — Augusta-inspired premium theme."""

# Color tokens — "Masters" palette
COLORS = {
    "bg":          "#0B1410",     # near-black with green undertone
    "bg_2":        "#0F1B16",     # raised surfaces
    "bg_3":        "#152620",     # cards
    "border":      "#1F3329",
    "border_2":    "#2A4536",
    "fairway":     "#0E5C3A",     # deep masters green
    "fairway_2":   "#137A4D",     # brighter fairway
    "flag":        "#D4A24C",     # warm gold (flag stick / accent)
    "cream":       "#F5EFE0",     # parchment text
    "cream_dim":   "#C9C2B0",
    "muted":       "#8A8B83",
    "danger":      "#D4574C",
    "text":        "#F5EFE0",
    "text_dim":    "#A8A99F",
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,700;9..144,900&family=Inter:wght@400;500;600;700;800;900&display=swap');

* {{ -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }}

html, body, [class*="css"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: {COLORS['text']};
}}

.stApp {{
    background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(19,122,77,0.18), transparent 60%),
        radial-gradient(ellipse 60% 40% at 100% 100%, rgba(212,162,76,0.06), transparent 70%),
        {COLORS['bg']};
    background-attachment: fixed;
}}

/* Hide default streamlit chrome */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 1.5rem; padding-bottom: 4rem; max-width: 1280px; }}

/* Display heading font */
h1, .display, .hero-title {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: {COLORS['cream']} !important;
}}

h2 {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em !important;
    color: {COLORS['cream']} !important;
}}

h3, h4 {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    color: {COLORS['cream']} !important;
}}

p, span, label, div {{
    color: {COLORS['text']};
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {COLORS['bg_2']} 0%, {COLORS['bg']} 100%) !important;
    border-right: 1px solid {COLORS['border']};
}}
section[data-testid="stSidebar"] > div {{ padding-top: 0.5rem; }}

/* Sidebar collapse button always visible */
[data-testid="stSidebarCollapseButton"], [data-testid="stSidebarCollapsedControl"] {{
    opacity: 1 !important;
    visibility: visible !important;
    background: {COLORS['fairway_2']} !important;
    border-radius: 10px !important;
    z-index: 999999 !important;
    box-shadow: 0 4px 14px rgba(19,122,77,0.4) !important;
}}
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapsedControl"] svg {{ color: {COLORS['cream']} !important; }}

/* Buttons */
.stButton > button {{
    background: {COLORS['bg_3']};
    color: {COLORS['cream']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 12px 18px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    letter-spacing: 0.01em;
    transition: all 0.18s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset;
}}
.stButton > button:hover {{
    background: {COLORS['border_2']};
    border-color: {COLORS['fairway_2']};
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(19,122,77,0.2);
}}
.stButton > button:active {{ transform: translateY(0); }}

/* Primary button = filled fairway green with gold accent */
.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {COLORS['fairway']} 0%, {COLORS['fairway_2']} 100%);
    color: {COLORS['cream']};
    border: 1px solid {COLORS['fairway_2']};
    box-shadow:
        0 8px 24px rgba(19,122,77,0.35),
        inset 0 1px 0 rgba(255,255,255,0.1);
}}
.stButton > button[kind="primary"]:hover {{
    background: linear-gradient(135deg, {COLORS['fairway_2']} 0%, #1A8F5C 100%);
    box-shadow:
        0 12px 30px rgba(19,122,77,0.5),
        inset 0 1px 0 rgba(255,255,255,0.15);
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: {COLORS['bg_2']};
    padding: 6px;
    border-radius: 14px;
    border: 1px solid {COLORS['border']};
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent;
    border-radius: 10px;
    padding: 10px 18px;
    color: {COLORS['cream_dim']};
    font-weight: 600;
    font-size: 13px;
    border: none;
}}
.stTabs [aria-selected="true"] {{
    background: {COLORS['fairway']} !important;
    color: {COLORS['cream']} !important;
    box-shadow: 0 4px 12px rgba(19,122,77,0.3);
}}

/* Inputs */
.stTextInput input, .stTextArea textarea, .stNumberInput input,
.stSelectbox > div > div, [data-baseweb="select"] > div {{
    background: {COLORS['bg_2']} !important;
    border: 1px solid {COLORS['border']} !important;
    border-radius: 10px !important;
    color: {COLORS['cream']} !important;
    font-family: 'Inter', sans-serif !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: {COLORS['fairway_2']} !important;
    box-shadow: 0 0 0 3px rgba(19,122,77,0.15) !important;
}}

/* Metric */
[data-testid="stMetricValue"] {{
    font-family: 'Fraunces', Georgia, serif !important;
    font-weight: 700 !important;
    color: {COLORS['cream']} !important;
    letter-spacing: -0.02em;
}}
[data-testid="stMetricLabel"] {{
    color: {COLORS['cream_dim']} !important;
    font-size: 11px !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    font-weight: 700 !important;
}}
[data-testid="stMetricDelta"] {{ font-weight: 700 !important; }}

/* Premium card */
.gj-card {{
    background: linear-gradient(165deg, {COLORS['bg_3']} 0%, {COLORS['bg_2']} 100%);
    border: 1px solid {COLORS['border']};
    border-radius: 18px;
    padding: 24px;
    box-shadow:
        0 1px 0 rgba(255,255,255,0.04) inset,
        0 20px 40px -20px rgba(0,0,0,0.5);
    backdrop-filter: blur(20px);
    transition: all 0.25s ease;
}}
.gj-card:hover {{
    border-color: {COLORS['border_2']};
    transform: translateY(-2px);
    box-shadow:
        0 1px 0 rgba(255,255,255,0.06) inset,
        0 24px 50px -20px rgba(0,0,0,0.6);
}}

.gj-card-flush {{
    background: linear-gradient(165deg, {COLORS['bg_3']} 0%, {COLORS['bg_2']} 100%);
    border: 1px solid {COLORS['border']};
    border-radius: 18px;
    padding: 24px;
}}

/* Hero stat — huge serif number */
.hero-stat {{
    font-family: 'Fraunces', Georgia, serif;
    font-size: 64px;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.04em;
    color: {COLORS['cream']};
    background: linear-gradient(180deg, {COLORS['cream']} 0%, {COLORS['cream_dim']} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}
.hero-stat-label {{
    font-size: 11px;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: {COLORS['cream_dim']};
    font-weight: 700;
    margin-bottom: 8px;
}}

/* Section header with gold underline */
.section-header {{
    display: flex;
    align-items: baseline;
    gap: 16px;
    margin: 28px 0 18px;
}}
.section-header h2 {{
    margin: 0 !important;
    font-size: 28px;
}}
.section-header .accent {{
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, {COLORS['flag']}, transparent);
}}
.section-header .eyebrow {{
    color: {COLORS['flag']};
    font-size: 11px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    font-weight: 800;
}}

/* Pill / chip */
.gj-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    background: rgba(19,122,77,0.15);
    border: 1px solid rgba(19,122,77,0.3);
    border-radius: 99px;
    font-size: 11px;
    font-weight: 700;
    color: {COLORS['fairway_2']};
    letter-spacing: 0.05em;
    text-transform: uppercase;
}}
.gj-pill-gold {{
    background: rgba(212,162,76,0.12);
    border-color: rgba(212,162,76,0.3);
    color: {COLORS['flag']};
}}
.gj-pill-danger {{
    background: rgba(212,87,76,0.12);
    border-color: rgba(212,87,76,0.3);
    color: {COLORS['danger']};
}}

/* Pro-comparison gauge */
.gauge-row {{
    margin: 14px 0;
}}
.gauge-label {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 6px;
}}
.gauge-label .name {{
    font-size: 13px;
    color: {COLORS['cream']};
    font-weight: 600;
}}
.gauge-label .vals {{
    font-size: 12px;
    color: {COLORS['cream_dim']};
    font-family: 'Fraunces', serif;
}}
.gauge-label .vals .you {{ color: {COLORS['flag']}; font-weight: 700; }}
.gauge-label .vals .pro {{ color: {COLORS['cream_dim']}; }}
.gauge-track {{
    height: 8px;
    background: {COLORS['bg_2']};
    border-radius: 99px;
    overflow: hidden;
    border: 1px solid {COLORS['border']};
    position: relative;
}}
.gauge-fill {{
    height: 100%;
    background: linear-gradient(90deg, {COLORS['fairway']}, {COLORS['fairway_2']});
    border-radius: 99px;
    box-shadow: 0 0 12px rgba(19,122,77,0.5);
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}}
.gauge-fill.danger {{
    background: linear-gradient(90deg, #8B3A33, {COLORS['danger']});
    box-shadow: 0 0 12px rgba(212,87,76,0.4);
}}
.gauge-marker {{
    position: absolute;
    top: -3px;
    width: 2px;
    height: 14px;
    background: {COLORS['flag']};
    box-shadow: 0 0 8px {COLORS['flag']};
}}

/* Insight card — gradient border */
.insight-card {{
    position: relative;
    background: {COLORS['bg_3']};
    border-radius: 16px;
    padding: 20px 22px;
    margin: 10px 0;
    border-left: 3px solid {COLORS['fairway_2']};
}}
.insight-card.gold {{ border-left-color: {COLORS['flag']}; }}
.insight-card.danger {{ border-left-color: {COLORS['danger']}; }}
.insight-card .icon {{
    font-size: 22px;
    margin-bottom: 6px;
}}
.insight-card .title {{
    font-size: 14px;
    font-weight: 800;
    color: {COLORS['cream']};
    margin-bottom: 4px;
}}
.insight-card .body {{
    font-size: 13px;
    color: {COLORS['cream_dim']};
    line-height: 1.5;
}}

/* Achievement badges */
.ach-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 10px;
}}
.ach-badge {{
    background: {COLORS['bg_3']};
    border: 1px solid {COLORS['border']};
    border-radius: 14px;
    padding: 14px 12px;
    text-align: center;
    transition: all 0.2s;
}}
.ach-badge.unlocked {{
    background: linear-gradient(160deg, rgba(212,162,76,0.12), {COLORS['bg_3']});
    border-color: {COLORS['flag']};
    box-shadow: 0 0 20px rgba(212,162,76,0.15);
}}
.ach-badge.locked {{ opacity: 0.4; }}
.ach-badge .icon {{
    font-size: 28px;
    margin-bottom: 4px;
}}
.ach-badge .name {{
    font-size: 11px;
    font-weight: 700;
    color: {COLORS['cream']};
    line-height: 1.3;
}}
.ach-badge .desc {{
    font-size: 10px;
    color: {COLORS['cream_dim']};
    margin-top: 3px;
    line-height: 1.3;
}}

/* Streak badge */
.streak-card {{
    display: flex;
    align-items: center;
    gap: 12px;
    background: linear-gradient(135deg, rgba(212,162,76,0.18), rgba(212,162,76,0.05));
    border: 1px solid rgba(212,162,76,0.3);
    border-radius: 14px;
    padding: 12px 14px;
    color: {COLORS['flag']};
}}

/* Animated subtle pulse */
@keyframes pulse-flag {{
    0%, 100% {{ box-shadow: 0 0 0 0 rgba(212,162,76,0.4); }}
    50% {{ box-shadow: 0 0 0 8px rgba(212,162,76,0); }}
}}
.live-dot {{
    width: 8px; height: 8px;
    border-radius: 99px;
    background: {COLORS['flag']};
    animation: pulse-flag 1.6s infinite;
    display: inline-block;
}}

/* Caddy card */
.caddy-card {{
    background: linear-gradient(160deg, {COLORS['fairway']} 0%, #0a4a2e 100%);
    border-radius: 22px;
    padding: 28px;
    color: {COLORS['cream']};
    box-shadow:
        0 1px 0 rgba(255,255,255,0.08) inset,
        0 30px 60px -20px rgba(0,0,0,0.6);
    border: 1px solid rgba(255,255,255,0.08);
}}
.caddy-card .yard {{
    font-family: 'Fraunces', serif;
    font-size: 72px;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.04em;
    color: {COLORS['cream']};
}}
.caddy-card .yard-unit {{
    font-size: 24px;
    color: rgba(245,239,224,0.6);
    margin-left: 6px;
}}
.caddy-card .rec {{
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(212,162,76,0.4);
    border-radius: 14px;
    padding: 16px 18px;
    margin-top: 18px;
    backdrop-filter: blur(20px);
}}
.caddy-card .rec .club {{
    font-family: 'Fraunces', serif;
    font-size: 32px;
    font-weight: 700;
    color: {COLORS['flag']};
}}

/* Drill card */
.drill-card {{
    background: linear-gradient(160deg, {COLORS['bg_3']}, {COLORS['bg_2']});
    border: 1px solid {COLORS['border']};
    border-radius: 18px;
    overflow: hidden;
    transition: all 0.25s;
}}
.drill-card:hover {{
    border-color: {COLORS['fairway_2']};
    transform: translateY(-3px);
}}
.drill-card .thumb {{
    height: 140px;
    background: linear-gradient(135deg, {COLORS['fairway']}, {COLORS['bg_3']});
    display: flex; align-items: center; justify-content: center;
    font-size: 50px;
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-track {{ background: {COLORS['bg']}; }}
::-webkit-scrollbar-thumb {{ background: {COLORS['border_2']}; border-radius: 99px; }}
::-webkit-scrollbar-thumb:hover {{ background: {COLORS['fairway_2']}; }}

/* Hide scrollbar in some elements */
.stMarkdown {{ color: {COLORS['text']}; }}

/* Slider */
.stSlider [data-baseweb="slider"] > div:nth-child(2) > div {{
    background: linear-gradient(90deg, {COLORS['fairway']}, {COLORS['fairway_2']}) !important;
}}

/* Expander */
.stExpander {{
    background: {COLORS['bg_2']};
    border: 1px solid {COLORS['border']};
    border-radius: 14px;
}}

/* File uploader */
[data-testid="stFileUploader"] section {{
    background: {COLORS['bg_2']};
    border: 2px dashed {COLORS['border_2']};
    border-radius: 14px;
}}
[data-testid="stFileUploader"] section:hover {{
    border-color: {COLORS['fairway_2']};
    background: rgba(19,122,77,0.05);
}}

/* Success/info/error/warning boxes */
.stAlert {{
    background: {COLORS['bg_3']} !important;
    border-radius: 12px !important;
    border: 1px solid {COLORS['border']} !important;
}}
</style>
"""
