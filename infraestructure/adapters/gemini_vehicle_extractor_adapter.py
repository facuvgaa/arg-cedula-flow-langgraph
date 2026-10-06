from typing import Optional, Literal
from pydantic import BaseModel, Field
from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from domain.prompt.prompt_extraction import PromptExtraction
from google import genai
from google.genai import types
from domain.models.vehicle_card import VehicleCard
from domain.models.owner import Owner
from domain.models.motor_bike import MotorBike
from domain.models.car import Car

class OwnerSchema(BaseModel):
    full_name: str = Field(description="Nombre y apellido completo del titular")
    dni: Optional[str] = Field(None, description="Número de documento / DNI / CUIT del titular")
    address: Optional[str] = Field(None, description="Domicilio completo que figura en el reverso")


class VehicleExtractionSchema(BaseModel):
    vehicle_category: Literal["CAR", "MOTOBIKE"] = Field(
        description="Categoría del vehículo: CAR para automóvil/camioneta, MOTORBIKE para motocicleta/cuatriciclo"
    )

    domain: str = Field(description="Patente / Dominio del vehículo (ej: AA123CD, ABC123)")
    brand: str = Field(description="Marca del vehículo")
    model: str = Field(description="Modelo exacto")
    vehicle_type: str = Field(description="Tipo de vehículo (ej: SEDAN, HATCHBACK, MOTOCICLETA)")
    use: str = Field(description="Uso del vehículo (ej: PARTICULAR, PUBLICO)")
    motor_number: str = Field(description="Número de motor")
    expiration_date: str = Field(description="Fecha de vencimiento impresa o texto literal como SIN VENCIMIENTO")
    
    chassis_number: Optional[str] = Field(None, description="Número de chasis (solo para autos)")
    
    frame_number: Optional[str] = Field(None, description="Número de cuadro (solo para motos)")
    engine_cc: Optional[str] = Field(None, description="Cilindrada en cc (solo para motos)")

    owner: Optional[OwnerSchema] = Field(None, description="Datos del titular si están presentes en la imagen")


class VehicleExtractorAdapter(VehicleExtractorPort):
    def __init__(self, api_key:str, model_name: str = "gemini-3.8-flash"):
        self._client = genai.Client(api_key=api_key)
        _raw_model = model_name
        self._model_name = _raw_model.replace("models/", "")

    async def extract_from_image(self, image_bytes: bytes, mime_type: str, file_storage_path: str)-> VehicleCard:

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

        extracted_data = VehicleExtractionSchema.model_validate_json(response.text)

        domain_owner = None

        if extracted_data.owner:
            domain_owner= Owner(
                full_name=extracted_data.owner.full_name,
                dni=extracted_data.owner.dni,
                address=extracted_data.owner.address,
            )

        if extracted_data.vehicle_category == 'MOTOBIKE':
            vehicle = MotorBike(
                domain=extracted_data.domain,
                brand=extracted_data.brand,
                model=extracted_data.model,
                vehicle_type=extracted_data.vehicle_type,
                use=extracted_data.use,
                frame_number=extracted_data.frame_number or "",
                motor_number=extracted_data.motor_number,
                engine_cc=extracted_data.engine_cc or "",
                expiration_date=extracted_data.expiration_date,
            )

        if extracted_data.vehicle_category == 'CAR':
            vehicle = Car(
                domain=extracted_data.domain,
                brand=extracted_data.brand,
                model=extracted_data.model,
                vehicle_type=extracted_data.vehicle_type,
                use=extracted_data.use,
                chassis_number=extracted_data.chassis_number or "",
                motor_number=extracted_data.motor_number,
                expiration_date=extracted_data.expiration_date,
            )
        return VehicleCard(
            vehicle=vehicle,
            owner=domain_owner,
            contact=None,
        )
