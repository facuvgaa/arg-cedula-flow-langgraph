import pytest
from infraestructure.adapters.bedrock.bedrock_insurance_negotiator_adapter import BedrockInsuranceNegotiatorAdapter
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.asyncio
async def test_bedrock_live():

    adapter = BedrockInsuranceNegotiatorAdapter()

    mensaje_usuario = "¿Qué diferencia hay entre Responsabilidad Civil y Todo Riesgo?"
    contexto = {
        "vehiculo": {"marca": "Renault", "modelo": "Kangoo", "year": 2018}
    }

    resultado = await adapter.negotiate(
        user_message=mensaje_usuario,
        context=contexto
    )


    print("\n--- Respuesta REAL de AWS Bedrock ---")
    print("Respuesta:", resultado["reply"])
    print("Intent detectado:", resultado["intent"])

    assert "reply" in resultado
    assert len(resultado["reply"]) > 20, "La respuesta fue demasiado corta o vacía"
    assert resultado["intent"] == "ASKING_QUESTION", "El LLM debería haber detectado que es una consulta"