import pytest

from app.models import AirRequest


@pytest.fixture
def make_request():
    """Factory for valid AirRequest objects with optional overrides."""

    def _make(**overrides):
        data = {"location": "Test City", "pm25": 40.0}
        data.update(overrides)
        return AirRequest(**data)

    return _make
