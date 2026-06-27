"""
🔐 RBAC & Users — GOD-LEVEL Access Control
3D gate cards, animated permissions matrix, and premium user management.
"""

import streamlit as st
import pandas as pd
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.themes import get_theme, inject_css, inject_viewport

st.set_page_config(page_title="RBAC — Plotcode", page_icon="🔐", layout="wide")
st.markdown(inject_viewport(), unsafe_allow_html=True)

theme_name = st.session_state.get('theme_name', '🌑 Obsidian Dark')
t = get_theme(theme_name)
st.markdown(inject_css(t), unsafe_allow_html=True)

# Particles
particle_html = '<div class="particle-bg">'
for i in range(8):
    x = random.randint(0, 100)
    delay = random.uniform(0, 8)
    particle_html += f'<div class="particle" style="left:{x}%; animation-delay:{delay}s; animation-duration:{random.uniform(8,14)}s;"></div>'
particle_html += '</div>'
st.markdown(particle_html, unsafe_allow_html=True)
st.markdown('<div class="aurora-bg"><div class="aurora-blob"></div><div class="aurora-blob"></div></div>', unsafe_allow_html=True)

# ── Hero Header ──────────────────────────────────────────────────
st.markdown(f"""
<div class="hero-header animate-in">
    <div class="hero-badge">🔐 SECURITY — Role-Based Access Control</div>
    <div class="hero-title">RBAC & Access Control</div>
    <div class="hero-subtitle">Manage user roles, permissions, and human-in-the-loop gate assignments across your delivery pipeline.</div>
</div>
""", unsafe_allow_html=True)

# ── HITL Gates Overview — 3D Cards ──────────────────────────────
st.markdown(f"""
<div class="section-header animate-in"><div class="section-header-accent"></div>Human-in-the-Loop Checkpoints</div>
""", unsafe_allow_html=True)

gates = [
    {"gate": "Gate 1", "action": "Approve Initial Request", "role": "Product Owner", "icon": "📋", "color": t['accent_purple']},
    {"gate": "Gate 2", "action": "Approve Implementation Plan", "role": "Developer / Architect", "icon": "🏗️", "color": t['accent_cyan']},
    {"gate": "Gate 3", "action": "Review & Merge PR", "role": "Reviewer", "icon": "👀", "color": t['accent_amber']},
    {"gate": "Gate 4", "action": "Validate in QA", "role": "Requester / QA Owner", "icon": "🧪", "color": t['accent_emerald']},
    {"gate": "Gate 5", "action": "Approve Prod Deploy", "role": "Production Owner", "icon": "🚀", "color": t['accent_rose']},
]

gate_html = '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:16px; margin-bottom:32px;">'
for i, g in enumerate(gates):
    gate_html += f'''
    <div class="glass-card animate-in" style="text-align:center; padding:28px 16px; border-radius:18px; animation-delay:{i*0.1}s; border-top:4px solid {g['color']}; position:relative; overflow:hidden;">
        <div style="position:absolute; top:-20px; right:-20px; width:80px; height:80px; background:{g['color']}11; border-radius:50%; filter:blur(20px);"></div>
        <div style="font-size:2.4rem; margin-bottom:10px; filter:drop-shadow(0 0 8px {g['color']}44); position:relative; z-index:2;">{g['icon']}</div>
        <div style="font-size:0.72rem; font-weight:800; color:{g['color']}; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:8px; position:relative; z-index:2;">{g['gate']}</div>
        <div style="font-size:0.9rem; font-weight:700; color:{t['text_primary']}; margin-bottom:8px; position:relative; z-index:2;">{g['action']}</div>
        <div style="font-size:0.72rem; color:{t['text_muted']}; position:relative; z-index:2;">Required: {g['role']}</div>
    </div>
    '''
gate_html += '</div>'
st.markdown(gate_html, unsafe_allow_html=True)

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# ── Permissions Matrix ───────────────────────────────────────────
st.markdown(f"""
<div class="section-header animate-in"><div class="section-header-accent"></div>Permissions Matrix</div>
""", unsafe_allow_html=True)

