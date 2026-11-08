import pytest
from fastapi.testclient import TestClient

def test_assistant_chat_grounded_response(client: TestClient):
    payload = {
        "farmer_id": "farmer_demo_01",
        "farm_id": "farm_demo_pune_01",
        "message": "Why is my crop at risk today and what should I do?"
    }
    response = client.post("/v1/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "reply" in data
    assert len(data["reply"]) > 20
    assert "citations" in data
    assert isinstance(data["citations"], list)
    assert len(data["citations"]) > 0
    assert "provider_used" in data
    assert "session_id" in data
    assert data["session_id"].startswith("sess_")

    # Safety checks
    reply_lower = data["reply"].lower()
    assert "automatic pmfby claim approval" not in reply_lower

def test_assistant_chat_crop_question(client: TestClient):
    payload = {
        "farmer_id": "farmer_demo_01",
        "farm_id": "farm_demo_pune_01",
        "message": "What is the today weather and status for my crop?"
    }
    response = client.post("/v1/assistant/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 20
    assert "citations" in data
