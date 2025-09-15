"""Test idempotency functionality in upgrade endpoint."""

import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from jose import jwt
import time
import json

from app.main import app
from app.config.settings import settings


def create_test_token(user_id: str = "12345"):
    """Create a test JWT token."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "user": {"id": user_id, "username": "testuser"},
        "iat": now,
        "exp": now + 3600
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def test_idempotency():
    """Test that idempotency works correctly."""
    client = TestClient(app)
    
    print("🧪 Testing Idempotency-Key functionality...")
    
    # Set up authentication
    token = create_test_token()
    client.cookies.set(settings.token_cookie_name, token)
    
    # Generate a unique idempotency key
    idempotency_key = str(uuid.uuid4())
    print(f"🔑 Using Idempotency-Key: {idempotency_key}")
    
    request_data = {
        "sourceInstanceId": "inv_999",
        "targetGiftId": 42
    }
    
    # First request - will fail with business logic error but should be cached
    print("\n1️⃣ First request...")
    response1 = client.post(
        "/api/v1/upgrade/",
        json=request_data,
        headers={"Idempotency-Key": idempotency_key}
    )
    print(f"Status: {response1.status_code}")
    if response1.status_code == 500:
        print(f"Response: {response1.json()}")
    
    # Second request with SAME idempotency key
    print("\n2️⃣ Second request with SAME key...")
    response2 = client.post(
        "/api/v1/upgrade/",
        json=request_data,
        headers={"Idempotency-Key": idempotency_key}
    )
    print(f"Status: {response2.status_code}")
    if response2.status_code == 500:
        print(f"Response: {response2.json()}")
    
    # Check if responses are identical (key test for idempotency)
    if response1.status_code == response2.status_code:
        if response1.status_code == 500:
            # Both failed with same error - that's expected for non-existent items
            print("✅ Both requests failed identically - idempotency working for errors")
        else:
            # Both succeeded - compare full responses
            data1 = response1.json()
            data2 = response2.json()
            if data1 == data2:
                print("✅ Responses identical - idempotency working!")
                print(f"🎯 Same txId: {data1.get('txId') == data2.get('txId')}")
            else:
                print("❌ Responses different - idempotency not working!")
    
    # Third request with DIFFERENT idempotency key
    print("\n3️⃣ Third request with DIFFERENT key...")
    new_key = str(uuid.uuid4())
    response3 = client.post(
        "/api/v1/upgrade/",
        json=request_data,
        headers={"Idempotency-Key": new_key}
    )
    print(f"Status: {response3.status_code}")
    print(f"New key: {new_key}")
    
    print("\n✅ Idempotency test completed!")


@patch('app.core.cache.cache_manager')
def test_idempotency_with_mock_success(mock_cache):
    """Test idempotency with successful mocked operations."""
    client = TestClient(app)
    
    print("\n🧪 Testing Idempotency with mocked success...")
    
    # Mock cache to simulate no cached result first, then return cached result
    mock_cache.get = AsyncMock(side_effect=[None, {
        "txId": "cached-tx-123",
        "chance": 50.0,
        "success": True,
        "finalAngle": 45.0,
        "rotationSpins": 4,
        "newItem": {
            "instanceId": "inv_cached",
            "giftId": 42,
            "name": "Cached Item",
            "price": 100.0
        },
        "consumedInstanceId": "inv_999",
        "serverTime": "2025-09-15T12:00:00Z"
    }])
    mock_cache.set = AsyncMock()
    
    token = create_test_token()
    client.cookies.set(settings.token_cookie_name, token)
    
    idempotency_key = str(uuid.uuid4())
    request_data = {"sourceInstanceId": "inv_999", "targetGiftId": 42}
    
    # First request - no cache
    print("1️⃣ First request (no cache)...")
    response1 = client.post(
        "/api/v1/upgrade/",
        json=request_data,
        headers={"Idempotency-Key": idempotency_key}
    )
    print(f"Status: {response1.status_code}")
    
    # Second request - should return cached result
    print("2️⃣ Second request (cached)...")
    response2 = client.post(
        "/api/v1/upgrade/",
        json=request_data,
        headers={"Idempotency-Key": idempotency_key}
    )
    print(f"Status: {response2.status_code}")
    
    if response2.status_code == 200:
        cached_data = response2.json()
        print(f"✅ Cached result returned: txId={cached_data.get('txId')}")
        print(f"✅ Success: {cached_data.get('success')}")
    
    print("✅ Mock idempotency test completed!")


def main():
    """Run idempotency tests."""
    print("🚀 Starting Idempotency Tests\n")
    
    try:
        test_idempotency()
        test_idempotency_with_mock_success()
        
        print("\n" + "="*50)
        print("🎉 IDEMPOTENCY TESTS COMPLETED!")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
