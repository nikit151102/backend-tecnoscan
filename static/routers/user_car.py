from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from models import Car
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from static.template.token import decryptToken
from models import User
from database.database_app import get_session

class CarCreateRequest(BaseModel):
    user_id: UUID
    brand_id: UUID
    model: str
    year: int
    engine_volume: UUID
    transmission_type_id: UUID
    vin_code: str

class CarUpdateRequest(BaseModel):
    brand_id: Optional[UUID]
    model: Optional[str]
    year: Optional[int]
    engine_volume: Optional[UUID]
    transmission_type_id: Optional[UUID]
    vin_code: Optional[str]


async def create_car(db: AsyncSession, car_data: CarCreateRequest, current_user_id: UUID) -> Car:
    if car_data.user_id != current_user_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав для создания этого автомобиля.")
    car = Car(**car_data.dict())
    db.add(car)
    await db.commit()
    await db.refresh(car)
    return car


async def get_car(db: AsyncSession, car_id: UUID) -> Optional[Car]:
    result = await db.execute(select(Car).filter(Car.id == car_id))
    return result.scalar_one_or_none()

async def get_all_cars(db: AsyncSession, current_user_id: UUID) -> list[Car]:
    result = await db.execute(select(Car).filter(Car.user_id == current_user_id))
    return result.scalars().all()


async def update_car(db: AsyncSession, car_id: UUID, updates: CarUpdateRequest, current_user_id: UUID) -> Optional[Car]:
    car = await get_car(db, car_id)
    if car and car.user_id == current_user_id:
        for key, value in updates.dict(exclude_unset=True).items():
            setattr(car, key, value)
        await db.commit()
        await db.refresh(car)
        return car
    return None


async def delete_car(db: AsyncSession, car_id: UUID, current_user_id: UUID) -> bool:
    car = await get_car(db, car_id)
    if car and car.user_id == current_user_id:
        await db.delete(car)
        await db.commit()
        return True
    return False



router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def verify_token_and_user(token: str, session: AsyncSession):
    if token.startswith("Bearer "):
        token = token[7:]
    decoded_token = decryptToken(token)
    print("decoded_token", decoded_token)
    user_id = decoded_token.get("id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Токен недействителен или истек.")

    result = await session.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден.")

    return user_id


@router.post("/", summary="Создать автомобиль")
async def create_car_route(
    request: CarCreateRequest,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme)
):
    try:
        current_user_id = await verify_token_and_user(token, session)
        car = await create_car(session, request, current_user_id)
        return {"message": "Автомобиль успешно создан", "data": car}
    except Exception as e:
        print(f"Ошибка при создании автомобиля: {e}")
        return JSONResponse(
            content={"code": 500, "message": "Ошибка сервера при обработке запроса."},
            status_code=500
        )


@router.put("/{car_id}", summary="Обновить данные автомобиля")
async def update_car_route(
    car_id: UUID,
    request: CarUpdateRequest,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme)
):
    current_user_id = await verify_token_and_user(token, session)
    updated_car = await update_car(session, car_id, request, current_user_id)
    if updated_car:
        return {"message": "Автомобиль успешно обновлен", "data": updated_car}
    raise HTTPException(status_code=404, detail="Автомобиль не найден")


@router.delete("/{car_id}", summary="Удалить автомобиль по ID")
async def delete_car_route(
    car_id: UUID,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme)
):
    current_user_id = await verify_token_and_user(token, session)
    success = await delete_car(session, car_id, current_user_id)
    if success:
        return {"message": "Автомобиль успешно удален"}
    raise HTTPException(status_code=404, detail="Автомобиль не найден")



@router.get("/{car_id}", summary="Получить автомобиль по ID")
async def get_car_route(
    car_id: UUID,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme)
):
    await verify_token_and_user(token, session)
    car = await get_car(session, car_id)
    if car:
        return {"message": "Автомобиль найден", "data": car}
    raise HTTPException(status_code=404, detail="Автомобиль не найден")


@router.get("/", summary="Получить все личные автомобили")
async def get_all_cars_route(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(oauth2_scheme)
):
    current_user_id = await verify_token_and_user(token, session)
    cars = await get_all_cars(session, current_user_id)
    return {"message": "Список всех автомобилей", "data": cars}

