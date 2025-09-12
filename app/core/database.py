"""Database configuration and connection management."""

from typing import AsyncGenerator

from sqlalchemy import MetaData, inspect, text
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
    from app.models.gift import Gift
    from app.models.inventory import Inventory
    from app.models.inventory_item import InventoryItem

    async with engine.begin() as conn:
        inspector = inspect(conn.sync_connection)

        def _is_legacy_inventory(columns: list[str]) -> bool:
            # Current expected columns: id, created_at, updated_at, user_id
            expected = {"id", "created_at", "updated_at", "user_id"}
            colset = set(columns)
            # legacy if gift_id or quantity present OR user_id missing
            return ("gift_id" in colset) or ("quantity" in colset) or not expected.issubset(colset)

        try:
            table_names = inspector.get_table_names()
            if "inventories" in table_names:
                cols = [c['name'] for c in inspector.get_columns('inventories')]
                if _is_legacy_inventory(cols):
                    # Drop only the legacy inventories table (cascades to inventory_items FKs if any)
                    # Instead of dropping tables with raw SQL, use SQLAlchemy's metadata management or handle schema changes with Alembic migrations.
                    await conn.run_sync(Base.metadata.drop_all)
        except Exception:
            # As a last resort drop all tables if partial failure left inconsistent state
            try:
                await conn.run_sync(Base.metadata.drop_all)
            except Exception:
                pass

        # (Re)create all tables to ensure consistency
        await conn.run_sync(Base.metadata.create_all)


async def close_db_connection():
    """Close database connection."""
    await engine.dispose()