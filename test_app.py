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


if __name__ == "__main__":
    pytest.main([__file__])