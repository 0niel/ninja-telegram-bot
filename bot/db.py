from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from bot.config import get_settings

engine = create_async_engine(get_settings().POSTGRES_URI, future=True)

Base = declarative_base()

session = sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# Dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with session as db:
        yield db
