"""Inventory endpoints (read-only for frontend).

Only exposes GET /inventory to fetch current user's inventory and items.
Mutation endpoints removed.
"""
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.dao.inventory import get_inventory_dao, InventoryDAO
from app.dao.inventory_item import get_inventory_item_dao, InventoryItemDAO
from app.dao.gift import get_gift_dao, GiftDAO
from app.dao import get_user_dao
from app.api.auth import auth

router = APIRouter(prefix="/inventory", tags=["inventory"])


async def get_daos(
    session: AsyncSession = Depends(get_async_session),
):
    return {
        "user_dao": get_user_dao(session),
        "inventory": get_inventory_dao(session),
        "items": get_inventory_item_dao(session),
        "gifts": get_gift_dao(session),
    }


@router.get("/", summary="Get current user's inventory with items")
async def get_my_inventory(
    auth_data=Depends(auth),
    daos=Depends(get_daos),
):
    inv_dao: InventoryDAO = daos["inventory"]
    item_dao: InventoryItemDAO = daos["items"]
    user_dao = daos["user_dao"]
    user = await user_dao.get_by_tg_id(auth_data.user_id)
    if not user:
        return {"inventory": None, "items": []}
    inventory = await inv_dao.get_or_create(user_id=user["id"])
    items = await item_dao.list_for_inventory(inventory.id)
    return {
        "inventory": inventory.to_dict(),
        "items": [i.to_dict() for i in items],
    }


## Mutating endpoints removed (add/set/remove) for read-only mode.
