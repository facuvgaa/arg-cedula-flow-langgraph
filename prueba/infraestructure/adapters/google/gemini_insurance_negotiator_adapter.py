import json
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from domain.ports.insurance_negotiator_port import InsuranceNegotiatorPort
from domain.prompt.prompt_insurance_negotiator import PromptInsuranceNegotiator


class NegotiationResponseSchema(BaseModel):
    reply: str = Field(
        ...,
        description="Respuesta comercial empática para el cliente respondiendo sus dudas sobre coberturas, precios o confirmando su elección.",
    )
    intent: Literal["ASKING_QUESTION", "HIRE_SELECTED"] = Field(
        ...,
        description="'ASKING_QUESTION' si el cliente hace preguntas o aún no decidió contratar. 'HIRE_SELECTED' si el cliente ya confirmó explícitamente qué seguro quiere contratar.",
    )
    selected_coverage: Optional[Literal["RESPONSABILIDAD_CIVIL", "TERCEROS_COMPLETO", "TODO_RIESGO"]] = Field(
        None,
        description="La cobertura elegida si el intent es HIRE_SELECTED ('RESPONSABILIDAD_CIVIL', 'TERCEROS_COMPLETO' o 'TODO_RIESGO'). Null si está preguntando o no decidió.",
    )
    customer_email: Optional[str] = Field(
        None,
        description="Dirección de correo electrónico del cliente si la proporcionó en el mensaje o historial, sino null.",
    )
    customer_phone: Optional[str] = Field(
        None,
        description="Número de teléfono celular / WhatsApp del cliente si lo proporcionó en el mensaje o historial, sino null.",
    )


class GeminiInsuranceNegotiatorAdapter(InsuranceNegotiatorPort):
    def __init__(self, api_key: str, model_name: str = "gemini-3.8-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name.replace("models/", "")

    async def negotiate(
        self,
        user_message: str,
        context: Dict[str, Any],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        prompt = PromptInsuranceNegotiator(
            user_message=user_message,
            context=context,
            chat_history=chat_history,
        )

        response = await self._client.aio.models.generate_content(
            model=self._model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=NegotiationResponseSchema,
                temperature=0.3,
            ),
        )

        if not response.text:
            return {
                "reply": "¿Tenés alguna duda sobre las coberturas o te gustaría avanzar con alguna de las opciones?",
                "intent": "ASKING_QUESTION",
                "selected_coverage": None,
            }

        try:
            data = json.loads(response.text)
            return {
                "reply": data.get("reply", ""),
                "intent": data.get("intent", "ASKING_QUESTION"),
                "selected_coverage": data.get("selected_coverage"),
                "customer_email": data.get("customer_email"),
                "customer_phone": str(data["customer_phone"]) if data.get("customer_phone") is not None else None,
            }
        except Exception:
            return {
                "reply": response.text.strip(),
                "intent": "ASKING_QUESTION",
                "selected_coverage": None,
                "customer_email": None,
                "customer_phone": None,
            }




