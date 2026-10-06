from typing import Optional
from domain.models.car import Car
from domain.models.contact_owner import ContactOwner
from domain.models.motor_bike import MotorBike
from domain.models.owner import Owner
from domain.models.vehicle_card import VehicleCard
from domain.ports.vehicle_card_repository_port import VehicleCardRepositoryPort
from infraestructure.database.models import (
    ContactOwnerModel,
    OwnerModel,
    VehicleCardModel,
    VehicleModel,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload


class PostgresVehicleCardRepositoryAdapter(VehicleCardRepositoryPort):

  def __init__(self, session_factory: async_sessionmaker):
    self._session_factory = session_factory

  async def save(self, vehicle_card: VehicleCard) -> None:
    async with self._session_factory() as session:
      async with session.begin():
        vehicle = vehicle_card.vehicle

        if isinstance(vehicle, Car):
          db_vehicle = VehicleModel(
              domain=vehicle.domain.upper(),
              category="CAR",
              brand=vehicle.brand,
              model=vehicle.model,
              vehicle_type=vehicle.vehicle_type,
              use=vehicle.use,
              motor_number=vehicle.motor_number,
              expiration_date=vehicle.expiration_date,
              chassis_number=vehicle.chassis_number,
          )
        else:
          db_vehicle = VehicleModel(
              domain=vehicle.domain.upper(),
              category="MOTORBIKE",
              brand=vehicle.brand,
              model=vehicle.model,
              vehicle_type=vehicle.vehicle_type,
              use=vehicle.use,
              motor_number=vehicle.motor_number,
              expiration_date=vehicle.expiration_date,
              frame_number=vehicle.frame_number,
              engine_cc=vehicle.engine_cc,
          )

        db_owner = None
        if vehicle_card.owner:
          db_owner = OwnerModel(
              full_name=vehicle_card.owner.full_name,
              dni=vehicle_card.owner.dni,
              address=vehicle_card.owner.address,
          )

        # 3. Instanciamos el contacto si existe
        db_contact = None
        if vehicle_card.contact:
          db_contact = ContactOwnerModel(
              phone_number=vehicle_card.contact.phone_number,
              email=vehicle_card.contact.email,
          )

        db_card = VehicleCardModel(
            file_storage_path="",
            vehicle=db_vehicle,
            owner=db_owner,
            contact=db_contact,
        )

        session.add(db_card)

  async def get_by_domain(self, domain_code: str) -> Optional[VehicleCard]:
    async with self._session_factory() as session:
      stmt = (
          select(VehicleCardModel)
          .join(VehicleModel)
          .where(VehicleModel.domain == domain_code.upper())
          .options(
              selectinload(VehicleCardModel.vehicle),
              selectinload(VehicleCardModel.owner),
              selectinload(VehicleCardModel.contact),
          )
      )

      result = await session.execute(stmt)
      db_card = result.scalar_one_or_none()

      if not db_card:
        return None

      db_v = db_card.vehicle
      if db_v.category == "CAR":
        domain_vehicle = Car(
            domain=db_v.domain,
            brand=db_v.brand,
            model=db_v.model,
            vehicle_type=db_v.vehicle_type,
            use=db_v.use,
            chassis_number=db_v.chassis_number or "",
            motor_number=db_v.motor_number,
            expiration_date=db_v.expiration_date,
        )
      else:
        domain_vehicle = MotorBike(
            domain=db_v.domain,
            brand=db_v.brand,
            model=db_v.model,
            vehicle_type=db_v.vehicle_type,
            use=db_v.use,
            frame_number=db_v.frame_number or "",
            motor_number=db_v.motor_number,
            engine_cc=db_v.engine_cc or "",
            expiration_date=db_v.expiration_date,
        )

      domain_owner = None
      if db_card.owner:
        domain_owner = Owner(
            full_name=db_card.owner.full_name,
            dni=db_card.owner.dni,
            address=db_card.owner.address,
        )

      domain_contact = None
      if db_card.contact:
        domain_contact = ContactOwner(
            phone_number=db_card.contact.phone_number,
            email=db_card.contact.email,
        )

      return VehicleCard(
          vehicle=domain_vehicle, owner=domain_owner, contact=domain_contact
      )