"""Runtime configuration, read from environment variables only.

All settings are read once at startup via :meth:`Settings.from_env` and
remain immutable for the lifetime of the process.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-haiku-5-5"

__all__ = ["DEFAULT_MODEL", "Settings"]


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings.

    ``repr=False`` on the API key keeps it out of logs and tracebacks.
    """

    anthropic_api_key: str | None = field(default=None, repr=False)
    model: str = DEFAULT_MODEL
    request_timeout: float = 15.0

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings from environment variables with validation."""
        raw_key = os.environ.get("ANTHROPIC_API_KEY")
        api_key = raw_key.strip() if raw_key else None
        # Treat blank / whitespace-only keys as absent.
        if api_key is not None and not api_key:
            api_key = None

        try:
            timeout = float(os.environ.get("PLANNER_TIMEOUT_SECONDS", "15"))
        except (ValueError, TypeError):
            logger.warning("Invalid PLANNER_TIMEOUT_SECONDS; defaulting to 15 s.")
            timeout = 15.0

        settings = cls(
            anthropic_api_key=api_key,
            model=os.environ.get("PLANNER_MODEL", DEFAULT_MODEL),
            request_timeout=timeout,
        )
        logger.info(
            "Settings loaded: model=%s, timeout=%.1fs, api_key=%s",
            settings.model,
            settings.request_timeout,
            "configured" if settings.anthropic_api_key else "not set",
        )
        return settings
