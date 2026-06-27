"""
Plotcode AI Delivery Automation — GOD-LEVEL Theme Engine
Ultra-premium 3D effects, particle systems, aurora backgrounds, neon glows,
animated gradients, glassmorphism, and cinematic transitions.
"""

THEMES = {
    "🌑 Obsidian Dark": {
        "key": "dark",
        "bg": "#030810",
        "bg_secondary": "#0a1628",
        "bg_tertiary": "#0d1f3c",
        "card_bg": "rgba(10, 22, 40, 0.7)",
        "card_border": "rgba(120, 80, 255, 0.18)",
        "card_hover_border": "rgba(0, 210, 255, 0.5)",
        "text_primary": "#f0f4ff",
        "text_secondary": "#7b8db0",
        "text_muted": "#3d4f6f",
        "accent_purple": "#a855f7",
        "accent_cyan": "#06d6f6",
        "accent_rose": "#ff2d6f",
        "accent_emerald": "#00e89d",
        "accent_amber": "#fbbf24",
        "accent_blue": "#3b82f6",
        "gradient_primary": "linear-gradient(135deg, #a855f7 0%, #06d6f6 50%, #00e89d 100%)",
        "gradient_hero": "linear-gradient(135deg, #030810 0%, #0a1628 40%, #1a0a3e 70%, #030810 100%)",
        "gradient_card": "linear-gradient(180deg, rgba(168,85,247,0.08) 0%, rgba(6,214,246,0.03) 100%)",
        "gradient_glow": "0 0 40px rgba(168,85,247,0.2), 0 0 80px rgba(6,214,246,0.1), 0 0 120px rgba(0,232,157,0.05)",
        "shadow_3d": "0 25px 60px -12px rgba(0,0,0,0.7), 0 12px 28px -8px rgba(168,85,247,0.15), inset 0 1px 0 rgba(255,255,255,0.05)",
        "shadow_hover": "0 35px 80px -12px rgba(0,0,0,0.8), 0 18px 40px -8px rgba(6,214,246,0.2), inset 0 1px 0 rgba(255,255,255,0.08)",
        "glass_blur": "24px",
        "glass_bg": "rgba(10, 22, 40, 0.6)",
        "glass_border": "1px solid rgba(255,255,255,0.06)",
        "neon_glow": "0 0 10px rgba(168,85,247,0.4), 0 0 30px rgba(168,85,247,0.2), 0 0 60px rgba(168,85,247,0.1)",
        "neon_cyan": "0 0 10px rgba(6,214,246,0.4), 0 0 30px rgba(6,214,246,0.2), 0 0 60px rgba(6,214,246,0.1)",
        "particle_color": "#a855f7",
        "aurora_1": "rgba(168,85,247,0.15)",
        "aurora_2": "rgba(6,214,246,0.12)",
        "aurora_3": "rgba(0,232,157,0.08)",
    },
    "☀️ Frost Light": {
        "key": "light",
        "bg": "#f0f2f8",
        "bg_secondary": "#ffffff",
        "bg_tertiary": "#e8ecf4",
        "card_bg": "rgba(255, 255, 255, 0.88)",
        "card_border": "rgba(100, 60, 210, 0.1)",
        "card_hover_border": "rgba(100, 60, 210, 0.35)",
        "text_primary": "#111827",
        "text_secondary": "#4b5563",
        "text_muted": "#9ca3af",
        "accent_purple": "#7c3aed",
        "accent_cyan": "#0891b2",
        "accent_rose": "#e11d48",
        "accent_emerald": "#059669",
        "accent_amber": "#d97706",
        "accent_blue": "#2563eb",
        "gradient_primary": "linear-gradient(135deg, #7c3aed 0%, #0891b2 50%, #059669 100%)",
        "gradient_hero": "linear-gradient(135deg, #f0f2f8 0%, #e0e7ff 40%, #ddd6fe 70%, #f0f2f8 100%)",
        "gradient_card": "linear-gradient(180deg, rgba(124,58,237,0.04) 0%, rgba(8,145,178,0.02) 100%)",
        "gradient_glow": "0 0 40px rgba(124,58,237,0.1), 0 0 80px rgba(8,145,178,0.05)",
        "shadow_3d": "0 25px 60px -12px rgba(0,0,0,0.08), 0 12px 28px -8px rgba(124,58,237,0.06), inset 0 1px 0 rgba(255,255,255,0.8)",
        "shadow_hover": "0 35px 80px -12px rgba(0,0,0,0.12), 0 18px 40px -8px rgba(8,145,178,0.08), inset 0 1px 0 rgba(255,255,255,0.9)",
        "glass_blur": "20px",
        "glass_bg": "rgba(255,255,255,0.75)",
        "glass_border": "1px solid rgba(0,0,0,0.05)",
        "neon_glow": "0 0 10px rgba(124,58,237,0.2), 0 0 30px rgba(124,58,237,0.1)",
        "neon_cyan": "0 0 10px rgba(8,145,178,0.2), 0 0 30px rgba(8,145,178,0.1)",
        "particle_color": "#7c3aed",
        "aurora_1": "rgba(124,58,237,0.08)",
        "aurora_2": "rgba(8,145,178,0.06)",
        "aurora_3": "rgba(5,150,105,0.04)",
    },
}


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES["🌑 Obsidian Dark"])


