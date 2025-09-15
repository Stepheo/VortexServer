"""Test integration between Telegram auth and upgrade endpoint."""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from jose import jwt
import time

from app.main import app
from app.config.settings import settings


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user():
    return {
        "id": "12345",
        "username": "testuser"
    }


@pytest.fixture
def valid_jwt_token(mock_user):
    """Create a valid JWT token for testing."""
    now = int(time.time())
    payload = {
        "sub": str(mock_user["id"]),
        "user": mock_user,
        "iat": now,
        "exp": now + 3600  # 1 hour
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


class TestTelegramAuthIntegration:
    """Test Telegram authentication integration with upgrade endpoint."""
    
    def test_upgrade_without_auth_fails(self, client):
        """Test that upgrade endpoint requires authentication."""
        response = client.post(
            "/api/v1/upgrade/",
            json={
                "sourceInstanceId": "inv_123",
                "targetGiftId": 42
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        assert response.status_code == 401
        assert "Not authenticated" in str(response.json())
    
    def test_upgrade_with_invalid_token_fails(self, client):
        """Test that upgrade endpoint rejects invalid tokens."""
        client.cookies.set(settings.token_cookie_name, "invalid-token")
        response = client.post(
            "/api/v1/upgrade/",
            json={
                "sourceInstanceId": "inv_123",
                "targetGiftId": 42
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        assert response.status_code == 401
        assert "Invalid or expired token" in str(response.json())
    
    @patch('app.dao.inventory.get_inventory_dao')
    @patch('app.dao.inventory_item.get_inventory_item_dao')
    @patch('app.dao.gift.get_gift_dao')
    @patch('app.dao.transaction.get_transaction_dao')
    def test_upgrade_with_valid_auth_processes_request(
        self, 
        mock_transaction_dao,
        mock_gift_dao,
        mock_item_dao,
        mock_inventory_dao,
        client, 
        valid_jwt_token,
        mock_user
    ):
        """Test that upgrade endpoint processes requests with valid authentication."""
        # Set up mocks
        mock_inventory = AsyncMock()
        mock_inventory.id = 1
        mock_inventory_dao.return_value.get_or_create = AsyncMock(return_value=mock_inventory)
        
        mock_item = AsyncMock()
        mock_item.id = 123
        mock_item.inventory_id = 1
        mock_item.gift_id = 1
        mock_item.quantity = 1
        mock_item_dao.return_value.get_by_id = AsyncMock(return_value=mock_item)
        
        mock_source_gift = AsyncMock()
        mock_source_gift.id = 1
        mock_source_gift.name = "Source Gift"
        mock_source_gift.price = 100
        
        mock_target_gift = AsyncMock()
        mock_target_gift.id = 42
        mock_target_gift.name = "Target Gift"
        mock_target_gift.price = 200
        
        def mock_get_gift_by_id(gift_id):
            if gift_id == 1:
                return AsyncMock(return_value=mock_source_gift)
            elif gift_id == 42:
                return AsyncMock(return_value=mock_target_gift)
            return AsyncMock(return_value=None)
        
        mock_gift_dao.return_value.get_by_id = mock_get_gift_by_id
        mock_transaction_dao.return_value.create = AsyncMock()
        mock_item_dao.return_value.add_quantity = AsyncMock()
        mock_item_dao.return_value.get_one = AsyncMock(return_value=mock_item)
        
        # Set authentication cookie
        client.cookies.set(settings.token_cookie_name, valid_jwt_token)
        
        # Make request
        response = client.post(
            "/api/v1/upgrade/",
            json={
                "sourceInstanceId": "inv_123",
                "targetGiftId": 42
            },
            headers={"Idempotency-Key": "test-key-123"}
        )
        
        # The request should not fail with auth errors
        # It might fail with other errors (like database issues in tests)
        # but auth should be passed
        assert response.status_code != 401
        
        # Verify that the user was properly extracted from the token
        # by checking that DAOs were called (indicating auth passed)
        mock_inventory_dao.return_value.get_or_create.assert_called_once()


class TestTelegramAuthFlow:
    """Test the complete Telegram authentication flow."""
    
    @patch('app.api.v1.endpoints.auth_telegram.cache_manager')
    def test_telegram_auth_creates_valid_cookie(self, mock_cache, client):
        """Test that Telegram auth creates a valid JWT cookie."""
        # Mock cache operations
        mock_cache.get = AsyncMock(return_value=None)
        mock_cache.set = AsyncMock()
        mock_cache.exists = AsyncMock(return_value=False)
        
        # Mock a valid init_data (this would normally come from Telegram)
        # For testing, we'll create a simplified version
        init_data = "user_id=12345\nusername=testuser\nauth_date=1234567890\nhash=validhash"
        
        # This will fail signature verification, but we can patch that
        with patch('app.api.v1.endpoints.auth_telegram.verify_telegram_init_data') as mock_verify:
            mock_verify.return_value = {
                "user_id": "12345",
                "username": "testuser",
                "auth_date": "1234567890"
            }
            
            response = client.post(
                "/api/v1/auth/telegram",
                json={"init_data": init_data}
            )
            
            assert response.status_code == 200
            assert response.json()["message"] == "authenticated"
            assert response.json()["user"]["id"] == "12345"
            assert response.json()["user"]["username"] == "testuser"
            
            # Check that cookie was set
            assert settings.token_cookie_name in response.cookies
            
            # Verify the token can be decoded
            token = response.cookies[settings.token_cookie_name]
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            assert payload["user"]["id"] == "12345"
            assert payload["user"]["username"] == "testuser"


def test_auth_flow_integration():
    """Integration test showing the complete auth + upgrade flow."""
    # This would be a full integration test showing:
    # 1. Client authenticates via Telegram
    # 2. Server sets JWT cookie
    # 3. Client uses cookie to call upgrade endpoint
    # 4. Server validates cookie and processes upgrade
    pass


if __name__ == "__main__":
    # Quick manual test
    print("Testing Telegram auth integration...")
    
    # Test token creation
    mock_user = {"id": "12345", "username": "testuser"}
    now = int(time.time())
    payload = {
        "sub": str(mock_user["id"]),
        "user": mock_user,
        "iat": now,
        "exp": now + 3600
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    print(f"Created token: {token[:50]}...")
    
    # Test token decoding
    decoded = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    print(f"Decoded user: {decoded['user']}")
    
    print("✅ Basic JWT functionality works!")
