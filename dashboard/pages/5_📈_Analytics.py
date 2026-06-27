"""
📈 Analytics — GOD-LEVEL Delivery Insights
Deep analytics with animated gauges, premium charts, team leaderboard, and SLA tracking.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import random
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.themes import get_theme, inject_css, inject_viewport
from components.data import generate_requests, generate_daily_throughput

st.set_page_config(page_title="Analytics — Plotcode", page_icon="📈", layout="wide")
st.markdown(inject_viewport(), unsafe_allow_html=True)

theme_name = st.session_state.get('theme_name', '🌑 Obsidian Dark')
t = get_theme(theme_name)
st.markdown(inject_css(t), unsafe_allow_html=True)

# Particles
particle_html = '<div class="particle-bg">'
for i in range(10):
    x = random.randint(0, 100)
    delay = random.uniform(0, 8)
    dur = random.uniform(8, 14)
    particle_html += f'<div class="particle" style="left:{x}%; animation-delay:{delay}s; animation-duration:{dur}s;"></div>'
particle_html += '</div>'
st.markdown(particle_html, unsafe_allow_html=True)
st.markdown('<div class="aurora-bg"><div class="aurora-blob"></div><div class="aurora-blob"></div></div>', unsafe_allow_html=True)

if 'requests_df' not in st.session_state:
    st.session_state['requests_df'] = generate_requests(80)
df = st.session_state['requests_df']

# ── Hero Header ──────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-header animate-in">
    <div class="hero-badge">📈 ANALYTICS — Deep Pipeline Intelligence</div>
    <div class="hero-title">Delivery Analytics</div>
    <div class="hero-subtitle">Performance insights, SLA tracking, team metrics, and pipeline health across your entire delivery lifecycle.</div>
</div>
""", unsafe_allow_html=True)

# ── Top Stats ────────────────────────────────────────────────────
deployed = len(df[df['status'].isin(['deployed', 'closed'])])
avg_time = round(random.uniform(4.2, 12.8), 1)
sla_compliance = round(random.uniform(91.0, 98.5), 1)
ai_contribution = round(random.uniform(72.0, 89.0), 1)

stats = [
    (f"{deployed}", "Features Deployed", "🚀", f"+{random.randint(5, 20)}%", "up"),
    (f"{avg_time}h", "Avg Time to Deploy", "⏱️", f"-{random.randint(10, 30)}%", "down"),
    (f"{sla_compliance}%", "SLA Compliance", "📊", f"+{random.randint(1, 5)}%", "up"),
    (f"{ai_contribution}%", "AI Contribution", "🤖", f"+{random.randint(5, 15)}%", "up"),
]

