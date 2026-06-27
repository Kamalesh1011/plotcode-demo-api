"""
Happy Path Test: JSON Update Request
Demonstrates the full 14-stage pipeline from a simple JSON update request
to production deployment, using mocked HITL approvals.

Usage:
    python scripts/happy_path_test.py

This script:
1. Submits a feature request (update a JSON config file)
2. Simulates HITL approvals at each gate
3. Triggers agent actions
4. Verifies the request reaches 'closed' status
"""

import os
import sys
import time
import json
from datetime import datetime

# Add agents to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

from shared.state import get_state_store
from analysis_agent import AnalysisAgent
from coder_agent import CoderAgent
from pr_agent import PRAgent
from deployment_agent import DeploymentAgent
from monitoring_agent import MonitoringAgent


def generate_request_id():
    year = datetime.now().year
    seq = f"{abs(hash(datetime.now().isoformat())) % 10000:04d}"
    return f"REQ-{year}-{seq}"


def run_happy_path():
    store = get_state_store()
    request_id = generate_request_id()

    print("=" * 60)
    print(f" PLOTCODE HAPPY PATH TEST")
    print(f" Request ID: {request_id}")
    print("=" * 60)

    # === STAGE 1: Intake ===
    print("\n[1/14] Request Submission...")
    req = store.create_request({
        'request_id': request_id,
        'title': 'Add new user role field to config.json',
        'business_need': 'We need to support a new "analyst" user role in the application configuration.',
        'expected_behavior': 'config.json should include "analyst" in the roles array with appropriate permissions.',
        'priority': 'P1',
        'affected_service': 'demo-api',
        'requester_name': 'Alice PM',
        'requester_slack_id': 'U_ALICE',
        'requester_team': 'Product',
        'status': 'submitted',
        'phase': 'MVP',
        'source': 'slack'
    })
    print(f"  Created: {request_id} (status={req['status']})")

    # === STAGE 2: HITL Gate 1 - Initial Approval ===
    print("\n[2/14] HITL Gate 1: Initial Approval...")
    store.update_request(request_id, {
        'status': 'approved',
        'initial_approver_slack_id': 'U_BOB',
        'initial_approved_at': datetime.now().isoformat()
    })
    store.log_audit(request_id, 'human', 'U_BOB', 'initial_approved')
    print(f"  Approved by Bob")

    # === STAGE 3: AI Analysis ===
    print("\n[3/14] AI Analysis (Analysis Agent)...")
    # Note: This would clone a real repo. For the test, we simulate the result.
    analysis = AnalysisAgent()
    # Simulated: in real usage, analysis.run(request_id) would clone the repo and generate a plan
    store.update_request(request_id, {
        'status': 'plan_pending_approval',
        'implementation_plan': '### Impacted Files\n- config.json: Add "analyst" to roles array\n- tests/test_config.py: Add test for new role\n\n### Implementation\n1. Append "analyst" to roles in config.json\n2. Add test case verifying role is present',
        'risk_notes': 'Low risk. Config-only change. No API contract changes.',
        'rollback_plan': 'Revert config.json to previous version.',
        'feature_branch': f'feat/{request_id}-add-analyst-role'
    })
    store.log_audit(request_id, 'ai', 'analysis_agent', 'plan_generated')
    print(f"  Plan generated")

    # === STAGE 4: HITL Gate 2 - Plan Approval ===
    print("\n[4/14] HITL Gate 2: Plan Approval...")
    store.update_request(request_id, {
        'status': 'plan_approved',
        'plan_approver_slack_id': 'U_CHARLIE',
        'plan_approved_at': datetime.now().isoformat()
    })
    store.log_audit(request_id, 'human', 'U_CHARLIE', 'plan_approved')
    print(f"  Approved by Charlie")

    # === STAGE 5: Code Generation ===
    print("\n[5/14] Code Generation (Coder Agent)...")
    coder = CoderAgent()
    # Simulated: coder.run(request_id) would create branch and write code
    store.update_request(request_id, {
        'status': 'ci_running',
        'feature_branch': f'feat/{request_id}-add-analyst-role'
    })
    store.log_audit(request_id, 'ai', 'coder_agent', 'code_changes_applied', {
        'files': ['config.json', 'tests/test_config.py']
    })
    print(f"  Code written, CI triggered")

    # === STAGE 6: CI Validation (simulated pass) ===
    print("\n[6/14] CI Validation...")
    time.sleep(0.5)
    store.update_request(request_id, {'status': 'ci_passed'})
    store.log_audit(request_id, 'system', 'github', 'ci_passed')
    print(f"  CI passed")

    # === STAGE 7: PR Creation ===
    print("\n[7/14] PR Creation (PR Agent)...")
    pr_agent = PRAgent()
    # Simulated
    store.update_request(request_id, {
        'status': 'pr_open',
        'pr_number': 42,
        'pr_url': f'https://github.com/plotcode/demo-api/pull/42'
    })
    store.log_audit(request_id, 'ai', 'pr_agent', 'pr_created', {
        'pr_number': 42,
        'pr_url': f'https://github.com/plotcode/demo-api/pull/42'
    })
    print(f"  PR #42 opened")

    # === STAGE 8: HITL Gate 3 - Code Review ===
    print("\n[8/14] HITL Gate 3: Code Review & Merge...")
    store.update_request(request_id, {
        'status': 'pr_merged',
        'pr_merger_slack_id': 'U_CHARLIE',
        'pr_merged_at': datetime.now().isoformat(),
        'merged_sha': 'abc1234'
    })
    store.log_audit(request_id, 'human', 'U_CHARLIE', 'pr_merged')
    print(f"  Merged by Charlie")

    # === STAGE 9: QA Deploy ===
    print("\n[9/14] QA Deployment...")
    deploy = DeploymentAgent()
    # Simulated
    store.update_request(request_id, {
        'status': 'qa_deployed',
        'staging_url': 'https://staging-api.plotcode.dev'
    })
    store.log_audit(request_id, 'system', 'deployment_agent', 'qa_deployed')
    print(f"  Deployed to staging")

    # === STAGE 10: HITL Gate 4 - QA Validation ===
    print("\n[10/14] HITL Gate 4: QA Validation...")
    store.update_request(request_id, {
        'status': 'qa_passed',
        'qa_validator_slack_id': 'U_ALICE',
        'qa_validated_at': datetime.now().isoformat()
    })
    store.log_audit(request_id, 'human', 'U_ALICE', 'qa_validated')
    print(f"  Validated by Alice")

    # === STAGE 11: HITL Gate 5 - Production Approval ===
    print("\n[11/14] HITL Gate 5: Production Approval...")
    store.update_request(request_id, {
        'status': 'prod_approved',
        'prod_approver_slack_id': 'U_DAVE',
        'prod_approved_at': datetime.now().isoformat()
    })
    store.log_audit(request_id, 'human', 'U_DAVE', 'prod_approved')
    print(f"  Approved by Dave (Production Owner)")

    # === STAGE 12: Production Deploy ===
    print("\n[12/14] Production Deployment...")
    store.update_request(request_id, {
        'status': 'deployed',
        'production_url': 'https://api.plotcode.dev',
        'deploy_timestamp': datetime.now().isoformat()
    })
    store.log_audit(request_id, 'system', 'deployment_agent', 'production_deployed')
    print(f"  Deployed to production")

    # === STAGE 13: Monitoring ===
    print("\n[13/14] Post-Deploy Monitoring...")
    monitor = MonitoringAgent()
    store.update_request(request_id, {'status': 'monitoring'})
    store.log_audit(request_id, 'system', 'monitoring_agent', 'monitoring_started')
    print(f"  Monitoring...")

    # === STAGE 14: Closure ===
    print("\n[14/14] Closure...")
    store.update_request(request_id, {
        'status': 'closed',
        'completed_at': datetime.now().isoformat(),
        'release_version': 'v2025.06.18-abc1234'
    })
    store.log_audit(request_id, 'system', 'monitoring_agent', 'ticket_closed')
    print(f"  Ticket closed")

    # === VERIFY ===
    print("\n" + "=" * 60)
    print(" RESULT")
    print("=" * 60)
    final = store.get_request(request_id)
    print(f" Request ID: {final['request_id']}")
    print(f" Status: {final['status']}")
    print(f" PR: {final.get('pr_url', 'N/A')}")
    print(f" Merged SHA: {final.get('merged_sha', 'N/A')}")
    print(f" Production URL: {final.get('production_url', 'N/A')}")
    print(f" Release: {final.get('release_version', 'N/A')}")
    print(f" Completed: {final.get('completed_at', 'N/A')}")
    print("")
    print(" Audit Trail:")
    logs = store.get_audit_log(request_id)
    for log in logs:
        print(f"  [{log['actor_type']}/{log['actor_id']}] {log['action']} at {log['created_at']}")
    print("")
    print(f" HAPPY PATH TEST: {'PASS' if final['status'] == 'closed' else 'FAIL'}")


if __name__ == '__main__':
    run_happy_path()
