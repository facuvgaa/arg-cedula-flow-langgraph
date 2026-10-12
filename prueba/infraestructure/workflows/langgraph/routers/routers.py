from infraestructure.workflows.langgraph.state.cedula_workflow_state import CedulaWorkflowState

def route_next_step(state: CedulaWorkflowState) -> str:
    """Determina si el grafo debe continuar al guardado o frenar."""
    vehicle = state.get("vehicle_data")
    owner = state.get("owner_data")

    if vehicle and owner:
        return "finalize"
    return "wait"

def quote_router(state: CedulaWorkflowState)-> str:
    status = status.get(status)

    if status == "READY_FOR_QUOTE":
        return "calculate_quote_mcp"

    elif status in ("WAITING_YEAR", "WAITING_CP", "WAITING_YEAR_AND_CP"):
        return "request_missing_data"

    return 'END'

def negotiation_router(state: CedulaWorkflowState) -> str:
    status = state.get("status")
    if status == "READY_TO_HIRE":
        return "add_mail_to_client"
    return "END"