def inject_viewport() -> str:
    return """
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<style>html { -webkit-text-size-adjust: 100%; }</style>
"""


def inject_css(t: dict) -> str:
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&family=Orbitron:wght@400;500;600;700;800;900&display=swap');

/* =============================================
   GLOBAL RESET & BASE
   ============================================= */
.stApp {{
    background: {t['bg']} !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    overflow-x: hidden;
}}
.stApp > header {{ background: transparent !important; }}
.block-container {{ padding-top: 2rem !important; max-width: 1500px !important; }}

/* =============================================
   CUSTOM SCROLLBAR — Neon Style
   ============================================= */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{
    background: linear-gradient(180deg, {t['accent_purple']}, {t['accent_cyan']});
    border-radius: 10px;
    box-shadow: 0 0 6px {t['accent_purple']}66;
}}
::-webkit-scrollbar-thumb:hover {{ background: linear-gradient(180deg, {t['accent_cyan']}, {t['accent_purple']}); }}

/* =============================================
   PARTICLE BACKGROUND
   ============================================= */
.particle-bg {{
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}}
.particle {{
    position: absolute;
    width: 3px; height: 3px;
    background: {t['accent_purple']};
    border-radius: 50%;
    box-shadow: 0 0 6px {t['accent_purple']}, 0 0 12px {t['accent_purple']}44;
    animation: float-particle linear infinite;
    opacity: 0;
}}
@keyframes float-particle {{
    0% {{ transform: translateY(100vh) translateX(0) scale(0); opacity: 0; }}
    10% {{ opacity: 0.8; }}
    90% {{ opacity: 0.3; }}
    100% {{ transform: translateY(-10vh) translateX(100px) scale(1.5); opacity: 0; }}
}}

/* =============================================
   AURORA BACKGROUND
   ============================================= */
.aurora-bg {{
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    z-index: 0;
    overflow: hidden;
}}
.aurora-blob {{
    position: absolute;
    border-radius: 50%;
    filter: blur(80px);
    animation: aurora-drift 20s ease-in-out infinite alternate;
    opacity: 0.5;
}}
.aurora-blob:nth-child(1) {{
    width: 600px; height: 600px;
    background: {t['aurora_1']};
    top: -10%; left: -5%;
    animation-delay: 0s;
    animation-duration: 25s;
}}
.aurora-blob:nth-child(2) {{
    width: 500px; height: 500px;
    background: {t['aurora_2']};
    top: 40%; right: -10%;
    animation-delay: -5s;
    animation-duration: 20s;
}}
.aurora-blob:nth-child(3) {{
    width: 400px; height: 400px;
    background: {t['aurora_3']};
    bottom: -5%; left: 30%;
    animation-delay: -10s;
    animation-duration: 30s;
}}
@keyframes aurora-drift {{
    0% {{ transform: translate(0, 0) rotate(0deg) scale(1); }}
    33% {{ transform: translate(60px, -40px) rotate(120deg) scale(1.1); }}
    66% {{ transform: translate(-40px, 30px) rotate(240deg) scale(0.9); }}
    100% {{ transform: translate(20px, -20px) rotate(360deg) scale(1.05); }}
}}

/* =============================================
   GLASSMORPHISM CARD — Ultra Premium
   ============================================= */
