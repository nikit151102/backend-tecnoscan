from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class ConnectModel(BaseModel):
    UserLogin: str
    UserPassword: str

class registrationModel(BaseModel):
    Login: str
    Email: str
    Password: str


class MailRequest(BaseModel):
    email: EmailStr  
    token: str 
    generatePassword: str

class UpdateUserModel(BaseModel):
    lastname: Optional[str]
    firstname: Optional[str]
    middlename: Optional[str]
    phone: Optional[str]
    email: Optional[EmailStr]
    login: Optional[str]
