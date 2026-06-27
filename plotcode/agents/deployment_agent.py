"""
Deployment Agent
Manages deployments to QA/staging and production environments.
Requires explicit human approval for production.
"""

import os
import time
import json
from typing import Dict, Any, Optional
from shared.state import get_state_store
from shared.git_client import get_git_client


class DeploymentAgent:
    """Orchestrates environment deployments via CI/CD triggers."""

    def __init__(self):
        self.store = get_state_store()
        self.git = get_git_client()

    def deploy_qa(self, request_id: str) -> Dict[str, Any]:
        """Deploy merged code to QA/staging environment."""
        req = self.store.get_request(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found")

        service_name = req.get('affected_service', 'demo-api')
        service = self.store.get_service(service_name)
        repo_name = service['name'] if service else service_name
        branch = req.get('base_branch', 'main')
        merged_sha = req.get('merged_sha', '')

        # Trigger staging deployment workflow
        # In production: GitHub Actions workflow dispatch with environment=staging
        staging_url = service.get('staging_env', os.getenv('STAGING_ENV_URL')) if service else os.getenv('STAGING_ENV_URL')

        self._trigger_deploy(repo_name, branch, 'staging', merged_sha)

        self.store.update_request(request_id, {
            'status': 'qa_deployed',
            'staging_url': staging_url
        })

        self.store.log_audit(request_id, 'system', 'deployment_agent', 'qa_deploy_triggered', {
            'branch': branch,
            'sha': merged_sha,
            'staging_url': staging_url
        })

        return {
            'request_id': request_id,
            'environment': 'staging',
            'status': 'qa_deployed',
            'url': staging_url
        }

    def deploy_production(self, request_id: str) -> Dict[str, Any]:
        """Deploy approved code to production environment."""
        req = self.store.get_request(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found")

        # Guardrail: must have prod approval
        if not req.get('prod_approved_at'):
            raise PermissionError("Production approval required before deployment")

        service_name = req.get('affected_service', 'demo-api')
        service = self.store.get_service(service_name)
        repo_name = service['name'] if service else service_name
        branch = req.get('base_branch', 'main')
        merged_sha = req.get('merged_sha', '')

        production_url = service.get('production_env', os.getenv('PRODUCTION_ENV_URL')) if service else os.getenv('PRODUCTION_ENV_URL')

        self._trigger_deploy(repo_name, branch, 'production', merged_sha)

        self.store.update_request(request_id, {
            'status': 'deployed',
            'production_url': production_url,
            'deploy_timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        })

        self.store.log_audit(request_id, 'system', 'deployment_agent', 'production_deploy_triggered', {
            'branch': branch,
            'sha': merged_sha,
            'production_url': production_url,
            'approved_by': req.get('prod_approver_slack_id')
        })

        return {
            'request_id': request_id,
            'environment': 'production',
            'status': 'deployed',
            'url': production_url
        }

    def _trigger_deploy(self, repo_name: str, branch: str, environment: str, sha: str) -> None:
        """Trigger deployment via GitHub Actions workflow dispatch."""
        print(f"[DEPLOY] Triggering {environment} deploy for {repo_name}@{sha}")
        deploy_workflow = os.getenv('DEPLOY_WORKFLOW_FILENAME', 'deploy.yml')
        self.git.trigger_workflow(repo_name, deploy_workflow, branch, {
            'environment': environment,
            'sha': sha,
        })

    def check_health(self, request_id: str) -> Dict[str, Any]:
        """Run post-deploy health checks."""
        req = self.store.get_request(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found")

        url = req.get('production_url') or req.get('staging_url')
        if not url:
            return {'status': 'unknown', 'url': None}

        # Simple HTTP smoke test
        try:
            import requests
            resp = requests.get(url, timeout=30)
            healthy = resp.status_code < 500
            self.store.log_audit(request_id, 'system', 'deployment_agent', 'health_check', {
                'url': url,
                'status_code': resp.status_code,
                'healthy': healthy
            })
            return {'status': 'healthy' if healthy else 'unhealthy', 'url': url, 'status_code': resp.status_code}
        except Exception as e:
            self.store.log_audit(request_id, 'system', 'deployment_agent', 'health_check_failed', {
                'url': url,
                'error': str(e)
            })
            return {'status': 'error', 'url': url, 'error': str(e)}


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2:
        agent = DeploymentAgent()
        env = sys.argv[2]
        if env == 'qa':
            result = agent.deploy_qa(sys.argv[1])
        elif env == 'production':
            result = agent.deploy_production(sys.argv[1])
        else:
            print(f"Unknown environment: {env}")
            sys.exit(1)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python deployment_agent.py <request_id> <qa|production>")
