"""
🚀 Plotcode AI Delivery Automation Dashboard — GOD-LEVEL UI
Particle systems, aurora backgrounds, 3D transforms, animated counters,
cinematic charts, and premium glassmorphism throughout.
"""

import streamlit as st
import sys
import os
import random
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from components.themes import THEMES, get_theme, inject_css
from components.data import generate_requests, generate_activity_feed, generate_daily_throughput

st.set_page_config(
    page_title="Plotcode — AI Delivery Automation",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; margin-bottom: 28px; padding: 20px 0;">
        <div style="font-size: 3rem; margin-bottom: 8px; filter: drop-shadow(0 0 20px rgba(168,85,247,0.4));">🚀</div>
        <div style="font-size: 1.5rem; font-weight: 900; letter-spacing: -0.03em; background: linear-gradient(135deg, #a855f7, #06d6f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-family: 'Orbitron', sans-serif;">Plotcode</div>
        <div style="font-size: 0.68rem; color: #556677; letter-spacing: 0.15em; text-transform: uppercase; margin-top: 4px;">AI Delivery Engine v2.0</div>
    </div>
    """, unsafe_allow_html=True)

    theme_choice = st.selectbox("🎨 Theme", list(THEMES.keys()), index=0, key="theme_select")
    t = get_theme(theme_choice)

    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.12em; color: #556677; margin-bottom: 14px;">Navigation</div>
    """, unsafe_allow_html=True)
    st.page_link("app.py", label="📊  Dashboard", icon=None)
    st.page_link("pages/1_📋_Pipeline.py", label="📋  Pipeline Board")
    st.page_link("pages/2_🤖_AI_Agents.py", label="🤖  AI Agents")
    st.page_link("pages/3_🔐_RBAC.py", label="🔐  RBAC & Users")
    st.page_link("pages/4_📝_Submit_Request.py", label="📝  Submit Request")
    st.page_link("pages/5_📈_Analytics.py", label="📈  Analytics")

    st.markdown("---")
    st.markdown(f"""
    <div style="font-size:0.68rem; color:#3d4f6f; text-align:center; margin-top:24px; line-height:1.8;">
        <span style="font-family:'Orbitron',monospace; font-weight:700;">v2.0.0</span><br/>
        14-Stage Workflow · 5 HITL Gates<br/>
        <span style="color:{t['accent_purple']};">●</span> System Online
    </div>
    """, unsafe_allow_html=True)

# ── Inject CSS ───────────────────────────────────────────────────
st.markdown(inject_css(t), unsafe_allow_html=True)
st.session_state['current_theme'] = t
st.session_state['theme_name'] = theme_choice

# ── Particle Background ─────────────────────────────────────────
particle_html = '<div class="particle-bg">'
for i in range(25):
    x = random.randint(0, 100)
    delay = random.uniform(0, 15)
    dur = random.uniform(10, 20)
    size = random.uniform(2, 5)
    opacity = random.uniform(0.3, 0.7)
    particle_html += f'''<div class="particle" style="left:{x}%; animation-delay:{delay}s; animation-duration:{dur}s; width:{size}px; height:{size}px; opacity:{opacity};"></div>'''
particle_html += '</div>'
st.markdown(particle_html, unsafe_allow_html=True)

# ── Aurora Background ────────────────────────────────────────────
st.markdown('''<div class="aurora-bg"><div class="aurora-blob"></div><div class="aurora-blob"></div><div class="aurora-blob"></div></div>''', unsafe_allow_html=True)

# ── Cache Data ───────────────────────────────────────────────────
if 'requests_df' not in st.session_state:
    st.session_state['requests_df'] = generate_requests(80)
df = st.session_state['requests_df']

