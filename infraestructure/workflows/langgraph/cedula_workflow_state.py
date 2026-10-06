from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class CedulaWorkflowState(BaseModel):
    session_id: str
    current_storage_path: Optional[str] = None
    current_mime_type: Optional[str] = None

    front_storage_path: Optional[str] = None
    back_storage_path: Optional[str] = None

    vehicle_data: Optional[Dict[str, Any]] = None
    owner_data: Optional[Dict[str, Any]] = None


    status: str = "PENDING"
    message: Optional[str] = None