from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import TransmissionType
from uuid import UUID
from database.database_app import engine_a


async def create_transmission_type(db: AsyncSession, name: str) -> TransmissionType:
    transmission_type = TransmissionType(name=name)
    db.add(transmission_type)
    await db.commit()
    await db.refresh(transmission_type) 
    return transmission_type

async def get_transmission_type(db: AsyncSession, type_id: UUID) -> TransmissionType:
    result = await db.execute(select(TransmissionType).filter(TransmissionType.id == type_id))
    return result.scalar()

async def get_all_transmission_types(db: AsyncSession) -> list:
    result = await db.execute(select(TransmissionType))
    return result.scalars().all()

async def update_transmission_type(db: AsyncSession, type_id: UUID, name: str) -> TransmissionType:
    transmission_type = await get_transmission_type(db, type_id)
    if transmission_type:
        transmission_type.name = name
        await db.commit()
        await db.refresh(transmission_type) 
        return transmission_type
    return None

async def delete_transmission_type(db: AsyncSession, type_id: UUID) -> bool:
    transmission_type = await get_transmission_type(db, type_id)
    if transmission_type:
        await db.delete(transmission_type)
        await db.commit()
        return True
    return False


router = APIRouter()

@router.post("/", summary="Создание нового типа коробки передач.")
async def create_transmission_type_route(name: str):
    async with AsyncSession(engine_a) as session:
        transmission_type = await create_transmission_type(session, name)
        return {"message": "Тип коробки передач успешно создан", "data": transmission_type}

@router.get("/{type_id}", summary="Получение типа коробки передач по ID.")
async def get_transmission_type_route(type_id: UUID):
    async with AsyncSession(engine_a) as session:
        transmission_type = await get_transmission_type(session, type_id)
        if transmission_type:
            return {"message": "Тип коробки передач найден", "data": transmission_type}
        raise HTTPException(status_code=404, detail="Тип коробки передач не найден")

@router.get("/", summary="Получение списка всех типов коробок передач.")
async def get_all_transmission_types_route():
    async with AsyncSession(engine_a) as session:
        transmission_types = await get_all_transmission_types(session)
        return {"message": "Список типов коробок передач", "data": transmission_types}

@router.patch("/{type_id}", summary="Обновление типа коробки передач по ID.")
async def update_transmission_type_route(type_id: UUID, name: str):
    async with AsyncSession(engine_a) as session:
        transmission_type = await update_transmission_type(session, type_id, name)
        if transmission_type:
            return {"message": "Тип коробки передач успешно обновлен", "data": transmission_type}
        raise HTTPException(status_code=404, detail="Тип коробки передач не найден")

@router.delete("/{type_id}", summary="Удаление типа коробки передач по ID.")
async def delete_transmission_type_route(type_id: UUID):
    async with AsyncSession(engine_a) as session:
        success = await delete_transmission_type(session, type_id)
        if success:
            return {"message": "Тип коробки передач успешно удален"}
        raise HTTPException(status_code=404, detail="Тип коробки передач не найден")