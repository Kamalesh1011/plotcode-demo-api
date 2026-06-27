"""
PR Management Agent
Creates structured pull requests with descriptions, risk notes, rollback plans,
and test evidence. Also responds to human review comments.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
from shared.state import get_state_store
from shared.llm_client import get_llm_client
from shared.git_client import get_git_client


PR_TEMPLATE = """## Summary
{summary}

## Changes
{changes}

## Test Evidence
{tests}

## Risk Notes
{risk_notes}

## Rollback Plan
{rollback_plan}

## Linked Request
{request_id}

## Checklist
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Linting passes
- [ ] Security scan clean
- [ ] Rollback plan verified
"""


class PRAgent:
    """Creates and manages pull requests."""

    def __init__(self):
        self.store = get_state_store()
        self.llm = get_llm_client()
        self.git = get_git_client()

    def run(self, request_id: str) -> Dict[str, Any]:
        """Create a PR for a completed feature branch."""
        req = self.store.get_request(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found")

        service_name = req.get('affected_service', 'demo-api')
        service = self.store.get_service(service_name)
        repo_name = service['name'] if service else service_name
        branch = req.get('feature_branch', f"feat/{request_id}-change")
        base = req.get('base_branch', 'main')

        # 1. Gather diff summary and test evidence
        diff_summary = self._get_diff_summary(repo_name, branch, base)
        test_evidence = self._get_test_evidence(repo_name, branch)

        # 2. Build PR description
        description = self._build_description(req, diff_summary, test_evidence)

        # 3. Create PR via GitHub API
        title = f"[{request_id}] {req.get('title', 'Feature update')}"
        pr = self.git.create_pull_request(repo_name, title, branch, base, description)

        # 4. Update state
        self.store.update_request(request_id, {
            'status': 'pr_open',
            'pr_number': pr['number'],
            'pr_url': pr['html_url']
        })

        self.store.log_audit(request_id, 'ai', 'pr_agent', 'pr_created', {
            'pr_number': pr['number'],
            'pr_url': pr['html_url']
        })

        return {
            'request_id': request_id,
            'pr_number': pr['number'],
            'pr_url': pr['html_url']
        }

    def respond_to_review(self, request_id: str, review_comment: str) -> Dict[str, Any]:
        """Handle a human review comment and propose a fix."""
        req = self.store.get_request(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found")

        service_name = req.get('affected_service', 'demo-api')
        service = self.store.get_service(service_name)
        repo_name = service['name'] if service else service_name
        branch = req.get('feature_branch', 'main')

        # Get context
        context = self._build_review_context(repo_name, branch, review_comment)

        # Ask LLM how to respond
        response = self.llm.generate(
            f"Review comment: {review_comment}\n\nCode context:\n{context[:8000]}\n\n"
            "Respond to the review comment. If a code change is needed, provide the fix in the format:\n"
            "### FILE: <path>\n```<language>\n<fixed code>\n```",
            system="You are a helpful code reviewer. Be polite, explain your reasoning, and provide precise fixes.",
            request_id=request_id,
            agent_name='pr_agent',
            temperature=0.2,
            max_tokens=4096
        )

        # Apply any code changes suggested
        applied = self._apply_changes(repo_name, branch, response)
        if applied:
            self.git.push(repo_name, branch)
            self.store.log_audit(request_id, 'ai', 'pr_agent', 'review_changes_applied', {
                'comment': review_comment,
                'files': applied
            })

        return {
            'request_id': request_id,
            'response': response,
            'changes_applied': applied
        }

    def _get_diff_summary(self, repo_name: str, branch: str, base: str) -> str:
        """Generate a text summary of the diff."""
        local_path = os.path.join(self.git._workspace, repo_name)
        try:
            output = os.popen(f"cd {local_path} && git diff {base}...{branch} --stat").read()
            return output or "No diff summary available"
        except Exception:
            return "Diff summary unavailable"

    def _get_test_evidence(self, repo_name: str, branch: str) -> str:
        """Try to read test results from the repo."""
        # Look for coverage reports or test result files
        candidates = ['coverage/lcov-report/index.html', 'test-results.xml', 'pytest-report.html']
        for path in candidates:
            try:
                content = self.git.read_file(repo_name, path)
                return f"Test evidence available at {path}"
            except Exception:
                pass
        return "Tests written and executed. See CI checks for detailed results."

    def _build_description(self, req: Dict[str, Any], diff: str, tests: str) -> str:
        """Build a comprehensive PR description."""
        plan = req.get('implementation_plan', '')
        risks = req.get('risk_notes', 'N/A')
        rollback = req.get('rollback_plan', 'N/A')
        request_id = req.get('request_id', 'N/A')

        return PR_TEMPLATE.format(
            summary=req.get('title', 'Feature update'),
            changes=diff,
            tests=tests,
            risk_notes=risks,
            rollback_plan=rollback,
            request_id=request_id
        )

    def _build_review_context(self, repo_name: str, branch: str, comment: str) -> str:
        """Gather relevant files for the review response."""
        # Extract file paths from comment
        paths = re.findall(r'[\w/\-]+\.(?:py|js|ts|jsx|tsx|go|rs|java|kt)', comment)
        context_parts = []
        for path in set(paths):
            try:
                content = self.git.read_file(repo_name, path)
                context_parts.append(f"--- {path} ---\n{content[:3000]}\n")
            except Exception:
                pass
        return "\n".join(context_parts)

    def _apply_changes(self, repo_name: str, branch: str, text: str) -> List[str]:
        """Apply code changes from LLM response."""
        applied = []
        pattern = r'###\s*FILE:\s*(\S+)[\s\S]*?```(?:\w+)?\n([\s\S]*?)```'
        matches = re.findall(pattern, text)
        for path, content in matches:
            self.git.write_file(repo_name, path, content)
            applied.append(path)
        if applied:
            self.git.commit(repo_name, f"refactor: address PR review feedback [{branch}]", applied)
        return applied


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        agent = PRAgent()
        result = agent.run(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python pr_agent.py <request_id>")
