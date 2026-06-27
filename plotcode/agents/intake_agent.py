"""
Request Intake Agent
Processes incoming feature requests from secondary channels (e.g., Telegram,
API) and records them in the central tracking system.
Primary Slack intake is handled by the Node.js orchestration layer.
"""

import re
from typing import Dict, Any, Optional
from shared.state import get_state_store
from shared.llm_client import get_llm_client


class IntakeAgent:
    """Validates and records incoming feature requests."""

    def __init__(self):
        self.store = get_state_store()
        self.llm = get_llm_client()

    def process_telegram_request(self, text: str, user_id: str, user_name: str) -> Dict[str, Any]:
        """Parse a Telegram /request message into a structured feature request."""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        title = lines[0] if lines else 'Untitled Request'
        business_need = lines[1] if len(lines) > 1 else title
        expected_behavior = lines[2] if len(lines) > 2 else 'To be defined'
        priority = self._extract_priority(text) or 'P2'
        service = self._extract_service(text)
        team = self._extract_team(text)

        return {
            'title': title,
            'business_need': business_need,
            'expected_behavior': expected_behavior,
            'priority': priority,
            'affected_service': service,
            'requester_name': user_name,
            'requester_telegram_id': user_id,
            'requester_team': team,
            'source': 'telegram'
        }

    def validate_request(self, request_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate a feature request before storing."""
        required = ['business_need', 'expected_behavior', 'requester_name']
        for field in required:
            if not request_data.get(field):
                return False, f"Missing required field: {field}"

        # Check business need isn't too vague
        need = request_data.get('business_need', '')
        if len(need) < 10:
            return False, "Business need is too vague (minimum 10 characters)"

        # Check service exists in registry if provided
        service = request_data.get('affected_service')
        if service:
            svc = self.store.get_service(service)
            if not svc:
                return False, f"Unknown service: {service}. Available services: {self._list_service_names()}"

        return True, None

    def auto_suggest_priority(self, business_need: str, expected_behavior: str) -> str:
        """Use LLM to suggest a priority based on request content."""
        prompt = f"""Analyze this feature request and suggest a priority:
- P0: Critical, production blocking, security issue, major revenue impact
- P1: High, significant user impact, important feature
- P2: Medium, nice to have, minor improvement
- P3: Low, cosmetic, cleanup, documentation

Business Need: {business_need}
Expected Behavior: {expected_behavior}

Respond with ONLY the priority code (P0, P1, P2, or P3)."""

        try:
            result = self.llm.generate(prompt, temperature=0.0, max_tokens=10)
            result = result.strip().upper()
            if result in ['P0', 'P1', 'P2', 'P3']:
                return result
        except Exception:
            pass
        return 'P2'

    def _extract_priority(self, text: str) -> Optional[str]:
        match = re.search(r'\b(P[0-3])\b', text, re.IGNORECASE)
        return match.group(1).upper() if match else None

    def _extract_service(self, text: str) -> Optional[str]:
        match = re.search(r'service[:\s]+(\w+)', text, re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_team(self, text: str) -> Optional[str]:
        match = re.search(r'team[:\s]+(\w+)', text, re.IGNORECASE)
        return match.group(1) if match else None

    def _list_service_names(self) -> str:
        # This would query the service registry; for now return placeholder
        return 'demo-api (and others in registry)'


if __name__ == '__main__':
    # Simple test
    agent = IntakeAgent()
    test_data = agent.process_telegram_request(
        '/request\nUpdate user profile API\nNeed to add email field to user profile\nExpected: PUT /users/{id} accepts email',
        '123456',
        'Test User'
    )
    print(test_data)
    valid, err = agent.validate_request(test_data)
    print('Valid:', valid, 'Error:', err)
