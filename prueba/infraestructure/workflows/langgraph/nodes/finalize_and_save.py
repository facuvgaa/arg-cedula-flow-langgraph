from typing import Any, Dict
from domain.models.motor_bike import MotorBike
from domain.models.car import Car
from domain.models.owner import Owner
from domain.models.vehicle_card import VehicleCard
from domain.ports.vehicle_card_repository_port import VehicleCardRepositoryPort
from infraestructure.workflows.langgraph.cedula_workflow_state import CedulaWorkflowState

class FinalizeAndSave:
    def __init__(self, vehicle_repo: VehicleCardRepositoryPort):
        self._repo = vehicle_repo

    async def __call__(self, state: CedulaWorkflowState) -> Dict[str, Any]:
        v_data = state.get("vehicle_data") or {}
        o_data = state.get("owner_data") or {}

        vehicle_entity = None
        if v_data and v_data.get("dominio"):
            vehicle_type = (v_data.get("tipo_vehiculo") or "CAR").upper()
            if vehicle_type == "MOTORBIKE":
                vehicle_entity = MotorBike(
                    domain=v_data.get("dominio") or "",
                    brand=v_data.get("marca") or "",
                    model=v_data.get("modelo") or "",
                    vehicle_type=v_data.get("tipo") or "",
                    use=v_data.get("uso") or "",
                    frame_number=v_data.get("chasis") or v_data.get("cuadro") or "",
                    engine_number=v_data.get("motor") or "",
                    expiration_date=v_data.get("vencimiento") or "",
                    engine_cc=v_data.get("cilindrada") or "",
                )
            else:
                vehicle_entity = Car(
                    domain=v_data.get("dominio") or "",
                    brand=v_data.get("marca") or "",
                    model=v_data.get("modelo") or "",
                    vehicle_type=v_data.get("tipo") or "",
                    use=v_data.get("uso") or "",
                    chassis_number=v_data.get("chasis") or "",
                    motor_number=v_data.get("motor") or "",
                    expiration_date=v_data.get("vencimiento") or "",
                )

        owner_entity = None
        if o_data and (o_data.get("documento") or o_data.get("nombre_completo")):
            owner_entity = Owner(
                full_name=o_data.get("nombre_completo") or o_data.get("titular_nombre") or "",
                dni=o_data.get("documento") or o_data.get("titular_documento"),
                address=o_data.get("domicilio"),
            )

        storage_path = state.get("front_storage_path") or state.get("back_storage_path") or state.get("current_storage_path") or ""

        vehicle_card = VehicleCard(
            vehicle=vehicle_entity,
            owner=owner_entity,
            contact=None,
        )

        # Guardar inmediatamente en Postgres lo que tengamos
        await self._repo.save(vehicle_card)

        # Determinar status y mensaje final
        if vehicle_entity and owner_entity:
            return {
                "status": "COMPLETED",
                "message": "¡Cédula completa! Todos los datos fueron guardados y vinculados con éxito.",
            }
        elif vehicle_entity:
            return {
                "status": "WAITING_BACK",
                "message": "Frente recibido y guardado. Por favor, envíame la cara trasera (dorso) para completar los datos del titular.",
            }
        elif owner_entity:
            return {
                "status": "WAITING_FRONT",
                "message": "Cara trasera recibida y guardada. Por favor, envíame la cara frontal para completar los datos del vehículo.",
            }
        else:
            return {
                "status": "ERROR",
                "message": "No se pudieron extraer datos válidos de la imagen.",
            }