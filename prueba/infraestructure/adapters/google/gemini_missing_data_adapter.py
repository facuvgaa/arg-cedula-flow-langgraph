from domain.ports.missing_data_message_port import MissingDataMessagePort
from domain.prompt.prompt_request_missing_data import PromptRequestMissingData
from google import genai

class GeminiMissingDataAdapter(MissingDataMessagePort):
    def __init__(self, api_key: str, model_name: str = "gemini-3.8-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name.replace("models/", "")

    async def generate_missing_data_message(
        self, brand: str, model: str, owner_name: str | None, address: str | None, detected_cp: str | None, missing_fields: list[str]
    ) -> str:
        prompt = PromptRequestMissingData(
            brand=brand,
            model=model,
            owner_name=owner_name,
            city_or_address=address,
            detected_cp=detected_cp,
            missing_fields=missing_fields,
        )

        response = await self._client.aio.models.generate_content(
            model=self._model_name,
            contents=prompt,
        )

        return response.text.strip() if response.text else f"Detecté tu {brand} {model}. ¿De qué año es y cuál es tu código postal?"