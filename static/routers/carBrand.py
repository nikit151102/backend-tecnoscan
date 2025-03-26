from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from database.database_app import engine_a  
from sqlalchemy.future import select
from models import CarBrand

async def create_car_brand(db: AsyncSession, name: str) -> CarBrand:
    car_brand = CarBrand(name=name)
    db.add(car_brand)
    await db.commit()
    await db.refresh(car_brand)
    return car_brand

async def get_car_brand(db: AsyncSession, brand_id: UUID) -> CarBrand:
    result = await db.execute(select(CarBrand).filter(CarBrand.id == brand_id))
    return result.scalar()

async def get_all_car_brands(db: AsyncSession) -> list:
    result = await db.execute(select(CarBrand))
    return result.scalars().all()

async def update_car_brand(db: AsyncSession, brand_id: UUID, name: str) -> CarBrand:
    car_brand = await get_car_brand(db, brand_id)
    if car_brand:
        car_brand.name = name
        await db.commit()
        await db.refresh(car_brand)
        return car_brand
    return None

async def delete_car_brand(db: AsyncSession, brand_id: UUID) -> bool:
    car_brand = await get_car_brand(db, brand_id)
    if car_brand:
        await db.delete(car_brand)
        await db.commit()
        return True
    return False


router = APIRouter()

@router.post("/", summary="Создание новой марки автомобиля.")
async def create_car_brand_route(name: str):
    async with AsyncSession(engine_a) as session:
        car_brand = await create_car_brand(session, name)
        return {"message": "Марка автомобиля успешно создан", "data": car_brand}

@router.get("/{brand_id}", summary="Получение марки автомобиля по ID.")
async def get_car_brand_route(brand_id: UUID):
    async with AsyncSession(engine_a) as session:
        car_brand = await get_car_brand(session, brand_id)
        if car_brand:
            return {"message": "Марка автомобиля найден", "data": car_brand}
        raise HTTPException(status_code=404, detail="Марка автомобиля не найден")

@router.get("/", summary="Получение списка всех марок автомобилей.")
async def get_all_car_brands_route():
    async with AsyncSession(engine_a) as session:
        car_brands = await get_all_car_brands(session)
        return {"message": "Список марок автомобилей", "data": car_brands}

@router.patch("/{brand_id}", summary="Обновление марки автомобиля по ID.")
async def update_car_brand_route(brand_id: UUID, name: str):
    async with AsyncSession(engine_a) as session:
        car_brand = await update_car_brand(session, brand_id, name)
        if car_brand:
            return {"message": "Марка автомобиля успешно обновлен", "data": car_brand}
        raise HTTPException(status_code=404, detail="Марка автомобиля не найден")

@router.delete("/{brand_id}", summary="Удаление марки автомобиля по ID.")
async def delete_car_brand_route(brand_id: UUID):
    async with AsyncSession(engine_a) as session:
        success = await delete_car_brand(session, brand_id)
        if success:
            return {"message": "Марка автомобиля успешно удален"}
        raise HTTPException(status_code=404, detail="Марка автомобиля не найден")
