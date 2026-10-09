from typing import Any, Dict
from infraestructure.workflows.langgraph.cedula_workflow_state import CedulaWorkflowState

def route_next_step(state: CedulaWorkflowState) -> str:
    """Determina si el grafo debe continuar al guardado o frenar."""
    vehicle = state.get("vehicle_data")
    owner = state.get("owner_data")

    if vehicle and owner:
        return "finalize"
    return "wait"