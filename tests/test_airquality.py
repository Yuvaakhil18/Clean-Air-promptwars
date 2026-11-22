import math

import pytest

from app.airquality import ESTIMATED_LEVEL, assess, classify
from app.models import AqiScale


@pytest.mark.parametrize(
    "pm25, level",
    [(0, 0), (9.0, 0), (9.1, 1), (35.4, 1), (35.5, 2), (55.4, 2), (55.5, 3), (125.4, 3), (225.5, 5)],
)
def test_us_epa_boundaries(pm25, level):
    assert classify(pm25, AqiScale.US_EPA).level == level


@pytest.mark.parametrize("pm25, level", [(30, 0), (31, 1), (60, 1), (61, 2), (121, 4), (251, 5)])
def test_india_naqi_boundaries(pm25, level):
    assert classify(pm25, AqiScale.INDIA_NAQI).level == level


def test_missing_reading_is_estimated_not_measured():
    result = assess(None, AqiScale.US_EPA)
    assert result.level == ESTIMATED_LEVEL
    assert result.measured is False


def test_measured_reading_is_marked_measured():
    result = assess(60.0, AqiScale.US_EPA)
    assert result.measured is True
    assert result.label == "Unhealthy"
    assert math.isfinite(result.pm25)
