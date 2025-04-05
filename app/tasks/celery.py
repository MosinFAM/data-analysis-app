from celery import Celery
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database.database import DATABASE_URL


# Создаем асинхронный engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаем сессию с привязкой к engine
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

celery = Celery(__name__)
celery.conf.broker_url = "redis://redis:6379/0"
celery.conf.result_backend = "redis://redis:6379/0"

celery.conf.update(
    result_serializer='json',
    accept_content=['json'],
    task_serializer='json',
    result_extended=True
)
