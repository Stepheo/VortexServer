"""Simple validation test for the application structure."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


def test_app_creation():
    """Test that the app can be created without errors."""
    with patch('app.core.database.create_db_and_tables', new_callable=AsyncMock):
        with patch('app.core.cache.cache_manager.connect', new_callable=AsyncMock):
            from app.main import create_app
            
            app = create_app()
            assert app is not None
            assert app.title == "VortexServer"


def test_root_endpoint():
    """Test the root endpoint."""
    with patch('app.core.database.create_db_and_tables', new_callable=AsyncMock):
        with patch('app.core.cache.cache_manager.connect', new_callable=AsyncMock):
            with patch('app.core.cache.cache_manager.disconnect', new_callable=AsyncMock):
                with patch('app.core.database.close_db_connection', new_callable=AsyncMock):
                    from app.main import app
                    
                    with TestClient(app) as client:
                        response = client.get("/")
                        assert response.status_code == 200
                        data = response.json()
                        assert data["message"] == "Welcome to VortexServer"
                        assert "version" in data


def test_health_endpoint():
    """Test the health check endpoint."""
    with patch('app.core.database.create_db_and_tables', new_callable=AsyncMock):
        with patch('app.core.cache.cache_manager.connect', new_callable=AsyncMock):
            with patch('app.core.cache.cache_manager.disconnect', new_callable=AsyncMock):
                with patch('app.core.database.close_db_connection', new_callable=AsyncMock):
                    from app.main import app
                    
                    with TestClient(app) as client:
                        response = client.get("/api/v1/health")
                        assert response.status_code == 200
                        data = response.json()
                        assert data["status"] == "healthy"


def test_settings_loading():
    """Test that settings can be loaded."""
    from app.config.settings import settings
    
    assert settings is not None
    assert hasattr(settings, 'database_url')
    assert hasattr(settings, 'redis_url')
    assert hasattr(settings, 'debug')


def test_dao_pattern():
    """Test DAO pattern functionality."""
    from unittest.mock import Mock
    from app.dao.base import BaseDAO
    from app.models.base import BaseModel
    
    # Create a mock model
    class MockModel(BaseModel):
        __tablename__ = "mock"
        __table_args__ = {'extend_existing': True}
    
    # Create a mock session
    mock_session = Mock()
    
    # Test DAO creation
    dao = BaseDAO(MockModel, mock_session)
    assert dao.model == MockModel
    assert dao.session == mock_session


def test_user_dao():
    """Test UserDAO specific functionality."""
    from unittest.mock import Mock
    from app.dao.user import UserDAO
    
    # Create a mock session
    mock_session = Mock()
    
    # Test UserDAO creation
    user_dao = UserDAO(mock_session)
    assert user_dao.session == mock_session
    
    # Test that it has the specialized methods
    assert hasattr(user_dao, 'get_by_username')
    assert hasattr(user_dao, 'get_by_email')
    assert hasattr(user_dao, 'username_exists')
    assert hasattr(user_dao, 'email_exists')


def test_cache_keys():
    """Test cache key generation."""
    from app.core.cache_keys import (
        get_user_cache_key,
        get_users_list_cache_key,
        get_user_by_username_cache_key,
        get_user_by_email_cache_key,
    )
    
    # Test cache key generation
    assert get_user_cache_key(123) == "user:123"
    assert get_users_list_cache_key(0, 100) == "users:list:skip=0:limit=100"
    assert get_user_by_username_cache_key("testuser") == "user:username:testuser"
    assert get_user_by_email_cache_key("test@example.com") == "user:email:test@example.com"


if __name__ == "__main__":
    pytest.main([__file__])