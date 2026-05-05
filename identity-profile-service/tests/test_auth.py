import pytest


async def test_register_success(client):
    resp = await client.post("/api/v1/auth/register", json={
        "username": "alice", "email": "alice@test.com", "password": "Pass1234!"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert "id" in data


async def test_register_duplicate(client):
    payload = {"username": "bob", "email": "bob@test.com", "password": "Pass1234!"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409


async def test_login_success(client):
    await client.post("/api/v1/auth/register", json={
        "username": "carol", "email": "carol@test.com", "password": "Pass1234!"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "carol", "password": "Pass1234!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "username": "dave", "email": "dave@test.com", "password": "Pass1234!"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": "dave", "password": "WrongPass!"
    })
    assert resp.status_code == 401


async def test_login_unknown_user(client):
    resp = await client.post("/api/v1/auth/login", json={
        "username": "nobody", "password": "Pass1234!"
    })
    assert resp.status_code == 401
