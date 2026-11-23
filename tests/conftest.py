"""Shared test fixtures for the Clean Air Companion test suite."""

from collections.abc import Callable

import pytest

from app.main import limiter
from app.models import AirRequest


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Reset the slowapi rate limiter between tests to prevent 429 collisions."""
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def make_request() -> Callable[..., AirRequest]:
    """Factory for valid AirRequest objects with optional overrides."""

    def _make(**overrides: object) -> AirRequest:
        data: dict[str, object] = {"location": "Test City", "pm25": 40.0}
        data.update(overrides)
        return AirRequest(**data)

    return _make