perms = {
    'Action': [
        'Submit Feature Request',
        'View All Requests',
        'Approve Initial Request (Gate 1)',
        'Approve Implementation Plan (Gate 2)',
        'Review & Merge PR (Gate 3)',
        'Validate in QA (Gate 4)',
        'Approve Prod Deployment (Gate 5)',
        'View Audit Logs',
        'Manage Users & Roles',
        'Configure Services',
    ],
    'Requester': ['✅', '🔒 Own', '❌', '❌', '❌', '✅ Own', '❌', '❌', '❌', '❌'],
    'Reviewer': ['✅', '✅', '❌', '✅', '✅', '✅', '❌', '✅', '❌', '❌'],
    'Approver': ['✅', '✅', '✅', '✅', '✅', '✅', '❌', '✅', '❌', '❌'],
    'Prod Owner': ['✅', '✅', '✅', '✅', '✅', '✅', '✅', '✅', '❌', '❌'],
    'Admin': ['✅', '✅', '✅', '✅', '✅', '✅', '✅', '✅', '✅', '✅'],
}

perms_df = pd.DataFrame(perms)
st.markdown('<div class="glass-card" style="padding:0; overflow:hidden;">', unsafe_allow_html=True)
st.dataframe(perms_df, use_container_width=True, hide_index=True, height=440)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# ── Users Table ──────────────────────────────────────────────────
st.markdown(f"""
<div class="section-header animate-in"><div class="section-header-accent"></div>Registered Users</div>
""", unsafe_allow_html=True)

users_data = {
    'Name': ['Alex Rivera', 'Sarah Chen', 'Kevin Patel', 'Mia Thompson', 'Omar Farouk', 'Lena Müller', 'Raj Iyer', 'Fatima Al-Rashid'],
    'Email': ['alex@plotcode.dev', 'sarah@plotcode.dev', 'kevin@plotcode.dev', 'mia@plotcode.dev', 'omar@plotcode.dev', 'lena@plotcode.dev', 'raj@plotcode.dev', 'fatima@plotcode.dev'],
    'Role': ['admin', 'prod_owner', 'reviewer', 'requester', 'approver', 'reviewer', 'approver', 'prod_owner'],
    'Team': ['Platform', 'Backend', 'Frontend', 'Mobile', 'DevOps', 'Backend', 'Data', 'Security'],
    'Status': ['🟢 Active', '🟢 Active', '🟢 Active', '🟢 Active', '🟢 Active', '🟡 Away', '🟢 Active', '🟢 Active'],
}

users_df = pd.DataFrame(users_data)
st.markdown('<div class="glass-card" style="padding:0; overflow:hidden;">', unsafe_allow_html=True)
st.dataframe(users_df, use_container_width=True, hide_index=True)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

# ── AI Guardrails ────────────────────────────────────────────────
st.markdown(f"""
<div class="section-header animate-in"><div class="section-header-accent"></div>🛡️ AI Guardrails (Non-Negotiable)</div>
""", unsafe_allow_html=True)

guardrails = [
    "AI **never** merges a PR without human approval",
    "AI **never** deploys to production without explicit human approval",
    "AI **never** reads, logs, or transmits secrets",
    "AI **never** modifies RBAC or pipeline configuration",
    "AI **never** skips a defined HITL gate",
    "Self-healing loop halts after max retries and escalates to human",
    "All AI actions are logged with prompt hash, response hash, and timestamp",
]

guardrail_html = '<div style="display:grid; gap:4px;">'
for i, g in enumerate(guardrails):
    guardrail_html += f'''
    <div class="glass-card animate-in" style="display:flex; align-items:center; gap:16px; padding:18px 20px; border-radius:14px; animation-delay:{i*0.06}s; border-left:4px solid {t['accent_rose']};">
        <span style="font-size:1.4rem; filter:drop-shadow(0 0 6px {t['accent_rose']}44);">🛡️</span>
        <span style="font-size:0.9rem; color:{t['text_primary']}; line-height:1.6; font-weight:500;">{g}</span>
    </div>
    '''
guardrail_html += '</div>'
st.markdown(guardrail_html, unsafe_allow_html=True)
