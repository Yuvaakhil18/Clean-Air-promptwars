import pytest

from app.impact import (
    OPEN_WINDOW_ACH,
    ROOM_ACH,
    annual_commute_saving_kg,
    commute_target,
    indoor_pm25,
    purifier_reduction,
    required_cadr,
    room_volume,
)
from app.models import CommuteMode


def test_purifier_reduction_matches_formula():
    """Purifier reduction should match the k / (ACH + k) formula."""
    volume = room_volume(20, 2.5)  # 50 m³
    # k = 150 / 50 = 3 per hour; removal share = 3 / (0.5 + 3)
    assert purifier_reduction(volume, 150) == pytest.approx(3 / 3.5)


def test_purifier_reduction_zero_volume_returns_zero():
    """Zero volume should not cause a division error."""
    assert purifier_reduction(0, 150) == 0.0


def test_purifier_reduction_zero_cadr_returns_zero():
    """Zero CADR should mean no filtration."""
    assert purifier_reduction(50, 0) == 0.0


def test_required_cadr_achieves_target_reduction():
    volume = 50.0
    cadr = required_cadr(volume, target=0.8, ach=ROOM_ACH)
    assert purifier_reduction(volume, cadr, ach=ROOM_ACH) == pytest.approx(0.8)


def test_no_filtration_means_penetration_only():
    """With no purifier, indoor PM2.5 should be outdoor × penetration fraction."""
    assert indoor_pm25(100, ROOM_ACH) == pytest.approx(70.0)


def test_indoor_pm25_zero_ach_no_crash():
    """Zero air-change rate should not raise a division error."""
    result = indoor_pm25(100, ach=0, cadr_m3h=0, volume_m3=50)
    assert result == pytest.approx(0.0)


def test_closed_windows_lower_indoor_levels_with_purifier():
    volume, cadr = 50.0, 150.0
    closed = indoor_pm25(100, ROOM_ACH, cadr, volume)
    opened = indoor_pm25(100, OPEN_WINDOW_ACH, cadr, volume)
    assert closed < opened


def test_car_to_bus_saving_matches_hand_calculation():
    saving = annual_commute_saving_kg(CommuteMode.CAR, CommuteMode.BUS, 12, 5)
    assert saving == pytest.approx(441.6)


def test_no_saving_when_target_is_not_lower():
    assert annual_commute_saving_kg(CommuteMode.WALK, CommuteMode.WALK, 5, 5) == 0.0


def test_no_saving_when_zero_days():
    """With zero commute days there should be no saving."""
    assert annual_commute_saving_kg(CommuteMode.CAR, CommuteMode.BUS, 12, 0) == 0.0


def test_no_saving_when_zero_distance():
    """With zero distance there should be no saving."""
    assert annual_commute_saving_kg(CommuteMode.CAR, CommuteMode.BUS, 0, 5) == 0.0


@pytest.mark.parametrize(
    "mode, level, km, expected",
    [
        (CommuteMode.CAR, 1, 5, CommuteMode.BICYCLE),
        (CommuteMode.CAR, 3, 5, CommuteMode.BUS),  # no cycling on bad air days
        (CommuteMode.CAR, 1, 20, CommuteMode.BUS),  # too far to cycle
        (CommuteMode.BUS, 0, 10, CommuteMode.TRAIN),
    ],
)
def test_commute_target_logic(mode, level, km, expected):
    assert commute_target(mode, level, km) == expected
