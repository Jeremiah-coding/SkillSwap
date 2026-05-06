async def test_auth_me_requires_token(client):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403


async def test_auth_me_with_valid_token(client):
    await client.post(
        "/api/v1/auth/register",
        json={"username": "meuser", "email": "meuser@test.com", "password": "Pass1234!"},
    )
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": "meuser", "password": "Pass1234!"},
    )
    token = login.json()["access_token"]

    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "meuser"
    assert data["email"] == "meuser@test.com"
