from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class TelemetryEvent(BaseModel):
    event_id: str
    vin: str = Field(min_length=11, max_length=17)
    vehicle_model: Literal["Model S", "Model 3", "Model X", "Model Y", "Cybertruck"]
    event_ts: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    speed_mph: float = Field(ge=0, le=180)
    battery_pct: float = Field(ge=0, le=100)
    odometer_miles: float = Field(ge=0)
    power_kw: float
    charging_state: Literal["charging", "driving", "parked", "idle"]
    tire_pressure_fl: float = Field(ge=20, le=60)
    tire_pressure_fr: float = Field(ge=20, le=60)
    tire_pressure_rl: float = Field(ge=20, le=60)
    tire_pressure_rr: float = Field(ge=20, le=60)
    outside_temp_f: float = Field(ge=-60, le=140)

    @field_validator("vin")
    @classmethod
    def vin_must_be_uppercase(cls, value: str) -> str:
        return value.upper()

