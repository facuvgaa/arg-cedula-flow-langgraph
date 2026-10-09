import uuid
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from application.use_case.process_vehicle_card import ProcessVehicleCardUseCase
from infraestructure.adapters.mcp_insurance_client_adapter import McpInsuranceClientAdapter
from infraestructure.adapters.postgres_vehicle_card_repository_adapter import (
    PostgresVehicleCardRepositoryAdapter,
)
from infraestructure.database.models import Base
from infraestructure.database.session import AsyncSessionLocal, engine
from infraestructure.factories.llm_extractor_factory import LlmExtractorFactory
from infraestructure.factories.storage_factory import StorageFactory
from infraestructure.workflows.langgraph.langgraph_workflow_adapter import (
    LangGraphVehicleWorkflowAdapter,
)

from sqlalchemy import text

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        try:
            await conn.execute(
                text("ALTER TABLE vehicle_cards ALTER COLUMN vehicle_id DROP NOT NULL;")
            )
        except Exception:
            pass
    yield

app = FastAPI(title="Vehicle Card & Insurance MCP API", lifespan=lifespan)

mcp_client = McpInsuranceClientAdapter(base_url="http://localhost:8080")
repository_adapter = PostgresVehicleCardRepositoryAdapter(AsyncSessionLocal)
storage_adapter = StorageFactory.create()
extractor_adapter = LlmExtractorFactory.create()

workflow_adapter = LangGraphVehicleWorkflowAdapter(
    storage_port=storage_adapter,
    extractor_port=extractor_adapter,
    vehicle_repo=repository_adapter,
    mcp_client=mcp_client,
)

use_case = ProcessVehicleCardUseCase(workflow_port=workflow_adapter)

@app.post("/v1/vehicle-cards/process")
async def process_card(
    file: Optional[UploadFile] = File(None),
    session_id: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    postal_code: Optional[str] = Form(None),
):
    current_session_id = session_id or str(uuid.uuid4())
    
    file_bytes = None
    file_name = None
    mime_type = None

    if file:
        if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado")
        file_bytes = await file.read()
        file_name = file.filename or f"{current_session_id}.jpg"
        mime_type = file.content_type

    if not file_bytes and year is None and postal_code is None:
        raise HTTPException(status_code=400, detail="Debe proporcionar una imagen, el año o el código postal.")

    result = await use_case.execute(
        session_id=current_session_id,
        file_bytes=file_bytes,
        file_name=file_name,
        mime_type=mime_type,
        year=year,
        postal_code=postal_code,
    )

    return result

class HireInsuranceRequest(BaseModel):
    customer_name: str
    customer_dni: Optional[str] = ""
    customer_email: Optional[str] = ""
    license_plate: Optional[str] = ""
    brand: str
    model: str
    year: int
    postal_code: str
    coverage_type: str
    green_card_url: Optional[str] = ""
    inspection_photos_url: Optional[str] = ""

@app.post("/v1/insurance/hire")
async def hire_insurance(request: HireInsuranceRequest):
    """Contrata una póliza conectándose directamente al servidor Spring Boot MCP."""
    try:
        policy = await mcp_client.hire_policy(
            customer_name=request.customer_name,
            customer_dni=request.customer_dni or "",
            customer_email=request.customer_email or "",
            license_plate=request.license_plate or "",
            brand=request.brand,
            model=request.model,
            year=request.year,
            postal_code=request.postal_code,
            coverage_type=request.coverage_type,
            green_card_url=request.green_card_url,
            inspection_photos_url=request.inspection_photos_url,
        )
        return {
            "status": "POLICY_ISSUED",
            "message": f"Póliza {policy.get('policyNumber')} emitida con éxito.",
            "policy": policy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al emitir póliza vía MCP: {str(e)}")