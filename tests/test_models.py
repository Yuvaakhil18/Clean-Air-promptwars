"""Tests for Pydantic request/response models and their validators."""

import pytest

from app.models import (
    AirPlan,
    AirRequest,
    AqiScale,
    CommuteMode,
    CookingFuel,
    HomeType,
    Impact,
    Tip,
    _clean_text,
)

# ---------------------------------------------------------------------------
# _clean_text helper
# ---------------------------------------------------------------------------

class TestCleanText:
    """Unit tests for the input-sanitisation helper."""

    def test_strips_control_characters(self):
        assert _clean_text("hello\x00world") == "hello world"

    def test_collapses_whitespace(self):
        assert _clean_text("  foo   bar  ") == "foo bar"

    def test_preserves_normal_text(self):
        assert _clean_text("New Delhi") == "New Delhi"

    def test_handles_newlines_and_tabs(self):
        assert _clean_text("line1\nline2\ttab") == "line1 line2 tab"

    def test_empty_string(self):
        assert _clean_text("") == ""

    def test_all_control_characters(self):
        assert _clean_text("\x01\x02\x03") == ""


# ---------------------------------------------------------------------------
# AirRequest validation
# ---------------------------------------------------------------------------

class TestAirRequestValidation:
    """Boundary and edge-case tests for the AirRequest model."""

    def test_valid_minimal_request(self):
        req = AirRequest(location="London")
        assert req.location == "London"
        assert req.pm25 is None

    def test_location_whitespace_only_rejected(self):
        with pytest.raises(ValueError, match="visible characters"):
            AirRequest(location="   ")

    def test_location_control_chars_cleaned(self):
        req = AirRequest(location="Del\x00hi")
        assert req.location == "Del hi"

    def test_location_too_long(self):
        with pytest.raises(ValueError):
            AirRequest(location="x" * 101)

    def test_location_empty_rejected(self):
        with pytest.raises(ValueError):
            AirRequest(location="")

    def test_pm25_negative_rejected(self):
        with pytest.raises(ValueError):
            AirRequest(location="A", pm25=-1.0)

    def test_pm25_above_max_rejected(self):
        with pytest.raises(ValueError):
            AirRequest(location="A", pm25=1001.0)

    def test_pm25_nan_rejected(self):
        with pytest.raises(ValueError):
            AirRequest(location="A", pm25=float("nan"))

    def test_pm25_inf_rejected(self):
        with pytest.raises(ValueError):
            AirRequest(location="A", pm25=float("inf"))

    def test_notes_cleaned(self):
        req = AirRequest(location="A", notes="hello\x00world")
        assert req.notes == "hello world"

    def test_notes_too_long(self):
        with pytest.raises(ValueError):
            AirRequest(location="A", notes="x" * 501)

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValueError):
            AirRequest(location="A", is_admin=True)

    def test_adults_minimum(self):
        with pytest.raises(ValueError):
            AirRequest(location="A", adults=0)

    def test_children_max(self):
        req = AirRequest(location="A", children=20)
        assert req.children == 20

    def test_children_above_max_rejected(self):
        with pytest.raises(ValueError):
            AirRequest(location="A", children=21)

    def test_commute_km_max(self):
        req = AirRequest(location="A", commute_km=300)
        assert req.commute_km == 300

    def test_commute_km_above_max_rejected(self):
        with pytest.raises(ValueError):
            AirRequest(location="A", commute_km=301)

    def test_ceiling_height_boundaries(self):
        AirRequest(location="A", ceiling_height_m=2.0)
        AirRequest(location="A", ceiling_height_m=5.0)
        with pytest.raises(ValueError):
            AirRequest(location="A", ceiling_height_m=1.9)
        with pytest.raises(ValueError):
            AirRequest(location="A", ceiling_height_m=5.1)

    def test_all_enum_values_accepted(self):
        for scale in AqiScale:
            AirRequest(location="A", aqi_scale=scale)
        for home in HomeType:
            AirRequest(location="A", home=home)
        for fuel in CookingFuel:
            AirRequest(location="A", cooking_fuel=fuel)
        for mode in CommuteMode:
            AirRequest(location="A", commute_mode=mode)


# ---------------------------------------------------------------------------
# Tip dataclass
# ---------------------------------------------------------------------------

class TestTip:
    def test_construction(self):
        tip = Tip(title="Mask up", detail="Wear N95 on bad days")
        assert tip.title == "Mask up"
        assert tip.detail == "Wear N95 on bad days"


# ---------------------------------------------------------------------------
# Impact / AirPlan models
# ---------------------------------------------------------------------------

class TestResponseModels:
    def test_impact_construction(self):
        impact = Impact(title="T", estimate="E", explanation="X", assumptions="A")
        assert impact.title == "T"

    def test_air_plan_risk_level_bounds(self):
        with pytest.raises(ValueError):
            AirPlan(
                location="A", risk_level=-1, risk_label="x", measured=True,
                pm25=1.0, summary="s", summary_source="template",
                personal_tips=[], impacts=[], routines=[], indoor_hacks=[],
                alternatives=[], warnings=[], disclaimer="d",
            )
        with pytest.raises(ValueError):
            AirPlan(
                location="A", risk_level=6, risk_label="x", measured=True,
                pm25=1.0, summary="s", summary_source="template",
                personal_tips=[], impacts=[], routines=[], indoor_hacks=[],
                alternatives=[], warnings=[], disclaimer="d",
            )
