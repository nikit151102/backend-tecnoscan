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

    cars = relationship("Car", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")

    class Config:
        orm_mode = True


class TransmissionType(Base):
    __tablename__ = 'transmission_types'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)

    cars = relationship("Car", back_populates="transmission_type")

    class Config:
        orm_mode = True

class CarBrand(Base):
    __tablename__ = "car_brand"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)

    cars = relationship("Car", back_populates="car_brand")

    class Config:
        orm_mode = True

class EngineVolume(Base):
    __tablename__ = "engine_vol"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Float, unique=True, nullable=False)

    cars = relationship("Car", back_populates="engine_vol")

    class Config:
        orm_mode = True

class Car(Base):
    __tablename__ = "car"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("car_brand.id"), nullable=False)
    model = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    engine_volume = Column(UUID(as_uuid=True), ForeignKey("engine_vol.id"), nullable=False)
    transmission_type_id = Column(UUID(as_uuid=True), ForeignKey("transmission_types.id"), nullable=False)
    vin_code = Column(String(17), nullable=False, unique=True)

    user = relationship("User", back_populates="cars", cascade="all", single_parent=True)
    car_brand = relationship("CarBrand", back_populates="cars", cascade="all", single_parent=True)
    engine_vol = relationship("EngineVolume", back_populates="cars", cascade="all", single_parent=True)
    transmission_type = relationship("TransmissionType", back_populates="cars", cascade="all", single_parent=True)
    applications = relationship("Application", back_populates="car", cascade="all", single_parent=True)



class Application(Base):
    __tablename__ = "application"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    car_id = Column(UUID(as_uuid=True), ForeignKey("car.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False) 
    problem = Column(String, nullable=False)

    car = relationship("Car", back_populates="applications")
    user = relationship("User", back_populates="applications")  

    class Config:
        orm_mode = True
