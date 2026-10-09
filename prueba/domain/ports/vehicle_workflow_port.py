from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class VehicleWorkflowPort(ABC):
    @abstractmethod
    async def execute_step(
        self,
        session_id: str,
        file_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        file_name: Optional[str] = None,
        year: Optional[int] = None,
        postal_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Procesa una imagen o datos dentro de la sesión y retorna el estado actual del trámite."""
        pass