from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import Application
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import selectinload

async def create_application(
    db: AsyncSession,
    user_id: UUID,
    brand_id: UUID,
    model: str,
    year: int,
    engine_volume_id: UUID,
    transmission_type_id: UUID,
    vin_code: str
) -> Application:
    application = Application(
        user_id=user_id,
        brand_id=brand_id,
        model=model,
        year=year,
        engine_volume=engine_volume_id,
        transmission_type_id=transmission_type_id,
        vin_code=vin_code
    )
    db.add(application)
    await db.flush()

    current_application = await get_current_application(db, application.id)

    if current_application:
        return {**current_application.__dict__, 'user': current_application.user.__dict__, 'car_brand': application.car_brand.__dict__, 'transmission_type': current_application.transmission_type.__dict__}
    return None

async def get_current_application(db: AsyncSession, resume_id: str):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.user), selectinload(Application.car_brand), selectinload(Application.transmission_type))
        .filter(Application.id == resume_id)
    )
    return result.scalar_one_or_none() 

async def get_application(db: AsyncSession, app_id: UUID) -> Application:
    result = await db.execute(select(Application).filter(Application.id == app_id))
    return result.scalar()

async def get_all_applications(db: AsyncSession) -> list:
    result = await db.execute(select(Application))
    return result.scalars().all()

async def get_all_user_applications(db: AsyncSession, user_id: UUID) -> list:
    result = await db.execute(select(Application).filter(Application.user_id == user_id))
    return result.scalars().all()

async def update_application(
    db: AsyncSession,
    app_id: UUID,
    model: str = None,
    year: int = None,
    engine_volume: Decimal = None,
    transmission_type_id: UUID = None,
    vin_code: str = None
) -> Application:
    application = await get_application(db, app_id)
    if application:
        if model:
            application.model = model
        if year:
            application.year = year
        if engine_volume:
            application.engine_volume = engine_volume
        if transmission_type_id:
            application.transmission_type_id = transmission_type_id
        if vin_code:
            application.vin_code = vin_code
        await db.commit()
        await db.refresh(application)
        return application
    return None

async def delete_application(db: AsyncSession, app_id: UUID) -> bool:
    application = await get_application(db, app_id)
    if application:
        await db.delete(application)
        await db.commit()
        return True
    return False



from fastapi import APIRouter, HTTPException
from uuid import UUID
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from database.database_app import engine_a
from models import Application

router = APIRouter()

@router.post("/", summary="Создание новой заявки.")
async def create_application_route(
    user_id: UUID,
    brand_id: UUID,
    model: str,
    year: int,
    engine_volume: UUID,
    transmission_type_id: UUID,
    vin_code: str
):
    async with AsyncSession(engine_a) as session:
        application = await create_application(
            session, user_id, brand_id, model, year, engine_volume, transmission_type_id, vin_code
        )
        print('application',application)
        return {
            "message": "Заявка успешно создана",
            "data": {
                "id": application['id'],
                "user": {
                    "id": application['user']['id'],
                },
                "car_brand": {
                    "id": application['car_brand']['id'],
                    "name": application['car_brand']['name']  
                },
                "transmission_type": {
                    "id": application['transmission_type']['id'],
                    "name": application['transmission_type']['name']  
                },
                "model": application['model'],
                "year": application['year'],
                "engine_volume": application['engine_volume'],
                "vin_code": application['vin_code']
            }
        }

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from static.template.token import decryptToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/user/data", summary="Получение списка всех заявок пользователя.")
async def get_all_user_applications_route(token: str = Depends(oauth2_scheme)):
    if token.startswith("Bearer "):
        token = token[7:]  
    decoded_token = decryptToken(token)
    print("decoded_token",decoded_token)
    user_id = decoded_token.get("id")
    print("user_id",user_id)
    async with AsyncSession(engine_a) as session:
        applications = await get_all_user_applications(session, user_id)
        return {"message": "Список всех заявок пользователя", "data": applications}   


@router.get("/{app_id}", summary="Получение заявки по ID.")
async def get_application_route(app_id: UUID):
    async with AsyncSession(engine_a) as session:
        application = await get_application(session, app_id)
        if application:
            return {"message": "Заявка найдена", "data": application}
        raise HTTPException(status_code=404, detail="Заявка не найдена")

@router.get("/all/data", summary="Получение списка всех заявок.")
async def get_all_applications_route():
    async with AsyncSession(engine_a) as session:
        applications = await get_all_applications(session)
        return {"message": "Список всех заявок", "data": applications}
    

@router.patch("/{app_id}", summary="Обновление заявки по ID.")
async def update_application_route(
    app_id: UUID,
    model: str = None,
    year: int = None,
    engine_volume: Decimal = None,
    transmission_type_id: UUID = None,
    vin_code: str = None
):
    async with AsyncSession(engine_a) as session:
        application = await update_application(
            session, app_id, model, year, engine_volume, transmission_type_id, vin_code
        )
        if application:
            return {"message": "Заявка успешно обновлена", "data": application}
        raise HTTPException(status_code=404, detail="Заявка не найдена")

@router.delete("/{app_id}", summary="Удаление заявки по ID.")
async def delete_application_route(app_id: UUID):
    async with AsyncSession(engine_a) as session:
        success = await delete_application(session, app_id)
        if success:
            return {"message": "Заявка успешно удалена"}
        raise HTTPException(status_code=404, detail="Заявка не найдена")
