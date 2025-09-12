from fastapi.testclient import TestClient
from app.main import app
from app.config.settings import settings
from test_auth_telegram import make_init_data

def test_me_protected():
    client = TestClient(app)
    # Not authenticated
    resp = client.get("/api/v1/me")
    assert resp.status_code == 401
    # Auth flow
    init_data = make_init_data()
    login = client.post("/api/v1/auth/telegram", json={"init_data": init_data})
    assert login.status_code == 200
    # Cookie should be set
    cookie = login.cookies.get(settings.token_cookie_name)
    assert cookie
    # Now access /me with cookie
    resp2 = client.get("/api/v1/me", cookies={settings.token_cookie_name: cookie})
    assert resp2.status_code == 200
    assert resp2.json()["user"]["username"] == "testuser"
