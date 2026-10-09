from typing import Any, Dict
from infraestructure.adapters.mcp_insurance_client_adapter import McpInsuranceClientAdapter
from infraestructure.workflows.langgraph.state.cedula_workflow_state import CedulaWorkflowState

class CalculateQuoteMcpNode:
    def __init__(self, mcp_client: McpInsuranceClientAdapter):
        self._mcp_client = mcp_client

    async def __call__(self, state: CedulaWorkflowState) -> Dict[str, Any]:
        v_data = state.get("vehicle_data") or {}
        brand = v_data.get("marca") or ""
        model = v_data.get("modelo") or ""
        year = state.get("year") or v_data.get("year")
        postal_code = state.get("postal_code")

        if not (brand and model and year and postal_code):
            return {}

        try:
            quote_res = await self._mcp_client.calculate_quote(
                brand=brand,
                model=model,
                year=int(year),
                postal_code=str(postal_code)
            )
            return {
                "quote_result": quote_res,
                "status": "QUOTES_AVAILABLE",
                "message": f"¡Cotizaciones calculadas con éxito para {brand} {model} ({year})!"
            }
        except Exception as e:
            return {
                "status": "QUOTE_ERROR",
                "message": f"Error al consultar el servidor de cotizaciones MCP: {str(e)}"
            }

