"""
📝 Submit Feature Request — GOD-LEVEL Form Wizard
Animated form, 3D tips cards, and premium submission confirmation.
"""

import streamlit as st
import datetime
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from components.themes import get_theme, inject_css, inject_viewport

st.set_page_config(page_title="Submit Request — Plotcode", page_icon="📝", layout="wide")
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
    <div class="hero-badge">📝 NEW REQUEST — AI-Powered Delivery</div>
    <div class="hero-title">Submit Feature Request</div>
    <div class="hero-subtitle">Describe your feature and let AI handle the implementation — from code generation to production deployment.</div>
</div>
""", unsafe_allow_html=True)

# ── Form Layout ──────────────────────────────────────────────────
form_col, tips_col = st.columns([2.5, 1], gap="large")

with form_col:
    with st.form("feature_request_form", clear_on_submit=True):
        st.markdown(f"""
        <div class="section-header animate-in"><div class="section-header-accent"></div>Feature Details</div>
        """, unsafe_allow_html=True)

        title = st.text_input("Feature Title *", placeholder="e.g., Add OAuth 2.1 support to API Gateway")

        col1, col2 = st.columns(2)
        with col1:
            priority = st.selectbox("Priority *", ['P0 — Critical', 'P1 — High', 'P2 — Medium', 'P3 — Low'])
        with col2:
            service = st.selectbox("Affected Service *", [
                'auth-service', 'api-gateway', 'billing-engine',
                'user-portal', 'notification-hub', 'payment-ms',
                'analytics-api', 'search-index', 'Other'
            ])

        business_need = st.text_area(
            "Business Need *",
            placeholder="Describe the business problem this feature solves. Be specific — the AI uses this to understand context.",
            height=130,
        )

        expected_behavior = st.text_area(
            "Expected Behavior *",
            placeholder="What should happen after this feature is implemented? Include acceptance criteria if possible.",
            height=130,
        )

        st.markdown(f"""
        <div class="section-header animate-in" style="margin-top:28px;"><div class="section-header-accent"></div>Requester Information</div>
        """, unsafe_allow_html=True)

        r1, r2 = st.columns(2)
        with r1:
            requester_name = st.text_input("Your Name *", placeholder="e.g., Alex Rivera")
        with r2:
            requester_team = st.selectbox("Team", ['Platform', 'Frontend', 'Backend', 'DevOps', 'Mobile', 'Data', 'Security', 'Product'])

        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

        submitted = st.form_submit_button("🚀 Submit Feature Request", use_container_width=True, type="primary")

        if submitted:
            if not title or not business_need or not expected_behavior or not requester_name:
                st.error("❌ Please fill in all required fields (marked with *)")
            else:
                req_id = f"REQ-2025-{datetime.datetime.now().strftime('%H%M%S')}"
                st.success(f"✅ Feature request submitted successfully!")
                st.balloons()

                st.markdown(f"""
                <div class="glass-card animate-in" style="margin-top:20px; border-top:3px solid {t['accent_emerald']};">
                    <div style="font-size:1.15rem; font-weight:800; color:{t['text_primary']}; margin-bottom:16px; display:flex; align-items:center; gap:8px;">
                        <span style="filter:drop-shadow(0 0 8px {t['accent_emerald']}44);">📋</span> Request Submitted
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                        <div class="glass-card" style="padding:14px; border-radius:12px;">
                            <div style="font-size:0.68rem; color:{t['text_muted']}; text-transform:uppercase; letter-spacing:0.1em;">Request ID</div>
                            <div style="font-size:1rem; font-weight:800; color:{t['accent_cyan']}; font-family:'JetBrains Mono',monospace; margin-top:4px;">{req_id}</div>
                        </div>
                        <div class="glass-card" style="padding:14px; border-radius:12px;">
                            <div style="font-size:0.68rem; color:{t['text_muted']}; text-transform:uppercase; letter-spacing:0.1em;">Status</div>
                            <div style="font-size:1rem; font-weight:700; color:{t['accent_emerald']}; margin-top:4px;">✅ Submitted</div>
                        </div>
                        <div class="glass-card" style="padding:14px; border-radius:12px;">
                            <div style="font-size:0.68rem; color:{t['text_muted']}; text-transform:uppercase; letter-spacing:0.1em;">Priority</div>
                            <div style="font-size:1rem; font-weight:700; margin-top:4px;">{priority}</div>
                        </div>
                        <div class="glass-card" style="padding:14px; border-radius:12px;">
                            <div style="font-size:0.68rem; color:{t['text_muted']}; text-transform:uppercase; letter-spacing:0.1em;">Next Step</div>
                            <div style="font-size:1rem; font-weight:700; color:{t['accent_purple']}; margin-top:4px;">🔒 HITL Gate 1</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

