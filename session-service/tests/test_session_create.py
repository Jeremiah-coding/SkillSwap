import uuid


async def test_create_session_flow(client):
    payload = {
        "requester_profile_id": str(uuid.uuid4()),
        "mentor_profile_id": str(uuid.uuid4()),
        "requested_skill": "Go",
        "message": "Please teach me Go basics",
        "scheduled_date": "2026-06-01T10:00:00Z",
    }

    resp = await client.post("/api/v1/sessions", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["requested_skill"] == "Go"
    assert data["status"] == "pending"

    get_resp = await client.get(f"/api/v1/sessions/{data['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == data["id"]
