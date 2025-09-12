"""Gift endpoints."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_async_session
from app.dao.gift import get_gift_dao, GiftDAO

router = APIRouter(prefix="/gifts", tags=["gifts"])


async def get_dao(session: AsyncSession = Depends(get_async_session)) -> GiftDAO:
    return get_gift_dao(session)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_gift(
    name: str,
    real_rarity: float,
    visual_rarity: float,
    rarity_color: str,
    dao: GiftDAO = Depends(get_dao)
):
    existing = await dao.get_by_name(name)
    if existing:
        raise HTTPException(status_code=400, detail="Gift name already exists")
    gift = await dao.create(
        name=name,
        real_rarity=real_rarity,
        visual_rarity=visual_rarity,
        rarity_color=rarity_color,
    )
    return gift.to_dict()


@router.get("/{gift_id}")
async def get_gift(gift_id: int, dao: GiftDAO = Depends(get_dao)):
    gift = await dao.get_by_id(gift_id)
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    return gift.to_dict()


@router.get("/by-name/{name}")
async def get_gift_by_name(name: str, dao: GiftDAO = Depends(get_dao)):
    gift = await dao.get_by_name(name)
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    return gift.to_dict()


@router.get("/", response_model=List[dict])
async def list_gifts(
    skip: int = 0,
    limit: int = 100,
    min_real: Optional[float] = Query(None, ge=0),
    max_real: Optional[float] = Query(None, ge=0),
    dao: GiftDAO = Depends(get_dao),
):
    if min_real is not None and max_real is not None and min_real > max_real:
        raise HTTPException(status_code=400, detail="min_real > max_real")
    if min_real is not None or max_real is not None:
        gifts = await dao.list_by_rarity_range(min_real=min_real, max_real=max_real, skip=skip, limit=limit)
    else:
        gifts = await dao.get_all(skip=skip, limit=limit)
    return [g.to_dict() for g in gifts]


class GiftUpdate(BaseModel):
    name: Optional[str] = None
    real_rarity: Optional[float] = None
    visual_rarity: Optional[float] = None
    rarity_color: Optional[str] = None

@router.patch("/{gift_id}")
async def update_gift(
    gift_id: int,
    payload: GiftUpdate,
    dao: GiftDAO = Depends(get_dao)
):
    update_data = payload.dict(exclude_unset=True)
    if not update_data:
        gift = await dao.get_by_id(gift_id)
        if not gift:
            raise HTTPException(status_code=404, detail="Gift not found")
        return gift.to_dict()
    gift = await dao.update(gift_id, **update_data)
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    return gift.to_dict()


@router.delete("/{gift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gift(gift_id: int, dao: GiftDAO = Depends(get_dao)):
    deleted = await dao.delete(gift_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Gift not found")
    return None
