"""Base DAO pattern implementation."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseDAO(Generic[ModelType]):
    """Base Data Access Object for database operations."""
    
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session
    
    async def create(self, **kwargs) -> ModelType:
        """Create a new record."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance
    
    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get record by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """Get all records with optional filtering."""
        query = select(self.model)
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def update(
        self,
        id: int,
        **kwargs
    ) -> Optional[ModelType]:
        """Update record by ID."""
        # Remove None values
        update_data = {k: v for k, v in kwargs.items() if v is not None}
        
        if not update_data:
            return await self.get_by_id(id)
        
        await self.session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
        )
        await self.session.commit()
        
        return await self.get_by_id(id)
    
    async def delete(self, id: int) -> bool:
        """Delete record by ID."""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def count(self, **filters) -> int:
        """Count records with optional filtering."""
        query = select(func.count(self.model.id))
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def exists(self, **filters) -> bool:
        """Check if record exists with given filters."""
        query = select(self.model.id)
        
        # Apply filters
        for field, value in filters.items():
            if hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        
        query = query.limit(1)
        result = await self.session.execute(query)
        return result.scalar() is not None


def get_dao(model: Type[ModelType], session: AsyncSession) -> BaseDAO[ModelType]:
    """Factory function to create DAO instance."""
    return BaseDAO(model, session)