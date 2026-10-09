from typing import Any, Dict
from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from infraestructure.workflows.langgraph.state.cedula_workflow_state import CedulaWorkflowState

class ClassifyAndExtractNode:
    def __init__(self, extractor_port: VehicleExtractorPort):
        self._extractor = extractor_port

    async def __call__(self, state: CedulaWorkflowState) -> dict[str, Any]:
        image_bytes = state.get("current_file_bytes")
        if not image_bytes:
            return {}

        mime_type = state.get("current_mime_type") or "image/jpeg"
        storage_path = state.get("current_storage_path") or ""

        extracted = await self._extractor.extract_from_image(
            image_bytes=image_bytes,
            mime_type=mime_type,
            file_storage_path=storage_path,
        )

        updates: Dict[str, Any] = {}
        v_data = extracted.get("vehicle")
        o_data = extracted.get("owner")

        if v_data:
            updates["vehicle_data"] = v_data
            updates["front_storage_path"] = storage_path

        if o_data:
            updates["owner_data"] = o_data
            updates["back_storage_path"] = storage_path

        existing_vehicle = updates.get("vehicle_data") or state.get("vehicle_data")
        existing_owner = updates.get("owner_data") or state.get("owner_data")

        if existing_vehicle and existing_owner:
            updates["status"] = "READY_TO_FINALIZE"
            updates["message"] = "Ambos lados de la cédula fueron procesados con éxito."
        elif existing_vehicle:
            updates["status"] = "WAITING_BACK"
            updates["message"] = "Frente procesado. Por favor envíe el dorso de la cédula."
        elif existing_owner:
            updates["status"] = "WAITING_FRONT"
            updates["message"] = "Dorso procesado. Por favor envíe el frente de la cédula."
        else:
            updates["status"] = "ERROR"
            updates["message"] = "No se pudieron extraer datos válidos de la imagen."

        return updates