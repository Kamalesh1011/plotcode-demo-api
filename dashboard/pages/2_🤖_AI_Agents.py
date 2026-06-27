"""
🤖 AI Agents — GOD-LEVEL Performance Monitoring
3D agent cards with animated metrics, radar charts, neon gauges, and live workflow visualization.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os, random, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.themes import get_theme, inject_css, inject_viewport
from components.data import generate_agent_metrics

st.set_page_config(page_title="AI Agents — Plotcode", page_icon="🤖", layout="wide")
st.markdown(inject_viewport(), unsafe_allow_html=True)

theme_name = st.session_state.get('theme_name', '🌑 Obsidian Dark')
t = get_theme(theme_name)
st.markdown(inject_css(t), unsafe_allow_html=True)

# Particles
particle_html = '<div class="particle-bg">'
for i in range(12):
    x = random.randint(0, 100)
    delay = random.uniform(0, 10)
    dur = random.uniform(8, 16)
    particle_html += f'<div class="particle" style="left:{x}%; animation-delay:{delay}s; animation-duration:{dur}s;"></div>'
particle_html += '</div>'
st.markdown(particle_html, unsafe_allow_html=True)
st.markdown('<div class="aurora-bg"><div class="aurora-blob"></div><div class="aurora-blob"></div></div>', unsafe_allow_html=True)

# ── Hero Header ──────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-header animate-in">
    <div class="hero-badge">🤖 AI INTELLIGENCE — Real-time Agent Monitoring</div>
    <div class="hero-title">AI Agent Performance</div>
    <div class="hero-subtitle">Monitor all 7 AI agents across the delivery pipeline — invocations, latency, success rates, token usage, and self-healing metrics.</div>
</div>
""", unsafe_allow_html=True)

# ── Agent Metrics ────────────────────────────────────────────────
metrics = generate_agent_metrics()
metrics_df = pd.DataFrame(metrics)

# ── Stat Cards — Orbitron Numbers ────────────────────────────────
total_invocations = metrics_df['invocations'].sum()
avg_success = metrics_df['success_rate'].mean()
total_tokens = metrics_df['tokens_used'].sum()
avg_latency = metrics_df['avg_latency_s'].mean()

