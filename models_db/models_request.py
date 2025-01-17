from sqlalchemy import Column, Integer, String, ForeignKey, Text, Date, DECIMAL,Time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.uuid_generate_v4())
    lastname = Column(String(255))
    firstname = Column(String(255))
    middlename = Column(String(255))
    initials= Column(String(15))
    phone = Column(String(15))
    email = Column(String(255))
    login = Column(String(255))
    password = Column(String(255))
    iv = Column(String(255))
