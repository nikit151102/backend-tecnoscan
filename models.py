from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lastname = Column(String(255))
    firstname = Column(String(255))
    middlename = Column(String(255))
    initials = Column(String(15))
    phone = Column(String(15))
    email = Column(String(255))
    login = Column(String(255))
    password = Column(String(255))
    iv = Column(String(255))

    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")


class TransmissionType(Base):
    __tablename__ = 'transmission_types'  # Таблица должна называться transmission_types

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)

    applications = relationship("Application", back_populates="transmission_type")
    class Config:
            orm_mode = True

class CarBrand(Base):
    __tablename__ = "car_brand"  # Марки автомобиля

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)

    applications = relationship("Application", back_populates="car_brand")
    class Config:
        orm_mode = True

class EngineVolume(Base):
    __tablename__ = "engine_vol"  # Объем двигателя

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Float, unique=True, nullable=False)

    applications = relationship("Application", back_populates="engine_vol")
    class Config:
        orm_mode = True


class Application(Base):
    __tablename__ = "application"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("car_brand.id"), nullable=False)
    model = Column(String(255), nullable=False)  # Модель автомобиля
    year = Column(Integer, nullable=False)  # Год выпуска
    engine_volume = Column(UUID(as_uuid=True), ForeignKey("engine_vol.id"), nullable=False)  # Объем двигателя
    transmission_type_id = Column(UUID(as_uuid=True), ForeignKey("transmission_types.id"), nullable=False)  # Ссылка на тип коробки передач
    vin_code = Column(String(17), nullable=False)  # VIN-код

    # Связи с другими таблицами
    user = relationship("User", back_populates="applications")
    transmission_type = relationship("TransmissionType", back_populates="applications")
    car_brand = relationship("CarBrand", back_populates="applications")
    engine_vol = relationship("EngineVolume", back_populates="applications")
    class Config:
            orm_mode = True