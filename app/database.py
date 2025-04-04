from sqlalchemy.orm import DeclarativeBase
from fastapi import Depends, FastAPI
from typing import Annotated
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)


engine = create_async_engine('sqlite+aiosqlite:///./test.db', echo=True)

new_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session():
    async with new_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Инициализация БД прошла успешно")
    yield
