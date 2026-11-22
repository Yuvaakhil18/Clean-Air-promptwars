"""Request and response models for the clean-air assistant."""

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = [
    "AirPlan",
    "AirRequest",
    "AqiScale",
    "CommuteMode",
    "CookingFuel",
    "HomeType",
    "Impact",
    "Tip",
]


def _clean_text(value: str) -> str:
    """Replace control characters with spaces and collapse runs of whitespace."""
    printable = "".join(ch if ch.isprintable() else " " for ch in value)
    return " ".join(printable.split())


class AqiScale(str, Enum):
    US_EPA = "us_epa"
    INDIA_NAQI = "india_naqi"


class HomeType(str, Enum):
    APARTMENT = "apartment"
    HOUSE = "house"


class CookingFuel(str, Enum):
    ELECTRIC = "electric"
    LPG = "lpg"
    BIOMASS = "biomass"


class CommuteMode(str, Enum):
    CAR = "car"
    MOTORBIKE = "motorbike"
    BUS = "bus"
    TRAIN = "train"
    BICYCLE = "bicycle"
    WALK = "walk"
    REMOTE = "remote"


class AirRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location: str = Field(min_length=1, max_length=100)
    pm25: float | None = Field(default=None, ge=0, le=1000, allow_inf_nan=False)
    aqi_scale: AqiScale = AqiScale.US_EPA

    adults: int = Field(default=1, ge=1, le=20)
    children: int = Field(default=0, ge=0, le=20)
    older_adults: int = Field(default=0, ge=0, le=20)
    pregnant: bool = False
    respiratory_condition: bool = False

    home: HomeType = HomeType.APARTMENT
    cooking_fuel: CookingFuel = CookingFuel.LPG
    room_area_m2: float = Field(default=15, ge=5, le=500, allow_inf_nan=False)
    ceiling_height_m: float = Field(default=2.5, ge=2.0, le=5.0, allow_inf_nan=False)
    has_purifier: bool = False
    purifier_cadr_m3h: float | None = Field(default=None, ge=0, le=2000, allow_inf_nan=False)

    commute_mode: CommuteMode = CommuteMode.CAR
    commute_km: float = Field(default=10, ge=0, le=300, allow_inf_nan=False)
    commute_days_per_week: int = Field(default=5, ge=0, le=7)
    outdoor_work: bool = False

    notes: str = Field(default="", max_length=500)

    @field_validator("location")
    @classmethod
    def _location_has_content(cls, value: str) -> str:
        cleaned = _clean_text(value)
        if not cleaned:
            raise ValueError("location must contain visible characters")
        return cleaned

    @field_validator("notes")
    @classmethod
    def _notes_clean(cls, value: str) -> str:
        return _clean_text(value)


@dataclass(frozen=True)
class Tip:
    """Advice item. A dataclass so rule tables can build tips positionally."""

    title: str
    detail: str


class Impact(BaseModel):
    title: str
    estimate: str
    explanation: str
    assumptions: str


class AirPlan(BaseModel):
    location: str
    risk_level: int = Field(ge=0, le=5)
    risk_label: str
    measured: bool
    pm25: float | None
    summary: str
    summary_source: str  # "ai" or "template"
    personal_tips: list[str]
    impacts: list[Impact]
    routines: list[Tip]
    indoor_hacks: list[Tip]
    alternatives: list[Tip]
    warnings: list[str]
    disclaimer: str
