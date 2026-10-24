from typing import Any, Dict
from infraestructure.adapters.mcp import McpInsuranceClientAdapter
from infraestructure.workflows.state.cedula_workflow_state import CedulaWorkflowState

class AddMailToClientNode:
    """Nodo encargado de emitir la póliza en Spring Boot MCP una vez recopilados los datos de contacto."""
    def __init__(self, mcp_client: McpInsuranceClientAdapter):
        self._mcp_client = mcp_client

    async def __call__(self, state: CedulaWorkflowState) -> Dict[str, Any]:
        email = state.get("customer_email")
        phone = state.get("customer_phone")
        coverage = state.get("selected_coverage")

        if not (email and phone and coverage):
            return {
                "status": "WAITING_CONTACT_DATA",
                "message": "Faltan datos de contacto para completar la emisión de la póliza.",
            }

        v_data = state.get("vehicle_data") or {}
        o_data = state.get("owner_data") or {}
        year = state.get("year") or v_data.get("year") or 2020
        postal_code = state.get("postal_code") or o_data.get("codigo_postal") or "1000"

        try:
            policy = await self._mcp_client.hire_policy(
                customer_name=o_data.get("nombre_completo") or "Cliente",
                customer_dni=o_data.get("documento") or "",
                customer_email=email,
                license_plate=v_data.get("dominio") or "",
                brand=v_data.get("marca") or "",
                model=v_data.get("modelo") or "",
                year=int(year),
                postal_code=str(postal_code),
                coverage_type=str(coverage),
                green_card_url=state.get("front_storage_path") or "",
            )

            return {
                "policy_result": policy,
                "status": "POLICY_ISSUED",
                "message": (
                    f"¡Felicitaciones! Tu póliza N° {policy.get('policyNumber')} fue emitida con éxito.\n"
                    f"Te enviamos la constancia de cobertura a {email} y el comprobante digital a tu WhatsApp ({phone})."
                ),
            }
        except Exception as e:
            return {
                "status": "HIRE_ERROR",
                "message": f"Hubo un inconveniente al emitir la póliza vía MCP: {str(e)}",
            }
