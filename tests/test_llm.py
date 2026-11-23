"""Tests for the LLM client abstraction with mocked HTTP."""


import httpx
import pytest

from app.llm import AnthropicTextGenerator


class TestAnthropicTextGenerator:
    """Tests for the AnthropicTextGenerator using httpx mocking."""

    def _mock_response(self, text: str, status_code: int = 200) -> httpx.Response:
        """Build a mock httpx.Response matching the Anthropic messages API."""
        body = {"content": [{"type": "text", "text": text}]}
        return httpx.Response(
            status_code=status_code,
            json=body,
            request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
        )

    def test_generate_returns_text_content(self, monkeypatch):
        """The generator must extract text from the content blocks."""
        gen = AnthropicTextGenerator("sk-test", "claude-haiku-5-5", timeout=5.0)

        def mock_post(*args, **kwargs):
            return self._mock_response("Hello from Claude")

        monkeypatch.setattr(httpx, "post", mock_post)
        result = gen.generate("system prompt", "user prompt")
        assert result == "Hello from Claude"

    def test_generate_concatenates_multiple_blocks(self, monkeypatch):
        """Multiple text blocks should be concatenated."""
        gen = AnthropicTextGenerator("sk-test", "claude-haiku-5-5")

        def mock_post(*args, **kwargs):
            body = {"content": [
                {"type": "text", "text": "Part 1"},
                {"type": "text", "text": " Part 2"},
            ]}
            return httpx.Response(
                status_code=200, json=body,
                request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
            )

        monkeypatch.setattr(httpx, "post", mock_post)
        assert gen.generate("sys", "usr") == "Part 1 Part 2"

    def test_generate_ignores_non_text_blocks(self, monkeypatch):
        """Non-text content blocks must be ignored."""
        gen = AnthropicTextGenerator("sk-test", "claude-haiku-5-5")

        def mock_post(*args, **kwargs):
            body = {"content": [
                {"type": "image", "data": "..."},
                {"type": "text", "text": "Only text"},
            ]}
            return httpx.Response(
                status_code=200, json=body,
                request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
            )

        monkeypatch.setattr(httpx, "post", mock_post)
        assert gen.generate("sys", "usr") == "Only text"

    def test_generate_raises_on_http_error(self, monkeypatch):
        """Non-2xx responses must raise an HTTPStatusError."""
        gen = AnthropicTextGenerator("sk-test", "claude-haiku-5-5")

        def mock_post(*args, **kwargs):
            resp = httpx.Response(
                status_code=500, text="Internal Server Error",
                request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
            )
            return resp

        monkeypatch.setattr(httpx, "post", mock_post)
        with pytest.raises(httpx.HTTPStatusError):
            gen.generate("sys", "usr")

    def test_generate_handles_empty_content(self, monkeypatch):
        """An empty content array should return an empty string."""
        gen = AnthropicTextGenerator("sk-test", "claude-haiku-5-5")

        def mock_post(*args, **kwargs):
            body = {"content": []}
            return httpx.Response(
                status_code=200, json=body,
                request=httpx.Request("POST", "https://api.anthropic.com/v1/messages"),
            )

        monkeypatch.setattr(httpx, "post", mock_post)
        assert gen.generate("sys", "usr") == ""

    def test_repr_shows_model_not_key(self):
        """repr must show the model name but never the API key."""
        gen = AnthropicTextGenerator("sk-secret", "claude-haiku-5-5")
        r = repr(gen)
        assert "claude-haiku-5-5" in r
        assert "sk-secret" not in r

    def test_sends_correct_headers(self, monkeypatch):
        """The request must include the correct Anthropic headers."""
        gen = AnthropicTextGenerator("sk-test-key", "claude-haiku-5-5")
        captured = {}

        def mock_post(url, *, headers=None, **kwargs):
            captured["headers"] = headers
            return self._mock_response("ok")

        monkeypatch.setattr(httpx, "post", mock_post)
        gen.generate("sys", "usr")
        assert captured["headers"]["x-api-key"] == "sk-test-key"
        assert captured["headers"]["anthropic-version"] == "2023-06-01"
        assert captured["headers"]["content-type"] == "application/json"

    @pytest.mark.anyio
    async def test_agenerate_returns_text_content(self, monkeypatch):
        """Asynchronous generation must extract text from content blocks."""
        gen = AnthropicTextGenerator("sk-test", "claude-haiku-5-5", timeout=5.0)

        async def mock_async_post(*args, **kwargs):
            return self._mock_response("Async response")

        monkeypatch.setattr(httpx.AsyncClient, "post", mock_async_post)
        result = await gen.agenerate("system prompt", "user prompt")
        assert result == "Async response"
