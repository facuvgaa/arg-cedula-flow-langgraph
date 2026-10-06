from domain.ports.file_storage_port import FileStoragePort
from domain.ports.vehicle_card_repository_port import VehicleCardRepositoryPort
from domain.ports.vehicle_extractor_port import VehicleExtractorPort
from domain.models.vehicle_card import VehicleCard  

class ProcessVehicleCardUseCase:
    def __init__(self, storage_port: FileStoragePort, extractor_port:  VehicleExtractorPort, repository_port: VehicleCardRepositoryPort):

        self._storage_port = storage_port
        self._extractor_port = extractor_port
        self._repository_port = repository_port

    async def execute(self, file_bytes: bytes, file_name: str, mime_type:str)-> VehicleCard:
        file_storage_path = await self._storage_port.upload(file_bytes=file_bytes, file_name=file_name, content_type=mime_type)

        vehicle_card = await self._extractor_port.extract_from_image(image_bytes=file_bytes,mime_type=mime_type,file_storage_path=file_name)

        await self._repository_port.save(vehicle_card=vehicle_card)
        return vehicle_card