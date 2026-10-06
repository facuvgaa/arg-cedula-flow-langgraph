from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MotorBike:
    domain: str
    brand: str
    model: str
    vehicle_type: str
    use: str
    frame_number: str
    engine_number: str
    expiration_date: str
    engine_cc: str

