from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Car:
    domain: str
    brand: str
    model: str
    vehicle_type: str
    use: str 
    chassis_number: str
    motor_number: str
    expiration_date: str
    year: Optional[int] = None