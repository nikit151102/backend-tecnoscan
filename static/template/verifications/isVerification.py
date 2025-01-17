from fastapi import APIRouter
from fastapi import Request
from database.database_app import get_session,engine_a
from models_db.models_request import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

isVerification = APIRouter()

@isVerification.get("/{token}")
async def check_token_email(token):
    async with AsyncSession(engine_a) as session:

        existing_client = await session.execute(select(User).filter(User.emailtoken == str(token)))
        existing_client = existing_client.scalar()
        if existing_client:
  
            existing_client.emailtoken = ""   
            await session.commit()  
            return "Проверка"
        else:
            return "Не нужна"