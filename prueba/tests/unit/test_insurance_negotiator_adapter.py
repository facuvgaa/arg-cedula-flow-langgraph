import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from infraestructure.adapters.google import GeminiInsuranceNegotiatorAdapter

@pytest.mark.asyncio
async def test_negotiator_adapter_asking_question():
    adapter = GeminiInsuranceNegotiatorAdapter(api_key="fake-key")
    
    fake_payload = {
        "reply": "El seguro de Terceros Completo sí cubre granizo hasta $1.500.000.",
        "intent": "ASKING_QUESTION",
        "selected_coverage": None
    }
    
    mock_response = MagicMock()
    mock_response.text = json.dumps(fake_payload)
    
    adapter._client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    
    res = await adapter.negotiate(
        user_message="¿Cubre granizo el seguro?",
        context={
            "auto": "Ford Focus 2018",
            "precios": {"RESPONSABILIDAD_CIVIL": 20000, "TERCEROS_COMPLETO": 35000}
        }
    )
    
    assert res["intent"] == "ASKING_QUESTION"
    assert res["selected_coverage"] is None
    assert "granizo" in res["reply"]

@pytest.mark.asyncio
async def test_negotiator_adapter_hire_selected():
    adapter = GeminiInsuranceNegotiatorAdapter(api_key="fake-key")
    
    fake_payload = {
        "reply": "¡Excelente elección! Vamos a avanzar con la póliza de Todo Riesgo.",
        "intent": "HIRE_SELECTED",
        "selected_coverage": "TODO_RIESGO"
    }
    
    mock_response = MagicMock()
    mock_response.text = json.dumps(fake_payload)
    
    adapter._client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    
    res = await adapter.negotiate(
        user_message="Listo, me quedo con el de todo riesgo",
        context={"auto": "Toyota Corolla 2020", "precios": {"TODO_RIESGO": 65000}}
    )
    
    assert res["intent"] == "HIRE_SELECTED"
    assert res["selected_coverage"] == "TODO_RIESGO"

