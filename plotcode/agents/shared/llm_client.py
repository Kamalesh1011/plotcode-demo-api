"""
LLM client wrapper supporting OpenRouter (primary) and NVIDIA NIM (fallback).
Handles retries, token counting, and prompt logging.
"""

import os
import time
import json
from typing import Optional, List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

from .state import get_state_store

load_dotenv()


class LLMClient:
    """Unified LLM client with automatic logging and fallback."""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = provider or os.getenv("DEFAULT_LLM_PROVIDER", "openrouter")
        self.model = model or os.getenv("DEFAULT_LLM_MODEL", "openai/gpt-4o")
        self._openrouter: Optional[OpenAI] = None
        self._nim: Optional[OpenAI] = None

    def _get_openrouter(self) -> OpenAI:
        if self._openrouter is None:
            key = os.getenv("OPENROUTER_API_KEY")
            if not key:
                raise ValueError("OPENROUTER_API_KEY not set — get one at https://openrouter.ai/keys")
            self._openrouter = OpenAI(
                api_key=key,
                base_url="https://openrouter.ai/api/v1"
            )
        return self._openrouter

    def _get_nim(self) -> OpenAI:
        if self._nim is None:
            key = os.getenv("NIM_API_KEY")
            base_url = os.getenv("NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
            if not key:
                raise ValueError("NIM_API_KEY not set")
            self._nim = OpenAI(api_key=key, base_url=base_url)
        return self._nim

    def _get_client(self) -> OpenAI:
        if self.provider == "nim":
            return self._get_nim()
        return self._get_openrouter()

    def chat(self, messages: List[Dict[str, str]], system: Optional[str] = None,
             request_id: Optional[str] = None, agent_name: str = "unknown",
             temperature: float = 0.2, max_tokens: int = 4096,
             prompt_version: Optional[str] = None,
             confidence_score: Optional[float] = None) -> str:
        start = time.time()
        prompt_text = json.dumps(messages)
        response_text = ""
        tokens_input = 0
        tokens_output = 0
        success = True
        error_msg = None

        try:
            client = self._get_client()
            all_messages = ([{"role": "system", "content": system}] if system else []) + messages
            completion = client.chat.completions.create(
                model=self.model,
                messages=all_messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            response_text = completion.choices[0].message.content or ""
            tokens_input = completion.usage.prompt_tokens if completion.usage else 0
            tokens_output = completion.usage.completion_tokens if completion.usage else 0
        except Exception as e:
            success = False
            error_msg = str(e)
            raise
        finally:
            latency = int((time.time() - start) * 1000)
            if request_id:
                try:
                    store = get_state_store()
                    store.log_prompt(
                        request_id=request_id,
                        agent_name=agent_name,
                        model=self.model,
                        prompt=prompt_text,
                        response=response_text,
                        tokens_input=tokens_input,
                        tokens_output=tokens_output,
                        latency_ms=latency,
                        success=success,
                        error_message=error_msg,
                        confidence_score=confidence_score,
                        prompt_version=prompt_version,
                    )
                except Exception:
                    pass  # Don't fail agent work if logging fails

        return response_text

    def generate(self, prompt: str, system: Optional[str] = None,
                 request_id: Optional[str] = None, agent_name: str = "unknown",
                 temperature: float = 0.2, max_tokens: int = 4096,
                 prompt_version: Optional[str] = None,
                 confidence_score: Optional[float] = None) -> str:
        return self.chat(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            request_id=request_id,
            agent_name=agent_name,
            temperature=temperature,
            max_tokens=max_tokens,
            prompt_version=prompt_version,
            confidence_score=confidence_score,
        )


def get_llm_client(provider: Optional[str] = None, model: Optional[str] = None) -> LLMClient:
    return LLMClient(provider=provider, model=model)
