"""Combines risk assessment, impact estimates, advice and warnings into one plan.

The decision rules live here. Each one reads the household and home context and
decides what the user should be warned about and which impacts to explain.
"""

from __future__ import annotations

from datetime import date

from .advice import alternatives_for, indoor_tips_for, routines_for
from .airquality import Assessment, assess
from .impact import (
    OPEN_WINDOW_ACH,
    ROOM_ACH,
    annual_commute_saving_kg,
    commute_target,
    indoor_pm25,
    purifier_reduction,
    required_cadr,
    room_volume,
)
from .llm import TextGenerator
from .models import AirPlan, AirRequest, CommuteMode, CookingFuel, Impact
from .narrative import summarise

__all__ = ["build_plan"]

WINTER_MONTHS = {11, 12, 1, 2}
DISCLAIMER = (
    "General guidance, not medical advice. Check your national or local air-quality agency "
    "for official alerts, and speak to a doctor about any health condition."
)
MODE_NAMES = {
    CommuteMode.CAR: "car",
    CommuteMode.MOTORBIKE: "motorbike",
    CommuteMode.BUS: "bus",
    CommuteMode.TRAIN: "train",
    CommuteMode.BICYCLE: "bicycle",
    CommuteMode.WALK: "walking",
    CommuteMode.REMOTE: "working from home",
}


def purifier_impact(req: AirRequest, assessment: Assessment, volume: float) -> Impact:
    """Build an :class:`Impact` card for the user's air-purifier situation."""
    if req.has_purifier and req.purifier_cadr_m3h:
        cadr = req.purifier_cadr_m3h
        reduction = purifier_reduction(volume, cadr)
        turnovers = cadr / volume
        explanation = (
            f"Your purifier's rated delivery rate filters this room's air about {turnovers:.1f} times "
            "an hour, on top of normal air exchange, so PM2.5 that gets in is removed faster."
        )
        if assessment.pm25 is not None:
            closed = indoor_pm25(assessment.pm25, ROOM_ACH, cadr, volume)
            opened = indoor_pm25(assessment.pm25, OPEN_WINDOW_ACH, cadr, volume)
            explanation += (
                f" With outdoor PM2.5 at {assessment.pm25:.0f} µg/m³, indoor levels would be about "
                f"{closed:.0f} µg/m³ with windows closed and about {opened:.0f} µg/m³ with windows open. "
                "Keeping windows closed on bad days amplifies the purifier's effect."
            )
        return Impact(
            title="Your air purifier",
            estimate=f"About {reduction:.0%} less PM2.5 in the room at steady state",
            explanation=explanation,
            assumptions=f"Room volume {volume:.0f} m³, purifier {cadr:.0f} m³/h, {ROOM_ACH} air changes per hour.",
        )

    cadr = required_cadr(volume)
    explanation = (
        "A purifier sized for this room would remove most of the fine particles that enter through "
        "doors, windows and gaps, which matters most on high-pollution days."
    )
    if assessment.pm25 is not None:
        without = indoor_pm25(assessment.pm25, ROOM_ACH, 0.0, volume)
        explanation += f" Without one, indoor PM2.5 would be about {without:.0f} µg/m³ when outdoors is {assessment.pm25:.0f} µg/m³."
    return Impact(
        title="Adding an air purifier",
        estimate=f"A unit rated about {cadr:.0f} m³/h would cut indoor PM2.5 by about 80%",
        explanation=explanation,
        assumptions=f"Room volume {volume:.0f} m³ and {ROOM_ACH} air changes per hour, with a steady-state model.",
    )


def commute_impact(req: AirRequest, assessment: Assessment) -> Impact | None:
    """Build an emissions-saving :class:`Impact` for the commute, or *None* if irrelevant."""
    target = commute_target(req.commute_mode, assessment.level, req.commute_km)
    saving = annual_commute_saving_kg(req.commute_mode, target, req.commute_km, req.commute_days_per_week)
    if saving <= 0:
        return None
    return Impact(
        title=f"Commuting by {MODE_NAMES[target]}",
        estimate=f"About {saving:,.0f} kg CO2e less per year",
        explanation=(
            f"Swapping {MODE_NAMES[req.commute_mode]} trips for {MODE_NAMES[target]} trips on "
            f"{req.commute_days_per_week} days a week cuts emissions per passenger-kilometre. "
            "Fewer vehicle trips also means less exhaust on the roads you and your neighbours use."
        ),
        assumptions=f"{req.commute_km:g} km each way, 46 working weeks, approximate per-passenger factors.",
    )


def impacts_for(req: AirRequest, assessment: Assessment) -> list[Impact]:
    """Collect all relevant impact cards for this household and air quality."""
    volume = room_volume(req.room_area_m2, req.ceiling_height_m)
    impacts = [purifier_impact(req, assessment, volume)]

    commute = commute_impact(req, assessment)
    if commute:
        impacts.append(commute)

    if req.cooking_fuel == CookingFuel.BIOMASS:
        impacts.append(
            Impact(
                title="Cooking with solid fuel",
                estimate="A major source of indoor PM2.5 wherever it is used",
                explanation=(
                    "Smoke from solid-fuel cooking stays indoors unless it is vented. Switching to LPG "
                    "or electric cooking, and venting smoke while cooking, lowers household exposure."
                ),
                assumptions="Qualitative: no numeric estimate is made.",
            )
        )

    if assessment.level >= 2:
        impacts.append(
            Impact(
                title="Exercise and outdoor work",
                estimate="Breathing harder draws more pollution into the lungs",
                explanation=(
                    "Higher breathing rates increase the amount of PM2.5 that each hour of activity "
                    "delivers. Moving heavy activity to cleaner hours or indoors has a direct effect."
                ),
                assumptions="Qualitative: no numeric estimate is made.",
            )
        )
    return impacts


def warnings_for(req: AirRequest, assessment: Assessment, today: date) -> list[str]:
    """Generate contextual warning strings based on conditions and date."""
    warnings: list[str] = []
    if not assessment.measured:
        warnings.append(
            "No PM2.5 reading was entered, so this is a general estimate. Enter a reading from "
            "your local monitor or agency for tailored guidance."
        )
    if today.month in WINTER_MONTHS:
        warnings.append(
            "Winter is often the high-smog season in many cities, because heating, traffic and "
            "cold, still air can trap pollution near the ground."
        )
    if assessment.level >= 4:
        warnings.append("Pollution is very high. Avoid outdoor exertion and follow local authority guidance.")
    if req.respiratory_condition and assessment.level >= 3:
        warnings.append(
            "A household member has a respiratory condition. Keep prescribed medicines close and follow "
            "the doctor's action plan. Seek urgent help if breathing becomes severely difficult."
        )
    return warnings


def build_plan(req: AirRequest, today: date, generator: TextGenerator | None = None) -> AirPlan:
    """Orchestrate assessment, narrative, impacts, advice and warnings into a plan."""
    assessment = assess(req.pm25, req.aqi_scale)
    summary, personal_tips, summary_source = summarise(req, assessment, generator)

    return AirPlan(
        location=req.location,
        risk_level=assessment.level,
        risk_label=assessment.label,
        measured=assessment.measured,
        pm25=assessment.pm25,
        summary=summary,
        summary_source=summary_source,
        personal_tips=personal_tips,
        impacts=impacts_for(req, assessment),
        routines=routines_for(req, assessment.level),
        indoor_hacks=indoor_tips_for(req, assessment.level),
        alternatives=alternatives_for(req, assessment.level),
        warnings=warnings_for(req, assessment, today),
        disclaimer=DISCLAIMER,
    )
