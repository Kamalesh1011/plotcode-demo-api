"""
Plotcode AI Delivery — Mock Data Generator
Generates realistic demo data for the dashboard when Supabase is unavailable.
"""

import random
import datetime
import pandas as pd

STATUSES = [
    'submitted', 'pending_review', 'approved',
    'planning', 'plan_pending_approval', 'plan_approved',
    'coding', 'ci_running', 'ci_passed',
    'pr_open', 'pr_reviewing', 'pr_approved', 'pr_merged',
    'qa_deployed', 'qa_validating', 'qa_passed',
    'prod_pending_approval', 'prod_approved', 'deploying', 'deployed', 'closed'
]

PIPELINE_MAP = {
    'submitted': 'Submitted',
    'pending_review': 'Pending Review',
    'approved': 'Pending Review',
    'planning': 'AI Planning',
    'plan_pending_approval': 'AI Planning',
    'plan_approved': 'AI Planning',
    'coding': 'In Development',
    'ci_running': 'In Development',
    'ci_passed': 'In Development',
    'pr_open': 'In Development',
    'pr_reviewing': 'In Development',
    'pr_approved': 'In Development',
    'pr_merged': 'In Development',
    'qa_deployed': 'QA / Staging',
    'qa_validating': 'QA / Staging',
    'qa_passed': 'QA / Staging',
    'prod_pending_approval': 'Production',
    'prod_approved': 'Production',
    'deploying': 'Production',
    'deployed': 'Deployed ✅',
    'closed': 'Deployed ✅',
}

SERVICES = ['auth-service', 'api-gateway', 'billing-engine', 'user-portal', 'notification-hub', 'payment-ms', 'analytics-api', 'search-index']
TEAMS = ['Platform', 'Frontend', 'Backend', 'DevOps', 'Mobile', 'Data', 'Security']
NAMES = ['Alex Rivera', 'Sarah Chen', 'Kevin Patel', 'Mia Thompson', 'Omar Farouk', 'Lena Müller', 'Raj Iyer', 'Fatima Al-Rashid', 'Carlos Mendez', 'Yuki Tanaka']
PRIORITIES = ['P0', 'P1', 'P2', 'P3']

FEATURE_TITLES = [
    "API Gateway v2 Upgrade", "OAuth 2.1 Integration", "Rate Limiter Enhancement",
    "Billing Webhook Retry", "Search Autocomplete", "Push Notification Overhaul",
    "User Profile Caching", "Payment Refund API", "Analytics ETL Pipeline",
    "Mobile Deep Linking", "SSO SAML Support", "Audit Log Export",
    "Multi-Tenant Isolation", "GraphQL Federation", "CDN Cache Purge",
    "A/B Testing Framework", "Error Budget Alerting", "Data Masking PII",
    "Batch Import API", "Realtime Dashboard WS", "Config Hot Reload",
    "Canary Deployment v2", "Feature Flag Service", "Circuit Breaker Pattern",
]

ACTIVITY_TEMPLATES = [
    ("🤖", "AI generated implementation plan for", "accent_purple"),
    ("✅", "PR merged for", "accent_emerald"),
    ("🚀", "Deployed to production:", "accent_cyan"),
    ("👤", "Human approved plan for", "accent_purple"),
    ("🔄", "CI pipeline passed for", "accent_emerald"),
    ("📝", "Code review requested on", "accent_amber"),
    ("⚠️", "CI failure detected in", "accent_rose"),
    ("🧪", "QA validation completed for", "accent_cyan"),
    ("📋", "New feature request submitted:", "accent_purple"),
    ("🔒", "RBAC check passed for", "accent_emerald"),
]


def generate_requests(n: int = 50) -> pd.DataFrame:
    now = datetime.datetime.now()
    rows = []
    for i in range(n):
        status = random.choice(STATUSES)
        created = now - datetime.timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        rows.append({
            'request_id': f'REQ-2025-{1000 + i:04d}',
            'title': random.choice(FEATURE_TITLES),
            'priority': random.choice(PRIORITIES),
            'status': status,
            'pipeline_stage': PIPELINE_MAP.get(status, 'Unknown'),
            'affected_service': random.choice(SERVICES),
            'requester_name': random.choice(NAMES),
            'requester_team': random.choice(TEAMS),
            'created_at': created,
            'updated_at': created + datetime.timedelta(hours=random.randint(1, 48)),
            'pr_number': random.randint(100, 999) if status in ['pr_open', 'pr_reviewing', 'pr_approved', 'pr_merged', 'qa_deployed', 'deployed', 'closed'] else None,
            'feature_branch': f'feature/REQ-2025-{1000 + i:04d}' if status not in ['submitted', 'pending_review'] else None,
        })
    return pd.DataFrame(rows)


def generate_activity_feed(n: int = 20) -> list[dict]:
    now = datetime.datetime.now()
    feed = []
    for i in range(n):
        template = random.choice(ACTIVITY_TEMPLATES)
        req_id = f'REQ-2025-{random.randint(1000, 1049):04d}'
        minutes_ago = random.randint(1, 1440)
        feed.append({
            'icon': template[0],
            'text': f"{template[1]} {req_id}",
            'color_key': template[2],
            'time': now - datetime.timedelta(minutes=minutes_ago),
            'minutes_ago': minutes_ago,
        })
    feed.sort(key=lambda x: x['minutes_ago'])
    return feed


def generate_daily_throughput(days: int = 30) -> pd.DataFrame:
    now = datetime.datetime.now()
    rows = []
    for d in range(days):
        day = now - datetime.timedelta(days=days - d)
        rows.append({
            'date': day.strftime('%Y-%m-%d'),
            'submitted': random.randint(2, 12),
            'deployed': random.randint(1, 8),
            'failed': random.randint(0, 3),
        })
    return pd.DataFrame(rows)


def generate_agent_metrics() -> list[dict]:
    agents = ['Intake', 'Analysis', 'Coder', 'Validation', 'PR', 'Deployment', 'Monitoring']
    return [
        {
            'agent': a,
            'invocations': random.randint(30, 500),
            'avg_latency_s': round(random.uniform(1.5, 45.0), 1),
            'success_rate': round(random.uniform(92.0, 99.9), 1),
            'tokens_used': random.randint(5000, 200000),
        }
        for a in agents
    ]
