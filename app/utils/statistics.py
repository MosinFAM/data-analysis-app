from app.database import SessionDep
from statistics import median
from sqlalchemy import select, func
from app.models import (
    DeviceModel, DeviceStatisticModel
)
from app.schemas import (
    AxisStatisticSchema, FullStatisticsResponse, DeviceStatisticSchema
)


async def get_statistics(filters, session: SessionDep) -> FullStatisticsResponse:
    agg_query = select(
        func.min(DeviceStatisticModel.x), func.max(DeviceStatisticModel.x),
        func.count(DeviceStatisticModel.x), func.sum(DeviceStatisticModel.x),
        func.min(DeviceStatisticModel.y), func.max(DeviceStatisticModel.y),
        func.count(DeviceStatisticModel.y), func.sum(DeviceStatisticModel.y),
        func.min(DeviceStatisticModel.z), func.max(DeviceStatisticModel.z),
        func.count(DeviceStatisticModel.z), func.sum(DeviceStatisticModel.z),
    ).join(DeviceModel).filter(*filters)

    agg_result = await session.execute(agg_query)
    agg_data = agg_result.fetchone()

    raw_query = select(
        DeviceStatisticModel.x,
        DeviceStatisticModel.y,
        DeviceStatisticModel.z
    ).join(DeviceModel).filter(*filters)

    raw_result = await session.execute(raw_query)
    rows = raw_result.fetchall()

    x_vals = [r[0] for r in rows]
    y_vals = [r[1] for r in rows]
    z_vals = [r[2] for r in rows]

    stats = FullStatisticsResponse(
        x=format_stats(agg_data[0:4], x_vals),
        y=format_stats(agg_data[4:8], y_vals),
        z=format_stats(agg_data[8:12], z_vals),
    )
    return stats


def format_stats(agg, values) -> AxisStatisticSchema:
    return AxisStatisticSchema(
        min=agg[0],
        max=agg[1],
        count=agg[2],
        sum=agg[3],
        median=median(values) if values else None
    )


async def get_full_statistics(filters, session: SessionDep):
    query = select(DeviceStatisticModel).filter(*filters)
    result = await session.execute(query)
    stats = result.scalars().all()
    return [DeviceStatisticSchema.from_orm(stat) for stat in stats]
