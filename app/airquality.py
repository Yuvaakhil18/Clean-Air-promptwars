"""Turns a PM2.5 reading into a risk level on the chosen AQI scale."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .models import AqiScale

__all__ = ["ESTIMATED_LEVEL", "Assessment", "assess", "classify"]

# Upper bounds (inclusive, µg/m³, 24-hour PM2.5) for each category, level 0 (best) to 5 (worst).
# These are configuration, not hard-coded truth: check them against the current official tables
# (US EPA AQI or India's CPCB NAQI) before relying on them in production.
US_EPA_PM25 = (
    (0, "Good", 9.0),
    (1, "Moderate", 35.4),
    (2, "Unhealthy for sensitive groups", 55.4),
    (3, "Unhealthy", 125.4),
    (4, "Very unhealthy", 225.4),
    (5, "Hazardous", math.inf),
)
INDIA_NAQI_PM25 = (
    (0, "Good", 30.0),
    (1, "Satisfactory", 60.0),
    (2, "Moderate", 90.0),
    (3, "Poor", 120.0),
    (4, "Very poor", 250.0),
    (5, "Severe", math.inf),
)
SCALE_TABLES = {AqiScale.US_EPA: US_EPA_PM25, AqiScale.INDIA_NAQI: INDIA_NAQI_PM25}

# Used when no reading is entered: assume moderate, and say so.
ESTIMATED_LEVEL = 1


@dataclass(frozen=True)
class Assessment:
    level: int
    label: str
    measured: bool
    pm25: float | None


def classify(pm25: float, scale: AqiScale) -> Assessment:
    for level, label, upper in SCALE_TABLES[scale]:
        if pm25 <= upper:
            return Assessment(level=level, label=label, measured=True, pm25=pm25)
    raise ValueError("PM2.5 value outside the table")  # unreachable: last bound is infinite


def assess(pm25: float | None, scale: AqiScale) -> Assessment:
    if pm25 is None:
        return Assessment(level=ESTIMATED_LEVEL, label="Moderate (estimated)", measured=False, pm25=None)
    return classify(pm25, scale)