# ── Hero Header — Cinematic ─────────────────────────────────────
st.markdown(f"""
<div class="hero-header animate-in">
    <div class="hero-badge">⚡ LIVE — Real-time Pipeline Monitoring</div>
    <div class="hero-title">AI Delivery Automation</div>
    <div class="hero-subtitle">
        End-to-end autonomous pipeline: Slack request → AI analysis → Code generation →
        CI/CD → Production deployment — with human-in-the-loop checkpoints at every critical stage.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Stat Cards Row — Animated Counters ──────────────────────────
total = len(df)
pending = len(df[df['status'].isin(['submitted', 'pending_review'])])
ai_active = len(df[df['status'].isin(['planning', 'plan_pending_approval', 'coding', 'ci_running'])])
deployed = len(df[df['status'].isin(['deployed', 'closed'])])
failed = len(df[df['status'].isin(['ci_failed', 'qa_failed'])])
success_rate = round((deployed / max(total, 1)) * 100, 1)

stats = [
    {"value": total, "label": "Total Features", "icon": "📊", "trend": "+12%", "dir": "up", "color": "purple"},
    {"value": pending, "label": "Pending Approval", "icon": "⏳", "trend": "-8%", "dir": "down", "color": "amber"},
    {"value": ai_active, "label": "AI In Development", "icon": "🤖", "trend": "+23%", "dir": "up", "color": "cyan"},
    {"value": deployed, "label": "Deployed to Prod", "icon": "🚀", "trend": "+15%", "dir": "up", "color": "emerald"},
]

cols = st.columns(4, gap="medium")
for col, s in zip(cols, stats):
    with col:
        trend_class = "trend-up" if s["dir"] == "up" else "trend-down"
        trend_icon = "↑" if s["dir"] == "up" else "↓"
        st.markdown(f"""
        <div class="stat-card animate-in">
            <div class="stat-icon">{s['icon']}</div>
            <div class="stat-value">{s['value']}</div>
            <div class="stat-label">{s['label']}</div>
            <div class="stat-trend {trend_class}">{trend_icon} {s['trend']} vs last week</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)

# ── Performance Ring Gauges ──────────────────────────────────────
ring_cols = st.columns(3, gap="large")
ring_data = [
    {"label": "Success Rate", "value": success_rate, "max": 100, "color": t['accent_emerald']},
    {"label": "Avg Cycle Time", "value": 72, "max": 100, "color": t['accent_cyan']},
    {"label": "SLA Compliance", "value": 94, "max": 100, "color": t['accent_purple']},
]

for col, rd in zip(ring_cols, ring_data):
    with col:
        circumference = 2 * math.pi * 45
        offset = circumference - (rd["value"] / rd["max"]) * circumference
        st.markdown(f"""
        <div class="glass-card animate-in" style="text-align:center; padding:28px 20px;">
            <div class="ring-gauge" style="margin: 0 auto 16px;">
                <svg width="120" height="120" viewBox="0 0 120 120">
                    <defs>
                        <linearGradient id="ring-gradient-{rd['label']}" x1="0%" y1="0%" x2="100%" y2="100%">
                            <stop offset="0%" style="stop-color:{t['accent_purple']}"/>
                            <stop offset="100%" style="stop-color:{rd['color']}"/>
                        </linearGradient>
                    </defs>
                    <circle class="ring-bg" cx="60" cy="60" r="45"/>
                    <circle class="ring-fill" cx="60" cy="60" r="45"
                        stroke="url(#ring-gradient-{rd['label']})"
                        stroke-dasharray="{circumference}"
                        stroke-dashoffset="{offset}"/>
                </svg>
                <div class="ring-label">
                    <div style="font-size:1.4rem; font-weight:900; font-family:'Orbitron',sans-serif; background:{t['gradient_primary']}; -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{rd['value']}%</div>
                </div>
            </div>
            <div style="font-size:0.82rem; font-weight:700; color:{t['text_secondary']}; text-transform:uppercase; letter-spacing:0.08em;">{rd['label']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)

# ── Main Content: Chart + Activity Feed ──────────────────────────
chart_col, feed_col = st.columns([2.5, 1], gap="large")

with chart_col:
    st.markdown(f"""
    <div class="section-header animate-in">
        <div class="section-header-accent"></div>
        Delivery Throughput — Last 30 Days
    </div>
    """, unsafe_allow_html=True)

    import plotly.graph_objects as go

    throughput = generate_daily_throughput(30)
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=throughput['date'], y=throughput['deployed'],
        name='Deployed', fill='tozeroy',
        line=dict(color=t['accent_emerald'], width=3, shape='spline'),
        fillcolor=f"rgba(0,232,157,0.08)",
        hovertemplate='<b>Deployed</b>: %{y}<extra></extra>',
    ))
    fig.add_trace(go.Scatter(
        x=throughput['date'], y=throughput['submitted'],
        name='Submitted', fill='tozeroy',
        line=dict(color=t['accent_purple'], width=3, shape='spline'),
        fillcolor=f"rgba(168,85,247,0.06)",
        hovertemplate='<b>Submitted</b>: %{y}<extra></extra>',
    ))
    fig.add_trace(go.Bar(
        x=throughput['date'], y=throughput['failed'],
        name='Failed',
        marker_color=t['accent_rose'],
        marker_opacity=0.6,
        hovertemplate='<b>Failed</b>: %{y}<extra></extra>',
    ))

    fig.update_layout(
        height=420,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color=t['text_secondary'], size=12),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02,
            xanchor='right', x=1,
            font=dict(size=11, color=t['text_secondary']),
            bgcolor='rgba(0,0,0,0)',
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color=t['text_muted']), linecolor=t['card_border']),
        yaxis=dict(gridcolor=t['card_border'], gridwidth=0.5, tickfont=dict(size=10, color=t['text_muted']), linecolor=t['card_border']),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor=t['bg_secondary'],
            bordercolor=t['card_border'],
            font=dict(family='Inter', size=12, color=t['text_primary']),
        ),
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with feed_col:
    st.markdown(f"""
    <div class="section-header animate-in">
        <div class="section-header-accent"></div>
        Recent Activity
    </div>
    """, unsafe_allow_html=True)

    feed = generate_activity_feed(15)
    feed_html = ""
    for i, item in enumerate(feed[:15]):
        minutes = item['minutes_ago']
        if minutes < 60:
            time_str = f"{minutes}m ago"
        elif minutes < 1440:
            time_str = f"{minutes // 60}h ago"
        else:
            time_str = f"{minutes // 1440}d ago"

        color = t[item['color_key']]
        feed_html += f"""
        <div class="activity-item" style="animation-delay: {i * 0.05}s;">
            <div class="activity-dot" style="background:{color}; color:{color};"></div>
            <div>
                <div class="activity-text">{item['icon']} {item['text']}</div>
                <div class="activity-time">{time_str}</div>
            </div>
        </div>
        """

    st.markdown(f"""
    <div class="glass-card" style="max-height:520px; overflow-y:auto; padding:18px;">
        {feed_html}
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)

