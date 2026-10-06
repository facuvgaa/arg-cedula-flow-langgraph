from abc import ABC, abstractmethod
from domain.models.vehicle_card import Vehicle

class VehicleExtractorPort(ABC):
    @abstractmethod
    async def extract_from_image(self, image_bytes: bytes, mime_type: str) -> Vehicle:
        """Procesa los bytes de la cédula con Gemini, detecta si es auto o moto y retorna la entidad correspondiente (Car o Motorbike)."""
        "Process the ID card bytes with Gemini, detect if it's a car or motorcycle, and return the corresponding entity (Car or Motorbike)."
    pass