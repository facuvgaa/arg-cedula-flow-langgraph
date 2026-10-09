from typing import Any, Dict, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from domain.ports.vehicle_workflow_port import VehicleWorkflowPort
from domain.ports.file_storage_port import FileStoragePort
from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from domain.ports.vehicle_card_repository_port import VehicleCardRepositoryPort

from infraestructure.workflows.langgraph.cedula_workflow_state import CedulaWorkflowState
from infraestructure.workflows.langgraph.nodes.classify_and_extract_node import ClassifyAndExtractNode
from infraestructure.workflows.langgraph.nodes.finalize_and_save import FinalizeAndSave

class LangGraphVehicleWorkflowAdapter(VehicleWorkflowPort):
    def __init__(
        self,
        storage_port: FileStoragePort,
        extractor_port: VehicleExtractorPort,
        vehicle_repo: VehicleCardRepositoryPort,
        checkpointer: Optional[Any] = None,
    ):
        self._storage = storage_port
        self._extractor = extractor_port
        self._repo = vehicle_repo

        classify_node = ClassifyAndExtractNode(self._extractor)
        finalize_node = FinalizeAndSave(self._repo)

        workflow = StateGraph(CedulaWorkflowState)
        workflow.add_node("classify_and_extract", classify_node)
        workflow.add_node("finalize_and_save", finalize_node)

        # Flujo continuo: Extrae -> Guarda progresivamente en cada paso -> Listo para MCP
        workflow.add_edge(START, "classify_and_extract")
        workflow.add_edge("classify_and_extract", "finalize_and_save")
        workflow.add_edge("finalize_and_save", END)

        self._checkpointer = checkpointer or MemorySaver()
        self._app = workflow.compile(checkpointer=self._checkpointer)

    async def execute_step(
        self,
        session_id: str,
        file_bytes: bytes,
        mime_type: str,
        file_name: str,
    ) -> Dict[str, Any]:
        file_path = await self._storage.upload(
            file_bytes=file_bytes,
            file_name=file_name,
            content_type=mime_type,
        )

        input_state = {
            "session_id": session_id,
            "current_storage_path": file_path,
            "current_mime_type": mime_type,
            "current_file_bytes": file_bytes,
        }

        config = {"configurable": {"thread_id": session_id}}
        final_state = await self._app.ainvoke(input_state, config=config)

        res = dict(final_state)
        res.pop("current_file_bytes", None)
        return res