"""Inventory and inventory items endpoints for current user."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.dao.inventory import get_inventory_dao, InventoryDAO
from app.dao.inventory_item import get_inventory_item_dao, InventoryItemDAO
from app.dao.gift import get_gift_dao, GiftDAO
from app.api.v1.deps.current_user import get_current_user

router = APIRouter(prefix="/inventory", tags=["inventory"])


async def get_daos(
    session: AsyncSession = Depends(get_async_session),
):
    return {
        "inventory": get_inventory_dao(session),
        "items": get_inventory_item_dao(session),
        "gifts": get_gift_dao(session),
    }


@router.get("/", summary="Get current user's inventory with items")
async def get_my_inventory(
    user=Depends(get_current_user),
    daos=Depends(get_daos),
):
    inv_dao: InventoryDAO = daos["inventory"]
    item_dao: InventoryItemDAO = daos["items"]
    inventory = await inv_dao.get_or_create(user_id=user["id"])
    items = await item_dao.list_for_inventory(inventory.id)
    return {
        "inventory": inventory.to_dict(),
        "items": [i.to_dict() for i in items],
    }


@router.post("/add", summary="Add quantity to an item", status_code=status.HTTP_200_OK)
async def add_item_quantity(
    gift_id: int,
    delta: int = 1,
    user=Depends(get_current_user),
    daos=Depends(get_daos),
):
    if delta == 0:
        raise HTTPException(status_code=400, detail="delta cannot be zero")
    if delta < 0:
        raise HTTPException(status_code=400, detail="Use set or removal for negative adjustments")
    inv = await daos["inventory"].get_or_create(user_id=user["id"])
    # Ensure gift exists
    gift = await daos["gifts"].get_by_id(gift_id)
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    item = await daos["items"].add_quantity(inv.id, gift_id, delta)
    return item.to_dict()


@router.put("/set", summary="Set quantity for a gift")
async def set_item_quantity(
    gift_id: int,
    quantity: int,
    user=Depends(get_current_user),
    daos=Depends(get_daos),
):
    if quantity < 0:
        raise HTTPException(status_code=400, detail="quantity cannot be negative")
    inv = await daos["inventory"].get_or_create(user_id=user["id"])
    gift = await daos["gifts"].get_by_id(gift_id)
    if not gift:
        raise HTTPException(status_code=404, detail="Gift not found")
    item = await daos["items"].set_quantity(inv.id, gift_id, quantity)
    if not item:
        return {"removed": True}
    return item.to_dict()


@router.delete("/remove", summary="Remove a gift from inventory", status_code=status.HTTP_200_OK)
async def remove_item(
    gift_id: int,
    user=Depends(get_current_user),
    daos=Depends(get_daos),
):
    inv = await daos["inventory"].get_or_create(user_id=user["id"])
    deleted = await daos["items"].remove(inv.id, gift_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"removed": True}
