from typing import Any, Dict, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from domain.ports.vehicle_workflow_port import VehicleWorkflowPort
from domain.ports.file_storage_port import FileStoragePort
from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from domain.ports.vehicle_card_repository_port import VehicleCardRepositoryPort

from infraestructure.adapters.mcp_insurance_client_adapter import McpInsuranceClientAdapter
from infraestructure.workflows.langgraph.state.cedula_workflow_state import CedulaWorkflowState
from infraestructure.workflows.langgraph.nodes.classify_and_extract_node import ClassifyAndExtractNode
from infraestructure.workflows.langgraph.nodes.finalize_and_save import FinalizeAndSave
from infraestructure.workflows.langgraph.nodes.calculate_quote_mcp_node import CalculateQuoteMcpNode

def quote_router(state: CedulaWorkflowState) -> str:
    if state.get("status") == "READY_FOR_QUOTE":
        return "calculate_quote_mcp"
    return END

class LangGraphVehicleWorkflowAdapter(VehicleWorkflowPort):
    def __init__(
        self,
        storage_port: FileStoragePort,
        extractor_port: VehicleExtractorPort,
        vehicle_repo: VehicleCardRepositoryPort,
        mcp_client: Optional[McpInsuranceClientAdapter] = None,
        checkpointer: Optional[Any] = None,
    ):
        self._storage = storage_port
        self._extractor = extractor_port
        self._repo = vehicle_repo
        self._mcp_client = mcp_client or McpInsuranceClientAdapter()

        classify_node = ClassifyAndExtractNode(self._extractor)
        finalize_node = FinalizeAndSave(self._repo)
        quote_node = CalculateQuoteMcpNode(self._mcp_client)

        workflow = StateGraph(CedulaWorkflowState)
        workflow.add_node("classify_and_extract", classify_node)
        workflow.add_node("finalize_and_save", finalize_node)
        workflow.add_node("calculate_quote_mcp", quote_node)

        workflow.add_edge(START, "classify_and_extract")
        workflow.add_edge("classify_and_extract", "finalize_and_save")
        workflow.add_conditional_edges(
            "finalize_and_save",
            quote_router,
            {
                "calculate_quote_mcp": "calculate_quote_mcp",
                END: END
            }
        )
        workflow.add_edge("calculate_quote_mcp", END)

        self._checkpointer = checkpointer or MemorySaver()
        self._app = workflow.compile(checkpointer=self._checkpointer)

    async def execute_step(
        self,
        session_id: str,
        file_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        file_name: Optional[str] = None,
        year: Optional[int] = None,
        postal_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        input_state: Dict[str, Any] = {"session_id": session_id}

        if file_bytes and file_name:
            file_path = await self._storage.upload(
                file_bytes=file_bytes,
                file_name=file_name,
                content_type=mime_type or "image/jpeg",
            )
            input_state["current_storage_path"] = file_path
            input_state["current_mime_type"] = mime_type
            input_state["current_file_bytes"] = file_bytes

        if year is not None:
            input_state["year"] = int(year)
        if postal_code is not None:
            input_state["postal_code"] = str(postal_code)

        config = {"configurable": {"thread_id": session_id}}
        final_state = await self._app.ainvoke(input_state, config=config)

        res = dict(final_state)
        res.pop("current_file_bytes", None)
        return res