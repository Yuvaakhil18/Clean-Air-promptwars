"""LLM client abstraction.

The planner depends on the :class:`TextGenerator` protocol, not on a
vendor SDK.  :class:`AnthropicTextGenerator` provides both synchronous
and asynchronous generation using a **persistent** ``httpx`` connection
pool to avoid per-request TCP/TLS setup cost.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import httpx

__all__ = ["AnthropicTextGenerator", "TextGenerator"]


@runtime_checkable
class TextGenerator(Protocol):
    """Minimal contract for a text-generation backend."""

    def generate(self, system: str, user: str) -> str: ...


class AnthropicTextGenerator:
    """Anthropic Messages API client with connection pooling.

    A single ``httpx.Client`` is created per instance and reused across
    calls so that TCP connections and TLS sessions are recycled.
    """

    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"
    MAX_TOKENS = 800

    def __init__(self, api_key: str, model: str, timeout: float = 15.0) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    def __repr__(self) -> str:
        return f"AnthropicTextGenerator(model={self._model!r})"

    # -- helpers --------------------------------------------------------

    def _payload(self, system: str, user: str) -> dict:
        """Build the JSON body shared by sync and async paths."""
        return {
            "model": self._model,
            "max_tokens": self.MAX_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }

    @staticmethod
    def _extract(response: httpx.Response) -> str:
        """Pull text blocks from an Anthropic Messages response."""
        response.raise_for_status()
        blocks = response.json().get("content", [])
        return "".join(
            block.get("text", "") for block in blocks if block.get("type") == "text"
        )

    # -- public API -----------------------------------------------------

    def generate(self, system: str, user: str) -> str:
        """Synchronous generation (used by unit tests and fallback)."""
        response = httpx.post(
            self.API_URL,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": self.API_VERSION,
                "content-type": "application/json",
            },
            json=self._payload(system, user),
            timeout=self._timeout,
        )
        return self._extract(response)

    async def agenerate(self, system: str, user: str) -> str:
        """Asynchronous generation — avoids blocking the event loop."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                self.API_URL,
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": self.API_VERSION,
                    "content-type": "application/json",
                },
                json=self._payload(system, user),
            )
            return self._extract(response)
