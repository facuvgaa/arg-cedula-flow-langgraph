from typing import Any, Dict, Optional
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from domain.ports.vehicle_workflow_port import VehicleWorkflowPort
from domain.ports.file_storage_port import FileStoragePort
from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from domain.ports.vehicle_card_repository_port import VehicleCardRepositoryPort
from domain.ports.missing_data_message_port import MissingDataMessagePort
from domain.ports.insurance_negotiator_port import InsuranceNegotiatorPort
from domain.ports.policy_knowledge_port import PolicyKnowledgePort

from infraestructure.adapters.mcp import McpInsuranceClientAdapter
from infraestructure.workflows.state.cedula_workflow_state import CedulaWorkflowState
from infraestructure.workflows.nodes.classify_and_extract_node import ClassifyAndExtractNode
from infraestructure.workflows.nodes.finalize_and_save import FinalizeAndSave
from infraestructure.workflows.nodes.calculate_quote_mcp_node import CalculateQuoteMcpNode
from infraestructure.workflows.nodes.request_missing_data_node import RequestMissingDataNode
from infraestructure.workflows.nodes.negotiate_insurance_and_faqs_node import NegotiateInsuranceAndFaqsNode
from infraestructure.workflows.nodes.add_mail_to_client_node import AddMailToClientNode


def entry_router(state: CedulaWorkflowState) -> str:
    if state.get("current_file_bytes"):
        return "classify_and_extract"
    if state.get("user_message"):
        return "negotiator_and_faqs"
    return "classify_and_extract"

def quote_router(state: CedulaWorkflowState) -> str:
    status = state.get("status")
    if status == "READY_FOR_QUOTE":
        return "calculate_quote_mcp"
    elif status in ("WAITING_YEAR", "WAITING_CP", "WAITING_YEAR_AND_CP", "MISSING_DATA"):
        return "request_missing_data"
    if status == "READY_TO_HIRE":
        return "add_mail_to_client"
    return END

def negotiation_router(state: CedulaWorkflowState) -> str:
    status = state.get("status")
    if status == "READY_TO_HIRE":
        return "add_mail_to_client"
    return END

class LangGraphVehicleWorkflowAdapter(VehicleWorkflowPort):
    def __init__(
        self,
        storage_port: FileStoragePort,
        extractor_port: VehicleExtractorPort,
        vehicle_repo: VehicleCardRepositoryPort,
        missing_data_port: MissingDataMessagePort,
        negotiator_port: InsuranceNegotiatorPort,
        knowledge_port: Optional[PolicyKnowledgePort] = None,
        mcp_client: Optional[McpInsuranceClientAdapter] = None,
        checkpointer: Optional[Any] = None,
    ):
        self._storage = storage_port
        self._extractor = extractor_port
        self._repo = vehicle_repo
        self._missing_data_service = missing_data_port
        self._negotiator = negotiator_port
        self._mcp_client = mcp_client or McpInsuranceClientAdapter()

        classify_node = ClassifyAndExtractNode(self._extractor)
        finalize_node = FinalizeAndSave(self._repo)
        quote_node = CalculateQuoteMcpNode(self._mcp_client)
        missing_data_node = RequestMissingDataNode(self._missing_data_service)
        negotator_node = NegotiateInsuranceAndFaqsNode(self._negotiator, knowledge_port = knowledge_port)
        mail_node = AddMailToClientNode(self._mcp_client)

        workflow = StateGraph(CedulaWorkflowState)
        workflow.add_node("classify_and_extract", classify_node)
        workflow.add_node("finalize_and_save", finalize_node)
        workflow.add_node("calculate_quote_mcp", quote_node)
        workflow.add_node("request_missing_data", missing_data_node)
        workflow.add_node("negotiator_and_faqs", negotator_node)
        workflow.add_node("add_mail_to_client", mail_node)

        workflow.add_conditional_edges(
            START,
            entry_router,
            {
                "classify_and_extract": "classify_and_extract",
                "negotiator_and_faqs": "negotiator_and_faqs",
            }
        )
        workflow.add_edge("classify_and_extract", "finalize_and_save")
        workflow.add_conditional_edges(
            "finalize_and_save",
            quote_router,
            {
                "calculate_quote_mcp": "calculate_quote_mcp",
                "request_missing_data": "request_missing_data",
                END: END,
            }
        )

        workflow.add_edge("request_missing_data", END)
        workflow.add_edge("calculate_quote_mcp", END)

        workflow.add_conditional_edges(
            "negotiator_and_faqs",
            negotiation_router,
            {
                "add_mail_to_client": "add_mail_to_client",
                END: END,
            }
        )
        workflow.add_edge("add_mail_to_client", END)

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
        user_message: Optional[str] = None,
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
        else:
            input_state["current_file_bytes"] = None

        if year is not None:
            input_state["year"] = int(year)
        if postal_code is not None:
            input_state["postal_code"] = str(postal_code)
        if user_message is not None:
            input_state["user_message"] = str(user_message)
        else:
            input_state["user_message"] = None


        config = {"configurable": {"thread_id": session_id}}
        final_state = await self._app.ainvoke(input_state, config=config)

        res = dict(final_state)
        res.pop("current_file_bytes", None)
        return res