# DAO Pattern Implementation Guide

This document explains how to create DAOs (Data Access Objects) for your models in VortexServer.

## Overview

The DAO pattern provides a clean abstraction layer between your business logic and data persistence. Each model should have its own specialized DAO class that extends the base `BaseDAO` and includes model-specific methods.

## BaseDAO Features

The `BaseDAO` class provides standard CRUD operations:

- `create(**kwargs)` - Create a new record
- `get_by_id(id)` - Get record by ID
- `get_all(skip, limit, **filters)` - Get all records with pagination and filtering
- `update(id, **kwargs)` - Update record by ID
- `delete(id)` - Delete record by ID
- `count(**filters)` - Count records with optional filtering
- `exists(**filters)` - Check if record exists

## Creating a Specialized DAO

### 1. Create the DAO Class

Create a new file `app/dao/your_model.py`:

```python
"""YourModel Data Access Object with specialized methods."""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_manager
from app.dao.base import BaseDAO
from app.models.your_model import YourModel


class YourModelDAO(BaseDAO[YourModel]):
    """YourModel DAO with specialized methods and caching."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(YourModel, session)
    
    # Add your specialized methods here
    async def get_by_custom_field(self, field_value: str) -> Optional[YourModel]:
        """Get record by custom field with caching."""
        cache_key = f"your_model:custom_field:{field_value}"
        
        # Try cache first
        cached_data = await cache_manager.get(cache_key)
        if cached_data:
            return YourModel(**cached_data)
        
        # Get from database
        result = await self.session.execute(
            select(YourModel).where(YourModel.custom_field == field_value)
        )
        record = result.scalar_one_or_none()
        
        if record:
            # Cache for 5 minutes
            await cache_manager.set(cache_key, record.to_dict(), expire=300)
        
        return record
    
    async def create(self, **kwargs) -> YourModel:
        """Create record and invalidate relevant caches."""
        record = await super().create(**kwargs)
        
        # Invalidate relevant caches
        await self._invalidate_caches(record)
        
        return record
    
    async def update(self, id: int, **kwargs) -> Optional[YourModel]:
        """Update record and invalidate relevant caches."""
        # Get old record for cache invalidation
        old_record = await self.get_by_id(id)
        
        record = await super().update(id, **kwargs)
        
        if record:
            # Invalidate caches for both old and new data
            if old_record:
                await self._invalidate_caches(old_record)
            await self._invalidate_caches(record)
        
        return record
    
    async def delete(self, id: int) -> bool:
        """Delete record and invalidate relevant caches."""
        # Get record before deletion for cache invalidation
        record = await self.get_by_id(id)
        
        deleted = await super().delete(id)
        
        if deleted and record:
            await self._invalidate_caches(record)
        
        return deleted
    
    async def _invalidate_caches(self, record: YourModel) -> None:
        """Helper method to invalidate all caches related to a record."""
        await cache_manager.delete(f"your_model:{record.id}")
        await cache_manager.delete(f"your_model:custom_field:{record.custom_field}")
        # Add other cache invalidations as needed


def get_your_model_dao(session: AsyncSession) -> YourModelDAO:
    """Factory function to create YourModelDAO instance."""
    return YourModelDAO(session)
```

### 2. Update DAO Module Exports

Add your new DAO to `app/dao/__init__.py`:

```python
"""Data Access Object (DAO) module."""

from app.dao.base import BaseDAO, get_dao
from app.dao.user import UserDAO, get_user_dao
from app.dao.your_model import YourModelDAO, get_your_model_dao

__all__ = [
    "BaseDAO",
    "get_dao", 
    "UserDAO",
    "get_user_dao",
    "YourModelDAO",
    "get_your_model_dao",
]
```

### 3. Use in Endpoints

Use your DAO in API endpoints:

```python
"""YourModel endpoints with caching."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.dao.your_model import get_your_model_dao

router = APIRouter(prefix="/your-models", tags=["your-models"])


@router.get("/{record_id}")
async def get_record(
    record_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Get record by ID with caching."""
    dao = get_your_model_dao(session)
    record = await dao.get_by_id_cached(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record.to_dict()


@router.get("/by-field/{field_value}")
async def get_by_custom_field(
    field_value: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Get record by custom field with caching."""
    dao = get_your_model_dao(session)
    record = await dao.get_by_custom_field(field_value)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record.to_dict()
```

## Redis Caching Best Practices

### Cache Key Naming Convention

Use descriptive, hierarchical cache keys:

- `model:id:value` for individual records
- `model:field:value` for field-based lookups
- `models:query_params` for list queries

### Cache Expiration

- Individual records: 5 minutes (300 seconds)
- List queries: 2 minutes (120 seconds)
- Count queries: 1 minute (60 seconds)

### Cache Invalidation

Always invalidate relevant caches when data changes:

1. On `create()`: Invalidate list/count caches
2. On `update()`: Invalidate all caches related to old and new data
3. On `delete()`: Invalidate all caches related to the record

### Example Cache Methods

```python
async def get_by_id_cached(self, id: int) -> Optional[YourModel]:
    """Get by ID with caching."""
    cache_key = f"your_model:{id}"
    
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        return YourModel(**cached_data)
    
    record = await self.get_by_id(id)
    if record:
        await cache_manager.set(cache_key, record.to_dict(), expire=300)
    
    return record

async def get_all_cached(self, skip: int = 0, limit: int = 100, **filters) -> List[YourModel]:
    """Get all with caching."""
    cache_key = f"your_models:skip:{skip}:limit:{limit}:filters:{hash(str(sorted(filters.items())))}"
    
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        return [YourModel(**item) for item in cached_data]
    
    records = await self.get_all(skip=skip, limit=limit, **filters)
    if records:
        records_data = [record.to_dict() for record in records]
        await cache_manager.set(cache_key, records_data, expire=120)
    
    return records
```

## Testing Your DAO

Create tests for your DAO in `test_your_model_dao.py`:

```python
import pytest
from unittest.mock import Mock

from app.dao.your_model import YourModelDAO, get_your_model_dao
from app.models.your_model import YourModel


def test_your_model_dao_creation():
    """Test YourModelDAO creation."""
    mock_session = Mock()
    dao = YourModelDAO(mock_session)
    assert dao.model == YourModel
    assert dao.session == mock_session


def test_your_model_dao_factory():
    """Test factory function."""
    mock_session = Mock()
    dao = get_your_model_dao(mock_session)
    assert isinstance(dao, YourModelDAO)
```

## UserDAO Example

The `UserDAO` class is implemented as a complete example following these patterns. See `app/dao/user.py` for the full implementation including:

- Caching for all read operations
- Specialized methods (`get_by_username`, `get_by_email`, `search_users`)
- Proper cache invalidation on data changes
- Factory function for easy instantiation

This pattern ensures consistent, efficient data access with Redis caching throughout your application.