.glass-card {{
    background: {t['glass_bg']};
    backdrop-filter: blur({t['glass_blur']}) saturate(180%);
    -webkit-backdrop-filter: blur({t['glass_blur']}) saturate(180%);
    border: {t['glass_border']};
    border-radius: 20px;
    padding: 28px;
    box-shadow: {t['shadow_3d']};
    transition: all 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    position: relative;
    overflow: hidden;
    transform-style: preserve-3d;
    perspective: 1000px;
}}
.glass-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: {t['gradient_primary']};
    opacity: 0.6;
    border-radius: 20px 20px 0 0;
}}
.glass-card::after {{
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at var(--mouse-x, 50%) var(--mouse-y, 50%), rgba(255,255,255,0.03) 0%, transparent 50%);
    pointer-events: none;
    transition: opacity 0.3s;
    opacity: 0;
}}
.glass-card:hover::after {{ opacity: 1; }}
.glass-card:hover {{
    box-shadow: {t['shadow_hover']};
    border-color: {t['card_hover_border']};
    transform: translateY(-6px) rotateX(2deg) rotateY(-1deg);
}}

/* =============================================
   3D STAT CARDS — Cinematic
   ============================================= */
.stat-card {{
    background: {t['card_bg']};
    background-image: {t['gradient_card']};
    border: 1px solid {t['card_border']};
    border-radius: 24px;
    padding: 32px 28px;
    box-shadow: {t['shadow_3d']};
    transition: all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    position: relative;
    overflow: hidden;
    perspective: 1200px;
    transform-style: preserve-3d;
    cursor: default;
}}
.stat-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: {t['gradient_primary']};
    opacity: 0;
    transition: opacity 0.4s ease;
}}
.stat-card::after {{
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 24px;
    background: {t['gradient_primary']};
    opacity: 0;
    transition: opacity 0.5s ease;
}}
.stat-card:hover {{
    transform: translateY(-10px) rotateX(4deg) rotateY(-2deg) scale(1.02);
    box-shadow: {t['shadow_hover']}, {t['neon_glow']};
    border-color: {t['card_hover_border']};
}}
.stat-card:hover::before {{ opacity: 1; }}
.stat-card:hover::after {{ opacity: 0.04; }}

.stat-value {{
    font-size: 3.2rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    background: {t['gradient_primary']};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.05;
    margin-bottom: 6px;
    font-family: 'Orbitron', 'Inter', sans-serif;
    text-shadow: none;
    position: relative;
    z-index: 2;
}}
.stat-label {{
    font-size: 0.82rem;
    font-weight: 600;
    color: {t['text_secondary']};
    text-transform: uppercase;
    letter-spacing: 0.12em;
    position: relative;
    z-index: 2;
}}
.stat-icon {{
    font-size: 2.8rem;
    position: absolute;
    top: 20px;
    right: 20px;
    opacity: 0.2;
    filter: drop-shadow(0 0 8px {t['accent_purple']}44);
    z-index: 2;
    transition: all 0.5s ease;
}}
.stat-card:hover .stat-icon {{
    opacity: 0.4;
    transform: scale(1.15) rotate(5deg);
}}
.stat-trend {{
    font-size: 0.78rem;
    font-weight: 700;
    margin-top: 10px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 12px;
    border-radius: 24px;
    position: relative;
    z-index: 2;
}}
.trend-up {{
    color: {t['accent_emerald']};
    background: {t['accent_emerald']}15;
    box-shadow: 0 0 12px {t['accent_emerald']}22;
}}
.trend-down {{
    color: {t['accent_rose']};
    background: {t['accent_rose']}15;
    box-shadow: 0 0 12px {t['accent_rose']}22;
}}

/* =============================================
   RING GAUGE — Animated
   ============================================= */
