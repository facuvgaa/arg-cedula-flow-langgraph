from typing import Dict, Optional
from domain.models.vehicle_card import VehicleCard
from domain.ports.vehicle_card_repository_port import VehicleCardRepositoryPort


class InMemoryVehicleCardRepositoryAdapter(VehicleCardRepositoryPort):

  def __init__(self):
    self._db: Dict[str, VehicleCard] = {}

  async def save(self, vehicle_card: VehicleCard) -> None:
    """Guarda o actualiza la tarjeta en el diccionario usando el dominio/patente como clave."""
    domain_key = vehicle_card.vehicle.domain.upper()
    self._db[domain_key] = vehicle_card

  async def get_by_domain(self, domain_code: str) -> Optional[VehicleCard]:
    """Busca una tarjeta por patente/dominio."""
    return self._db.get(domain_code.upper())