with tips_col:
    st.markdown(f"""
    <div class="glass-card animate-in" style="border-left:4px solid {t['accent_purple']}; padding:24px 20px;">
        <div style="font-size:1.05rem; font-weight:800; margin-bottom:16px; color:{t['text_primary']}; display:flex; align-items:center; gap:8px;">
            <span style="filter:drop-shadow(0 0 6px {t['accent_purple']}44);">✨</span> AI Tips
        </div>
        <div style="font-size:0.85rem; color:{t['text_secondary']}; line-height:1.9;">
            The more detail you provide, the better the AI can generate your implementation plan.
            <br/><br/>
            <strong style="color:{t['text_primary']};">Include:</strong>
            <ul style="padding-left:18px; margin-top:10px; list-style:none;">
                <li style="margin-bottom:6px;">🔬 Technical context and constraints</li>
                <li style="margin-bottom:6px;">🔗 Affected endpoints or data models</li>
                <li style="margin-bottom:6px;">⚡ Performance requirements</li>
                <li style="margin-bottom:6px;">🎯 Edge cases to handle</li>
                <li style="margin-bottom:6px;">📄 Links to related documentation</li>
            </ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class="glass-card animate-in" style="border-left:4px solid {t['accent_cyan']}; padding:24px 20px; animation-delay:0.1s;">
        <div style="font-size:1.05rem; font-weight:800; margin-bottom:16px; color:{t['text_primary']}; display:flex; align-items:center; gap:8px;">
            <span style="filter:drop-shadow(0 0 6px {t['accent_cyan']}44);">🔄</span> What Happens Next
        </div>
        <div style="font-size:0.82rem; color:{t['text_secondary']}; line-height:2;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <span style="display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:50%; background:{t['accent_purple']}22; color:{t['accent_purple']}; font-size:0.72rem; font-weight:800;">1</span>
                Request enters <strong style="color:{t['text_primary']};">Pending Review</strong>
            </div>
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <span style="display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:50%; background:{t['accent_purple']}22; color:{t['accent_purple']}; font-size:0.72rem; font-weight:800;">2</span>
                Product Owner reviews & approves
            </div>
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <span style="display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:50%; background:{t['accent_cyan']}22; color:{t['accent_cyan']}; font-size:0.72rem; font-weight:800;">3</span>
                AI analyzes repo & proposes plan
            </div>
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <span style="display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:50%; background:{t['accent_cyan']}22; color:{t['accent_cyan']}; font-size:0.72rem; font-weight:800;">4</span>
                Tech Owner approves plan
            </div>
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                <span style="display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:50%; background:{t['accent_emerald']}22; color:{t['accent_emerald']}; font-size:0.72rem; font-weight:800;">5</span>
                AI writes code & creates PR
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
                <span style="display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px; border-radius:50%; background:{t['accent_emerald']}22; color:{t['accent_emerald']}; font-size:0.72rem; font-weight:800;">6</span>
                Human reviews, merges, deploys 🚀
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