sc = st.columns(4)
for col, (val, label, icon, trend, direction) in zip(sc, stats):
    with col:
        trend_class = "trend-up" if direction == "up" else "trend-down"
        trend_icon = "↑" if direction == "up" else "↓"
        st.markdown(f"""
        <div class="stat-card animate-in">
            <div class="stat-icon">{icon}</div>
            <div class="stat-value">{val}</div>
            <div class="stat-label">{label}</div>
            <div class="stat-trend {trend_class}">{trend_icon} {trend}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# ── Performance Ring Gauges ──────────────────────────────────────
ring_cols = st.columns(4, gap="medium")
ring_data = [
    {"label": "Deploy Rate", "value": round(deployed / max(len(df), 1) * 100), "color": t['accent_emerald']},
    {"label": "Code Quality", "value": random.randint(88, 97), "color": t['accent_cyan']},
    {"label": "Test Coverage", "value": random.randint(75, 95), "color": t['accent_purple']},
    {"label": "Uptime", "value": random.randint(96, 100), "color": t['accent_amber']},
]

for col, rd in zip(ring_cols, ring_data):
    with col:
        circumference = 2 * math.pi * 35
        offset = circumference - (rd["value"] / 100) * circumference
        st.markdown(f"""
        <div class="glass-card animate-in" style="text-align:center; padding:24px 16px;">
            <svg width="90" height="90" viewBox="0 0 90 90" style="margin-bottom:10px;">
                <defs>
                    <linearGradient id="analytics-ring-{rd['label']}" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:{t['accent_purple']}"/>
                        <stop offset="100%" style="stop-color:{rd['color']}"/>
                    </linearGradient>
                </defs>
                <circle cx="45" cy="45" r="35" fill="none" stroke="{t['card_border']}" stroke-width="6"/>
                <circle cx="45" cy="45" r="35" fill="none" stroke="url(#analytics-ring-{rd['label']})"
                    stroke-width="6" stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"
                    stroke-linecap="round" style="transform:rotate(-90deg); transform-origin:center;"/>
            </svg>
            <div style="font-size:1.3rem; font-weight:900; font-family:'Orbitron',sans-serif; background:{t['gradient_primary']}; -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{rd['value']}%</div>
            <div style="font-size:0.72rem; color:{t['text_muted']}; text-transform:uppercase; letter-spacing:0.08em; margin-top:4px;">{rd['label']}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Throughput", "🎯 Distribution", "⏱️ SLA Tracking"])

with tab1:
    throughput = generate_daily_throughput(30)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=throughput['date'], y=throughput['submitted'],
        name='Submitted', fill='tonexty',
        line=dict(color=t['accent_purple'], width=3, shape='spline'),
        fillcolor=f"{t['accent_purple']}12",
    ))
    fig.add_trace(go.Scatter(
        x=throughput['date'], y=throughput['deployed'],
        name='Deployed', fill='tozeroy',
        line=dict(color=t['accent_emerald'], width=3, shape='spline'),
        fillcolor=f"{t['accent_emerald']}18",
    ))
    fig.add_trace(go.Bar(
        x=throughput['date'], y=throughput['failed'],
        name='Failed',
        marker_color=t['accent_rose'],
        marker_opacity=0.5,
    ))
    fig.update_layout(
        height=440,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color=t['text_secondary']),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(size=11)),
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(showgrid=False, tickfont=dict(size=10, color=t['text_muted'])),
        yaxis=dict(gridcolor=t['card_border'], gridwidth=0.5, tickfont=dict(size=10, color=t['text_muted'])),
        hovermode='x unified',
        hoverlabel=dict(bgcolor=t['bg_secondary'], bordercolor=t['card_border'], font=dict(color=t['text_primary'])),
        bargap=0.3,
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with tab2:
    dist1, dist2 = st.columns(2, gap="large")

    with dist1:
        priority_counts = df['priority'].value_counts()
        colors = [t['accent_rose'], t['accent_amber'], t['accent_cyan'], t['accent_emerald']]

        fig_pie = go.Figure(go.Pie(
            labels=priority_counts.index,
            values=priority_counts.values,
            hole=0.7,
            marker=dict(colors=colors, line=dict(color=t['bg'], width=4)),
            textinfo='label+percent',
            textfont=dict(size=12, family='Inter', color=t['text_primary']),
            hoverlabel=dict(bgcolor=t['bg_secondary'], bordercolor=t['card_border']),
        ))
        fig_pie.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color=t['text_secondary']),
            showlegend=False,
            margin=dict(l=20, r=20, t=10, b=20),
        )
        fig_pie.add_annotation(
            text=f"<b>{len(df)}</b><br><span style='font-size:10px'>Total</span>",
            x=0.5, y=0.5, font=dict(size=22, color=t['text_primary'], family='Orbitron'),
            showarrow=False, xref='paper', yref='paper'
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})

    with dist2:
        service_counts = df['affected_service'].value_counts().head(8)

        fig_bar = go.Figure(go.Bar(
            x=service_counts.values,
            y=service_counts.index,
            orientation='h',
            marker=dict(
                color=service_counts.values,
                colorscale=[[0, t['accent_purple']], [0.5, t['accent_cyan']], [1, t['accent_emerald']]],
                cornerradius=8,
            ),
            text=service_counts.values,
            textposition='outside',
            textfont=dict(color=t['text_primary'], size=12, family='JetBrains Mono'),
        ))
        fig_bar.update_layout(
            height=400,
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', color=t['text_secondary']),
            margin=dict(l=0, r=70, t=10, b=0),
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, tickfont=dict(size=12, color=t['text_primary'])),
            hoverlabel=dict(bgcolor=t['bg_secondary'], bordercolor=t['card_border'], font=dict(color=t['text_primary'])),
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