c1, c2, c3, c4 = st.columns(4)
for col, val, label, icon in [
    (c1, f"{total_invocations:,}", "Total Invocations", "⚡"),
    (c2, f"{avg_success:.1f}%", "Avg Success Rate", "✅"),
    (c3, f"{total_tokens // 1000}K", "Tokens Used", "🔤"),
    (c4, f"{avg_latency:.1f}s", "Avg Latency", "⏱️"),
]:
    with col:
        st.markdown(f"""
        <div class="stat-card animate-in">
            <div class="stat-icon">{icon}</div>
            <div class="stat-value">{val}</div>
            <div class="stat-label">{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# ── 3D Agent Cards Grid ──────────────────────────────────────────
st.markdown(f"""
<div class="section-header animate-in"><div class="section-header-accent"></div>Agent Overview</div>
""", unsafe_allow_html=True)

agent_icons = {
    'Intake': '📥', 'Analysis': '🔍', 'Coder': '💻',
    'Validation': '✅', 'PR Agent': '📄', 'Deploy': '🚀', 'Monitor': '📊'
}
agent_colors = [t['accent_purple'], t['accent_cyan'], t['accent_emerald'], t['accent_amber'], t['accent_rose'], t['accent_blue'], t['accent_purple']]

agent_cards_html = '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:16px; margin-bottom:32px;">'
for i, (_, row) in enumerate(metrics_df.iterrows()):
    agent_name = row['agent']
    icon = agent_icons.get(agent_name, '🤖')
    color = agent_colors[i % len(agent_colors)]
    success = row['success_rate']
    invocations = row['invocations']

    circumference = 2 * math.pi * 30
    offset = circumference - (success / 100) * circumference

    agent_cards_html += f'''
    <div class="glass-card animate-in" style="text-align:center; padding:24px 16px; border-radius:18px; animation-delay:{i*0.08}s;">
        <div style="font-size:2.4rem; margin-bottom:8px; filter:drop-shadow(0 0 12px {color}44);">{icon}</div>
        <div style="font-size:0.9rem; font-weight:800; color:{t['text_primary']}; margin-bottom:12px;">{agent_name}</div>
        <svg width="70" height="70" viewBox="0 0 70 70" style="margin-bottom:8px;">
            <defs>
                <linearGradient id="ag-{agent_name}" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:{t['accent_purple']}"/>
                    <stop offset="100%" style="stop-color:{color}"/>
                </linearGradient>
            </defs>
            <circle cx="35" cy="35" r="30" fill="none" stroke="{t['card_border']}" stroke-width="5"/>
            <circle cx="35" cy="35" r="30" fill="none" stroke="url(#ag-{agent_name})" stroke-width="5"
                stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                stroke-linecap="round" style="transform:rotate(-90deg); transform-origin:center; transition:stroke-dashoffset 1.5s ease;"/>
        </svg>
        <div style="font-size:1.1rem; font-weight:900; font-family:'Orbitron',sans-serif; background:{t['gradient_primary']}; -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{success}%</div>
        <div style="font-size:0.68rem; color:{t['text_muted']}; margin-top:4px;">{invocations} calls</div>
    </div>
    '''
agent_cards_html += '</div>'
st.markdown(agent_cards_html, unsafe_allow_html=True)

# ── Charts Row — Premium ─────────────────────────────────────────
chart1, chart2 = st.columns(2, gap="large")

with chart1:
    st.markdown(f"""
    <div class="section-header animate-in"><div class="section-header-accent"></div>Agent Invocations</div>
    """, unsafe_allow_html=True)

    fig = go.Figure(go.Bar(
        x=metrics_df['invocations'],
        y=metrics_df['agent'],
        orientation='h',
        marker=dict(
            color=metrics_df['invocations'],
            colorscale=[[0, t['accent_purple']], [0.5, t['accent_cyan']], [1, t['accent_emerald']]],
            cornerradius=8,
        ),
        text=metrics_df['invocations'],
        textposition='outside',
        textfont=dict(color=t['text_primary'], size=13, family='JetBrains Mono'),
    ))
    fig.update_layout(
        height=380,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color=t['text_secondary']),
        margin=dict(l=0, r=70, t=10, b=0),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=False, tickfont=dict(size=13, color=t['text_primary'])),
        hoverlabel=dict(bgcolor=t['bg_secondary'], bordercolor=t['card_border'], font=dict(color=t['text_primary'])),
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with chart2:
    st.markdown(f"""
    <div class="section-header animate-in"><div class="section-header-accent"></div>Success Rate Radar</div>
    """, unsafe_allow_html=True)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatterpolar(
        r=metrics_df['success_rate'],
        theta=metrics_df['agent'],
        fill='toself',
        fillcolor=f"{t['accent_cyan']}18",
        line=dict(color=t['accent_cyan'], width=2.5),
        marker=dict(size=10, color=t['accent_purple'], line=dict(color='white', width=2)),
        name='Success Rate',
    ))
    fig2.update_layout(
        height=380,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color=t['text_secondary'], size=11),
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(range=[85, 100], showticklabels=True, gridcolor=t['card_border'], tickfont=dict(size=9, color=t['text_muted'])),
            angularaxis=dict(gridcolor=t['card_border'], tickfont=dict(size=11, color=t['text_primary'])),
        ),
        margin=dict(l=50, r=50, t=20, b=20),
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# ── Latency Timeline ─────────────────────────────────────────────
st.markdown(f"""
<div class="section-header animate-in"><div class="section-header-accent"></div>Latency Distribution</div>
""", unsafe_allow_html=True)

fig3 = go.Figure()
for i, agent in enumerate(metrics_df['agent']):
    fig3.add_trace(go.Box(
        y=[metrics_df.iloc[i]['avg_latency_s'] * random.uniform(0.7, 1.3) for _ in range(20)],
        name=agent,
        marker_color=agent_colors[i % len(agent_colors)],
        boxmean=True,
    ))
fig3.update_layout(
    height=350,
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Inter', color=t['text_secondary']),
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(showgrid=False, tickfont=dict(size=11, color=t['text_primary'])),
    yaxis=dict(title='Latency (s)', gridcolor=t['card_border'], tickfont=dict(size=10, color=t['text_muted'])),
    boxmode='group',
    hoverlabel=dict(bgcolor=t['bg_secondary'], bordercolor=t['card_border'], font=dict(color=t['text_primary'])),
    showlegend=False,
)
st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# ── Agent Details Table ──────────────────────────────────────────
st.markdown(f"""
<div class="section-header animate-in"><div class="section-header-accent"></div>Agent Details</div>
""", unsafe_allow_html=True)

st.markdown('<div class="glass-card" style="padding:0; overflow:hidden;">', unsafe_allow_html=True)
display_df = metrics_df.copy()
display_df.columns = ['Agent', 'Invocations', 'Avg Latency (s)', 'Success Rate (%)', 'Tokens Used']
st.dataframe(display_df, use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# ── Agent Workflow — Neon Flow Diagram ───────────────────────────
st.markdown(f"""
<div class="section-header animate-in"><div class="section-header-accent"></div>Agent Workflow</div>
""", unsafe_allow_html=True)

agents_flow = [
    ("📥", "Intake", "Parses Slack/Telegram requests"),
    ("🔍", "Analysis", "Scans repo, maps impact"),
    ("💻", "Coder", "Generates code + tests"),
    ("✅", "Validation", "Self-heals CI failures"),
    ("📄", "PR Agent", "Creates structured PRs"),
    ("🚀", "Deploy", "Stages & deploys"),
    ("📊", "Monitor", "Watches post-deploy"),
]

flow_html = '<div style="display:flex; gap:8px; overflow-x:auto; padding:8px 0;">'
for i, (icon, name, desc) in enumerate(agents_flow):
    color = agent_colors[i % len(agent_colors)]
    flow_html += f'''
    <div class="glass-card animate-in" style="flex:0 0 140px; text-align:center; padding:20px 12px; border-radius:16px; animation-delay:{i*0.1}s; border-top:3px solid {color};">
        <div style="font-size:2rem; margin-bottom:8px; filter:drop-shadow(0 0 8px {color}44);">{icon}</div>
        <div style="font-size:0.82rem; font-weight:800; color:{t['text_primary']}; margin-bottom:6px;">{name}</div>
        <div style="font-size:0.68rem; color:{t['text_muted']}; line-height:1.5;">{desc}</div>
    </div>
    '''
    if i < len(agents_flow) - 1:
        flow_html += f'<div style="display:flex; align-items:center; color:{t["accent_purple"]}; font-size:1.2rem; opacity:0.5;">→</div>'
flow_html += '</div>'
st.markdown(flow_html, unsafe_allow_html=True)
