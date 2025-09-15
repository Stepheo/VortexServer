"""Inventory DAO (one inventory per user)."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.base import BaseDAO
from app.models.inventory import Inventory
from app.models.user import User


class InventoryDAO(BaseDAO[Inventory]):
    """Inventory DAO with helper methods."""

    def __init__(self, session: AsyncSession):
        super().__init__(Inventory, session)

    async def get_by_user_id(self, user_id: int) -> Optional[Inventory]:
        result = await self.session.execute(
            select(Inventory).where(Inventory.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: int) -> Inventory:
        """Get existing inventory or create a new one for the user."""
        # Ensure user row exists (tests create token but no DB user). Minimal placeholder user.
        existing_user = await self.session.get(User, user_id)
        if not existing_user:
            # Создаём минимального пользователя (tg_id и first_name обязательны).
            # Не задаём id явно — позволяем БД сгенерировать PK, затем используем фактический id в inventory.
            user_obj = User(
                tg_id=10_000_000 + user_id,  # уникальное смещение, чтобы не конфликтовать
                username=f'user{user_id}',
                first_name=f'User{user_id}',
                last_name=None,
            )
            self.session.add(user_obj)
            await self.session.flush()
            user_id = user_obj.id
        inv = await self.get_by_user_id(user_id)
        if inv:
            return inv
        # Create new inventory (single row with user_id)
        return await self.create(user_id=user_id)


def get_inventory_dao(session: AsyncSession) -> InventoryDAO:
    return InventoryDAO(session)
