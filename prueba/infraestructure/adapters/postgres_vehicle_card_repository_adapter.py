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
        owner = vehicle_card.owner
        domain = (vehicle.domain.strip().upper()) if (vehicle and vehicle.domain) else None

        db_card = None

        # 1. Buscar por patente si tenemos vehículo
        if domain and domain not in ("NO VISIBLE", "NULL", "NONE", "N/A", ""):
          stmt = (
              select(VehicleCardModel)
              .join(VehicleModel)
              .where(VehicleModel.domain == domain)
              .options(
                  selectinload(VehicleCardModel.vehicle),
                  selectinload(VehicleCardModel.owner),
                  selectinload(VehicleCardModel.contact),
              )
          )
          result = await session.execute(stmt)
          db_card = result.scalar_one_or_none()

          # Si no hay cédula con esa patente, ver si hay una cédula pendiente sin vehículo
          if not db_card:
            stmt_unlinked = (
                select(VehicleCardModel)
                .where(VehicleCardModel.vehicle_id.is_(None))
                .order_by(VehicleCardModel.created_at.desc())
                .options(
                    selectinload(VehicleCardModel.vehicle),
                    selectinload(VehicleCardModel.owner),
                    selectinload(VehicleCardModel.contact),
                )
            )
            res_u = await session.execute(stmt_unlinked)
            db_card = res_u.scalar_one_or_none()

        # 2. Si solo tenemos el dorso (owner) y no vino patente
        elif owner and (owner.dni or owner.full_name):
          # Buscar si hay alguna cédula creada recientemente sin titular para enlazarla
          stmt_pending = (
              select(VehicleCardModel)
              .where(VehicleCardModel.owner_id.is_(None))
              .order_by(VehicleCardModel.created_at.desc())
              .options(
                  selectinload(VehicleCardModel.vehicle),
                  selectinload(VehicleCardModel.owner),
                  selectinload(VehicleCardModel.contact),
              )
          )
          res_p = await session.execute(stmt_pending)
          db_card = res_p.scalar_one_or_none()

        # 3. Si encontramos una cédula para actualizar o enlazar
        if db_card:
          if vehicle and domain and domain not in ("NO VISIBLE", "NULL", "NONE", "N/A", ""):
            if db_card.vehicle:
              db_v = db_card.vehicle
              if vehicle.brand: db_v.brand = vehicle.brand
              if vehicle.model: db_v.model = vehicle.model
              if vehicle.vehicle_type: db_v.vehicle_type = vehicle.vehicle_type
              if vehicle.use: db_v.use = vehicle.use
              motor_val = getattr(vehicle, "motor_number", None) or getattr(vehicle, "engine_number", None)
              if motor_val: db_v.motor_number = motor_val
              if vehicle.expiration_date: db_v.expiration_date = vehicle.expiration_date
              if isinstance(vehicle, Car):
                db_v.category = "CAR"
                if vehicle.chassis_number: db_v.chassis_number = vehicle.chassis_number
              else:
                db_v.category = "MOTORBIKE"
                if vehicle.frame_number: db_v.frame_number = vehicle.frame_number
                if vehicle.engine_cc: db_v.engine_cc = vehicle.engine_cc
            else:
              motor_val = getattr(vehicle, "motor_number", None) or getattr(vehicle, "engine_number", "") or ""
              if isinstance(vehicle, Car):
                db_vehicle = VehicleModel(
                    domain=domain,
                    category="CAR",
                    brand=vehicle.brand or "",
                    model=vehicle.model or "",
                    vehicle_type=vehicle.vehicle_type or "",
                    use=vehicle.use or "",
                    motor_number=motor_val,
                    expiration_date=vehicle.expiration_date or "",
                    chassis_number=vehicle.chassis_number or "",
                )
              else:
                db_vehicle = VehicleModel(
                    domain=domain,
                    category="MOTORBIKE",
                    brand=vehicle.brand or "",
                    model=vehicle.model or "",
                    vehicle_type=vehicle.vehicle_type or "",
                    use=vehicle.use or "",
                    motor_number=motor_val,
                    expiration_date=vehicle.expiration_date or "",
                    frame_number=vehicle.frame_number or "",
                    engine_cc=vehicle.engine_cc or "",
                )
              session.add(db_vehicle)
              db_card.vehicle = db_vehicle

          if owner and (owner.full_name or owner.dni):
            if db_card.owner:
              if owner.full_name: db_card.owner.full_name = owner.full_name
              if owner.dni: db_card.owner.dni = owner.dni
              if owner.address: db_card.owner.address = owner.address
            else:
              # Buscar si el titular ya existe en la tabla owners
              existing_owner = None
              if owner.dni:
                st_o = select(OwnerModel).where(OwnerModel.dni == str(owner.dni).strip())
                existing_owner = (await session.execute(st_o)).scalar_one_or_none()

              if existing_owner:
                if owner.full_name: existing_owner.full_name = owner.full_name
                if owner.address: existing_owner.address = owner.address
                db_card.owner = existing_owner
              else:
                new_owner = OwnerModel(
                    full_name=owner.full_name or "",
                    dni=owner.dni,
                    address=owner.address,
                )
                session.add(new_owner)
                db_card.owner = new_owner

        # 4. Si no existía ninguna cédula previa
        else:
          db_vehicle = None
          if vehicle and domain and domain not in ("NO VISIBLE", "NULL", "NONE", "N/A", ""):
            motor_val = getattr(vehicle, "motor_number", None) or getattr(vehicle, "engine_number", "") or ""
            if isinstance(vehicle, Car):
              db_vehicle = VehicleModel(
                  domain=domain,
                  category="CAR",
                  brand=vehicle.brand or "",
                  model=vehicle.model or "",
                  vehicle_type=vehicle.vehicle_type or "",
                  use=vehicle.use or "",
                  motor_number=motor_val,
                  expiration_date=vehicle.expiration_date or "",
                  chassis_number=vehicle.chassis_number or "",
              )
            else:
              db_vehicle = VehicleModel(
                  domain=domain,
                  category="MOTORBIKE",
                  brand=vehicle.brand or "",
                  model=vehicle.model or "",
                  vehicle_type=vehicle.vehicle_type or "",
                  use=vehicle.use or "",
                  motor_number=motor_val,
                  expiration_date=vehicle.expiration_date or "",
                  frame_number=vehicle.frame_number or "",
                  engine_cc=vehicle.engine_cc or "",
              )

          db_owner = None
          if owner and (owner.full_name or owner.dni):
            existing_owner = None
            if owner.dni:
              st_o = select(OwnerModel).where(OwnerModel.dni == str(owner.dni).strip())
              existing_owner = (await session.execute(st_o)).scalar_one_or_none()

            if existing_owner:
              if owner.full_name: existing_owner.full_name = owner.full_name
              if owner.address: existing_owner.address = owner.address
              db_owner = existing_owner
            else:
              db_owner = OwnerModel(
                  full_name=owner.full_name or "",
                  dni=owner.dni,
                  address=owner.address,
              )
              session.add(db_owner)

          db_contact = None
          if vehicle_card.contact:
            db_contact = ContactOwnerModel(
                phone_number=vehicle_card.contact.phone_number,
                email=vehicle_card.contact.email,
            )

          if db_vehicle:
            new_card = VehicleCardModel(
                file_storage_path="",
                vehicle=db_vehicle,
                owner=db_owner,
                contact=db_contact,
            )
            session.add(new_card)
          elif db_owner:
            session.add(db_owner)

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

      if not db_card or not db_card.vehicle:
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
            engine_number=db_v.motor_number,
            expiration_date=db_v.expiration_date,
            engine_cc=db_v.engine_cc or "",
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