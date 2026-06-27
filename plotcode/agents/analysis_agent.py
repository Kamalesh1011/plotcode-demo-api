"""
Planning & Analysis Agent (v2)
Clones the target repository, performs static analysis, and generates a
detailed Markdown implementation plan with risk assessment and rollback plan.

Enhancements:
  - AI confidence scoring (0–100)
  - Prompt versioning (stored in ai_prompt_log)
  - EventBus publishing for real-time dashboard updates
"""

import os
import json
import hashlib
from typing import Dict, Any, List, Optional
from shared.state import get_state_store
from shared.llm_client import get_llm_client
from shared.git_client import get_git_client
from shared.events import get_event_bus, EventTypes

# Prompt version — bump when SYSTEM_PROMPT changes
PROMPT_VERSION = "analysis-v2.0"


SYSTEM_PROMPT = """You are an expert software architect and senior developer. Your task is to analyze a feature request and a codebase, then produce a detailed implementation plan.

Your output must be a structured Markdown document with these sections:
1. **Summary** — One-line summary of the change
2. **Impacted Files** — List of files to modify/create with brief rationale
3. **Implementation Plan** — Step-by-step changes for each file
4. **Test Plan** — Unit tests and integration tests to write
5. **Risk Assessment** — Breaking changes, dependencies, performance concerns
6. **Rollback Plan** — How to undo this change (git revert, feature flags, etc.)
7. **Config Changes** — Any env vars, secrets, or infra changes needed
8. **Confidence Score** — End your response with a line: `CONFIDENCE: <0-100>` reflecting how complete and accurate this plan is.

Be specific. Include exact function names, API endpoints, and data structures where possible.
"""


class AnalysisAgent:
    """Analyzes repositories and generates implementation plans."""

    def __init__(self):
        self.store = get_state_store()
        self.llm = get_llm_client()
        self.git = get_git_client()

    def run(self, request_id: str) -> Dict[str, Any]:
        """Execute the full analysis pipeline for a request."""
        req = self.store.get_request(request_id)
        if not req:
            raise ValueError(f"Request {request_id} not found")

        service_name = req.get('affected_service', 'demo-api')
        service = self.store.get_service(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found in registry")

        # 1. Clone repo
        repo_url = service['repo_url']
        repo_name = service['name']
        local_path = self.git.clone_repo(repo_url, repo_name)

        # 2. Build codebase context (key files only)
        context = self._build_context(repo_name, req)

        # 3. Generate implementation plan via LLM
        plan = self._generate_plan(req, context)

        # 4. Parse plan sections
        parsed = self._parse_plan(plan)

        # 5. Extract confidence score from plan
        confidence = self._extract_confidence(plan)

        # 6. Update request in state store
        self.store.update_request(request_id, {
            'status': 'plan_pending_approval',
            'implementation_plan': plan,
            'risk_notes': parsed.get('risks', ''),
            'rollback_plan': parsed.get('rollback', ''),
            'feature_branch': f"feat/{request_id}-{self._slug(req.get('title', 'change'))[:30]}",
            'ai_confidence': confidence,
            'prompt_version': PROMPT_VERSION,
        })

        self.store.log_audit(request_id, 'ai', 'analysis_agent', 'plan_generated', {
            'service': service_name,
            'files_impacted': parsed.get('files', []),
            'confidence': confidence,
            'prompt_version': PROMPT_VERSION,
        })

        # 7. Publish event for dashboard real-time update
        bus = get_event_bus()
        bus.publish_sync(EventTypes.PLAN_GENERATED, {
            'request_id': request_id,
            'confidence': confidence,
            'service': service_name,
        })

        return {
            'request_id': request_id,
            'status': 'plan_pending_approval',
            'plan': plan,
            'parsed': parsed,
            'confidence': confidence,
        }

    def _build_context(self, repo_name: str, req: Dict[str, Any]) -> str:
        """Collect relevant repo files to feed into the LLM."""
        # Read key structural files
        files_to_read = ['README.md', 'package.json', 'requirements.txt', 'pyproject.toml', 'Dockerfile']
        context_parts = []

        for fname in files_to_read:
            try:
                content = self.git.read_file(repo_name, fname)
                context_parts.append(f"--- {fname} ---\n{content[:2000]}\n")
            except Exception:
                pass

        # Try to find relevant source files based on the request
        try:
            all_files = self.git.list_files(repo_name, "")
            # Filter for likely relevant files (simple heuristic)
            keywords = req.get('business_need', '').lower().split() + req.get('expected_behavior', '').lower().split()
            relevant = [f for f in all_files if any(k in f.lower() for k in keywords if len(k) > 3)]
            # Limit to top 10 most relevant
            relevant = relevant[:10]
            for f in relevant:
                try:
                    content = self.git.read_file(repo_name, f)
                    context_parts.append(f"--- {f} ---\n{content[:3000]}\n")
                except Exception:
                    pass
        except Exception:
            pass

        return "\n".join(context_parts)

    def _generate_plan(self, req: Dict[str, Any], context: str) -> str:
        """Call LLM to generate the implementation plan."""
        prompt = f"""Feature Request:
- Title: {req.get('title', 'N/A')}
- Business Need: {req.get('business_need', 'N/A')}
- Expected Behavior: {req.get('expected_behavior', 'N/A')}
- Priority: {req.get('priority', 'P2')}
- Service: {req.get('affected_service', 'N/A')}

Repository Context:
{context[:15000]}

Generate the implementation plan according to the system instructions. End with: CONFIDENCE: <0-100>"""

        # Compute prompt version hash for audit
        prompt_hash = hashlib.sha256(
            (SYSTEM_PROMPT + prompt).encode()
        ).hexdigest()[:12]

        return self.llm.generate(
            prompt,
            system=SYSTEM_PROMPT,
            request_id=req.get('request_id'),
            agent_name='analysis_agent',
            temperature=0.2,
            max_tokens=4096,
            prompt_version=f"{PROMPT_VERSION}-{prompt_hash}",
        )

    def _parse_plan(self, plan: str) -> Dict[str, Any]:
        """Extract key sections from the generated plan."""
        result = {}
        # Simple regex-based extraction
        sections = {
            'risks': r'##?\s*Risk Assessment\s*\n(.*?)(?:##?\s|$)',
            'rollback': r'##?\s*Rollback Plan\s*\n(.*?)(?:##?\s|$)',
            'files': r'##?\s*Impacted Files\s*\n(.*?)(?:##?\s|$)',
        }
        import re
        for key, pattern in sections.items():
            match = re.search(pattern, plan, re.IGNORECASE | re.DOTALL)
            if match:
                result[key] = match.group(1).strip()
        return result

    def _extract_confidence(self, plan: str) -> float:
        """Extract confidence score from the plan text."""
        import re
        match = re.search(r'CONFIDENCE:\s*(\d+)', plan, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            return min(100.0, max(0.0, float(score)))
        return 75.0  # Default if not found

    def _slug(self, text: str) -> str:
        """Convert text to a URL-safe slug."""
        return re.sub(r'[^a-zA-Z0-9]+', '-', text).strip('-').lower()


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        agent = AnalysisAgent()
        result = agent.run(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python analysis_agent.py <request_id>")
