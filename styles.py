CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Global ─────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #080808 !important;
    color: #fff !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 1.2rem 1.5rem !important;
    max-width: 1400px !important;
}

/* ── Sidebar ────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0D0D0D 0%, #050505 100%) !important;
    border-right: 1px solid #1A1A1A !important;
}
section[data-testid="stSidebar"] * { color: #fff !important; }
section[data-testid="stSidebar"] .stRadio label {
    padding: 12px 14px !important;
    border-radius: 12px !important;
    transition: all 0.15s ease !important;
    margin-bottom: 4px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    background: #161616 !important;
}

/* ── KPI Cards (premium gradient style) ─────────────── */
.kpi-card {
    background: linear-gradient(135deg, #111 0%, #0c0c0c 100%);
    border: 1px solid #1E1E1E;
    border-radius: 18px;
    padding: 22px 24px;
    margin-bottom: 4px;
    transition: all .25s ease;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, transparent, var(--accent, #00D4AA), transparent);
    opacity: 0.6;
}
.kpi-card:hover {
    border-color: #00D4AA50;
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,212,170,0.08);
}
.kpi-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #666;
    margin-bottom: 12px;
}
.kpi-value {
    font-size: 42px;
    font-weight: 900;
    letter-spacing: -1.5px;
    color: #fff;
    line-height: 1;
}
.kpi-unit {
    font-size: 16px;
    font-weight: 400;
    color: #777;
    margin-left: 4px;
}
.kpi-sub {
    font-size: 12px;
    color: #888;
    margin-top: 10px;
}
.kpi-up { color: #00D4AA !important; font-weight: 600; }
.kpi-warn { color: #FFB800 !important; font-weight: 600; }

/* ── Section labels ─────────────────────────────────── */
.section-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #888;
    padding-bottom: 12px;
    border-bottom: 1px solid #1A1A1A;
    margin-bottom: 18px;
    margin-top: 8px;
}

/* ── Progress bars ──────────────────────────────────── */
.prog-track {
    background: #1A1A1A;
    border-radius: 8px;
    height: 8px;
    overflow: hidden;
    position: relative;
}
.prog-fill {
    height: 100%;
    border-radius: 8px;
    transition: width .8s cubic-bezier(0.4, 0, 0.2, 1);
    background: linear-gradient(90deg, var(--c1, #00D4AA), var(--c2, #00B894));
    position: relative;
}
.prog-fill::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    animation: shimmer 2s infinite;
}
@keyframes shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

/* ── Data cards ─────────────────────────────────────── */
.data-card {
    background: #111;
    border: 1px solid #1E1E1E;
    border-radius: 16px;
    padding: 20px 22px;
    margin-bottom: 14px;
    transition: border-color .2s ease;
}
.data-card:hover { border-color: #2A2A2A; }

/* ── TheStack-style protocol bar ────────────────────── */
.stack-bar {
    background: linear-gradient(135deg, #FFB800 0%, #FF8C00 100%);
    padding: 16px 22px;
    border-radius: 14px 14px 0 0;
    font-weight: 800;
    font-size: 16px;
    color: #000;
    letter-spacing: 0.3px;
}
.stack-card {
    background: #0F0F0F;
    border: 1px solid #1A1A1A;
    border-top: none;
    border-radius: 0 0 14px 14px;
    padding: 16px 20px;
    margin-bottom: 14px;
}
.dot {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    border: 2px solid #FFB800;
    display: inline-block;
    margin-right: 6px;
    transition: all 0.2s ease;
}
.dot.done {
    background: #FFB800;
    box-shadow: 0 0 8px rgba(255,184,0,0.5);
}

/* ── Achievement chips ──────────────────────────────── */
.achievement {
    display: inline-block;
    background: linear-gradient(135deg, rgba(255,184,0,0.12), rgba(255,140,0,0.08));
    border: 1px solid rgba(255,184,0,0.3);
    border-radius: 24px;
    padding: 8px 16px;
    margin: 4px 6px 4px 0;
    font-size: 12px;
    font-weight: 600;
    color: #FFB800;
}
.achievement.locked {
    background: #0F0F0F;
    border-color: #222;
    color: #444;
}

/* ── Streak flame ───────────────────────────────────── */
.streak-card {
    background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
    border-radius: 16px;
    padding: 14px 20px;
    color: #000;
    font-weight: 800;
    display: flex;
    align-items: center;
    gap: 10px;
}

/* ── Streamlit metric override ──────────────────────── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #111 0%, #0c0c0c 100%) !important;
    border: 1px solid #1E1E1E !important;
    border-radius: 16px !important;
    padding: 18px !important;
}
[data-testid="stMetricValue"] {
    color: #fff !important;
    font-weight: 800 !important;
    font-size: 28px !important;
}
[data-testid="stMetricLabel"] {
    color: #888 !important;
    font-size: 10px !important;
    letter-spacing: 1.8px !important;
    text-transform: uppercase !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] {
    color: #00D4AA !important;
    font-weight: 600 !important;
}

/* ── Buttons ────────────────────────────────────────── */
.stButton button {
    background: linear-gradient(135deg, #00D4AA 0%, #00B894 100%) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    padding: 12px 24px !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(0,212,170,0.15) !important;
}
.stButton button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(0,212,170,0.25) !important;
}
.stButton button:active { transform: translateY(0); }

/* ── Inputs ─────────────────────────────────────────── */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
.stDateInput input,
.stTimeInput input {
    background: #0E0E0E !important;
    border: 1px solid #252525 !important;
    border-radius: 12px !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s ease !important;
}
.stTextInput input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus {
    border-color: #00D4AA !important;
    box-shadow: 0 0 0 3px rgba(0,212,170,0.1) !important;
}
.stSelectbox > div > div {
    background: #0E0E0E !important;
    border: 1px solid #252525 !important;
    border-radius: 12px !important;
    color: #fff !important;
}

/* ── Tabs (premium look) ────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #0A0A0A;
    border-radius: 12px;
    padding: 6px;
    border: 1px solid #161616;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #777 !important;
    border-radius: 8px !important;
    padding: 10px 18px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: #161616 !important;
    color: #00D4AA !important;
}

/* ── Tables ─────────────────────────────────────────── */
.stDataFrame {
    background: #0A0A0A !important;
    border-radius: 12px !important;
    border: 1px solid #1A1A1A !important;
}

/* ── Scrollbar ──────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0A0A0A; }
::-webkit-scrollbar-thumb { background: #2A2A2A; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #00D4AA; }

/* ── Mobile responsive ──────────────────────────────── */
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.75rem !important; }
    .kpi-value { font-size: 32px; }
    .kpi-card { padding: 16px 18px; }
    .data-card { padding: 16px 18px; }
}

/* ── Page header ────────────────────────────────────── */
.page-header {
    margin-bottom: 24px;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 16px;
}
.page-eyebrow {
    font-size: 11px;
    color: #00D4AA;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    font-weight: 700;
}
.page-title {
    font-size: 32px;
    font-weight: 900;
    margin-top: 6px;
    letter-spacing: -1px;
    line-height: 1.1;
}

/* ── Pill badges ────────────────────────────────────── */
.pill {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.pill-green { background: rgba(0,212,170,0.15); color: #00D4AA; }
.pill-amber { background: rgba(255,184,0,0.15); color: #FFB800; }
.pill-red   { background: rgba(255,59,48,0.15);  color: #FF3B30; }
.pill-blue  { background: rgba(74,158,255,0.15); color: #4A9EFF; }

/* ── Insight card (Stroke-Saver) ─────────────────────── */
.insight-card {
    background: linear-gradient(135deg, rgba(0,212,170,0.06) 0%, rgba(0,184,148,0.02) 100%);
    border: 1px solid rgba(0,212,170,0.2);
    border-radius: 16px;
    padding: 20px 22px;
    margin-bottom: 12px;
}
.insight-strokes {
    font-size: 32px;
    font-weight: 900;
    color: #00D4AA;
    line-height: 1;
}

/* ── Quick-log floating button area ──────────────────── */
.qlog {
    position: fixed;
    bottom: 24px;
    right: 24px;
    z-index: 100;
}
</style>
"""
