"""Integration tests for gifts and inventory endpoints.
These use the FastAPI test client and an in-memory SQLite (if configured by create_db_and_tables()).
"""

import pytest
from jose import jwt
from fastapi.testclient import TestClient

from app.main import app
from app.config.settings import settings


def make_token(user_id: int = 1):
    payload = {"user": {"id": user_id, "username": "tester"}}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def client_with_auth(user_id: int = 1):
    token = make_token(user_id)
    # Use context manager in tests to ensure lifespan runs; here return raw client for backwards compat
    client = TestClient(app)
    client.cookies.set(settings.token_cookie_name, token)
    return client


def test_gift_crud_flow():
    # Entire interaction must remain inside context manager to keep event loop alive
    with TestClient(app) as client:
        client.cookies.set(settings.token_cookie_name, make_token(1))

        # Create gift
        resp = client.post("/api/v1/gifts/", params={
            "name": "GiftA",
            "real_rarity": 0.1,
            "visual_rarity": 0.2,
            "rarity_color": "#fff"
        })
        if resp.status_code == 201:
            gift_id = resp.json()["id"]
        else:  # Already exists
            assert resp.status_code == 400
            existing = client.get("/api/v1/gifts/by-name/GiftA")
            assert existing.status_code == 200
            gift_id = existing.json()["id"]

        # Get gift
        resp = client.get(f"/api/v1/gifts/{gift_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "GiftA"

        # List gifts
        resp = client.get("/api/v1/gifts/")
        assert resp.status_code == 200
        assert any(g["name"] == "GiftA" for g in resp.json())

        # Filter by rarity
        resp = client.get("/api/v1/gifts/", params={"min_real": 0.05, "max_real": 0.2})
        assert resp.status_code == 200
        assert any(g["name"] == "GiftA" for g in resp.json())


def test_inventory_flow():
    with TestClient(app) as client:
        client.cookies.set(settings.token_cookie_name, make_token(2))

        # Ensure a gift exists
        resp = client.post("/api/v1/gifts/", params={
            "name": "GiftB",
            "real_rarity": 0.3,
            "visual_rarity": 0.4,
            "rarity_color": "#000"
        })
        if resp.status_code == 400:
            # Ensure the error is due to the gift already existing
            assert "already exists" in resp.text.lower()
        else:
            assert resp.status_code in (200, 201)

        # Get gift id (fetch by name if already exists)
        if resp.status_code == 201:
            gift_id = resp.json()["id"]
        else:
            gift = client.get("/api/v1/gifts/by-name/GiftB").json()
            gift_id = gift["id"]

        # Inventory initially empty
        inv_resp = client.get("/api/v1/inventory/")
        assert inv_resp.status_code == 200
        assert inv_resp.json()["items"] == []

        # Add quantity
        add_resp = client.post("/api/v1/inventory/add", params={"gift_id": gift_id, "delta": 5})
        assert add_resp.status_code == 200
        assert add_resp.json()["quantity"] == 5

        # Set quantity
        set_resp = client.put("/api/v1/inventory/set", params={"gift_id": gift_id, "quantity": 2})
        assert set_resp.status_code == 200
        assert set_resp.json()["quantity"] == 2

        # Remove
        del_resp = client.delete("/api/v1/inventory/remove", params={"gift_id": gift_id})
        assert del_resp.status_code == 200
        assert del_resp.json()["removed"] is True

        # Inventory empty again
        inv_resp2 = client.get("/api/v1/inventory/")
        assert inv_resp2.status_code == 200
        assert inv_resp2.json()["items"] == []
