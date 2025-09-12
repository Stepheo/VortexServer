import hashlib
import hmac
import time
from fastapi.testclient import TestClient
from app.main import app
from app.config.settings import settings

def make_init_data(user_id="12345", username="testuser", bot_token=None, auth_date=None, bad_hash=False, expired=False):
    if not bot_token:
        bot_token = settings.bot_token
    if not auth_date:
        auth_date = int(time.time())
    if expired:
        auth_date -= 90000  # 25h ago
    data = {
        "user_id": str(user_id),
        "username": username,
        "auth_date": str(auth_date),
    }
    pairs = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = "\n".join(pairs)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    hash_val = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if bad_hash:
        hash_val = "deadbeef" * 8
    data["hash"] = hash_val
    return "\n".join(f"{k}={v}" for k, v in data.items())

def test_auth_telegram_success():
    client = TestClient(app)
    init_data = make_init_data()
    resp = client.post("/api/v1/auth/telegram", json={"init_data": init_data})
    assert resp.status_code == 200
    assert resp.cookies.get(settings.token_cookie_name)
    assert resp.json()["message"] == "authenticated"

def test_auth_telegram_bad_signature():
    client = TestClient(app)
    init_data = make_init_data(bad_hash=True)
    resp = client.post("/api/v1/auth/telegram", json={"init_data": init_data})
    assert resp.status_code == 401

def test_auth_telegram_expired():
    client = TestClient(app)
    init_data = make_init_data(expired=True)
    resp = client.post("/api/v1/auth/telegram", json={"init_data": init_data})
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"]

def test_auth_telegram_cookie_flags():
    client = TestClient(app)
    init_data = make_init_data()
    resp = client.post("/api/v1/auth/telegram", json={"init_data": init_data})
    cookie = resp.cookies.get(settings.token_cookie_name)
    assert cookie
    # Check httpOnly and Secure flags in Set-Cookie header
    set_cookie = resp.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie
    if settings.token_cookie_secure:
        assert "Secure" in set_cookie