.ring-gauge {{
    position: relative;
    width: 120px;
    height: 120px;
}}
.ring-gauge svg {{
    transform: rotate(-90deg);
    filter: drop-shadow(0 0 8px {t['accent_purple']}44);
}}
.ring-gauge circle {{
    fill: none;
    stroke-width: 8;
    stroke-linecap: round;
    transition: stroke-dashoffset 1.5s cubic-bezier(0.4, 0, 0.2, 1);
}}
.ring-bg {{ stroke: {t['card_border']}; }}
.ring-fill {{
    stroke: url(#ring-gradient);
    stroke-dasharray: 283;
    animation: ring-fill 2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}}
@keyframes ring-fill {{
    from {{ stroke-dashoffset: 283; }}
}}
.ring-label {{
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}}

/* =============================================
   PIPELINE / KANBAN — Animated Columns
   ============================================= */
.pipeline-col {{
    background: {t['glass_bg']};
    backdrop-filter: blur(16px) saturate(150%);
    border: {t['glass_border']};
    border-radius: 18px;
    padding: 18px;
    min-height: 420px;
    box-shadow: {t['shadow_3d']};
    transition: all 0.4s ease;
    position: relative;
    overflow: hidden;
}}
.pipeline-col::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: {t['gradient_primary']};
    opacity: 0.4;
    border-radius: 18px 18px 0 0;
}}
.pipeline-col:hover {{
    border-color: {t['card_hover_border']};
    box-shadow: {t['shadow_hover']};
    transform: translateY(-4px);
}}
.pipeline-col-header {{
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: {t['text_secondary']};
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}}
.pipeline-count {{
    background: {t['gradient_primary']};
    color: white;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-family: 'Orbitron', monospace;
    font-weight: 700;
    box-shadow: 0 2px 8px {t['accent_purple']}44;
}}

/* =============================================
   FEATURE CARDS — 3D Depth
   ============================================= */
.feature-card {{
    background: {t['card_bg']};
    border: 1px solid {t['card_border']};
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 12px;
    transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    cursor: pointer;
    position: relative;
    overflow: hidden;
    transform-style: preserve-3d;
}}
.feature-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 4px; height: 0;
    background: {t['gradient_primary']};
    border-radius: 0 4px 4px 0;
    transition: height 0.4s ease;
}}
.feature-card:hover {{
    border-color: {t['card_hover_border']};
    transform: translateX(6px) translateZ(8px);
    box-shadow: 0 8px 24px rgba(168,85,247,0.12), 0 0 0 1px {t['card_hover_border']};
}}
.feature-card:hover::before {{ height: 100%; }}
.feature-title {{
    font-size: 0.9rem;
    font-weight: 600;
    color: {t['text_primary']};
    margin-bottom: 10px;
    line-height: 1.4;
}}

/* =============================================
   PRIORITY BADGES — Neon
   ============================================= */
.priority-badge {{
    display: inline-block;
    padding: 3px 10px;
    border-radius: 8px;
    font-size: 0.68rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    transition: all 0.3s ease;
}}
.priority-p0 {{
    background: {t['accent_rose']}18;
    color: {t['accent_rose']};
    box-shadow: 0 0 12px {t['accent_rose']}22;
    animation: pulse-badge-p0 2s ease-in-out infinite;
}}
@keyframes pulse-badge-p0 {{
    0%, 100% {{ box-shadow: 0 0 8px {t['accent_rose']}22; }}
    50% {{ box-shadow: 0 0 16px {t['accent_rose']}44; }}
}}
.priority-p1 {{
    background: {t['accent_amber']}18;
    color: {t['accent_amber']};
    box-shadow: 0 0 10px {t['accent_amber']}18;
}}
.priority-p2 {{
    background: {t['accent_cyan']}18;
    color: {t['accent_cyan']};
}}
.priority-p3 {{
    background: {t['accent_emerald']}18;
    color: {t['accent_emerald']};
}}

/* =============================================
   ACTIVITY FEED — Animated
   ============================================= */
.activity-item {{
    display: flex;
    gap: 14px;
    padding: 14px 0;
    border-bottom: 1px solid {t['card_border']};
    transition: all 0.3s ease;
    position: relative;
}}
.activity-item:hover {{
    background: linear-gradient(90deg, {t['accent_purple']}08, transparent);
    padding-left: 8px;
}}
.activity-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-top: 6px;
    flex-shrink: 0;
    box-shadow: 0 0 8px currentColor, 0 0 16px currentColor;
    animation: dot-glow 2s ease-in-out infinite;
}}
@keyframes dot-glow {{
    0%, 100% {{ box-shadow: 0 0 6px currentColor; transform: scale(1); }}
    50% {{ box-shadow: 0 0 12px currentColor, 0 0 24px currentColor; transform: scale(1.2); }}
}}
.activity-text {{
    font-size: 0.88rem;
    color: {t['text_primary']};
    line-height: 1.6;
}}
.activity-time {{
    font-size: 0.72rem;
    color: {t['text_muted']};
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.02em;
}}

