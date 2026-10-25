import base64
import json
import os
from typing import Any, Dict, Literal, Optional
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

from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from domain.prompt.prompt_extraction import PromptExtraction


def clean_str(val: Optional[str]) -> Optional[str]:
    if val is None:
        return None
    cleaned = str(val).strip()
    if cleaned.upper() in ("", "NO VISIBLE", "NULL", "NONE", "NO APLICA", "N/A", "DESCONOCIDO", "-", "UNDEFINED"):
        return None
    return cleaned


class OwnerSchema(BaseModel):
    full_name: Optional[str] = Field(None, description="Nombre y apellido completo del titular, o null")
    dni: Optional[str] = Field(None, description="Número de documento / DNI / CUIT del titular, o null")
    address: Optional[str] = Field(None, description="Domicilio completo que figura en el reverso, o null")
    postal_code: Optional[str] = Field(None, description="Código postal de 4 dígitos deducido de la localidad/provincia")


class VehicleExtractionSchema(BaseModel):
    vehicle_category: Optional[Literal["CAR", "MOTOBIKE"]] = Field(None, description="Categoría: CAR o MOTOBIKE")
    domain: Optional[str] = Field(None, description="Patente / Dominio del vehículo, o null")
    brand: Optional[str] = Field(None, description="Marca del vehículo, o null")
    model: Optional[str] = Field(None, description="Modelo exacto, o null")
    year: Optional[int] = Field(None, description="Año de fabricación/modelo si figura explícito, o null")
    vehicle_type: Optional[str] = Field(None, description="Tipo de vehículo, o null")
    use: Optional[str] = Field(None, description="Uso del vehículo, o null")
    motor_number: Optional[str] = Field(None, description="Número de motor, o null")
    expiration_date: Optional[str] = Field(None, description="Fecha de vencimiento impresa, o null")
    chassis_number: Optional[str] = Field(None, description="Número de chasis (autos), o null")
    frame_number: Optional[str] = Field(None, description="Número de cuadro (motos), o null")
    engine_cc: Optional[str] = Field(None, description="Cilindrada en cc (motos), o null")
    owner: Optional[OwnerSchema] = Field(None, description="Datos del titular si están presentes en la imagen")


