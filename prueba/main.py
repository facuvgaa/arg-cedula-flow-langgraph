import uuid
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from application.use_case.process_vehicle_card import ProcessVehicleCardUseCase
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

app = FastAPI(title="Vehicle Card Parser API", lifespan=lifespan)

repository_adapter = PostgresVehicleCardRepositoryAdapter(AsyncSessionLocal)
storage_adapter = StorageFactory.create()
extractor_adapter = LlmExtractorFactory.create()

workflow_adapter = LangGraphVehicleWorkflowAdapter(
    storage_port=storage_adapter,
    extractor_port=extractor_adapter,
    vehicle_repo=repository_adapter,
)

use_case = ProcessVehicleCardUseCase(workflow_port=workflow_adapter)

@app.post("/v1/vehicle-cards/process")
async def process_card(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
):
    if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado")

    current_session_id = session_id or str(uuid.uuid4())
    file_bytes = await file.read()

    result = await use_case.execute(
        session_id=current_session_id,
        file_bytes=file_bytes,
        file_name=file.filename or f"{current_session_id}.jpg",
        mime_type=file.content_type,
    )

    return result