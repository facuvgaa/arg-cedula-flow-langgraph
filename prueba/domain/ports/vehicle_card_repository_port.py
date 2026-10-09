from abc import ABC, abstractmethod
from typing import Optional
from domain.models.vehicle_card import VehicleCard


class VehicleCardRepositoryPort(ABC):

  @abstractmethod
  async def save(self, vehicle_card: VehicleCard) -> None:
    """Guarda o actualiza la VehicleCard en la base de datos."""
    pass

  @abstractmethod
  async def get_by_domain(self, domain_code: str) -> Optional[VehicleCard]:
    """Busca una cédula por la patente/dominio del vehículo."""
    pass