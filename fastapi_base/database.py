from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from fastapi_base.models import Base
from fastapi_base.settings import Settings

engine = create_async_engine(Settings().DATABASE_URL)


async def get_session():  # pragma: no cover
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session


async def create_tables():  # pragma: no cover
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
