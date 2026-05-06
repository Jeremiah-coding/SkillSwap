import pyotp


async def _register_and_login(client, username="mfauser"):
    await client.post("/api/v1/auth/register", json={
        "username": username, "email": f"{username}@test.com", "password": "Pass1234!"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "username": username, "password": "Pass1234!"
    })
    return resp.json()["access_token"]


async def test_totp_setup(client):
    token = await _register_and_login(client, "mfauser1")
    resp = await client.post("/api/v1/mfa/setup", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "totp_secret" in data
    assert "totp_uri" in data


async def test_totp_setup_already_enabled(client):
    token = await _register_and_login(client, "mfauser2")
    # Setup once
    setup = await client.post("/api/v1/mfa/setup", headers={"Authorization": f"Bearer {token}"})
    secret = setup.json()["totp_secret"]
    # Verify to enable
    code = pyotp.TOTP(secret).now()
    await client.post("/api/v1/mfa/verify", json={"code": code},
                      headers={"Authorization": f"Bearer {token}"})
    # Setup again should fail
    resp = await client.post("/api/v1/mfa/setup", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


async def test_totp_verify_success(client):
    token = await _register_and_login(client, "mfauser3")
    setup = await client.post("/api/v1/mfa/setup", headers={"Authorization": f"Bearer {token}"})
    secret = setup.json()["totp_secret"]
    code = pyotp.TOTP(secret).now()
    resp = await client.post("/api/v1/mfa/verify", json={"code": code},
                             headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "TOTP enabled successfully"


async def test_totp_verify_invalid_code(client):
    token = await _register_and_login(client, "mfauser4")
    await client.post("/api/v1/mfa/setup", headers={"Authorization": f"Bearer {token}"})
    resp = await client.post("/api/v1/mfa/verify", json={"code": "000000"},
                             headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 400


async def test_totp_verify_unauthenticated(client):
    resp = await client.post("/api/v1/mfa/verify", json={"code": "123456"})
    assert resp.status_code == 403
