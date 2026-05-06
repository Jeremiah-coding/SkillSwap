import uuid


async def test_create_notification_flow(client):
    payload = {
        "profile_id": str(uuid.uuid4()),
        "message": "Session request created",
        "type": "session_created",
    }

    resp = await client.post("/api/v1/notifications", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["type"] == "session_created"
    assert data["status"] == "unread"
