from fastapi import FastAPI, HTTPException
from typing import Optional
from datetime import datetime
from sqlalchemy import select
from fastapi.responses import JSONResponse
from app.logger import logger
from app.database.database import lifespan, SessionDep
from app.models.models import (
    UserModel, DeviceModel, DeviceStatisticModel
)
from app.schemas.schemas import (
    UserCreateSchema, DeviceSchema,
    DeviceStatisticSchema, UserSchema, DeviceOutSchema,
)
from celery.result import AsyncResult
from app.tasks.celery_worker import calculate_device_statistics, celery


app = FastAPI(lifespan=lifespan)


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
    return JSONResponse({"ok": True, "user_id": user.id})


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
    return JSONResponse({"ok": True, "device_id": new_device.id})


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
    return JSONResponse({"ok": True, "statistic_id": statistic.id})


# Статистика конкретного пользователя
@app.get("/user/{user_id}/statistics/async")
async def get_user_statistics_async(
    user_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    task = calculate_device_statistics.delay(
        user_id=user_id,
        device_id=None,
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None
    )
    return JSONResponse({"task_id": task.id, "status": "processing"})


# Статистика конкретного устройства пользователя
@app.get("/user/{user_id}/device/{device_id}/statistics/async")
async def get_device_statistics_for_user_async(
    user_id: int,
    device_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    task = calculate_device_statistics.delay(
        user_id=user_id,
        device_id=device_id,
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None
    )
    return JSONResponse({"task_id": task.id, "status": "processing"})


# Каждая статистика в отдельности
@app.get("/device/{device_id}/statistics/async")
async def get_device_statistics_async(
    device_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    task = calculate_device_statistics.delay(
        user_id=None,
        device_id=device_id,
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None
    )
    return JSONResponse({"task_id": task.id, "status": "processing"})


@app.get("/analytics/status/{task_id}")
def get_task_status(task_id: str):
    try:
        result = AsyncResult(task_id, app=celery)
        if result.failed():
            return {
                "status": "FAILED",
                "error": str(result.result),
                "traceback": result.traceback
            }
        if result.ready():
            return {
                "status": "ok",
                "result": result.result
            }
        return {"status": result.state}
    except Exception as e:
        logger.error(f"Ошибка при получении статуса задачи {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
