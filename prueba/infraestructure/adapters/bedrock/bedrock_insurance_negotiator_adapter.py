import asyncio
import json
import os
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
import boto3
import httpx

try:
    from langfuse.decorators import observe, langfuse_context
except ImportError:
    def observe(*args, **kwargs):
        def decorator(f):
            return f
        return decorator

from domain.ports.insurance_negotiator_port import InsuranceNegotiatorPort
from domain.prompt.prompt_insurance_negotiator import PromptInsuranceNegotiator


class NegotiationResponseSchema(BaseModel):
    reply: str = Field(
        ...,
        description="Respuesta comercial empática para el cliente respondiendo sus dudas o confirmando su elección.",
    )
    intent: Literal["ASKING_QUESTION", "HIRE_SELECTED"] = Field(
        ...,
        description="'ASKING_QUESTION' si consulta o no decidió. 'HIRE_SELECTED' si confirmó contratar.",
    )
    selected_coverage: Optional[Literal["RESPONSABILIDAD_CIVIL", "TERCEROS_COMPLETO", "TODO_RIESGO"]] = Field(
        None,
        description="Cobertura elegida si intent es HIRE_SELECTED, sino null.",
    )
    customer_email: Optional[str] = Field(
        None,
        description="Email del cliente si lo proporcionó, sino null.",
    )
    customer_phone: Optional[str] = Field(
        None,
        description="WhatsApp/celular del cliente si lo proporcionó, sino null.",
    )


class BedrockInsuranceNegotiatorAdapter(InsuranceNegotiatorPort):
    """
    Adaptador de negociación y preguntas frecuentes para AWS Bedrock.
    Utiliza RAG y razonamiento conversacional respondiendo en JSON estructurado.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        region_name: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self._region = region_name or os.getenv("AWS_DEFAULT_REGION", "us-east-2")
        self._model = model_name or os.getenv("OPENAI_MODEL") or os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
        self._base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self._api_key = (
            api_key
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("AWS_BEARER_TOKEN_BEDROCK")
            or os.getenv("AWS_BEDROCK_API_KEY")
        )
        self._boto_client = None

    @observe(as_type="generation", name="bedrock_negotiate_insurance")
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

        system_instruction = (
            "Eres el asesor de seguros oficial de Seguro Monkey. Responde de forma cordial y profesional en español rioplatense (Argentina). "
            "Debes responder OBLIGATORIAMENTE en formato JSON con las claves: "
            "'reply' (string con la respuesta), "
            "'intent' ('ASKING_QUESTION' o 'HIRE_SELECTED'), "
            "'selected_coverage' ('RESPONSABILIDAD_CIVIL', 'TERCEROS_COMPLETO', 'TODO_RIESGO' o null), "
            "'customer_email' (string o null), "
            "'customer_phone' (string o null). "
            "No incluyas texto fuera del objeto JSON."
        )

        response_text = ""

        # Modo 1: Bedrock Mantle / OpenAI-compatible endpoint
        if self._base_url and self._api_key:
            url = f"{self._base_url.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            }
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                res = await http_client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                response_text = data["choices"][0]["message"]["content"]

        # Modo 2: Boto3 Converse API
        else:
            if not self._boto_client:
                self._boto_client = boto3.client("bedrock-runtime", region_name=self._region)

            response = await asyncio.to_thread(
                self._boto_client.converse,
                modelId=self._model,
                messages=[{"role": "user", "content": [{"text": f"{system_instruction}\n\n{prompt}"}]}],
                inferenceConfig={"temperature": 0.2},
            )
            response_text = response["output"]["message"]["content"][0]["text"]

        try:
            langfuse_context.update_current_observation(
                model=self._model,
                input={"user_message": user_message, "context": context},
                output=response_text,
            )
        except Exception:
            pass

        cleaned_json = response_text.strip()
        if cleaned_json.startswith("```"):
            cleaned_json = cleaned_json.split("\n", 1)[1]
            if cleaned_json.endswith("```"):
                cleaned_json = cleaned_json.rsplit("\n", 1)[0]

        try:
            data = json.loads(cleaned_json)
            return {
                "reply": data.get("reply", ""),
                "intent": data.get("intent", "ASKING_QUESTION"),
                "selected_coverage": data.get("selected_coverage"),
                "customer_email": data.get("customer_email"),
                "customer_phone": str(data["customer_phone"]) if data.get("customer_phone") is not None else None,
            }
        except Exception:
            return {
                "reply": cleaned_json,
                "intent": "ASKING_QUESTION",
                "selected_coverage": None,
                "customer_email": None,
                "customer_phone": None,
            }

