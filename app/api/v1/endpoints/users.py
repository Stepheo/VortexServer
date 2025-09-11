"""User endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_manager
from app.core.cache_keys import (
    get_user_cache_key,
    get_users_list_cache_key,
    get_user_by_username_cache_key,
    get_user_by_email_cache_key,
)
from app.core.database import get_async_session
from app.dao.user import UserDAO

router = APIRouter(prefix="/users", tags=["users"])

# Cache expiration times (in seconds)
USER_CACHE_TTL = 300  # 5 minutes
USERS_LIST_CACHE_TTL = 120  # 2 minutes


@router.get("/", response_model=List[dict])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session)
):
    """Get all users."""
    # Check cache first
    cache_key = get_users_list_cache_key(skip, limit)
    cached_users = await cache_manager.get(cache_key)
    if cached_users is not None:
        return cached_users
    
    # If not in cache, get from database
    dao = UserDAO(session)
    users = await dao.get_all(skip=skip, limit=limit)
    result = [user.to_dict() for user in users]
    
    # Store in cache
    await cache_manager.set(cache_key, result, expire=USERS_LIST_CACHE_TTL)
    
    return result


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Get user by ID."""
    # Check cache first
    cache_key = get_user_cache_key(user_id)
    cached_user = await cache_manager.get(cache_key)
    if cached_user is not None:
        return cached_user
    
    # If not in cache, get from database
    dao = UserDAO(session)
    user = await dao.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = user.to_dict()
    
    # Store in cache
    await cache_manager.set(cache_key, result, expire=USER_CACHE_TTL)
    
    return result


@router.post("/", response_model=dict)
async def create_user(
    username: str,
    email: str,
    full_name: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new user."""
    dao = UserDAO(session)
    
    # Check if username or email already exists
    if await dao.username_exists(username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if await dao.email_exists(email):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create user
    user = await dao.create(
        username=username,
        email=email,
        full_name=full_name
    )
    result = user.to_dict()
    
    # Cache the new user
    cache_key = get_user_cache_key(user.id)
    await cache_manager.set(cache_key, result, expire=USER_CACHE_TTL)
    
    # Invalidate users list cache (since we added a new user)
    # We could be more sophisticated here, but for simplicity, we'll clear related cache patterns
    await cache_manager.delete(get_users_list_cache_key(0, 100))  # Clear default list
    
    return result


@router.get("/by-username/{username}", response_model=dict)
async def get_user_by_username(
    username: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Get user by username."""
    # Check cache first
    cache_key = get_user_by_username_cache_key(username)
    cached_user = await cache_manager.get(cache_key)
    if cached_user is not None:
        return cached_user
    
    # If not in cache, get from database
    dao = UserDAO(session)
    user = await dao.get_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = user.to_dict()
    
    # Store in cache
    await cache_manager.set(cache_key, result, expire=USER_CACHE_TTL)
    
    return result


@router.get("/by-email/{email}", response_model=dict)  
async def get_user_by_email(
    email: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Get user by email."""
    # Check cache first
    cache_key = get_user_by_email_cache_key(email)
    cached_user = await cache_manager.get(cache_key)
    if cached_user is not None:
        return cached_user
    
    # If not in cache, get from database
    dao = UserDAO(session)
    user = await dao.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    result = user.to_dict()
    
    # Store in cache
    await cache_manager.set(cache_key, result, expire=USER_CACHE_TTL)
    
    return result