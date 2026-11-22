"""Rule-based routines, indoor air hacks and alternatives, tiered by risk level."""

from __future__ import annotations

from .models import AirRequest, CommuteMode, CookingFuel, Tip

__all__ = ["alternatives_for", "indoor_tips_for", "is_sensitive", "routines_for"]

MAX_ROUTINES = 8
MAX_INDOOR = 8
MAX_ALTERNATIVES = 6

LEVEL_ROUTINES: dict[int, list[Tip]] = {
    0: [
        Tip("Normal routine", "Air quality is good. Outdoor activity is fine, and airing the home is a good idea."),
    ],
    1: [
        Tip("Pick the cleanest hours", "Pollution is often higher in early morning and evening in winter. Check the day's reading before you go out."),
    ],
    2: [
        Tip("Ease up outdoors", "Sensitive groups should limit time outside. Others should keep exercise light and short."),
    ],
    3: [
        Tip("Shorten outings", "Combine errands into one trip. If you must go out, wear a well-fitted N95 or FFP2 mask. Cloth masks filter very little fine particulate."),
    ],
    4: [
        Tip("Stay mostly indoors", "Cancel non-essential outdoor activity and keep children indoors for play. Check school or workplace guidance."),
    ],
    5: [
        Tip("Stay indoors and seal the home", "Keep doors and windows shut, run a purifier continuously, and avoid any outdoor exertion."),
    ],
}


def is_sensitive(req: AirRequest) -> bool:
    """Return *True* when the household includes a vulnerable member."""
    return req.children > 0 or req.older_adults > 0 or req.pregnant or req.respiratory_condition


def _sensitive_tips(req: AirRequest) -> list[Tip]:
    tips: list[Tip] = []
    if req.children > 0:
        tips.append(Tip("For children", "Keep play indoors on high-pollution days. Masks often do not fit young children, so reducing outdoor time matters most."))
    if req.older_adults > 0:
        tips.append(Tip("For older adults", "Check on older neighbours and keep their regular medicines and any rescue inhaler within reach."))
    if req.pregnant:
        tips.append(Tip("During pregnancy", "Discuss exposure concerns with your midwife or doctor, and avoid strenuous outdoor activity on higher-risk days."))
    if req.respiratory_condition:
        tips.append(Tip("Respiratory conditions", "Follow your doctor's action plan and keep rescue medicine close. If breathing worsens, seek medical help promptly."))
    return tips


def routines_for(req: AirRequest, level: int) -> list[Tip]:
    """Return daily-routine tips appropriate for *level* and the household."""
    tips = list(LEVEL_ROUTINES[level])
    if is_sensitive(req) and level >= 1:
        tips.extend(_sensitive_tips(req))
    if req.outdoor_work and level >= 2:
        tips.append(Tip("Outdoor work", "Use a well-fitted respirator, schedule heavy tasks for the cleanest hours, and take breaks indoors."))
    return tips[:MAX_ROUTINES]


def indoor_tips_for(req: AirRequest, level: int) -> list[Tip]:
    """Return indoor-air-quality tips appropriate for *level* and the home setup."""
    tips = [
        Tip("Keep windows closed on bad days", "Open them briefly when the outdoor reading drops, such as after rain or strong wind."),
        Tip("Avoid indoor smoke", "Skip smoking, incense, candles and mosquito coils indoors on high-pollution days. Each adds fine particles."),
        Tip("Clean with a HEPA vacuum", "Dry dusting spreads particles. Use a HEPA-filter vacuum and damp cloths."),
        Tip("Leave outdoor shoes at the door", "Shoes carry road dust and soot into the home."),
    ]
    if req.cooking_fuel == CookingFuel.BIOMASS:
        tips.append(Tip("Ventilate solid-fuel cooking", "Cook where smoke can leave, with a chimney or an open window. Switching to LPG or electric cooking gives the biggest reduction."))
    else:
        tips.append(Tip("Run the kitchen exhaust", "Use the range hood while frying or boiling, and let it run a few minutes after cooking."))
    if req.has_purifier:
        tips.append(Tip("Use the purifier on a higher setting", "Run it at a higher fan speed on bad days, and replace the filter on schedule."))
    elif level >= 3:
        tips.append(Tip("Consider a purifier for your main room", "Choose one with a clean air delivery rate (CADR) sized for the room's area."))
    return tips[:MAX_INDOOR]


def alternatives_for(req: AirRequest, level: int) -> list[Tip]:
    """Return lower-emission alternative suggestions for the household."""
    tips: list[Tip] = []
    if req.commute_mode in (CommuteMode.CAR, CommuteMode.MOTORBIKE):
        tips.append(Tip("Share rides or take transit", "Buses and trains move more people per vehicle, so they emit less per passenger than a solo car trip."))
    if req.commute_mode == CommuteMode.CAR:
        tips.append(Tip("Avoid idling", "Switch the engine off when stopped for more than about a minute."))
    tips.append(Tip("Chain errands into one loop", "Fewer cold starts and fewer trips cut both fuel use and exhaust."))
    tips.append(Tip("Choose cleaner heating", "Electric heaters or heat pumps avoid open fires and solid-fuel heating, which are major winter sources indoors and out."))
    tips.append(Tip("Report open burning", "Burning waste, leaves or crop residue is a major winter source. Report it to your local authority."))
    tips.append(Tip("Share the day's reading", "Post it in your building, school or community group so neighbours can plan."))
    if req.outdoor_work and level >= 2:
        tips.append(Tip("Adjust work timing", "Where possible, move heavy outdoor work to the cleanest hours or to lower-traffic routes."))
    return tips[:MAX_ALTERNATIVES]
