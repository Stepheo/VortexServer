"""(Deprecated) Gift endpoints removed from public API.

File kept temporarily for reference. Router not included in main API router.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_async_session
from app.dao.gift import get_gift_dao, GiftDAO

router = APIRouter(prefix="/gifts", tags=["gifts"], include_in_schema=False)


async def get_dao(session: AsyncSession = Depends(get_async_session)) -> GiftDAO:
    return get_gift_dao(session)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_gift(
    name: str,
    real_rarity: float,
    visual_rarity: float,
    rarity_color: str,
    price: float = Query(0, ge=0),
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
        price=price,
    )
    data = gift.to_dict()
    data.pop('real_rarity', None)
    data.pop('visual_rarity', None)
    return data


@router.get("/{gift_id}")
async def get_gift(gift_id: int, dao: GiftDAO = Depends(get_dao)):
    gift = await dao.get_by_id(gift_id)
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    data = gift.to_dict()
    data.pop('real_rarity', None)
    data.pop('visual_rarity', None)
    return data


@router.get("/by-name/{name}")
async def get_gift_by_name(name: str, dao: GiftDAO = Depends(get_dao)):
    gift = await dao.get_by_name(name)
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    data = gift.to_dict()
    data.pop('real_rarity', None)
    data.pop('visual_rarity', None)
    return data


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
    result = []
    for g in gifts:
        d = g.to_dict()
        d.pop('real_rarity', None)
        d.pop('visual_rarity', None)
        result.append(d)
    return result


class GiftUpdate(BaseModel):
    name: Optional[str] = None
    real_rarity: Optional[float] = None
    visual_rarity: Optional[float] = None
    rarity_color: Optional[str] = None
    price: Optional[float] = None

@router.patch("/{gift_id}")
async def update_gift(
    gift_id: int,
    payload: GiftUpdate,
    dao: GiftDAO = Depends(get_dao)
):
    update_data = payload.dict(exclude_unset=True)
    # Validation
    if 'price' in update_data and update_data['price'] is not None and update_data['price'] < 0:
        raise HTTPException(status_code=400, detail="price must be >= 0")
    if not update_data:
        gift = await dao.get_by_id(gift_id)
        if not gift:
            raise HTTPException(status_code=404, detail="Gift not found")
        d = gift.to_dict()
        d.pop('real_rarity', None)
        d.pop('visual_rarity', None)
        return d
    gift = await dao.update(gift_id, **update_data)
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    d = gift.to_dict()
    d.pop('real_rarity', None)
    d.pop('visual_rarity', None)
    return d


@router.delete("/{gift_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_gift(gift_id: int, dao: GiftDAO = Depends(get_dao)):
    deleted = await dao.delete(gift_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Gift not found")
    return None
