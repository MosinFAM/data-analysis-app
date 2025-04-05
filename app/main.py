import logging
from fastapi import FastAPI, Query, HTTPException
from typing import Optional
from datetime import datetime
from app.database import lifespan, SessionDep
from sqlalchemy import select
from app.models import (
    UserModel, DeviceModel, DeviceStatisticModel
)
from app.schemas import (
    UserCreateSchema, DeviceSchema,
    DeviceStatisticSchema, UserSchema, DeviceOutSchema,
)
from app.utils.statistics import get_statistics


app = FastAPI(lifespan=lifespan)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.get("/users", response_model=list[UserSchema])
async def get_all_users(session: SessionDep):
    query = select(UserModel)
    result = await session.execute(query)
    users = result.scalars().all()
    logger.info("Fetched %d users", len(users))
    return users


@app.get("/devices", response_model=list[DeviceOutSchema])
async def get_all_devices(session: SessionDep):
    query = select(DeviceModel)
    result = await session.execute(query)
    devices = result.scalars().all()
    logger.info("Fetched %d devices", len(devices))
    return devices


@app.post("/users")
async def create_user(data: UserCreateSchema, session: SessionDep):
    user = UserModel(name=data.name)
    session.add(user)
    await session.commit()
    logger.info("Created user with id=%d", user.id)
    return {"ok": True, "user_id": user.id}


@app.post("/devices")
async def add_device(data: DeviceSchema, session: SessionDep):

    user_exists = await session.get(UserModel, data.user_id)
    if not user_exists:
        logger.warning("Attempt to create device for non-existent user_id=%d",
                       data.user_id)
        raise HTTPException(status_code=404, detail="User not found")

    new_device = DeviceModel(
        name=data.name,
        user_id=data.user_id,
    )
    session.add(new_device)
    await session.commit()
    logger.info("Created device with id=%d for user_id=%d", new_device.id,
                data.user_id)
    return {"ok": True, "device_id": new_device.id}


@app.post("/statistics")
async def add_statistic(data: DeviceStatisticSchema, session: SessionDep):
    device = await session.get(DeviceModel, data.device_id)
    if not device:
        logger.warning("Attempt to add statistic to non-existent device_id=%d",
                       data.device_id)
        raise HTTPException(status_code=404, detail="Device not found")

    statistic = DeviceStatisticModel(
        x=data.x,
        y=data.y,
        z=data.z,
        device_id=data.device_id
    )
    session.add(statistic)
    await session.commit()
    logger.info("Added statistic with id=%d to device_id=%d", statistic.id,
                data.device_id)
    return {"ok": True, "statistic_id": statistic.id}


# Каждая статистика в отдельности
@app.get("/device/{device_id}/statistics")
async def get_device_statistics(
    device_id: int,
    session: SessionDep,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):

    filters = [DeviceStatisticModel.device_id == device_id]
    if start_date:
        filters.append(DeviceStatisticModel.created_at >= start_date)
    if end_date:
        filters.append(DeviceStatisticModel.created_at <= end_date)

    query = select(DeviceStatisticModel).filter(*filters)
    result = await session.execute(query)
    stats = result.scalars().all()
    logger.info("Fetched %d statistics for device_id=%d",
                len(stats),
                device_id)
    return stats


# Статистика устройств конкретного пользователя
@app.get("/user/{user_id}/statistics")
async def get_user_statistics(
    user_id: int,
    session: SessionDep,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):

    filters = [DeviceModel.user_id == user_id]
    if start_date:
        filters.append(DeviceStatisticModel.created_at >= start_date)
    if end_date:
        filters.append(DeviceStatisticModel.created_at <= end_date)

    logger.info("Fetching statistics for user_id=%d", user_id)
    return await get_statistics(filters, session)


# Статистика конкретного устройства пользователя
@app.get("/user/{user_id}/device/{device_id}/statistics")
async def get_device_statistics_for_user(
    user_id: int,
    device_id: int,
    session: SessionDep,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None)
):

    filters = [
        DeviceModel.user_id == user_id,
        DeviceModel.id == device_id
    ]
    if start_date:
        filters.append(DeviceStatisticModel.created_at >= start_date)
    if end_date:
        filters.append(DeviceStatisticModel.created_at <= end_date)

    logger.info("Fetching statistics for user_id=%d and device_id=%d",
                user_id,
                device_id)
    return await get_statistics(filters, session)
