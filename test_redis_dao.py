"""Test Redis caching and UserDAO functionality."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.dao.user import UserDAO
from app.models.user import User


@pytest.fixture
def mock_session():
    """Create mock async session."""
    session = AsyncMock()
    return session


@pytest.fixture 
def mock_user():
    """Create mock user."""
    user = User()
    user.id = 1
    user.username = "testuser"
    user.email = "test@example.com"
    user.full_name = "Test User"
    return user


@pytest.mark.asyncio
async def test_user_dao_creation(mock_session):
    """Test UserDAO creation."""
    dao = UserDAO(mock_session)
    assert dao.model == User
    assert dao.session == mock_session


@pytest.mark.asyncio
async def test_user_dao_get_by_username(mock_session, mock_user):
    """Test get user by username without cache."""
    # Mock session execute
    result_mock = AsyncMock()
    result_mock.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = result_mock
    
    # Mock cache manager to return None (cache miss)
    with patch('app.dao.user.cache_manager') as mock_cache:
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        
        dao = UserDAO(mock_session)
        user = await dao.get_by_username("testuser")
        
        assert user == mock_user
        mock_cache.get.assert_called_once_with("user:username:testuser")
        mock_cache.set.assert_called_once_with(
            "user:username:testuser", 
            mock_user.to_dict(), 
            expire=300
        )


@pytest.mark.asyncio
async def test_user_dao_get_by_username_cached(mock_session, mock_user):
    """Test get user by username with cache hit."""
    # Mock cache manager to return cached user
    with patch('app.dao.user.cache_manager') as mock_cache:
        mock_cache.get = AsyncMock(return_value=mock_user.to_dict())
        
        dao = UserDAO(mock_session)
        user = await dao.get_by_username("testuser")
        
        # Should not call database
        mock_session.execute.assert_not_called()
        mock_cache.get.assert_called_once_with("user:username:testuser")


@pytest.mark.asyncio
async def test_user_dao_cache_invalidation(mock_session, mock_user):
    """Test cache invalidation on user update."""
    # Mock get_by_id to return user
    with patch.object(UserDAO, 'get_by_id', return_value=mock_user):
        # Mock parent update method
        with patch('app.dao.base.BaseDAO.update', return_value=mock_user):
            # Mock cache manager
            with patch('app.dao.user.cache_manager') as mock_cache:
                mock_cache.delete = AsyncMock()
                
                dao = UserDAO(mock_session)
                await dao.update(1, username="newusername")
                
                # Check that all relevant caches are invalidated
                expected_calls = [
                    f"user:{mock_user.id}",
                    f"user:username:{mock_user.username}",  
                    f"user:email:{mock_user.email}",
                ]
                
                for call in expected_calls:
                    assert any(call in str(c) for c in mock_cache.delete.call_args_list)


@pytest.mark.asyncio
async def test_user_dao_search_users(mock_session, mock_user):
    """Test user search functionality."""
    result_mock = AsyncMock()
    scalars_mock = AsyncMock()
    scalars_mock.all.return_value = [mock_user]
    result_mock.scalars.return_value = scalars_mock
    mock_session.execute.return_value = result_mock
    
    dao = UserDAO(mock_session)
    users = await dao.search_users("test")
    
    assert users == [mock_user]
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_user_dao_get_count_cached(mock_session):
    """Test get user count with caching."""
    # Mock database result
    result_mock = AsyncMock()
    result_mock.scalar.return_value = 42
    mock_session.execute.return_value = result_mock
    
    # Mock cache manager (cache miss)
    with patch('app.dao.user.cache_manager') as mock_cache:
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        
        dao = UserDAO(mock_session)
        count = await dao.get_user_count()
        
        assert count == 42
        mock_cache.set.assert_called_once_with("users:count", 42, expire=60)


def test_user_dao_factory_function(mock_session):
    """Test the get_user_dao factory function."""
    from app.dao.user import get_user_dao
    
    dao = get_user_dao(mock_session)
    assert isinstance(dao, UserDAO)
    assert dao.session == mock_session


if __name__ == "__main__":
    pytest.main([__file__, "-v"])