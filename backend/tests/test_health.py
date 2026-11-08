def test_health_check(client):
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["timezone"] == "Asia/Kolkata"
    assert "+05:30" in data["time_local_ist"]
    assert "time_utc" in data
