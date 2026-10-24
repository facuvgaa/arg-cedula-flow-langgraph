import asyncio
import os
from typing import List, Optional
import boto3
import httpx

from domain.ports.missing_data_message_port import MissingDataMessagePort
from domain.prompt.prompt_request_missing_data import PromptRequestMissingData


class BedrockMissingDataAdapter(MissingDataMessagePort):
    """
    Genera un mensaje cordial solicitando los datos faltantes del vehículo o titular
    utilizando AWS Bedrock (Mantle OpenAI-compatible o Boto3).
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

    async def generate_missing_data_message(
        self,
        brand: str,
        model: str,
        owner_name: Optional[str],
        address: Optional[str],
        detected_cp: Optional[str],
        missing_fields: List[str],
    ) -> str:
        prompt = PromptRequestMissingData(
            brand=brand,
            model=model,
            owner_name=owner_name,
            city_or_address=address,
            detected_cp=detected_cp,
            missing_fields=missing_fields,
        )

        fallback = f"¡Hola! Detecté tu {brand} {model}. Para poder cotizarte, ¿de qué año es y cuál es tu código postal?"

        try:
            # Modo 1: Bedrock Mantle / OpenAI-compatible endpoint
            if self._base_url and self._api_key:
                url = f"{self._base_url.rstrip('/')}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                }
                async with httpx.AsyncClient(timeout=20.0) as http_client:
                    res = await http_client.post(url, headers=headers, json=payload)
                    res.raise_for_status()
                    data = res.json()
                    return data["choices"][0]["message"]["content"].strip()

            # Modo 2: Boto3 Converse API
            else:
                if not self._boto_client:
                    self._boto_client = boto3.client("bedrock-runtime", region_name=self._region)

                response = await asyncio.to_thread(
                    self._boto_client.converse,
                    modelId=self._model,
                    messages=[{"role": "user", "content": [{"text": prompt}]}],
                    inferenceConfig={"temperature": 0.3},
                )
                return response["output"]["message"]["content"][0]["text"].strip()

        except Exception as e:
            return fallback

