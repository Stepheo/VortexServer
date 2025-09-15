"""Upgrade endpoints."""

import random
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.dao.inventory import get_inventory_dao
from app.dao.inventory_item import get_inventory_item_dao
from app.dao.gift import get_gift_dao
from app.dao.transaction import get_transaction_dao
from app.api.v1.deps.current_user import get_current_user

router = APIRouter(prefix="/upgrade", tags=["upgrade"])


class UpgradeRequest(BaseModel):
    """Request model for upgrade operation."""
    sourceInstanceId: str = Field(..., description="Instance ID of the item to upgrade")
    targetGiftId: int = Field(..., description="Target gift ID to upgrade to")
    clientSeed: Optional[str] = Field(None, description="Client seed for fairness")


class NewItemResponse(BaseModel):
    """New item details in upgrade response."""
    instanceId: str
    giftId: int
    name: str
    price: float


class UpgradeSuccessResponse(BaseModel):
    """Successful upgrade response."""
    txId: str
    chance: float
    success: bool = True
    finalAngle: float
    rotationSpins: int
    newItem: NewItemResponse
    consumedInstanceId: str
    serverTime: str


class UpgradeFailureResponse(BaseModel):
    """Failed upgrade response."""
    txId: str
    chance: float
    success: bool = False
    finalAngle: float
    rotationSpins: int
    consumedInstanceId: str
    serverTime: str


class UpgradeErrorResponse(BaseModel):
    """Error response for upgrade."""
    error: str
    message: str


def calculate_upgrade_chance(source_price: float, target_price: float) -> float:
    """Calculate upgrade chance based on price difference."""
    if target_price <= source_price:
        return 80.0  # High chance if target is cheaper or equal
    
    ratio = source_price / target_price
    # Base chance decreases as price ratio decreases
    chance = min(80.0, max(10.0, ratio * 100))
    return round(chance, 1)


def generate_wheel_result(chance: float) -> tuple[bool, float, int]:
    """Generate wheel animation result."""
    success = random.random() * 100 < chance
    rotation_spins = random.randint(3, 6)
    
    if success:
        # Success zone: 0-45 degrees or 315-360 degrees (25% of wheel)
        if random.random() < 0.5:
            final_angle = random.uniform(0, 45)
        else:
            final_angle = random.uniform(315, 360)
    else:
        # Failure zone: 45-315 degrees (75% of wheel)
        final_angle = random.uniform(45, 315)
    
    return success, round(final_angle, 2), rotation_spins


@router.post("/", response_model=UpgradeSuccessResponse | UpgradeFailureResponse)
async def upgrade_item(
    request: UpgradeRequest,
    user=Depends(get_current_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Upgrade an item in user's inventory.
    
    The upgrade system works like a spinning wheel where success chance 
    depends on the price ratio between source and target items.
    """
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
    
    # Get DAOs
    inventory_dao = get_inventory_dao(session)
    item_dao = get_inventory_item_dao(session)
    gift_dao = get_gift_dao(session)
    transaction_dao = get_transaction_dao(session)
    
    # Check if this operation was already performed using cache
    from app.core.cache import cache_manager
    cache_key = f"upgrade_idempotency:{user['id']}:{idempotency_key}"
    
    # Try to get cached result
    cached_result = await cache_manager.get(cache_key)
    if cached_result:
        # Return the cached result (idempotency in action!)
        return cached_result
    
    try:
        # Convert user ID to integer (Telegram sends it as string)
        user_id = int(user["id"])
        
        # Get user's inventory
        inventory = await inventory_dao.get_or_create(user_id=user_id)
        
        # Parse source instance ID (assuming format "inv_{item_id}")
        if not request.sourceInstanceId.startswith("inv_"):
            raise HTTPException(status_code=400, detail="Invalid sourceInstanceId format")
        
        try:
            source_item_id = int(request.sourceInstanceId.replace("inv_", ""))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid sourceInstanceId format")
        
        # Get source item
        source_item = await item_dao.get_by_id(source_item_id)
        if not source_item or source_item.inventory_id != inventory.id:
            raise HTTPException(status_code=404, detail="Source item not found in inventory")
        
        if source_item.quantity <= 0:
            raise HTTPException(status_code=409, detail="Source item is locked", 
                              headers={"Content-Type": "application/json"})
        
        # Get source and target gifts
        source_gift = await gift_dao.get_by_id(source_item.gift_id)
        target_gift = await gift_dao.get_by_id(request.targetGiftId)
        
        if not source_gift or not target_gift:
            raise HTTPException(status_code=404, detail="Gift not found")
        
        # Calculate upgrade chance
        chance = calculate_upgrade_chance(float(source_gift.price), float(target_gift.price))
        
        # Generate wheel result
        success, final_angle, rotation_spins = generate_wheel_result(chance)
        
        # Generate transaction ID
        tx_id = str(uuid.uuid4())
        server_time = datetime.now(timezone.utc).isoformat()
        
        # Create transaction record
        await transaction_dao.create(
            user_id=user_id,
            amount=float(source_gift.price),
            type="upgrade",
            description=f"Upgrade {source_gift.name} -> {target_gift.name} ({'success' if success else 'failure'})",
            status="completed"
        )
        
        # Remove source item (consumed in upgrade)
        await item_dao.add_quantity(inventory.id, source_gift.id, -1)
        
        # Create response object
        if success:
            # Add target item to inventory
            await item_dao.add_quantity(inventory.id, target_gift.id, 1)
            
            # Get the new item for response
            new_item_record = await item_dao.get_one(inventory.id, target_gift.id)
            new_instance_id = f"inv_{new_item_record.id}"
            
            result = UpgradeSuccessResponse(
                txId=tx_id,
                chance=chance,
                success=True,
                finalAngle=final_angle,
                rotationSpins=rotation_spins,
                newItem=NewItemResponse(
                    instanceId=new_instance_id,
                    giftId=target_gift.id,
                    name=target_gift.name,
                    price=float(target_gift.price)
                ),
                consumedInstanceId=request.sourceInstanceId,
                serverTime=server_time
            )
        else:
            result = UpgradeFailureResponse(
                txId=tx_id,
                chance=chance,
                success=False,
                finalAngle=final_angle,
                rotationSpins=rotation_spins,
                consumedInstanceId=request.sourceInstanceId,
                serverTime=server_time
            )
        
        # Cache the result for idempotency (24 hours TTL)
        await cache_manager.set(cache_key, result.dict(), expire=86400)
        
        return result
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upgrade failed: {str(e)}")
