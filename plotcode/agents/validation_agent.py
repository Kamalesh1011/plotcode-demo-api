"""
Validation & Remediation Agent (Loop Engineer)
Monitors CI status, reads failure logs, diagnoses issues, and proposes fixes.
Retries up to a configurable limit before escalating to human.
"""

import os
import re
import json
import time
from typing import Dict, Any, List, Optional
from shared.state import get_state_store
from shared.llm_client import get_llm_client
from shared.git_client import get_git_client


SYSTEM_PROMPT = """You are a CI/CD debugging expert. You will be given CI failure logs and the codebase.
Your task is to diagnose the root cause and propose a precise fix.

Rules:
- Analyze the error logs carefully. Identify the file and line causing the failure.
- Propose minimal, targeted changes to fix the issue.
- Do not change unrelated code.
- If the fix requires adding a dependency, specify it exactly.
- Output in the same format as the Coder Agent: ### FILE: path with code blocks.

If you cannot determine the cause, state that clearly and explain what additional information would help."""


class ValidationAgent:
    """Monitors CI and attempts self-healing on failures."""

    def __init__(self):
        self.store = get_state_store()
        self.llm = get_llm_client()
        self.git = get_git_client()
        self.max_retries = int(os.getenv('CI_MAX_RETRY', '3'))

    def run(self, request_id: str, ci_logs: Optional[str] = None) -> Dict[str, Any]:
        """Process CI failure and attempt self-healing."""
        req = self.store.get_request(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found")

        service_name = req.get('affected_service', 'demo-api')
        service = self.store.get_service(service_name)
        repo_name = service['name'] if service else service_name
        branch = req.get('feature_branch', 'main')

        # Get retry count from audit log
        retries = self._count_retries(request_id)
        if retries >= self.max_retries:
            self._escalate(request_id, f"Exceeded max retry limit ({self.max_retries})")
            return {'status': 'escalated', 'reason': 'max_retries_exceeded'}

        # 1. Read CI logs (if not provided, try to fetch from GitHub)
        logs = ci_logs or self._fetch_ci_logs(repo_name, branch)

        # 2. Read relevant source files
        context = self._build_context(repo_name, logs)

        # 3. Ask LLM to diagnose and fix
        fix = self._generate_fix(req, logs, context)

        # 4. Apply fix and commit
        applied_files = self._apply_fix(repo_name, branch, fix, request_id)

        if not applied_files:
            self._escalate(request_id, "AI could not generate a fix")
            return {'status': 'escalated', 'reason': 'no_fix_generated'}

        # 5. Push and re-trigger CI
        self.git.push(repo_name, branch)
        self._trigger_ci(repo_name, branch)

        self.store.log_audit(request_id, 'ai', 'validation_agent', 'fix_applied', {
            'retry_count': retries + 1,
            'files': applied_files,
            'log_snippet': logs[:500]
        })

        self.store.update_request(request_id, {'status': 'ci_running'})

        return {
            'request_id': request_id,
            'status': 'ci_running',
            'retry_count': retries + 1,
            'files': applied_files
        }

    def _count_retries(self, request_id: str) -> int:
        """Count how many self-heal attempts have been made."""
        logs = self.store.get_audit_log(request_id)
        return sum(1 for log in logs if log.get("action") == "fix_applied")

    def _fetch_ci_logs(self, repo_name: str, branch: str) -> str:
        """
        Fetch latest CI check run logs via GitHub Checks API.
        Uses GitClient.get_failed_check_logs() which:
          1. Gets the latest commit SHA for the branch
          2. Lists check runs for that SHA
          3. Filters to failed/cancelled runs
          4. Fetches annotations (file:line + error messages) for each
        Returns a formatted log string suitable for LLM diagnosis.
        """
        try:
            logs = self.git.get_failed_check_logs(repo_name, branch)
            if not logs:
                # Empty string means all checks passed — shouldn't reach here
                # in a failure scenario, but handle gracefully
                return f"No failed CI checks found for {repo_name}@{branch}. " \
                       f"The branch may have passed CI or checks are still running."
            return logs
        except Exception as e:
            return f"Failed to fetch CI logs via GitHub Checks API: {e}. " \
                   f"Check GITHUB_TOKEN and GITHUB_ORG configuration."

    def _build_context(self, repo_name: str, logs: str) -> str:
        """Gather relevant files based on error log mentions."""
        # Extract file paths from logs
        paths = re.findall(r'(?:File\s+"|\s)([\w/\-]+\.(?:py|js|ts|jsx|tsx|go|rs|java|kt|swift))', logs)
        context_parts = []
        for path in set(paths[:5]):
            try:
                content = self.git.read_file(repo_name, path)
                context_parts.append(f"--- {path} ---\n{content[:3000]}\n")
            except Exception:
                pass
        return "\n".join(context_parts)

    def _generate_fix(self, req: Dict[str, Any], logs: str, context: str) -> str:
        """Call LLM to diagnose and fix the CI failure."""
        prompt = f"""CI Failure Logs:
{logs[:8000]}

Relevant Code:
{context[:8000]}

Request Context: {req.get('business_need', 'N/A')}

Diagnose the failure and propose the fix. Output in the format:
### FILE: <path>
```<language>
<corrected code>
```"""

        return self.llm.generate(
            prompt,
            system=SYSTEM_PROMPT,
            request_id=req.get('request_id'),
            agent_name='validation_agent',
            temperature=0.2,
            max_tokens=4096
        )

    def _apply_fix(self, repo_name: str, branch: str, fix_text: str, request_id: str) -> List[str]:
        """Checkout branch and apply the fix."""
        local_path = os.path.join(self.git._workspace, repo_name)
        # Ensure correct branch
        # (GitClient would handle this via its methods)
        applied = []
        pattern = r'###\s*FILE:\s*(\S+)[\s\S]*?```(?:\w+)?\n([\s\S]*?)```'
        matches = re.findall(pattern, fix_text)
        for path, content in matches:
            self.git.write_file(repo_name, path, content)
            applied.append(path)
        if applied:
            self.git.commit(repo_name, f"fix: resolve CI failure [{request_id}]", applied)
        return applied

    def _trigger_ci(self, repo_name: str, branch: str) -> None:
        """Re-trigger CI pipeline via GitHub Actions workflow dispatch."""
        ci_workflow = os.getenv('CI_WORKFLOW_FILENAME', 'ci.yml')
        self.git.trigger_workflow(repo_name, ci_workflow, branch)

    def _escalate(self, request_id: str, reason: str) -> None:
        """Escalate to human after max retries or unfixable issue."""
        self.store.update_request(request_id, {
            'status': 'ci_failed',
            'risk_notes': f"Escalated: {reason}"
        })
        self.store.log_audit(request_id, 'ai', 'validation_agent', 'escalated', {
            'reason': reason
        })


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        agent = ValidationAgent()
        logs = sys.argv[2] if len(sys.argv) > 2 else None
        result = agent.run(sys.argv[1], logs)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python validation_agent.py <request_id> [ci_logs_file]")