/* =============================================
   HERO HEADER — Cinematic
   ============================================= */
.hero-header {{
    background: {t['gradient_hero']};
    backdrop-filter: blur(40px) saturate(200%);
    border: {t['glass_border']};
    border-radius: 24px;
    padding: 40px 44px;
    margin-bottom: 32px;
    box-shadow: {t['shadow_3d']}, {t['gradient_glow']};
    position: relative;
    overflow: hidden;
    transform-style: preserve-3d;
}}
.hero-header::before {{
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background:
        radial-gradient(ellipse at 20% 50%, {t['aurora_1']} 0%, transparent 50%),
        radial-gradient(ellipse at 80% 50%, {t['aurora_2']} 0%, transparent 50%),
        radial-gradient(ellipse at 50% 80%, {t['aurora_3']} 0%, transparent 50%);
    animation: hero-aurora 20s ease infinite alternate;
}}
@keyframes hero-aurora {{
    0% {{ transform: translate(0, 0) rotate(0deg) scale(1); }}
    25% {{ transform: translate(-5%, 5%) rotate(5deg) scale(1.05); }}
    50% {{ transform: translate(5%, -3%) rotate(-3deg) scale(0.95); }}
    75% {{ transform: translate(-3%, -5%) rotate(2deg) scale(1.02); }}
    100% {{ transform: translate(3%, 3%) rotate(-2deg) scale(1); }}
}}
.hero-header::after {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: {t['gradient_primary']};
    opacity: 0.8;
}}
.hero-title {{
    font-size: 2.4rem;
    font-weight: 900;
    letter-spacing: -0.04em;
    background: {t['gradient_primary']};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    position: relative;
    z-index: 2;
    font-family: 'Orbitron', 'Inter', sans-serif;
    text-shadow: none;
    line-height: 1.1;
}}
.hero-subtitle {{
    color: {t['text_secondary']};
    font-size: 1rem;
    margin-top: 10px;
    position: relative;
    z-index: 2;
    line-height: 1.6;
    max-width: 700px;
}}
.hero-badge {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 16px;
    border-radius: 24px;
    background: {t['accent_purple']}15;
    color: {t['accent_purple']};
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    border: 1px solid {t['accent_purple']}33;
    margin-bottom: 16px;
    position: relative;
    z-index: 2;
    box-shadow: 0 0 20px {t['accent_purple']}22;
}}

/* =============================================
   BUTTONS — Neon Glow
   ============================================= */
.btn-primary {{
    background: {t['gradient_primary']} !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 14px 32px !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    box-shadow: 0 8px 30px rgba(168,85,247,0.3), 0 0 20px rgba(168,85,247,0.15);
    transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
    cursor: pointer !important;
    position: relative;
    overflow: hidden;
    letter-spacing: 0.03em;
}}
.btn-primary::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.2), transparent);
    opacity: 0;
    transition: opacity 0.3s;
}}
.btn-primary:hover {{
    box-shadow: 0 12px 40px rgba(168,85,247,0.4), 0 0 30px rgba(6,214,246,0.2) !important;
    transform: translateY(-3px) scale(1.02) !important;
}}
.btn-primary:hover::before {{ opacity: 1; }}

/* =============================================
   SECTION HEADER — Accent Line
   ============================================= */
.section-header {{
    font-size: 1.2rem;
    font-weight: 800;
    color: {t['text_primary']};
    margin-bottom: 22px;
    display: flex;
    align-items: center;
    gap: 12px;
    letter-spacing: -0.01em;
}}
.section-header-accent {{
    width: 5px;
    height: 24px;
    background: {t['gradient_primary']};
    border-radius: 6px;
    box-shadow: 0 0 10px {t['accent_purple']}44;
}}

/* =============================================
   TABLE STYLES — Premium
   ============================================= */
.dataframe {{
    border: none !important;
    border-radius: 14px !important;
    overflow: hidden !important;
    box-shadow: {t['shadow_3d']} !important;
}}
.dataframe th {{
    background: linear-gradient(135deg, {t['accent_purple']}12, {t['accent_cyan']}08) !important;
    color: {t['text_secondary']} !important;
    font-weight: 700 !important;
    font-size: 0.75rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    padding: 14px 18px !important;
    border: none !important;
    border-bottom: 2px solid {t['card_border']} !important;
}}
.dataframe td {{
    padding: 14px 18px !important;
    border-bottom: 1px solid {t['card_border']} !important;
    font-size: 0.88rem !important;
    color: {t['text_primary']} !important;
    transition: background 0.2s ease !important;
}}
.dataframe tr:hover td {{
    background: {t['accent_purple']}06 !important;
}}