class BedrockVehicleExtractorAdapter(VehicleExtractorPort):
    """
    Adaptador de extracción vehicular para AWS Bedrock.
    Soporta tanto el endpoint OpenAI-compatible de Bedrock Mantle (vía httpx)
    como Boto3 (Bedrock Runtime Converse API).
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        region_name: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self._region = region_name or os.getenv("AWS_DEFAULT_REGION", "us-east-2")
        self._model = (
            model_name
            or os.getenv("OPENAI_VISION_MODEL")
            or os.getenv("BEDROCK_VISION_MODEL")
            or "qwen.qwen3-vl-235b-a22b-instruct"
        )
        self._base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self._api_key = (
            api_key
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("AWS_BEARER_TOKEN_BEDROCK")
            or os.getenv("AWS_BEDROCK_API_KEY")
        )

        # Cliente boto3 como fallback si no se usa endpoint OpenAI
        self._boto_client = None
        if not self._base_url:
            self._boto_client = boto3.client("bedrock-runtime", region_name=self._region)

    @observe(as_type="generation", name="bedrock_vision_extract_vehicle_card")
    async def extract_from_image(
        self, image_bytes: bytes, mime_type: str, file_storage_path: str = ""
    ) -> Dict[str, Any]:
        prompt = PromptExtraction()
        system_instruction = (
            "Eres un experto en OCR y extracción de cédulas verdes/azules de Argentina.\n"
            "Analiza minuciosamente la imagen de la cédula y devuelve OBLIGATORIAMENTE un único objeto JSON válido con esta estructura exacta:\n"
            "{\n"
            '  "vehicle_category": "CAR",\n'
            '  "domain": "dominio/patente (ej: AA123BB o AB123CD)" o null,\n'
            '  "brand": "marca del vehiculo (ej: Renault, Ford, Fiat)" o null,\n'
            '  "model": "modelo del vehiculo (ej: Kangoo, Focus, Cronos)" o null,\n'
            '  "year": anio como numero entero (ej: 2018) o null,\n'
            '  "vehicle_type": "tipo de vehiculo (ej: SEDAN, FURGON)" o null,\n'
            '  "use": "uso (ej: PARTICULAR)" o null,\n'
            '  "motor_number": "numero de motor" o null,\n'
            '  "chassis_number": "numero de chasis" o null,\n'
            '  "frame_number": null,\n'
            '  "engine_cc": null,\n'
            '  "expiration_date": "fecha vencimiento" o null,\n'
            '  "owner": {\n'
            '    "full_name": "nombre y apellido completo del titular" o null,\n'
            '    "dni": "numero de documento / DNI" o null,\n'
            '    "address": "domicilio completo" o null,\n'
            '    "postal_code": "codigo postal de 4 digitos deducido" o null\n'
            '  }\n'
            "}\n"
            "REGLAS:\n"
            "- Si no puedes leer o no figura un campo, pon null.\n"
            "- Responde ÚNICAMENTE el objeto JSON puro sin bloques markdown ni explicaciones adicionales."
        )

        response_text = ""

        # Modo 1: Bedrock Mantle / OpenAI-compatible endpoint
        if self._base_url and self._api_key:
            b64_image = base64.b64encode(image_bytes).decode("utf-8")
            url = f"{self._base_url.rstrip('/')}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_instruction},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:{mime_type};base64,{b64_image}"},
                            },
                        ],
                    },
                ],
                "temperature": 0.0,
            }

            async with httpx.AsyncClient(timeout=45.0) as http_client:
                res = await http_client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()
                response_text = data["choices"][0]["message"]["content"]

        # Modo 2: Boto3 Bedrock Runtime (Converse API)
        else:
            if not self._boto_client:
                self._boto_client = boto3.client("bedrock-runtime", region_name=self._region)

            img_format = "jpeg" if "jpeg" in mime_type or "jpg" in mime_type else "png"
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": {"format": img_format, "source": {"bytes": image_bytes}}},
                        {"text": f"{system_instruction}\n\n{prompt}"},
                    ],
                }
            ]

            import asyncio
            response = await asyncio.to_thread(
                self._boto_client.converse,
                modelId=self._model,
                messages=messages,
                inferenceConfig={"temperature": 0.0},
            )
            response_text = response["output"]["message"]["content"][0]["text"]

        try:
            langfuse_context.update_current_observation(
                model=self._model,
                input=f"Image ({len(image_bytes)} bytes, mime={mime_type})",
                output=response_text,
            )
        except Exception:
            pass

        # Limpiar posibles bloques markdown y extraer el objeto JSON
        cleaned_json = response_text.strip()
        if cleaned_json.startswith("```"):
            cleaned_json = cleaned_json.split("\n", 1)[1]
            if cleaned_json.endswith("```"):
                cleaned_json = cleaned_json.rsplit("\n", 1)[0]

        start = cleaned_json.find("{")
        end = cleaned_json.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned_json = cleaned_json[start : end + 1]

        raw_dict: Dict[str, Any] = {}
        try:
            raw_dict = json.loads(cleaned_json)
        except Exception:
            pass

        try:
            extracted = VehicleExtractionSchema.model_validate_json(cleaned_json)
        except Exception:
            extracted = VehicleExtractionSchema()

        domain = clean_str(extracted.domain or raw_dict.get("patente") or raw_dict.get("dominio"))
        motor = clean_str(extracted.motor_number or raw_dict.get("motor") or raw_dict.get("numero_motor"))
        chassis = clean_str(extracted.chassis_number or raw_dict.get("chasis") or raw_dict.get("numero_chasis"))
        frame = clean_str(extracted.frame_number or raw_dict.get("cuadro"))
        brand = clean_str(extracted.brand or raw_dict.get("marca"))
        model = clean_str(extracted.model or raw_dict.get("modelo"))

        year_val = extracted.year or raw_dict.get("year") or raw_dict.get("anio") or raw_dict.get("año")
        if year_val:
            try:
                year_val = int(year_val)
            except Exception:
                year_val = None

        vehicle_dict = None
        if domain or motor or chassis or frame or brand or model:
            vehicle_dict = {
                "dominio": domain,
                "marca": brand,
                "modelo": model,
                "year": year_val,
                "tipo": clean_str(extracted.vehicle_type or raw_dict.get("tipo")),
                "uso": clean_str(extracted.use or raw_dict.get("uso")),
                "chasis": chassis,
                "cuadro": frame,
                "motor": motor,
                "cilindrada": clean_str(extracted.engine_cc or raw_dict.get("cilindrada")),
                "vencimiento": clean_str(extracted.expiration_date or raw_dict.get("vencimiento")),
                "tipo_vehiculo": extracted.vehicle_category or raw_dict.get("tipo_vehiculo") or "CAR",
            }

        owner_raw = raw_dict.get("owner") or raw_dict.get("titular") or {}
        if not isinstance(owner_raw, dict):
            owner_raw = {}

        owner_full_name = clean_str(
            (extracted.owner.full_name if extracted.owner else None)
            or owner_raw.get("full_name")
            or owner_raw.get("nombre_completo")
            or raw_dict.get("titular")
        )
        owner_dni = clean_str(
            (extracted.owner.dni if extracted.owner else None)
            or owner_raw.get("dni")
            or owner_raw.get("documento")
            or raw_dict.get("dni")
        )
        owner_address = clean_str(
            (extracted.owner.address if extracted.owner else None)
            or owner_raw.get("address")
            or owner_raw.get("domicilio")
        )
        owner_cp = clean_str(
            (extracted.owner.postal_code if extracted.owner else None)
            or owner_raw.get("postal_code")
            or owner_raw.get("codigo_postal")
            or owner_raw.get("cp")
        )

        owner_dict = None
        if owner_full_name or owner_dni or owner_address or owner_cp:
            owner_dict = {
                "nombre_completo": owner_full_name,
                "documento": owner_dni,
                "domicilio": owner_address,
                "codigo_postal": owner_cp,
            }

        return {
            "vehicle": vehicle_dict,
            "owner": owner_dict,
        }

