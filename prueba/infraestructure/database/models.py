from datetime import datetime
import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class OwnerModel(Base):
  __tablename__ = "owners"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  full_name = Column(String, nullable=False)
  dni = Column(String, nullable=True)
  address = Column(String, nullable=True)


class ContactOwnerModel(Base):
  __tablename__ = "contact_owners"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  phone_number = Column(String, nullable=True)
  email = Column(String, nullable=True)


class VehicleModel(Base):
  __tablename__ = "vehicles"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  domain = Column(String, unique=True, index=True, nullable=False)
  category = Column(
      String, nullable=False
  ) 
  brand = Column(String, nullable=False)
  model = Column(String, nullable=False)
  vehicle_type = Column(String, nullable=False)
  use = Column(String, nullable=False)
  motor_number = Column(String, nullable=False)
  expiration_date = Column(String, nullable=False)

  chassis_number = Column(String, nullable=True)

  frame_number = Column(String, nullable=True)
  engine_cc = Column(String, nullable=True)


class VehicleCardModel(Base):
  __tablename__ = "vehicle_cards"

  id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
  file_storage_path = Column(String, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

  # Relaciones
  vehicle_id = Column(
      UUID(as_uuid=True),
      ForeignKey("vehicles.id"),
      nullable=True,
      unique=True,
  )
  owner_id = Column(
      UUID(as_uuid=True), ForeignKey("owners.id"), nullable=True
  )
  contact_id = Column(
      UUID(as_uuid=True), ForeignKey("contact_owners.id"), nullable=True
  )

  vehicle = relationship("VehicleModel", cascade="all, delete")
  owner = relationship("OwnerModel", cascade="all, delete")
  contact = relationship("ContactOwnerModel", cascade="all, delete")