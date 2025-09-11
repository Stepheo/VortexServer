"""User endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.dao.base import get_dao
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[dict])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session)
):
    """Get all users."""
    dao = get_dao(User, session)
    users = await dao.get_all(skip=skip, limit=limit)
    return [user.to_dict() for user in users]


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Get user by ID."""
    dao = get_dao(User, session)
    user = await dao.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.to_dict()


@router.post("/", response_model=dict)
async def create_user(
    username: str,
    email: str,
    full_name: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new user."""
    dao = get_dao(User, session)
    user = await dao.create(
        username=username,
        email=email,
        full_name=full_name
    )
    return user.to_dict()