from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from domain.prompt.prompt_extraction import PromptExtraction
from google import genai
from google.genai import types

def clean_str(val: Optional[str]) -> Optional[str]:
    if val is None:
        return None
    cleaned = str(val).strip()
    if cleaned.upper() in ("", "NO VISIBLE", "NULL", "NONE", "NO APLICA", "N/A", "DESCONOCIDO", "-", "UNDEFINED"):
        return None
    return cleaned

class OwnerSchema(BaseModel):
    full_name: Optional[str] = Field(None, description="Nombre y apellido completo del titular, o null si no se observa")
    dni: Optional[str] = Field(None, description="Número de documento / DNI / CUIT del titular, o null si no se observa")
    address: Optional[str] = Field(None, description="Domicilio completo que figura en el reverso, o null si no se observa")
    postal_code: Optional[str] = Field(
        None,
        description="Código postal de 4 dígitos deducido de la localidad/provincia del domicilio (ej: 4000 para Tucumán, 5000 para Córdoba, 1000 para CABA). Si no se puede deducir, null."
    )

class VehicleExtractionSchema(BaseModel):
    vehicle_category: Optional[Literal["CAR", "MOTOBIKE"]] = Field(
        None, description="Categoría del vehículo si se detecta el frente"
    )
    domain: Optional[str] = Field(None, description="Patente / Dominio del vehículo, o null si no se observa")
    brand: Optional[str] = Field(None, description="Marca del vehículo, o null si no se observa")
    model: Optional[str] = Field(None, description="Modelo exacto, o null si no se observa")
    year: Optional[int] = Field(None, description="Año de fabricación/modelo si figura explícito en el texto o modelo, o null")
    vehicle_type: Optional[str] = Field(None, description="Tipo de vehículo, o null si no se observa")
    use: Optional[str] = Field(None, description="Uso del vehículo, o null si no se observa")
    motor_number: Optional[str] = Field(None, description="Número de motor, o null si no se observa")
    expiration_date: Optional[str] = Field(None, description="Fecha de vencimiento impresa, o null si no se observa")
    chassis_number: Optional[str] = Field(None, description="Número de chasis (autos), o null si no se observa")
    frame_number: Optional[str] = Field(None, description="Número de cuadro (motos), o null si no se observa")
    engine_cc: Optional[str] = Field(None, description="Cilindrada en cc (motos), o null si no se observa")

    owner: Optional[OwnerSchema] = Field(None, description="Datos del titular si están presentes en la imagen")

class VehicleExtractorAdapter(VehicleExtractorPort):
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name.replace("models/", "")

    async def extract_from_image(
        self, image_bytes: bytes, mime_type: str, file_storage_path: str = ""
    ) -> Dict[str, Any]:
        prompt = PromptExtraction()

        response = await self._client.aio.models.generate_content(
            model=self._model_name,
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VehicleExtractionSchema,
                temperature=0.0,
            ),
        )

        extracted = VehicleExtractionSchema.model_validate_json(response.text)

        domain = clean_str(extracted.domain)
        motor = clean_str(extracted.motor_number)
        chassis = clean_str(extracted.chassis_number)
        frame = clean_str(extracted.frame_number)
        brand = clean_str(extracted.brand)

        vehicle_dict = None
        # Solo se considera que se detectó el vehículo si tiene al menos dominio o motor o chasis o marca
        if domain or motor or chassis or frame or brand:
            vehicle_dict = {
                "dominio": domain,
                "marca": brand,
                "modelo": clean_str(extracted.model),
                "year": extracted.year,
                "tipo": clean_str(extracted.vehicle_type),
                "uso": clean_str(extracted.use),
                "chasis": chassis,
                "cuadro": frame,
                "motor": motor,
                "cilindrada": clean_str(extracted.engine_cc),
                "vencimiento": clean_str(extracted.expiration_date),
                "tipo_vehiculo": extracted.vehicle_category or "CAR",
            }

        owner_dict = None
        if extracted.owner:
            full_name = clean_str(extracted.owner.full_name)
            dni = clean_str(extracted.owner.dni)
            address = clean_str(extracted.owner.address)
            postal_code = clean_str(extracted.owner.postal_code)
            if full_name or dni or address or postal_code:
                owner_dict = {
                    "nombre_completo": full_name,
                    "documento": dni,
                    "domicilio": address,
                    "codigo_postal": postal_code,
                }

        return {
            "vehicle": vehicle_dict,
            "owner": owner_dict,
        }