from typing import Any, Dict, Optional
from domain.ports.vehicle_workflow_port import VehicleWorkflowPort


class ProcessVehicleCardUseCase:

    def __init__(self, workflow_port: VehicleWorkflowPort):
        self._workflow_port = workflow_port

    async def execute(
        self,
        session_id: str,
        file_bytes: Optional[bytes] = None,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
        year: Optional[int] = None,
        postal_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await self._workflow_port.execute_step(
            session_id=session_id,
            file_bytes=file_bytes,
            file_name=file_name,
            mime_type=mime_type,
            year=year,
            postal_code=postal_code,
        )