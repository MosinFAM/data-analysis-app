from fastapi import Query, HTTPException
from app.logger import logger
from app.models.models import DeviceModel, DeviceStatisticModel
from datetime import datetime
from typing import Optional
import asyncio
from app.utils.statistics import get_statistics, get_full_statistics
from app.tasks.celery import AsyncSessionLocal, celery


@celery.task(name="get_statistics")
def calculate_device_statistics(
    user_id: Optional[int] = None,
    device_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):

    try:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None

        result = asyncio.run(
            _calculate_device_statistics(user_id, device_id, start_dt, end_dt)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


async def _calculate_device_statistics(
        user_id: Optional[int] = Query(None),
        device_id: Optional[int] = Query(None),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None)
):
    try:
        async with AsyncSessionLocal() as session:
            filters = list()
            if device_id:
                filters.append(DeviceModel.id == device_id)
            if start_date:
                filters.append(DeviceStatisticModel.created_at >= start_date)
            if end_date:
                filters.append(DeviceStatisticModel.created_at <= end_date)
            if user_id:
                filters.append(DeviceModel.user_id == user_id)
                result = await get_statistics(filters, session)
                return result.model_dump()
            else:

                full_stats = await get_full_statistics(filters, session)
                return [stat.model_dump() for stat in full_stats]

    except Exception as e:
        logger.error(f"Error in statistics calculation: {str(e)}")
        raise
