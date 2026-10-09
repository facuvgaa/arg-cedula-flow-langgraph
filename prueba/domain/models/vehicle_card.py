from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Union
import uuid

from .car import Car
from .contact_owner import ContactOwner
from .motor_bike import MotorBike
from .owner import Owner

Vehicle = Union[Car, MotorBike]


class CardStatus(str, Enum):
  PROCESSED = 'PROCESSED'
  REQUIRES_REVIEW = 'REQUIRES_REVIEW'


@dataclass(frozen=True)
class VehicleCard:
  vehicle: Optional[Vehicle] = None
  owner: Optional[Owner] = None
  contact: Optional[ContactOwner] = None

  @classmethod
  def create(
      cls,
      file_storage_path: str,
      official_number: str,
      is_original: bool,
      vehicle: Vehicle,
      owner: Optional[Owner] = None,
      contact: Optional[ContactOwner] = None,
  ) -> 'VehicleCard':
    """Método de fábrica para instanciar la entidad con reglas de negocio."""


    status = CardStatus.PROCESSED

    if isinstance(vehicle, MotorBike):
      if not vehicle.motor_number or not vehicle.frame_number:
        status = CardStatus.REQUIRES_REVIEW
    elif isinstance(vehicle, Car):
      if not vehicle.motor_number or not vehicle.chassis_number:
        status = CardStatus.REQUIRES_REVIEW

    return cls(
        id=uuid.uuid4(),
        file_storage_path=file_storage_path,
        official_number=official_number.strip().upper(),
        is_original=is_original,
        status=status,
        created_at=datetime.utcnow(),
        vehicle=vehicle,
        owner=owner,
        contact=contact,
    )