/* =============================================
   METRICS OVERRIDE
   ============================================= */
[data-testid="stMetric"] {{
    background: {t['card_bg']};
    border: 1px solid {t['card_border']};
    border-radius: 18px;
    padding: 24px !important;
    box-shadow: {t['shadow_3d']};
    transition: all 0.4s ease;
}}
[data-testid="stMetric"]:hover {{
    transform: translateY(-4px);
    box-shadow: {t['shadow_hover']}, {t['neon_glow']};
}}
[data-testid="stMetricValue"] {{
    font-weight: 900 !important;
    font-size: 2.2rem !important;
    font-family: 'Orbitron', 'Inter', sans-serif !important;
    background: {t['gradient_primary']};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}

/* =============================================
   TABS — Neon Underline
   ============================================= */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    background: {t['card_bg']};
    border-radius: 14px;
    padding: 5px;
    border: 1px solid {t['card_border']};
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
}}
.stTabs [data-baseweb="tab"] {{
    border-radius: 12px;
    padding: 10px 24px;
    font-weight: 600;
    color: {t['text_secondary']};
    transition: all 0.3s ease;
    font-size: 0.88rem;
}}
.stTabs [aria-selected="true"] {{
    background: {t['gradient_primary']} !important;
    color: white !important;
    box-shadow: 0 4px 15px {t['accent_purple']}44;
}}

/* =============================================
   SIDEBAR — Glassmorphism
   ============================================= */
[data-testid="stSidebar"] {{
    background: {t['bg_secondary']} !important;
    border-right: 1px solid {t['card_border']} !important;
    box-shadow: 4px 0 20px rgba(0,0,0,0.2);
}}
[data-testid="stSidebar"] .block-container {{
    padding-top: 1rem !important;
}}

/* =============================================
   ANIMATIONS — Premium Collection
   ============================================= */
@keyframes pulse3d {{
    0%, 100% {{ transform: scale(1); box-shadow: {t['shadow_3d']}; }}
    50% {{ transform: scale(1.02); box-shadow: {t['shadow_hover']}, {t['neon_glow']}; }}
}}
.pulse-3d {{ animation: pulse3d 3s ease-in-out infinite; }}

@keyframes glow-pulse {{
    0%, 100% {{ opacity: 1; box-shadow: 0 0 6px currentColor; }}
    50% {{ opacity: 0.5; box-shadow: 0 0 12px currentColor, 0 0 24px currentColor; }}
}}
.glow-dot {{
    animation: glow-pulse 2s ease-in-out infinite;
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
}}

