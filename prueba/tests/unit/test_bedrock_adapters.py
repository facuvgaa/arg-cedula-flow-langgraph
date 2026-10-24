import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from infraestructure.adapters.bedrock.bedrock_missing_data_adapter import BedrockMissingDataAdapter
from infraestructure.adapters.bedrock.bedrock_insurance_negotiator_adapter import BedrockInsuranceNegotiatorAdapter
from infraestructure.adapters.bedrock.bedrock_vehicle_extractor_adapter import BedrockVehicleExtractorAdapter


@pytest.mark.asyncio
async def test_bedrock_missing_data_adapter_http_mode():
    adapter = BedrockMissingDataAdapter(
        base_url="https://fake-bedrock-mantle.aws/v1",
        api_key="fake-key",
        model_name="amazon.nova-lite-v1:0"
    )

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Hola Facundo, ¿de qué año es tu Kangoo?"}}]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        msg = await adapter.generate_missing_data_message(
            brand="Renault",
            model="Kangoo",
            owner_name="Facundo Vega",
            address="San Miguel de Tucumán",
            detected_cp="4000",
            missing_fields=["year"]
        )

        assert "Kangoo" in msg
        assert "¿de qué año es" in msg


@pytest.mark.asyncio
async def test_bedrock_negotiator_adapter_asking_question():
    adapter = BedrockInsuranceNegotiatorAdapter(
        base_url="https://fake-bedrock-mantle.aws/v1",
        api_key="fake-key",
        model_name="amazon.nova-lite-v1:0"
    )

    fake_payload = {
        "reply": "El seguro de Terceros Completo cubre daños por granizo hasta el tope de póliza.",
        "intent": "ASKING_QUESTION",
        "selected_coverage": None,
        "customer_email": None,
        "customer_phone": None
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": json.dumps(fake_payload)}}]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        res = await adapter.negotiate(
            user_message="¿Cubre granizo?",
            context={"vehiculo": {"marca": "Renault", "modelo": "Kangoo"}}
        )

        assert res["intent"] == "ASKING_QUESTION"
        assert res["selected_coverage"] is None
        assert "granizo" in res["reply"]


@pytest.mark.asyncio
async def test_bedrock_negotiator_adapter_hire_selected():
    adapter = BedrockInsuranceNegotiatorAdapter(
        base_url="https://fake-bedrock-mantle.aws/v1",
        api_key="fake-key",
        model_name="amazon.nova-lite-v1:0"
    )

    fake_payload = {
        "reply": "¡Perfecto! Vamos con Todo Riesgo. ¿Me pasas tu email?",
        "intent": "HIRE_SELECTED",
        "selected_coverage": "TODO_RIESGO",
        "customer_email": "test@example.com",
        "customer_phone": "381123456"
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": json.dumps(fake_payload)}]  # Choices format can vary
    }
    # Fix standard format
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": json.dumps(fake_payload)}}]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        res = await adapter.negotiate(
            user_message="Quiero el de todo riesgo, mi mail es test@example.com y cel 381123456",
            context={"vehiculo": {"marca": "Renault", "modelo": "Kangoo"}}
        )

        assert res["intent"] == "HIRE_SELECTED"
        assert res["selected_coverage"] == "TODO_RIESGO"
        assert res["customer_email"] == "test@example.com"
        assert res["customer_phone"] == "381123456"


@pytest.mark.asyncio
async def test_bedrock_vehicle_extractor_adapter():
    adapter = BedrockVehicleExtractorAdapter(
        base_url="https://fake-bedrock-mantle.aws/v1",
        api_key="fake-key",
        model_name="amazon.nova-lite-v1:0"
    )

    extracted_payload = {
        "vehicle_category": "CAR",
        "domain": "AC789XY",
        "brand": "Renault",
        "model": "Kangoo",
        "year": 2018,
        "vehicle_type": "FURGON",
        "use": "PARTICULAR",
        "motor_number": "MTR123456",
        "chassis_number": "CHS987654",
        "expiration_date": "2028-10-10",
        "owner": {
            "full_name": "Facundo Vega",
            "dni": "38123456",
            "address": "San Miguel de Tucumán",
            "postal_code": "4000"
        }
    }

    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": f"```json\n{json.dumps(extracted_payload)}\n```"}}]
    }
    mock_resp.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):
        res = await adapter.extract_from_image(
            image_bytes=b"fake-bytes",
            mime_type="image/jpeg"
        )

        assert res["vehicle"]["dominio"] == "AC789XY"
        assert res["vehicle"]["marca"] == "Renault"
        assert res["vehicle"]["modelo"] == "Kangoo"
        assert res["vehicle"]["year"] == 2018
        assert res["owner"]["nombre_completo"] == "Facundo Vega"
        assert res["owner"]["codigo_postal"] == "4000"

