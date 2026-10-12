from abc import ABC, abstractmethod
from typing import List, Optional
class MissingDataMessagePort(ABC):
    @abstractmethod
    async def generate_missing_data_message(
        self,
        brand: str,
        model: str,
        owner_name: Optional[str],
        address: Optional[str],
        detected_cp: Optional[str],
        missing_fields: List[str],
    ) -> str:
        """Genera un mensaje cordial solicitando los datos faltantes para cotizar."""
        pass