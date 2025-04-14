from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, HTTPException, Depends
from database.database_app import engine_a, get_session
from models import Application, Car
from pydantic import BaseModel

router = APIRouter()

async def create_application(
    db: AsyncSession,
    car_id: UUID,
    user_id: UUID,
    problem: str
) -> Application:
    try:
        application = Application(car_id=car_id, user_id=user_id, problem=problem)
        db.add(application)
        await db.commit()
        await db.refresh(application)
        return application
    except Exception as e:
        await db.rollback()
        print(f"Error saving application: {e}")
        raise

async def get_application(db: AsyncSession, app_id: UUID) -> Application:
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.car).selectinload(Car.car_brand),
                 selectinload(Application.car).selectinload(Car.transmission_type))
        .filter(Application.id == app_id)
    )
    return result.scalar_one_or_none()


async def get_all_user_applications(db: AsyncSession, user_id: UUID) -> dict:
    try:
        query = (
            select(Application)
            .filter(Application.user_id == user_id)
            .options(
                selectinload(Application.car)
                .selectinload(Car.car_brand) 
            )
            .options(
                selectinload(Application.car)
                .selectinload(Car.engine_vol) 
            )
            .options(
                selectinload(Application.car)
                .selectinload(Car.transmission_type) 
            )
        )

        result = await db.execute(query)

        applications = result.scalars().all()

        if not applications:
            return {"message": "Заявки не найдены"}
        
        return {"message": "Список всех заявок пользователя", "data": applications}

    except Exception as e:
        return {"message": "Ошибка при получении данных", "error": str(e)}




async def get_current_application(db: AsyncSession, resume_id: str):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.user), selectinload(Application.car_brand), selectinload(Application.transmission_type))
        .filter(Application.id == resume_id)
    )
    return result.scalar_one_or_none() 


async def get_all_applications(db: AsyncSession) -> list:

    query = (
        select(Application)
        .options(
            selectinload(Application.car)  
            .selectinload(Car.car_brand) 
        )
        .options(
            selectinload(Application.car)
            .selectinload(Car.engine_vol)  
        )
        .options(
            selectinload(Application.car)
            .selectinload(Car.transmission_type)  
        )
    )
      
    result = await db.execute(query)
    return result.scalars().all()


async def update_application(
    db: AsyncSession,
    app_id: UUID,
    model: str = None,
    year: int = None,
    engine_volume: Decimal = None,
    transmission_type_id: UUID = None,
    vin_code: str = None,
    problem: str = None
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
        if problem:
            application.problem = problem
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



class ApplicationCreateRequest(BaseModel):
    user_id: UUID
    car_id: UUID
    problem: str


from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
from static.template.token import decryptToken

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
@router.post("/", summary="Создание новой заявки.")
async def create_application_route(
    request: ApplicationCreateRequest,  
    session: AsyncSession = Depends(get_session)
):
    application = await create_application(
        session, request.car_id, request.user_id, request.problem
    )
    return {
        "message": "Заявка успешно создана",
        "data": {
            "id": application.id,
            "problem": application.problem,
            "car_id": application.car_id
        }
    }

@router.get("/user/data", summary="Получение всех заявок пользователя.")
async def get_all_user_applications_route(session: AsyncSession = Depends(get_session), token: str = Depends(oauth2_scheme)):
    if token.startswith("Bearer "):
        token = token[7:]
    decoded_token = decryptToken(token)
    user_id = decoded_token.get("id")

    apps = await get_all_user_applications(session, user_id)
    return apps


@router.get("/application/{app_id}", summary="Получение заявки по ID.")
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
    

@router.put("/{app_id}", summary="Обновление заявки по ID.")
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