@keyframes slide-in-up {{
    from {{ opacity: 0; transform: translateY(30px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
.animate-in {{
    animation: slide-in-up 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
    opacity: 0;
}}
.animate-in:nth-child(1) {{ animation-delay: 0.05s; }}
.animate-in:nth-child(2) {{ animation-delay: 0.1s; }}
.animate-in:nth-child(3) {{ animation-delay: 0.15s; }}
.animate-in:nth-child(4) {{ animation-delay: 0.2s; }}

@keyframes shimmer {{
    0% {{ background-position: -200% 0; }}
    100% {{ background-position: 200% 0; }}
}}
.shimmer {{
    background: linear-gradient(90deg, transparent 0%, {t['accent_purple']}08 50%, transparent 100%);
    background-size: 200% 100%;
    animation: shimmer 3s ease-in-out infinite;
}}

@keyframes border-glow {{
    0%, 100% {{ border-color: {t['card_border']}; }}
    50% {{ border-color: {t['accent_purple']}44; }}
}}
.border-glow {{ animation: border-glow 3s ease-in-out infinite; }}

@keyframes counter-spin {{
    from {{ transform: rotate(0deg); }}
    to {{ transform: rotate(360deg); }}
}}

/* =============================================
   CHARTS — Premium Plotly Overrides
   ============================================= */
.js-plotly-plot .plotly .modebar {{ display: none !important; }}

/* =============================================
   HIDE DEFAULTS
   ============================================= */
#MainMenu {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

/* =============================================
   RESPONSIVE DESIGN
   ============================================= */
@media (max-width: 480px) {{
    .block-container {{ padding: 0.5rem !important; max-width: 100% !important; }}
    .hero-header {{ padding: 24px 18px; border-radius: 18px; margin-bottom: 20px; }}
    .hero-title {{ font-size: 1.4rem; }}
    .hero-subtitle {{ font-size: 0.8rem; }}
    .stat-card {{ padding: 20px 16px; border-radius: 18px; margin-bottom: 12px; }}
    .stat-value {{ font-size: 2rem; }}
    .stat-label {{ font-size: 0.7rem; }}
    .stat-icon {{ font-size: 1.8rem; }}
    .glass-card {{ padding: 18px; border-radius: 16px; }}
    .section-header {{ font-size: 1rem; margin-bottom: 16px; }}
    .pipeline-col {{ padding: 14px; border-radius: 14px; min-height: 250px; margin-bottom: 12px; }}
    .pipeline-col-header {{ font-size: 0.7rem; }}
    .feature-card {{ padding: 14px; border-radius: 12px; }}
    .feature-title {{ font-size: 0.82rem; }}
    .activity-item {{ gap: 10px; padding: 12px 0; }}
    .activity-text {{ font-size: 0.8rem; }}
    .dataframe th {{ font-size: 0.65rem !important; padding: 10px 12px !important; }}
    .dataframe td {{ font-size: 0.75rem !important; padding: 10px 12px !important; }}
    .stTabs [data-baseweb="tab"] {{ padding: 8px 14px; font-size: 0.8rem; }}
    [data-testid="stMetric"] {{ padding: 16px !important; }}
    [data-testid="stMetricValue"] {{ font-size: 1.6rem !important; }}
    [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; gap: 10px !important; }}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ flex: 1 1 100% !important; min-width: 100% !important; }}
    .btn-primary {{ padding: 12px 22px !important; font-size: 0.82rem !important; }}
    .aurora-blob {{ filter: blur(60px); opacity: 0.3; }}
}}

@media (max-width: 360px) {{
    .hero-title {{ font-size: 1.2rem; }}
    .stat-value {{ font-size: 1.7rem; }}
    .stat-label {{ font-size: 0.62rem; }}
    .section-header {{ font-size: 0.88rem; }}
}}

@media (min-width: 481px) and (max-width: 768px) {{
    .block-container {{ padding: 1rem !important; max-width: 100% !important; }}
    .hero-header {{ padding: 28px 24px; border-radius: 20px; }}
    .hero-title {{ font-size: 1.8rem; }}
    .stat-card {{ padding: 24px 20px; }}
    .stat-value {{ font-size: 2.4rem; }}
    .glass-card {{ padding: 20px; }}
    .pipeline-col {{ min-height: 300px; }}
    [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap !important; gap: 10px !important; }}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{ flex: 1 1 calc(50% - 10px) !important; min-width: calc(50% - 10px) !important; }}
}}

@media (min-width: 769px) and (max-width: 1024px) {{
    .block-container {{ padding: 1.5rem !important; max-width: 100% !important; }}
    .hero-title {{ font-size: 2rem; }}
    .stat-value {{ font-size: 2.6rem; }}
    .pipeline-col {{ min-height: 350px; }}
}}

@media (min-width: 1400px) {{
    .block-container {{ max-width: 1700px !important; }}
    .hero-title {{ font-size: 2.8rem; }}
    .stat-value {{ font-size: 3.6rem; }}
    .stat-card {{ padding: 36px 32px; }}
}}

@media (hover: none) and (pointer: coarse) {{
    .stat-card:hover, .glass-card:hover, .feature-card:hover {{ transform: none !important; }}
    .feature-card {{ padding: 16px; min-height: 44px; }}
    .btn-primary {{ min-height: 48px !important; padding: 14px 28px !important; }}
    *:focus {{ outline: none !important; }}
}}

@media print {{
    .hero-header::before, .aurora-bg, .particle-bg {{ display: none !important; }}
    .stat-card {{ box-shadow: none; border: 1px solid #ddd; }}
    .glass-card {{ backdrop-filter: none; background: white; }}
    [data-testid="stSidebar"] {{ display: none !important; }}
}}
</style>
"""
