from abc import ABC, abstractmethod


class VehicleWorkflowPort(ABC):
    @abstractmethod
    async def execute_step(self,session_id: str,file_bytes: bytes,mime_type: str, file_name: str)-> dict[str, any]:
        """Procesa una imagen dentro de la sesión y retorna el estado actual del trámite."""
        "Processes an image within the session and returns the current status of the process."
        pass