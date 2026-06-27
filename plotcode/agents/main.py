"""
Plotcode Agent Worker
Main entry point for the Python AI agent layer.
Listens for work via HTTP/webhooks or polling from Supabase,
invokes the right agent for each pipeline stage.
"""

import os
import time
import json
import argparse
from typing import Optional
from shared.state import get_state_store
from shared.llm_client import get_llm_client
from shared.git_client import get_git_client
from intake_agent import IntakeAgent
from analysis_agent import AnalysisAgent
from coder_agent import CoderAgent
from validation_agent import ValidationAgent
from pr_agent import PRAgent
from deployment_agent import DeploymentAgent
from monitoring_agent import MonitoringAgent


class AgentWorker:
    """Polls Supabase for requests that need agent action and executes them."""

    def __init__(self):
        self.store = get_state_store()
        self.agents = {
            'intake': IntakeAgent(),
            'analysis': AnalysisAgent(),
            'coding': CoderAgent(),
            'validation': ValidationAgent(),
            'pr': PRAgent(),
            'deployment': DeploymentAgent(),
            'monitoring': MonitoringAgent(),
        }

    def poll_and_work(self, interval: int = 10) -> None:
        """Main loop: poll for work and execute agents."""
        print(f"[AGENT WORKER] Started. Polling every {interval}s")
        while True:
            try:
                self._tick()
            except Exception as e:
                print(f"[AGENT WORKER] Error in tick: {e}")
            time.sleep(interval)

    def _tick(self) -> None:
        """One iteration: check for requests that need AI action."""
        # Find requests in AI-actionable states
        actionable = [
            'approved',      # -> analysis
            'plan_approved',  # -> coding
            'ci_failed',      # -> self-heal
            'ci_passed',      # -> PR creation
            'pr_merged',      # -> QA deploy
            'qa_passed',      # -> production deploy (after approval)
            'deployed',       # -> monitoring
        ]

        for status in actionable:
            requests = self.store.list_requests(status=status)
            for req in requests:
                self._process_request(req)

    def _process_request(self, req: dict) -> None:
        """Route a request to the appropriate agent based on status."""
        request_id = req['request_id']
        status = req['status']

        print(f"[AGENT WORKER] Processing {request_id} (status={status})")

        try:
            if status == 'approved':
                self.agents['analysis'].run(request_id)
            elif status == 'plan_approved':
                self.agents['coding'].run(request_id)
            elif status == 'ci_failed':
                self.agents['validation'].run(request_id)
            elif status == 'ci_passed':
                self.agents['pr'].run(request_id)
            elif status == 'pr_merged':
                self.agents['deployment'].deploy_qa(request_id)
            elif status == 'qa_passed':
                # Only deploy to production if prod_approved
                if req.get('prod_approved_at'):
                    self.agents['deployment'].deploy_production(request_id)
            elif status == 'deployed':
                self.agents['monitoring'].run(request_id)
        except Exception as e:
            print(f"[AGENT WORKER] Failed to process {request_id}: {e}")
            self.store.log_audit(request_id, 'system', 'agent_worker', 'agent_error', {
                'status': status,
                'error': str(e)
            })

    def run_single(self, request_id: str, agent_name: str) -> None:
        """Run a specific agent for a specific request (CLI mode)."""
        agent = self.agents.get(agent_name)
        if not agent:
            raise ValueError(f"Unknown agent: {agent_name}")

        if agent_name == 'analysis':
            agent.run(request_id)
        elif agent_name == 'coding':
            agent.run(request_id)
        elif agent_name == 'validation':
            agent.run(request_id)
        elif agent_name == 'pr':
            agent.run(request_id)
        elif agent_name == 'deployment':
            req = self.store.get_request(request_id)
            if req and req.get('prod_approved_at'):
                agent.deploy_production(request_id)
            else:
                agent.deploy_qa(request_id)
        elif agent_name == 'monitoring':
            agent.run(request_id)
        else:
            raise ValueError(f"Agent {agent_name} has no run handler")


def main():
    parser = argparse.ArgumentParser(description='Plotcode Agent Worker')
    parser.add_argument('--poll', action='store_true', help='Run in polling mode')
    parser.add_argument('--request-id', type=str, help='Request ID to process')
    parser.add_argument('--agent', type=str, choices=['intake', 'analysis', 'coding', 'validation', 'pr', 'deployment', 'monitoring'],
                        help='Agent to run')
    parser.add_argument('--interval', type=int, default=10, help='Polling interval in seconds')
    args = parser.parse_args()

    worker = AgentWorker()

    if args.poll:
        worker.poll_and_work(interval=args.interval)
    elif args.request_id and args.agent:
        worker.run_single(args.request_id, args.agent)
    else:
        print("Usage:")
        print("  python main.py --poll [--interval 10]")
        print("  python main.py --request-id REQ-2025-0001 --agent analysis")


if __name__ == '__main__':
    main()
