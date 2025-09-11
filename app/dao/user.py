"""User-specific DAO with special methods."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dao.base import BaseDAO
from app.models.user import User


class UserDAO(BaseDAO[User]):
    """User Data Access Object with specialized methods."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def search_by_name(self, name_pattern: str) -> List[User]:
        """Search users by full name pattern."""
        result = await self.session.execute(
            select(User).where(User.full_name.ilike(f"%{name_pattern}%"))
        )
        return list(result.scalars().all())
    
    async def get_users_by_domain(self, domain: str) -> List[User]:
        """Get all users with email from specific domain."""
        result = await self.session.execute(
            select(User).where(User.email.ilike(f"%@{domain}"))
        )
        return list(result.scalars().all())
    
    async def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        return await self.exists(username=username)
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        return await self.exists(email=email)