"""Tests for runtime configuration loading and validation."""


import pytest

from app.config import DEFAULT_MODEL, Settings


class TestSettingsFromEnv:
    """Verify Settings.from_env() reads and validates environment variables."""

    def test_defaults_when_no_env_vars(self, monkeypatch):
        """With no env vars set, settings should use safe defaults."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("PLANNER_MODEL", raising=False)
        monkeypatch.delenv("PLANNER_TIMEOUT_SECONDS", raising=False)
        settings = Settings.from_env()
        assert settings.anthropic_api_key is None
        assert settings.model == DEFAULT_MODEL
        assert settings.request_timeout == 15.0

    def test_reads_api_key_from_env(self, monkeypatch):
        """A valid API key should be read."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
        settings = Settings.from_env()
        assert settings.anthropic_api_key == "sk-ant-test-key"

    def test_empty_api_key_becomes_none(self, monkeypatch):
        """An empty string key should be treated as absent."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")
        settings = Settings.from_env()
        assert settings.anthropic_api_key is None

    def test_whitespace_only_api_key_becomes_none(self, monkeypatch):
        """A whitespace-only key should be treated as absent."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "   ")
        settings = Settings.from_env()
        assert settings.anthropic_api_key is None

    def test_reads_custom_model(self, monkeypatch):
        monkeypatch.setenv("PLANNER_MODEL", "claude-sonnet-4-5")
        settings = Settings.from_env()
        assert settings.model == "claude-sonnet-4-5"

    def test_reads_custom_timeout(self, monkeypatch):
        monkeypatch.setenv("PLANNER_TIMEOUT_SECONDS", "30")
        settings = Settings.from_env()
        assert settings.request_timeout == 30.0

    def test_invalid_timeout_falls_back_to_default(self, monkeypatch):
        """Non-numeric timeout values should fall back to 15 s without crashing."""
        monkeypatch.setenv("PLANNER_TIMEOUT_SECONDS", "not-a-number")
        settings = Settings.from_env()
        assert settings.request_timeout == 15.0

    def test_api_key_hidden_from_repr(self):
        """The API key must not appear in repr output."""
        settings = Settings(anthropic_api_key="secret-key-123")
        assert "secret-key-123" not in repr(settings)


class TestSettingsFrozen:
    """Settings must be immutable once created."""

    def test_cannot_mutate_settings(self):
        settings = Settings()
        with pytest.raises(AttributeError):
            settings.model = "other"
