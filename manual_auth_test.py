"""Manual test for auth flow integration."""

import asyncio
import json
from fastapi.testclient import TestClient
from jose import jwt
import time
from unittest.mock import patch, AsyncMock

from app.main import app
from app.config.settings import settings


def create_test_token(user_id: str = "12345", username: str = "testuser"):
    """Create a test JWT token."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "user": {"id": user_id, "username": username},
        "iat": now,
        "exp": now + 3600
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def test_upgrade_endpoint_auth():
    """Test that upgrade endpoint properly handles authentication."""
    client = TestClient(app)
    
    print("🧪 Testing upgrade endpoint authentication...")
    
    # Test 1: No authentication
    print("\n1️⃣ Testing without authentication...")
    response = client.post(
        "/api/v1/upgrade/",
        json={"sourceInstanceId": "inv_123", "targetGiftId": 42},
        headers={"Idempotency-Key": "test-123"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 401, "Should require authentication"
    
    # Test 2: Invalid token
    print("\n2️⃣ Testing with invalid token...")
    client.cookies.set(settings.token_cookie_name, "invalid-token")
    response = client.post(
        "/api/v1/upgrade/",
        json={"sourceInstanceId": "inv_123", "targetGiftId": 42},
        headers={"Idempotency-Key": "test-123"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 401, "Should reject invalid token"
    
    # Test 3: Valid token but missing Idempotency-Key
    print("\n3️⃣ Testing with valid token but missing Idempotency-Key...")
    valid_token = create_test_token()
    client.cookies.set(settings.token_cookie_name, valid_token)
    response = client.post(
        "/api/v1/upgrade/",
        json={"sourceInstanceId": "inv_123", "targetGiftId": 42}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 400, "Should require Idempotency-Key"
    
    # Test 4: Valid auth but will fail on business logic (expected)
    print("\n4️⃣ Testing with valid token and Idempotency-Key...")
    response = client.post(
        "/api/v1/upgrade/",
        json={"sourceInstanceId": "inv_123", "targetGiftId": 42},
        headers={"Idempotency-Key": "test-123"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    # This should fail with business logic error, not auth error
    assert response.status_code != 401, "Auth should pass, business logic may fail"
    
    print("\n✅ Authentication integration works correctly!")


def test_telegram_auth_endpoint():
    """Test the Telegram auth endpoint."""
    client = TestClient(app)
    
    print("\n🔐 Testing Telegram auth endpoint...")
    
    # Test with invalid init_data (expected to fail)
    print("\n1️⃣ Testing with invalid init_data...")
    response = client.post(
        "/api/v1/auth/telegram",
        json={"init_data": "invalid_data"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("\n✅ Telegram auth endpoint is accessible!")


def check_dependencies():
    """Check that all dependencies are properly configured."""
    print("\n🔍 Checking dependencies...")
    
    # Check settings
    print(f"Bot token configured: {'yes' if settings.bot_token != 'your-bot-token-here' else 'no'}")
    print(f"Secret key configured: {'yes' if settings.secret_key != 'dev-secret-key-change-in-production' else 'NO (using dev key)'}")
    print(f"Token cookie name: {settings.token_cookie_name}")
    print(f"Token expires in: {settings.access_token_expire_minutes} minutes")
    
    # Check JWT functionality
    test_token = create_test_token()
    decoded = jwt.decode(test_token, settings.secret_key, algorithms=["HS256"])
    print(f"JWT test successful: {decoded['user']['id']}")
    
    print("\n✅ Dependencies check complete!")


def main():
    """Run all integration tests."""
    print("🚀 Starting Telegram Auth + Upgrade Integration Tests\n")
    
    try:
        check_dependencies()
        test_telegram_auth_endpoint()
        test_upgrade_endpoint_auth()
        
        print("\n" + "="*50)
        print("🎉 ALL TESTS PASSED!")
        print("Your Telegram auth integration is working correctly!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
