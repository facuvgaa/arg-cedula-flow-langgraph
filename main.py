from fastapi import FastAPI, File, HTTPException, UploadFile
from infraestructure.adapters.postgres_vehicle_card_repository_adapter import (
    PostgresVehicleCardRepositoryAdapter,
)
from infraestructure.database.session import AsyncSessionLocal, engine
from infraestructure.database.models import Base
from infraestructure.factories.llm_extractor_factory import LlmExtractorFactory
from infraestructure.factories.storage_factory import StorageFactory
from application.use_case.process_vehicle_card import ProcessVehicleCardUseCase

app = FastAPI(title="Vehicle Card Parser API")

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

repository_adapter = PostgresVehicleCardRepositoryAdapter(AsyncSessionLocal)
storage_adapter = StorageFactory.create()
extractor_adapter = LlmExtractorFactory.create()

use_case = ProcessVehicleCardUseCase(
    storage_port=storage_adapter,
    extractor_port=extractor_adapter,
    repository_port=repository_adapter,
)

@app.post("/v1/vehicle-cards/process")
async def process_card(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado")

    file_bytes = await file.read()

    result = await use_case.execute(
        file_bytes=file_bytes,
        file_name=file.filename,
        mime_type=file.content_type,
    )

    return result