with tab3:
    sla_data = []
    for i in range(30):
        sla_data.append({
            'day': f'Day {i+1}',
            'actual_hours': round(random.uniform(2, 18), 1),
            'sla_target': 12.0,
        })
    sla_df = pd.DataFrame(sla_data)

    fig_sla = go.Figure()
    fig_sla.add_trace(go.Bar(
        x=sla_df['day'], y=sla_df['actual_hours'],
        name='Actual Hours',
        marker=dict(
            color=[t['accent_emerald'] if h <= 12 else t['accent_rose'] for h in sla_df['actual_hours']],
            cornerradius=6,
        ),
    ))
    fig_sla.add_trace(go.Scatter(
        x=sla_df['day'], y=sla_df['sla_target'],
        name='SLA Target (12h)',
        line=dict(color=t['accent_amber'], width=2.5, dash='dash'),
    ))
    fig_sla.update_layout(
        height=420,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color=t['text_secondary']),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(showgrid=False, tickangle=45, tickfont=dict(size=9, color=t['text_muted'])),
        yaxis=dict(gridcolor=t['card_border'], gridwidth=0.5, title='Hours', tickfont=dict(size=10, color=t['text_muted'])),
        hovermode='x unified',
        hoverlabel=dict(bgcolor=t['bg_secondary'], bordercolor=t['card_border'], font=dict(color=t['text_primary'])),
    )
    st.plotly_chart(fig_sla, use_container_width=True, config={'displayModeBar': False})

st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

# ── Team Leaderboard ──────────────────────────────────────────────
st.markdown(f"""
<div class="section-header animate-in"><div class="section-header-accent"></div>Team Leaderboard</div>
""", unsafe_allow_html=True)

team_counts = df.groupby('requester_team').agg(
    total=('request_id', 'count'),
    deployed=('status', lambda x: (x.isin(['deployed', 'closed'])).sum()),
).reset_index()
team_counts['rate'] = (team_counts['deployed'] / team_counts['total'] * 100).round(1)
team_counts = team_counts.sort_values('deployed', ascending=False)

leaderboard_html = ""
for i, (_, row) in enumerate(team_counts.iterrows()):
    medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"
    bar_width = int(row['rate'])
    leaderboard_html += f"""
    <div style="display:flex; align-items:center; gap:16px; padding:16px 0; border-bottom:1px solid {t['card_border']}; transition:all 0.3s ease;" onmouseover="this.style.background='linear-gradient(90deg, {t['accent_purple']}08, transparent)'" onmouseout="this.style.background='transparent'">
        <div style="font-size:1.6rem; width:48px; text-align:center; filter:drop-shadow(0 0 4px {t['accent_purple']}44);">{medal}</div>
        <div style="flex:1;">
            <div style="font-size:0.95rem; font-weight:700; color:{t['text_primary']};">{row['requester_team']}</div>
            <div style="font-size:0.72rem; color:{t['text_muted']}; margin-top:4px;">{row['total']} features · {row['deployed']} deployed</div>
        </div>
        <div style="width:220px;">
            <div style="background:{t['card_border']}; border-radius:12px; height:10px; overflow:hidden;">
                <div style="background:{t['gradient_primary']}; height:100%; width:{bar_width}%; border-radius:12px; box-shadow:0 0 12px {t['accent_purple']}44; transition:width 1.5s ease;"></div>
            </div>
        </div>
        <div style="font-size:0.92rem; font-weight:800; background:{t['gradient_primary']}; -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-family:'Orbitron',monospace; width:55px; text-align:right;">{row['rate']}%</div>
    </div>
    """

st.markdown(f"""
<div class="glass-card animate-in">
    {leaderboard_html}
</div>
""", unsafe_allow_html=True)
