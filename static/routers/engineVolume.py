from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.database_app import engine_a
from models import EngineVolume
from sqlalchemy.future import select
from uuid import UUID

async def create_engine_volume(db: AsyncSession, name: float) -> EngineVolume:
    engine_volume = EngineVolume(name=name)
    db.add(engine_volume)
    await db.commit()
    await db.refresh(engine_volume)
    return engine_volume

async def get_engine_volume(db: AsyncSession, volume_id: UUID) -> EngineVolume:
    result = await db.execute(select(EngineVolume).filter(EngineVolume.id == volume_id))
    return result.scalar()

async def get_all_engine_volumes(db: AsyncSession) -> list:
    result = await db.execute(select(EngineVolume))
    return result.scalars().all()

async def update_engine_volume(db: AsyncSession, volume_id: UUID, name: float) -> EngineVolume:
    engine_volume = await get_engine_volume(db, volume_id)
    if engine_volume:
        engine_volume.name = name
        await db.commit()
        await db.refresh(engine_volume)
        return engine_volume
    return None

async def delete_engine_volume(db: AsyncSession, volume_id: UUID) -> bool:
    engine_volume = await get_engine_volume(db, volume_id)
    if engine_volume:
        await db.delete(engine_volume)
        await db.commit()
        return True
    return False


router = APIRouter()


@router.post("/", summary="Создание нового объема двигателя.")
async def create_engine_volume_route(name: float):
    async with AsyncSession(engine_a) as session:
        engine_volume = await create_engine_volume(session, name)
        return {"message": "Объем двигателя успешно создан", "data": engine_volume}

@router.get("/{volume_id}", summary="Получение объема двигателя по ID.")
async def get_engine_volume_route(volume_id: UUID):
    async with AsyncSession(engine_a) as session:
        engine_volume = await get_engine_volume(session, volume_id)
        if engine_volume:
            return {"message": "Объем двигателя найден", "data": engine_volume}
        raise HTTPException(status_code=404, detail="Объем двигателя не найден")

@router.get("/", summary="Получение списка всех объемов двигателей.")
async def get_all_engine_volumes_route():
    async with AsyncSession(engine_a) as session:
        engine_volumes = await get_all_engine_volumes(session)
        return {"message": "Список объемов двигателей", "data": engine_volumes}

@router.patch("/{volume_id}", summary="Обновление объема двигателя по ID.")
async def update_engine_volume_route(volume_id: UUID, name: float):
    async with AsyncSession(engine_a) as session:
        engine_volume = await update_engine_volume(session, volume_id, name)
        if engine_volume:
            return {"message": "Объем двигателя успешно обновлен", "data": engine_volume}
        raise HTTPException(status_code=404, detail="Объем двигателя не найден")

@router.delete("/{volume_id}", summary="Удаление объема двигателя по ID.")
async def delete_engine_volume_route(volume_id: UUID):
    async with AsyncSession(engine_a) as session:
        success = await delete_engine_volume(session, volume_id)
        if success:
            return {"message": "Объем двигателя успешно удален"}
        raise HTTPException(status_code=404, detail="Объем двигателя не найден")