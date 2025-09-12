"""Gift Data Access Object with specialized methods."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_manager
from app.dao.base import BaseDAO
from app.models.gift import Gift


class GiftDAO(BaseDAO[Gift]):
    """Gift DAO with caching and rarity helpers."""

    def __init__(self, session: AsyncSession):
        super().__init__(Gift, session)

    async def get_by_name(self, name: str) -> Optional[Gift]:
        cache_key = f"gift:name:{name}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return Gift(**cached)
        result = await self.session.execute(select(Gift).where(Gift.name == name))
        gift = result.scalar_one_or_none()
        if gift:
            await cache_manager.set(cache_key, gift.to_dict(), expire=300)
        return gift

    async def list_by_rarity_range(
        self,
        min_real: float | None = None,
        max_real: float | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Gift]:
        filters_sig = f"{min_real}:{max_real}:{skip}:{limit}"
        cache_key = f"gifts:rarity:{filters_sig}"
        cached = await cache_manager.get(cache_key)
        if cached:
            return [Gift(**d) for d in cached]
        query = select(Gift)
        if min_real is not None:
            query = query.where(Gift.real_rarity >= min_real)
        if max_real is not None:
            query = query.where(Gift.real_rarity <= max_real)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        gifts = list(result.scalars().all())
        if gifts:
            await cache_manager.set(cache_key, [g.to_dict() for g in gifts], expire=120)
        return gifts

    async def create(self, **kwargs) -> Gift:
        gift = await super().create(**kwargs)
        await self._invalidate_caches(gift)
        return gift

    async def update(self, id: int, **kwargs) -> Optional[Gift]:
        old = await self.get_by_id(id)
        gift = await super().update(id, **kwargs)
        if gift:
            if old:
                await self._invalidate_caches(old)
            await self._invalidate_caches(gift)
        return gift

    async def delete(self, id: int) -> bool:
        gift = await self.get_by_id(id)
        deleted = await super().delete(id)
        if deleted and gift:
            await self._invalidate_caches(gift)
        return deleted

    async def _invalidate_caches(self, gift: Gift) -> None:
        await cache_manager.delete(f"gift:{gift.id}")
        await cache_manager.delete(f"gift:name:{gift.name}")


def get_gift_dao(session: AsyncSession) -> GiftDAO:
    return GiftDAO(session)
