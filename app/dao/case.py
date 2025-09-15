"""Case DAO."""
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.base import BaseDAO
from app.models.case import Case
from app.models.gift import Gift


class CaseDAO(BaseDAO[Case]):
    def __init__(self, session: AsyncSession):
        super().__init__(Case, session)

    async def add_gifts(self, case_id: int, gift_ids: list[int]) -> Optional[Case]:
        case = await self.get_by_id(case_id)
        if not case:
            return None
        result = await self.session.execute(select(Gift).where(Gift.id.in_(gift_ids)))
        gifts = list(result.scalars().all())
        for g in gifts:
            if g not in case.gifts:
                case.gifts.append(g)
        await self.session.commit()
        await self.session.refresh(case)
        return case

    async def remove_gift(self, case_id: int, gift_id: int) -> Optional[Case]:
        case = await self.get_by_id(case_id)
        if not case:
            return None
        case.gifts = [g for g in case.gifts if g.id != gift_id]
        await self.session.commit()
        await self.session.refresh(case)
        return case


def get_case_dao(session: AsyncSession) -> CaseDAO:
    return CaseDAO(session)
