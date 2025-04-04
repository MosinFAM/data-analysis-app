from fastapi import FastAPI
from app.database import lifespan, SessionDep, engine, Base
from statistics import median
from sqlalchemy import select, func
from app.models import (
    UserModel, DeviceModel, DeviceStatisticModel
)

from app.schemas import (
    UserCreateSchema, DeviceSchema,
    DeviceStatisticSchema, UserSchema, DeviceOutSchema
)


app = FastAPI(lifespan=lifespan)


@app.post("/users")
async def create_user(data: UserCreateSchema, session: SessionDep):
    user = UserModel(name=data.name)
    session.add(user)
    await session.commit()
    return {"ok": True, "user_id": user.id}


@app.post("/devices")
async def add_device(data: DeviceSchema, session: SessionDep):
    new_device = DeviceModel(
        name=data.name,
        user_id=data.user_id,
    )
    session.add(new_device)
    await session.commit()
    return {"ok": True}


@app.post("/statistics")
async def add_statistic(data: DeviceStatisticSchema, session: SessionDep):
    statistic = DeviceStatisticModel(
        x=data.x,
        y=data.y,
        z=data.z,
        device_id=data.device_id
    )
    session.add(statistic)
    await session.commit()
    return {"ok": True}


# Каждая статистика в отдельности 
@app.get("/device/{device_id}/statistics")
async def get_device_statistics(device_id: int, session: SessionDep):
    query = select(DeviceStatisticModel).filter(
        DeviceStatisticModel.device_id == device_id
        )
    result = await session.execute(query)
    return result.scalars().all()


# Статистика устройств по пользователю
@app.get("/user/{user_id}/statistics")
async def get_user_statistics(user_id: int, session: SessionDep):
    # Считаем агрегаты через SQL
    aggregate_query = select(
        func.min(DeviceStatisticModel.x), func.max(DeviceStatisticModel.x),
        func.count(DeviceStatisticModel.x), func.sum(DeviceStatisticModel.x),
        func.min(DeviceStatisticModel.y), func.max(DeviceStatisticModel.y),
        func.count(DeviceStatisticModel.y), func.sum(DeviceStatisticModel.y),
        func.min(DeviceStatisticModel.z), func.max(DeviceStatisticModel.z),
        func.count(DeviceStatisticModel.z), func.sum(DeviceStatisticModel.z),
    ).join(DeviceModel).filter(DeviceModel.user_id == user_id)
    agg_result = await session.execute(aggregate_query)
    agg_data = agg_result.fetchone()

    # Получаем все значения для медианы
    raw_query = select(DeviceStatisticModel.x, 
                       DeviceStatisticModel.y, 
                       DeviceStatisticModel.z)\
        .join(DeviceModel).filter(DeviceModel.user_id == user_id)
    raw_result = await session.execute(raw_query)
    rows = raw_result.fetchall()

    x_values = [row[0] for row in rows]
    y_values = [row[1] for row in rows]
    z_values = [row[2] for row in rows]

    return {
        "x": {
            "min": agg_data[0],
            "max": agg_data[1],
            "count": agg_data[2],
            "sum": agg_data[3],
            "median": median(x_values) if x_values else None
        },
        "y": {
            "min": agg_data[4],
            "max": agg_data[5],
            "count": agg_data[6],
            "sum": agg_data[7],
            "median": median(y_values) if y_values else None
        },
        "z": {
            "min": agg_data[8],
            "max": agg_data[9],
            "count": agg_data[10],
            "sum": agg_data[11],
            "median": median(z_values) if z_values else None
        }
    }


# Статистика конкретного устройства пользователя
@app.get("/user/{user_id}/device/{device_id}/statistics")
async def get_device_statistics_for_user(user_id: int,
                                         device_id: int,
                                         session: SessionDep):
    # Анализ статистики по конкретному устройству пользователя
    aggregate_query = select(
        func.min(DeviceStatisticModel.x), func.max(DeviceStatisticModel.x),
        func.count(DeviceStatisticModel.x), func.sum(DeviceStatisticModel.x),
        func.min(DeviceStatisticModel.y), func.max(DeviceStatisticModel.y),
        func.count(DeviceStatisticModel.y), func.sum(DeviceStatisticModel.y),
        func.min(DeviceStatisticModel.z), func.max(DeviceStatisticModel.z),
        func.count(DeviceStatisticModel.z), func.sum(DeviceStatisticModel.z),
    ).join(DeviceModel).filter(
        DeviceModel.user_id == user_id,
        DeviceModel.id == device_id)
    agg_result = await session.execute(aggregate_query)
    agg_data = agg_result.fetchone()

    # Получаем все значения для медианы
    raw_query = select(DeviceStatisticModel.x,
                       DeviceStatisticModel.y,
                       DeviceStatisticModel.z)\
        .join(DeviceModel).filter(DeviceModel.user_id == user_id)
    raw_result = await session.execute(raw_query)
    rows = raw_result.fetchall()

    x_values = [row[0] for row in rows]
    y_values = [row[1] for row in rows]
    z_values = [row[2] for row in rows]

    return {
        "x": {
            "min": agg_data[0],
            "max": agg_data[1],
            "count": agg_data[2],
            "sum": agg_data[3],
            "median": median(x_values) if x_values else None
        },
        "y": {
            "min": agg_data[4],
            "max": agg_data[5],
            "count": agg_data[6],
            "sum": agg_data[7],
            "median": median(y_values) if y_values else None
        },
        "z": {
            "min": agg_data[8],
            "max": agg_data[9],
            "count": agg_data[10],
            "sum": agg_data[11],
            "median": median(z_values) if z_values else None
        }
    }


@app.get("/users", response_model=list[UserSchema])
async def get_all_users(session: SessionDep):
    query = select(UserModel)
    result = await session.execute(query)
    return result.scalars().all()


@app.get("/devices", response_model=list[DeviceOutSchema])
async def get_all_devices(session: SessionDep):
    query = select(DeviceModel)
    result = await session.execute(query)
    return result.scalars().all()
