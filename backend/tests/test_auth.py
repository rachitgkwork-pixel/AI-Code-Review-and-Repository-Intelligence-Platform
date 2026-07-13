import pytest

BASE = "/api/v1/auth"


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register a new user
    resp = await client.post(
        f"{BASE}/register",
        json={"email": "test@example.com", "password": "password123", "full_name": "Test User"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["role"] == "user"

    # Login with same credentials
    resp = await client.post(
        f"{BASE}/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    token_data = resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_duplicate_registration(client):
    payload = {"email": "dup@example.com", "password": "password123"}
    await client.post(f"{BASE}/register", json=payload)
    resp = await client.post(f"{BASE}/register", json=payload)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post(
        f"{BASE}/register",
        json={"email": "bad@example.com", "password": "correctpass"},
    )
    resp = await client.post(
        f"{BASE}/login",
        json={"email": "bad@example.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_endpoint(client):
    await client.post(
        f"{BASE}/register",
        json={"email": "me@example.com", "password": "password123"},
    )
    login_resp = await client.post(
        f"{BASE}/login",
        json={"email": "me@example.com", "password": "password123"},
    )
    token = login_resp.json()["access_token"]

    resp = await client.get(f"{BASE}/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"
