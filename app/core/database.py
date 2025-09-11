"""Database configuration and connection management."""

from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Create sessionmaker
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_db_and_tables():
    """Create database and tables."""
    # Import models here to ensure they are registered
    from app.models.base import Base
    from app.models.user import User  # Import all model modules here
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db_connection():
    """Close database connection."""
    await engine.dispose()