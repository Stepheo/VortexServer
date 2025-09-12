"""InventoryItem DAO for managing per-gift quantities."""

from typing import Optional, List
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_manager
from app.dao.base import BaseDAO
from app.models.inventory_item import InventoryItem


class InventoryItemDAO(BaseDAO[InventoryItem]):
    """InventoryItem specific data operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(InventoryItem, session)

    def _cache_key_item(self, inventory_id: int, gift_id: int) -> str:
        return f"inventory_item:{inventory_id}:{gift_id}"

    def _cache_key_list(self, inventory_id: int) -> str:
        return f"inventory_items:list:{inventory_id}"

    async def get_one(self, inventory_id: int, gift_id: int) -> Optional[InventoryItem]:
        cache_key = self._cache_key_item(inventory_id, gift_id)
        cached = await cache_manager.get(cache_key)
        if cached:
            return InventoryItem(**cached)
        result = await self.session.execute(
            select(InventoryItem).where(
                InventoryItem.inventory_id == inventory_id,
                InventoryItem.gift_id == gift_id,
            )
        )
        item = result.scalar_one_or_none()
        if item:
            await cache_manager.set(cache_key, item.to_dict(), expire=300)
        return item

    async def list_for_inventory(self, inventory_id: int) -> List[InventoryItem]:
        cache_key = self._cache_key_list(inventory_id)
        cached = await cache_manager.get(cache_key)
        if cached:
            return [InventoryItem(**d) for d in cached]
        result = await self.session.execute(
            select(InventoryItem).where(InventoryItem.inventory_id == inventory_id)
        )
        items = list(result.scalars().all())
        if items:
            await cache_manager.set(cache_key, [i.to_dict() for i in items], expire=120)
        return items

    async def add_quantity(self, inventory_id: int, gift_id: int, delta: int) -> InventoryItem:
        item = await self.get_one(inventory_id, gift_id)
        if item:
            new_qty = item.quantity + delta
            if new_qty <= 0:
                await self.remove(inventory_id, gift_id)
                raise ValueError("Quantity became non-positive; item removed")
            await self.session.execute(
                update(InventoryItem)
                .where(InventoryItem.id == item.id)
                .values(quantity=new_qty)
            )
            await self.session.commit()
            return await self._post_change_refresh(item.inventory_id, item.gift_id)
        # create new
        item = await self.create(inventory_id=inventory_id, gift_id=gift_id, quantity=delta)
        await self._invalidate_inventory_cache(inventory_id, gift_id)
        return item

    async def set_quantity(self, inventory_id: int, gift_id: int, quantity: int) -> Optional[InventoryItem]:
        if quantity <= 0:
            await self.remove(inventory_id, gift_id)
            return None
        item = await self.get_one(inventory_id, gift_id)
        if item:
            await self.session.execute(
                update(InventoryItem)
                .where(InventoryItem.id == item.id)
                .values(quantity=quantity)
            )
            await self.session.commit()
            return await self._post_change_refresh(inventory_id, gift_id)
        item = await self.create(inventory_id=inventory_id, gift_id=gift_id, quantity=quantity)
        await self._invalidate_inventory_cache(inventory_id, gift_id)
        return item

    async def remove(self, inventory_id: int, gift_id: int) -> bool:
        item = await self.get_one(inventory_id, gift_id)
        if not item:
            return False
        await self.session.execute(
            delete(InventoryItem).where(InventoryItem.id == item.id)
        )
        await self.session.commit()
        await self._invalidate_inventory_cache(inventory_id, gift_id)
        return True

    async def _post_change_refresh(self, inventory_id: int, gift_id: int) -> InventoryItem:
        # re-fetch fresh
        result = await self.session.execute(
            select(InventoryItem).where(
                InventoryItem.inventory_id == inventory_id,
                InventoryItem.gift_id == gift_id,
            )
        )
        item = result.scalar_one()
        await self._invalidate_inventory_cache(inventory_id, gift_id)
        return item

    async def _invalidate_inventory_cache(self, inventory_id: int, gift_id: int) -> None:
        await cache_manager.delete(self._cache_key_item(inventory_id, gift_id))
        await cache_manager.delete(self._cache_key_list(inventory_id))


def get_inventory_item_dao(session: AsyncSession) -> InventoryItemDAO:
    return InventoryItemDAO(session)
