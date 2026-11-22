from app.advice import alternatives_for, indoor_tips_for, is_sensitive, routines_for
from app.models import CookingFuel


def titles(tips):
    return [tip.title for tip in tips]


def test_hazardous_level_says_stay_indoors(make_request):
    assert "Stay indoors and seal the home" in titles(routines_for(make_request(), 5))


def test_children_add_child_specific_tip(make_request):
    req = make_request(children=2)
    assert is_sensitive(req)
    assert "For children" in titles(routines_for(req, 2))


def test_no_sensitive_tip_on_clean_air_days(make_request):
    req = make_request(children=2)
    assert "For children" not in titles(routines_for(req, 0))


def test_biomass_cooking_gets_ventilation_tip(make_request):
    req = make_request(cooking_fuel=CookingFuel.BIOMASS)
    assert "Ventilate solid-fuel cooking" in titles(indoor_tips_for(req, 2))


def test_purifier_recommended_only_when_air_is_poor_and_none_owned(make_request):
    no_purifier = make_request(has_purifier=False)
    assert "Consider a purifier for your main room" in titles(indoor_tips_for(no_purifier, 3))
    assert "Consider a purifier for your main room" not in titles(indoor_tips_for(no_purifier, 1))


def test_car_commuters_get_transit_alternative(make_request):
    assert "Share rides or take transit" in titles(alternatives_for(make_request(commute_mode="car"), 2))
