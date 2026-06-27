"""
📋 Pipeline Board — GOD-LEVEL Kanban View
Animated columns, 3D card transforms, neon stage indicators, and live counters.
"""

import streamlit as st
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.themes import THEMES, get_theme, inject_css, inject_viewport
from components.data import generate_requests, PIPELINE_MAP

st.set_page_config(page_title="Pipeline Board — Plotcode", page_icon="📋", layout="wide")
st.markdown(inject_viewport(), unsafe_allow_html=True)

theme_name = st.session_state.get('theme_name', '🌑 Obsidian Dark')
t = get_theme(theme_name)
st.markdown(inject_css(t), unsafe_allow_html=True)

# Particles
particle_html = '<div class="particle-bg">'
for i in range(15):
    x = random.randint(0, 100)
    delay = random.uniform(0, 12)
    dur = random.uniform(8, 18)
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
    <div class="hero-badge">📋 KANBAN VIEW — Real-time Pipeline Tracking</div>
    <div class="hero-title">Pipeline Board</div>
    <div class="hero-subtitle">Full Kanban view of all feature requests across the 14-stage delivery workflow with live status tracking.</div>
</div>
""", unsafe_allow_html=True)

# ── Stats Bar ────────────────────────────────────────────────────
total = len(df)
stages_order = ['Submitted', 'Pending Review', 'AI Planning', 'In Development', 'QA / Staging', 'Production', 'Deployed ✅']
stage_counts = {s: len(df[df['pipeline_stage'] == s]) for s in stages_order}

stats_bar_html = '<div style="display:flex; gap:12px; margin-bottom:24px; flex-wrap:wrap;">'
for stage in stages_order:
    count = stage_counts[stage]
    stats_bar_html += f'''
    <div class="glass-card" style="flex:1; min-width:120px; padding:16px; text-align:center; border-radius:14px;">
        <div style="font-size:1.6rem; font-weight:900; font-family:'Orbitron',sans-serif; background:{t['gradient_primary']}; -webkit-background-clip:text; -webkit-text-fill-color:transparent;">{count}</div>
        <div style="font-size:0.68rem; color:{t['text_muted']}; text-transform:uppercase; letter-spacing:0.08em; margin-top:4px;">{stage.split(' ')[0]}</div>
    </div>
    '''
stats_bar_html += '</div>'
st.markdown(stats_bar_html, unsafe_allow_html=True)

# ── Filters ───────────────────────────────────────────────────────
filter_cols = st.columns([1, 1, 1, 2])
with filter_cols[0]:
    priority_filter = st.multiselect("Priority", ['P0', 'P1', 'P2', 'P3'], default=['P0', 'P1', 'P2', 'P3'])
with filter_cols[1]:
    service_filter = st.multiselect("Service", df['affected_service'].unique().tolist(), default=df['affected_service'].unique().tolist())
with filter_cols[2]:
    team_filter = st.multiselect("Team", df['requester_team'].unique().tolist(), default=df['requester_team'].unique().tolist())
with filter_cols[3]:
    search = st.text_input("🔍 Search features", placeholder="Type to search...")

filtered = df[
    (df['priority'].isin(priority_filter)) &
    (df['affected_service'].isin(service_filter)) &
    (df['requester_team'].isin(team_filter))
]
if search:
    filtered = filtered[filtered['title'].str.contains(search, case=False, na=False) | filtered['request_id'].str.contains(search, case=False, na=False)]

st.markdown(f"""
<div style="font-size:0.82rem; color:{t['text_muted']}; margin: 8px 0 20px 0; display:flex; align-items:center; gap:8px;">
    <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:{t['accent_emerald']}; box-shadow:0 0 8px {t['accent_emerald']}; animation: glow-pulse 2s ease-in-out infinite;"></span>
    Showing <strong style="color:{t['text_primary']};">{len(filtered)}</strong> of <strong style="color:{t['text_primary']};">{len(df)}</strong> features
</div>
""", unsafe_allow_html=True)

# ── Kanban Board ──────────────────────────────────────────────────
stage_icons = {
    'Submitted': '📥', 'Pending Review': '👀', 'AI Planning': '🤖',
    'In Development': '⚡', 'QA / Staging': '🧪', 'Production': '🏭', 'Deployed ✅': '🚀'
}
stage_colors = {
    'Submitted': t['accent_purple'], 'Pending Review': t['accent_amber'],
    'AI Planning': t['accent_cyan'], 'In Development': t['accent_blue'],
    'QA / Staging': t['accent_amber'], 'Production': t['accent_rose'],
    'Deployed ✅': t['accent_emerald'],
}

board_cols = st.columns(len(stages_order), gap="small")

for col, stage in zip(board_cols, stages_order):
    with col:
        stage_df = filtered[filtered['pipeline_stage'] == stage]
        count = len(stage_df)
        color = stage_colors[stage]
        icon = stage_icons[stage]

        cards_html = ""
        for i, (_, row) in enumerate(stage_df.iterrows()):
            p_class = f"priority-{row['priority'].lower()}"
            time_diff = row['updated_at'] - row['created_at']
            hours = int(time_diff.total_seconds() / 3600)
            time_str = f"{hours}h" if hours < 48 else f"{hours // 24}d"
            branch = f"<div style='font-size:0.68rem; color:{t['accent_cyan']}; font-family:JetBrains Mono,monospace; margin-top:6px; opacity:0.8;'>🌿 {row['feature_branch'][:22]}...</div>" if row['feature_branch'] else ""
            pr_badge = f"<span style='font-size:0.65rem; background:{t['accent_emerald']}18; color:{t['accent_emerald']}; padding:2px 8px; border-radius:6px; font-weight:700;'>PR #{row['pr_number']}</span>" if row['pr_number'] else ""

            cards_html += f"""
            <div class="feature-card" style="animation-delay: {i * 0.05}s;">
                <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:8px;">
                    <div class="feature-title">{row['title'][:26]}{'...' if len(row['title']) > 26 else ''}</div>
                </div>
                <div style="display:flex; align-items:center; gap:6px; margin-bottom:8px;">
                    <span class="priority-badge {p_class}">{row['priority']}</span>
                    {pr_badge}
                </div>
                <div style="font-size:0.72rem; color:{t['text_muted']}; display:flex; justify-content:space-between; align-items:center;">
                    <span>👤 {row['requester_name'].split(' ')[0]}</span>
                    <span style="font-family:'JetBrains Mono',monospace;">⏱ {time_str}</span>
                </div>
                {branch}
                <div style="font-size:0.65rem; color:{t['text_muted']}; margin-top:6px; font-family:'JetBrains Mono',monospace; opacity:0.6;">{row['request_id']}</div>
            </div>
            """

        st.markdown(f"""
        <div class="pipeline-col animate-in">
            <div class="pipeline-col-header">
                <span>{icon} {stage.split('✅')[0].strip()}</span>
                <span class="pipeline-count">{count}</span>
            </div>
            <div style="max-height:620px; overflow-y:auto; padding-right:4px;">
                {cards_html if cards_html else f"<div style='text-align:center; padding:50px 0; font-size:0.82rem; color:{t['text_muted']};'>No items</div>"}
            </div>
        </div>
        """, unsafe_allow_html=True)
