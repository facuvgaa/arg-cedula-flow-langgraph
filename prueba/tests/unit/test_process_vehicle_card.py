import pytest
from unittest.mock import AsyncMock
from domain.ports.file_storage_port import FileStoragePort
from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from domain.ports.vehicle_card_repository_port import VehicleCardRepositoryPort
from infraestructure.adapters.mcp_insurance_client_adapter import McpInsuranceClientAdapter
from infraestructure.workflows.langgraph.langgraph_workflow_adapter import LangGraphVehicleWorkflowAdapter

@pytest.mark.asyncio
async def test_workflow_extracts_and_triggers_mcp_quote():
    storage_mock = AsyncMock(spec=FileStoragePort)
    storage_mock.upload.return_value = "bucket/test_front.jpg"

    extractor_mock = AsyncMock(spec=VehicleExtractorPort)
    extractor_mock.extract_from_image.return_value = {
        "vehicle": {
            "dominio": "AC789XY",
            "marca": "Ford",
            "modelo": "EcoSport",
            "tipo": "SEDAN 5 PTAS",
            "uso": "PRIVADO",
            "chasis": "8A123456789",
            "motor": "MTR987654",
            "tipo_vehiculo": "CAR",
            "year": 2010
        },
        "owner": {
            "nombre_completo": "Facundo Vega",
            "documento": "38123456",
            "domicilio": "San Miguel de Tucumán",
            "codigo_postal": "4000"
        }
    }

    repo_mock = AsyncMock(spec=VehicleCardRepositoryPort)
    repo_mock.save.return_value = None

    mcp_mock = AsyncMock(spec=McpInsuranceClientAdapter)
    mcp_mock.calculate_quote.return_value = {
        "vehicleDescription": "FORD ECOSPORT (2010)",
        "vehicleMarketValue": 9200000.0,
        "postalCode": "4000",
        "coverages": {
            "RESPONSABILIDAD_CIVIL": 22500.0,
            "TERCEROS_COMPLETO": 34776.0,
            "TODO_RIESGO": 64584.0
        }
    }

    adapter = LangGraphVehicleWorkflowAdapter(
        storage_port=storage_mock,
        extractor_port=extractor_mock,
        vehicle_repo=repo_mock,
        mcp_client=mcp_mock
    )

    result = await adapter.execute_step(
        session_id="test-session-123",
        file_bytes=b"fake-image-bytes",
        file_name="cedula.jpg",
        mime_type="image/jpeg"
    )

    assert result["status"] == "QUOTES_AVAILABLE"
    assert "quote_result" in result
    assert result["quote_result"]["coverages"]["TODO_RIESGO"] == 64584.0
    mcp_mock.calculate_quote.assert_called_once_with(
        brand="Ford",
        model="EcoSport",
        year=2010,
        postal_code="4000"
    )

@pytest.mark.asyncio
async def test_workflow_asks_for_year_and_completes_when_provided():
    storage_mock = AsyncMock(spec=FileStoragePort)
    storage_mock.upload.return_value = "bucket/test_front.jpg"

    extractor_mock = AsyncMock(spec=VehicleExtractorPort)
    # Cédula sin año impreso pero con CP inferido
    extractor_mock.extract_from_image.return_value = {
        "vehicle": {
            "dominio": "AC789XY",
            "marca": "Renault",
            "modelo": "Kangoo",
            "tipo_vehiculo": "CAR",
            "year": None
        },
        "owner": {
            "nombre_completo": "Facundo Vega",
            "documento": "38123456",
            "domicilio": "San Miguel de Tucumán",
            "codigo_postal": "4000"
        }
    }

    repo_mock = AsyncMock(spec=VehicleCardRepositoryPort)
    repo_mock.save.return_value = None

    mcp_mock = AsyncMock(spec=McpInsuranceClientAdapter)
    mcp_mock.calculate_quote.return_value = {
        "vehicleDescription": "RENAULT KANGOO (2018)",
        "vehicleMarketValue": 8500000.0,
        "postalCode": "4000",
        "coverages": {
            "RESPONSABILIDAD_CIVIL": 22500.0,
            "TERCEROS_COMPLETO": 32130.0,
            "TODO_RIESGO": 59670.0
        }
    }

    adapter = LangGraphVehicleWorkflowAdapter(
        storage_port=storage_mock,
        extractor_port=extractor_mock,
        vehicle_repo=repo_mock,
        mcp_client=mcp_mock
    )

    # Paso 1: Sube la foto de la cédula (sin año)
    res_step1 = await adapter.execute_step(
        session_id="session-user-slot-1",
        file_bytes=b"fake-bytes",
        file_name="cedula.jpg",
        mime_type="image/jpeg"
    )

    assert res_step1["status"] == "WAITING_YEAR"
    assert "año" in res_step1["message"].lower()

    # Paso 2: Usuario responde con el año
    res_step2 = await adapter.execute_step(
        session_id="session-user-slot-1",
        year=2018
    )

    assert res_step2["status"] == "QUOTES_AVAILABLE"
    assert res_step2["quote_result"]["coverages"]["TODO_RIESGO"] == 59670.0
    mcp_mock.calculate_quote.assert_called_once_with(
        brand="Renault",
        model="Kangoo",
        year=2018,
        postal_code="4000"
    )

