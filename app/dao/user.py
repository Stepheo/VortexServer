"""User Data Access Object with specialized methods."""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_manager
from app.dao.base import BaseDAO
from app.models.user import User


class UserDAO(BaseDAO[User]):
    """User DAO with specialized methods and caching."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_id_cached(self, user_id: int) -> Optional[User]:
        """Get user by ID with Redis caching."""
        cache_key = f"user:{user_id}"
        
        # Try to get from cache first
        cached_user = await cache_manager.get(cache_key)
        if cached_user:
            # Convert cached dict back to User object
            user = User(**cached_user)
            return user
        
        # If not in cache, get from database
        user = await self.get_by_id(user_id)
        if user:
            # Cache the user data for 5 minutes
            await cache_manager.set(cache_key, user.to_dict(), expire=300)
        
        return user
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        cache_key = f"user:username:{username}"
        
        # Try cache first
        cached_user = await cache_manager.get(cache_key)
        if cached_user:
            user = User(**cached_user)
            return user
        
        # Get from database
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Cache for 5 minutes
            await cache_manager.set(cache_key, user.to_dict(), expire=300)
        
        return user
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        cache_key = f"user:email:{email}"
        
        # Try cache first
        cached_user = await cache_manager.get(cache_key)
        if cached_user:
            user = User(**cached_user)
            return user
        
        # Get from database
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Cache for 5 minutes
            await cache_manager.set(cache_key, user.to_dict(), expire=300)
        
        return user
    
    async def get_all_cached(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[User]:
        """Get all users with caching for common queries."""
        # Create cache key based on parameters
        cache_key = f"users:skip:{skip}:limit:{limit}:filters:{hash(str(sorted(filters.items())))}"
        
        # Try cache first
        cached_users = await cache_manager.get(cache_key)
        if cached_users:
            return [User(**user_data) for user_data in cached_users]
        
        # Get from database
        users = await self.get_all(skip=skip, limit=limit, **filters)
        
        if users:
            # Cache for 2 minutes (shorter for list queries)
            users_data = [user.to_dict() for user in users]
            await cache_manager.set(cache_key, users_data, expire=120)
        
        return users
    
    async def search_users(self, query: str, limit: int = 10) -> List[User]:
        """Search users by username or full name."""
        search_query = select(User).where(
            (User.username.ilike(f"%{query}%")) |
            (User.full_name.ilike(f"%{query}%"))
        ).limit(limit)
        
        result = await self.session.execute(search_query)
        return list(result.scalars().all())
    
    async def get_user_count(self) -> int:
        """Get total user count with caching."""
        cache_key = "users:count"
        
        cached_count = await cache_manager.get(cache_key)
        if cached_count is not None:
            return cached_count
        
        result = await self.session.execute(
            select(func.count(User.id))
        )
        count = result.scalar() or 0
        
        # Cache count for 1 minute
        await cache_manager.set(cache_key, count, expire=60)
        
        return count
    
    async def create(self, **kwargs) -> User:
        """Create user and invalidate relevant caches."""
        user = await super().create(**kwargs)
        
        # Invalidate relevant caches
        await self._invalidate_user_caches(user)
        await cache_manager.delete("users:count")
        
        return user
    
    async def update(self, id: int, **kwargs) -> Optional[User]:
        """Update user and invalidate relevant caches."""
        # Get old user data for cache invalidation
        old_user = await self.get_by_id(id)
        
        user = await super().update(id, **kwargs)
        
        if user:
            # Invalidate caches for both old and new user data
            if old_user:
                await self._invalidate_user_caches(old_user)
            await self._invalidate_user_caches(user)
        
        return user
    
    async def delete(self, id: int) -> bool:
        """Delete user and invalidate relevant caches."""
        # Get user data before deletion for cache invalidation
        user = await self.get_by_id(id)
        
        deleted = await super().delete(id)
        
        if deleted and user:
            await self._invalidate_user_caches(user)
            await cache_manager.delete("users:count")
        
        return deleted
    
    async def _invalidate_user_caches(self, user: User) -> None:
        """Helper method to invalidate all caches related to a user."""
        await cache_manager.delete(f"user:{user.id}")
        await cache_manager.delete(f"user:username:{user.username}")
        await cache_manager.delete(f"user:email:{user.email}")
        
        # Invalidate list caches (we could be more sophisticated here)
        # For simplicity, we'll clear common list cache patterns
        for skip in [0, 10, 20]:
            for limit in [10, 100]:
                await cache_manager.delete(f"users:skip:{skip}:limit:{limit}:filters:{hash(str([]))}")


def get_user_dao(session: AsyncSession) -> UserDAO:
    """Factory function to create UserDAO instance."""
    return UserDAO(session)