from typing import Any, Dict, List
from domain.ports.missing_data_message_port import MissingDataMessagePort
from infraestructure.workflows.state.cedula_workflow_state import CedulaWorkflowState

class RequestMissingDataNode:
    def __init__(self, message_port: MissingDataMessagePort):
        self._message_service = message_port

    async def __call__(self, state: CedulaWorkflowState) -> Dict[str, Any]:
        v_data = state.get("vehicle_data") or {}
        o_data = state.get("owner_data") or {}

        brand = v_data.get("marca") or "Vehículo"
        model = v_data.get("modelo") or ""
        owner_name = o_data.get("nombre_completo") or o_data.get("titular_nombre")
        address = o_data.get("domicilio")
        detected_cp = state.get("postal_code") or o_data.get("codigo_postal")
        year_val = state.get("year") or v_data.get("year")

        missing_fields: List[str] = []
        if not year_val:
            missing_fields.append("Año de fabricación")
        if not detected_cp:
            missing_fields.append("Código postal o ciudad de guarda")

        message_text = await self._message_service.generate_missing_data_message(
            brand=brand,
            model=model,
            owner_name=owner_name,
            address=address,
            detected_cp=detected_cp,
            missing_fields=missing_fields,
        )

        status = "WAITING_YEAR_AND_CP" if (not year_val and not detected_cp) else (
            "WAITING_YEAR" if not year_val else "WAITING_CP"
        )

        return {
            "status": status,
            "message": message_text,
            "postal_code": detected_cp,
            "year": year_val,
        }   
     