# ── Pipeline Overview — Animated Kanban ──────────────────────────
st.markdown(f"""
<div class="section-header animate-in">
    <div class="section-header-accent"></div>
    Pipeline Overview
</div>
""", unsafe_allow_html=True)

stages = ['Submitted', 'Pending Review', 'AI Planning', 'In Development', 'QA / Staging', 'Production', 'Deployed ✅']
stage_cols = st.columns(len(stages), gap="small")

for col, stage in zip(stage_cols, stages):
    with col:
        stage_df = df[df['pipeline_stage'] == stage]
        count = len(stage_df)
        cards_html = ""
        for _, row in stage_df.head(3).iterrows():
            p_class = f"priority-{row['priority'].lower()}"
            cards_html += f"""
            <div class="feature-card">
                <div class="feature-title">{row['title'][:30]}{'...' if len(row['title']) > 30 else ''}</div>
                <span class="priority-badge {p_class}">{row['priority']}</span>
                <div style="font-size:0.72rem; color:{t['text_muted']}; margin-top:8px;">{row['requester_name']}</div>
            </div>
            """
        if count > 3:
            cards_html += f"""<div style="text-align:center; font-size:0.72rem; color:{t['accent_purple']}; padding:10px; font-weight:700;">+{count - 3} more</div>"""

        st.markdown(f"""
        <div class="pipeline-col animate-in">
            <div class="pipeline-col-header">
                {stage.split(' ')[0]}
                <span class="pipeline-count">{count}</span>
            </div>
            {cards_html}
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height: 44px'></div>", unsafe_allow_html=True)

# ── Footer ───────────────────────────────────────────────────────
st.markdown(f"""
<div style="text-align:center; padding:28px 0; font-size:0.72rem; color:{t['text_muted']}; line-height:2;">
    <span style="font-family:'Orbitron',sans-serif; font-weight:700; background:{t['gradient_primary']}; -webkit-background-clip:text; -webkit-text-fill-color:transparent;">Plotcode AI Delivery Platform</span><br/>
    14-Stage Workflow · 5 Human-in-the-Loop Gates<br/>
    Built with 💜 by Plotcode Engineering
</div>
""", unsafe_allow_html=True)
