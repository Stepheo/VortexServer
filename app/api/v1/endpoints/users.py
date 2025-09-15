"""(Deprecated) User endpoints removed from public API.

Router kept for internal reference; not included in main router.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.dao.user import get_user_dao
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"], include_in_schema=False)


class UserCreate(BaseModel):
    """User creation model."""
    tg_id: int
    username: str
    first_name: str
    last_name: Optional[str] = None


class UserUpdate(BaseModel):
    """User update model."""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


@router.get("/", response_model=List[dict])
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=100, description="Number of users to return"),
    session: AsyncSession = Depends(get_async_session)
):
    """Get all users with caching."""
    dao = get_user_dao(session)
    users = await dao.get_all_cached(skip=skip, limit=limit)
    return [user.to_dict() for user in users]


@router.get("/count", response_model=dict)
async def get_user_count(
    session: AsyncSession = Depends(get_async_session)
):
    """Get total user count with caching."""
    dao = get_user_dao(session)
    count = await dao.get_user_count()
    return {"count": count}


@router.get("/search", response_model=List[dict])
async def search_users(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    session: AsyncSession = Depends(get_async_session)
):
    """Search users by username or first name."""
    dao = get_user_dao(session)
    users = await dao.search_users(q, limit)
    return [user.to_dict() for user in users]


@router.get("/by-username/{username}", response_model=dict)
async def get_user_by_username(
    username: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Get user by username with caching."""
    dao = get_user_dao(session)
    user = await dao.get_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Get user by ID with caching."""
    dao = get_user_dao(session)
    user = await dao.get_by_id_cached(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()


@router.post("/", response_model=dict)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new user with cache invalidation."""
    dao = get_user_dao(session)
    
    # Check if username already exists
    existing_user = await dao.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = await dao.create(
        **user_data.model_dump()
    )
    return user.to_dict()


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_async_session)
):
    """Update user with cache invalidation."""
    dao = get_user_dao(session)
    
    # Check if user exists
    existing_user = await dao.get_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check for duplicate username if provided
    if user_data.username and user_data.username != existing_user.username:
        username_user = await dao.get_by_username(user_data.username)
        if username_user:
            raise HTTPException(status_code=400, detail="Username already exists")
    
    # Update user
    update_data = user_data.model_dump(exclude_unset=True)
    updated_user = await dao.update(user_id, **update_data)
    
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return updated_user.to_dict()


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Delete user with cache invalidation."""
    dao = get_user_dao(session)
    
    # Check if user exists
    existing_user = await dao.get_by_id(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    deleted = await dao.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}