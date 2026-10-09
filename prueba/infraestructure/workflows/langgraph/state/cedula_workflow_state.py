from typing import Any, Dict, List, Optional, TypedDict

class CedulaWorkflowState(TypedDict, total=False):
    session_id: str
    current_storage_path: Optional[str]
    current_mime_type: Optional[str]
    current_file_bytes: Optional[bytes]

    front_storage_path: Optional[str]
    back_storage_path: Optional[str]
    inspection_storage_paths: Optional[List[str]]

    vehicle_data: Optional[Dict[str, Any]]
    owner_data: Optional[Dict[str, Any]]

    year: Optional[int]
    postal_code: Optional[str]

    quote_result: Optional[Dict[str, Any]]
    policy_result: Optional[Dict[str, Any]]

    status: str
    message: Optional[str]