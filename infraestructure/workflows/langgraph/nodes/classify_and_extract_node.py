from typing import Any, Dict
from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from infraestructure.workflows.langgraph.cedula_workflow_state import CedulaWorkflowState

class ClassifyAndExtractNode:
    def __init__(self, extractor_port: VehicleExtractorPort):
        self._extractor = extractor_port
    