"""Transparent estimates of what the user's choices change.

Every number here comes from a formula with stated assumptions, so the
explanation shown to the user can say exactly how it was calculated.
"""

from __future__ import annotations

from .models import CommuteMode

__all__ = [
    "annual_commute_saving_kg",
    "commute_target",
    "indoor_pm25",
    "purifier_reduction",
    "required_cadr",
    "room_volume",
]

# Steady-state room model assumptions.
ROOM_ACH = 0.5          # air changes per hour through a home with closed windows
OPEN_WINDOW_ACH = 2.0   # air changes per hour with windows open
PENETRATION = 0.7       # share of outdoor PM2.5 that gets indoors through the building envelope
TARGET_REDUCTION = 0.8  # reduction used when sizing a purifier

# Approximate kg CO2e per passenger-km. Defaults for illustration; not a lifecycle study.
KG_CO2E_PER_KM = {
    CommuteMode.CAR: 0.17,
    CommuteMode.MOTORBIKE: 0.11,
    CommuteMode.BUS: 0.09,
    CommuteMode.TRAIN: 0.04,
    CommuteMode.BICYCLE: 0.0,
    CommuteMode.WALK: 0.0,
    CommuteMode.REMOTE: 0.0,
}
WORKING_WEEKS = 46


def room_volume(area_m2: float, ceiling_m: float) -> float:
    return area_m2 * ceiling_m


def purifier_reduction(volume_m3: float, cadr_m3h: float, ach: float = ROOM_ACH) -> float:
    """Fraction of indoor PM2.5 removed by a purifier, at steady state.

    The clean-air delivery rate (CADR) divided by room volume gives the filtration rate k
    per hour. Removal share = k / (ACH + k).
    """
    if volume_m3 <= 0 or cadr_m3h <= 0:
        return 0.0
    k = cadr_m3h / volume_m3
    return k / (ach + k)


def required_cadr(volume_m3: float, target: float = TARGET_REDUCTION, ach: float = ROOM_ACH) -> float:
    """CADR (m³/h) needed to reach the target reduction, inverting the formula above."""
    k = target * ach / (1 - target)
    return k * volume_m3


def indoor_pm25(outdoor: float, ach: float, cadr_m3h: float = 0.0, volume_m3: float = 1.0) -> float:
    """Estimated indoor PM2.5 (µg/m³) from outdoor PM2.5, air exchange and filtration."""
    k = cadr_m3h / volume_m3 if volume_m3 > 0 else 0.0
    denominator = ach + k
    if denominator <= 0:
        return 0.0
    return outdoor * PENETRATION * ach / denominator


def commute_target(mode: CommuteMode, level: int, km_one_way: float) -> CommuteMode:
    """Lower-emission option to suggest. Cycling is only suggested on clean-air days,
    because breathing harder outdoors increases the dose of pollution."""
    if mode in (CommuteMode.CAR, CommuteMode.MOTORBIKE):
        if level <= 1 and km_one_way <= 8:
            return CommuteMode.BICYCLE
        return CommuteMode.BUS
    if mode == CommuteMode.BUS:
        return CommuteMode.TRAIN
    return mode


def annual_commute_saving_kg(
    current: CommuteMode, target: CommuteMode, km_one_way: float, days_per_week: int
) -> float:
    diff = KG_CO2E_PER_KM[current] - KG_CO2E_PER_KM[target]
    if diff <= 0 or km_one_way <= 0 or days_per_week <= 0:
        return 0.0
    return diff * km_one_way * 2 * days_per_week * WORKING_WEEKS
