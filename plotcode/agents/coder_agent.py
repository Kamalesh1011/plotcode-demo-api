"""
Code Generation Agent
Creates a feature branch, applies code changes based on an approved
implementation plan, and generates unit tests.
"""

import os
import re
import json
from typing import Dict, Any, List, Optional
from shared.state import get_state_store
from shared.llm_client import get_llm_client
from shared.git_client import get_git_client


SYSTEM_PROMPT = """You are an expert software engineer. You will be given an implementation plan and asked to write code changes.

Rules:
- Follow existing code style and conventions in the repository.
- Include comprehensive unit tests for all new logic.
- Use the project's existing testing framework.
- Write clean, maintainable code with appropriate comments.
- Do not modify unrelated files.
- Prefer small, focused commits.

For each file to change, output in this format:

### FILE: <path>
```<language>
<full file content or diff>
```

If the change is small, output the complete new file content.
If the change is large, output a clear diff-style description.
"""


class CoderAgent:
    """Generates code and tests based on approved plans."""

    def __init__(self):
        self.store = get_state_store()
        self.llm = get_llm_client()
        self.git = get_git_client()

    def run(self, request_id: str) -> Dict[str, Any]:
        """Execute the coding pipeline for a request."""
        req = self.store.get_request(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found")

        service_name = req.get('affected_service', 'demo-api')
        service = self.store.get_service(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found")

        repo_name = service['name']
        branch = req.get('feature_branch', f"feat/{request_id}-change")
        base_branch = req.get('base_branch', 'main')
        plan = req.get('implementation_plan', '')

        # 1. Ensure repo is cloned and up-to-date
        self.git.clone_repo(service['repo_url'], repo_name)

        # 2. Create feature branch
        self.git.create_branch(repo_name, branch, base_branch)

        # 3. Build context from plan and repo files
        context = self._build_coding_context(repo_name, plan)

        # 4. Generate code changes via LLM
        changes = self._generate_changes(req, context)

        # 5. Apply changes to files
        applied_files = self._apply_changes(repo_name, changes)

        # 6. Run linter/formatter if available (best-effort)
        self._run_formatter(repo_name, applied_files)

        # 7. Commit with conventional commit format
        commit_msg = f"feat({service_name}): {req.get('title', 'update')} [{request_id}]"
        commit_sha = self.git.commit(repo_name, commit_msg, applied_files)

        # 8. Push branch
        self.git.push(repo_name, branch)

        # 9. Update state
        self.store.update_request(request_id, {
            'status': 'ci_running',
            'feature_branch': branch
        })

        self.store.log_audit(request_id, 'ai', 'coder_agent', 'code_changes_applied', {
            'branch': branch,
            'commit_sha': commit_sha,
            'files': applied_files
        })

        return {
            'request_id': request_id,
            'branch': branch,
            'commit_sha': commit_sha,
            'files': applied_files
        }

    def _build_coding_context(self, repo_name: str, plan: str) -> str:
        """Gather relevant existing files to guide the LLM."""
        # Extract file paths mentioned in the plan
        file_paths = re.findall(r'###?\s*FILE:\s*(\S+)', plan)
        context_parts = []
        for path in file_paths[:10]:
            try:
                content = self.git.read_file(repo_name, path)
                context_parts.append(f"--- {path} ---\n{content[:4000]}\n")
            except Exception:
                pass
        return "\n".join(context_parts)

    def _generate_changes(self, req: Dict[str, Any], context: str) -> str:
        """Call LLM to generate the actual code changes."""
        prompt = f"""Implementation Plan:
{req.get('implementation_plan', '')}

Existing Code Context:
{context[:15000]}

Write the complete code changes for all files mentioned in the plan. Include tests."""

        return self.llm.generate(
            prompt,
            system=SYSTEM_PROMPT,
            request_id=req.get('request_id'),
            agent_name='coder_agent',
            temperature=0.2,
            max_tokens=4096
        )

    def _apply_changes(self, repo_name: str, changes_text: str) -> List[str]:
        """Parse LLM output and write files to the repo."""
        applied = []
        # Parse ### FILE: path blocks with code fences
        pattern = r'###\s*FILE:\s*(\S+)[\s\S]*?```(?:\w+)?\n([\s\S]*?)```'
        matches = re.findall(pattern, changes_text)
        for path, content in matches:
            self.git.write_file(repo_name, path, content)
            applied.append(path)
        return applied

    def _run_formatter(self, repo_name: str, files: List[str]) -> None:
        """Best-effort auto-formatting."""
        local_path = os.path.join(self.git._workspace, repo_name)
        # Try common formatters
        for cmd in [
            f"cd {local_path} && npx prettier --write {' '.join(files)} 2>/dev/null",
            f"cd {local_path} && black {' '.join(files)} 2>/dev/null",
        ]:
            os.system(cmd)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        agent = CoderAgent()
        result = agent.run(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python coder_agent.py <request_id>")
