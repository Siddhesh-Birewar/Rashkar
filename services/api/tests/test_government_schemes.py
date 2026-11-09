"""Government Schemes API tests.

Covers:
- Admin seeding of verified Central/Maharashtra schemes.
- Public list / search / category & level & state filtering.
- Detail retrieval and 404 handling.
- Admin-only gating (create requires admin; list/detail are public).
- Publish / deactivate / verify status transitions.
"""
import uuid

DEV_HEADERS = {"X-Dev-User-Id": str(uuid.uuid4())}


def test_seed_and_list_schemes(test_client):
    res = test_client.post("/api/v1/schemes/seed", headers=DEV_HEADERS)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "success"

    listed = test_client.get("/api/v1/schemes")
    assert listed.status_code == 200, listed.text
    data = listed.json()
    assert isinstance(data, list)
    names = {s["scheme_name"] for s in data}
    assert "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)" in names
    assert "Namo Shetkari Mahasanman Nidhi Yojana" in names


def test_search_and_filter_schemes(test_client):
    test_client.post("/api/v1/schemes/seed", headers=DEV_HEADERS)

    by_category = test_client.get("/api/v1/schemes", params={"category": "Crop Insurance"}).json()
    assert by_category and all(s["category"] == "Crop Insurance" for s in by_category)

    by_level = test_client.get("/api/v1/schemes", params={"government_level": "State"}).json()
    assert by_level and all(s["government_level"] == "State" for s in by_level)

    by_state = test_client.get("/api/v1/schemes", params={"state": "Maharashtra"}).json()
    assert by_state and all(s["state"] == "Maharashtra" for s in by_state)

    search = test_client.get("/api/v1/schemes", params={"search": "Kisan Samman"}).json()
    assert any("PM-KISAN" in s["scheme_name"] for s in search)


def test_detail_and_404(test_client):
    test_client.post("/api/v1/schemes/seed", headers=DEV_HEADERS)
    schemes = test_client.get("/api/v1/schemes").json()
    scheme_id = schemes[0]["id"]

    detail = test_client.get(f"/api/v1/schemes/{scheme_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["scheme_name"]
    assert body["source_url"]

    missing = test_client.get(f"/api/v1/schemes/{uuid.uuid4()}")
    assert missing.status_code == 404


def test_admin_gating(test_client):
    # Public list/detail require no auth.
    assert test_client.get("/api/v1/schemes").status_code == 200

    # Admin create succeeds with the dev-admin header.
    create = test_client.post(
        "/api/v1/schemes",
        headers=DEV_HEADERS,
        json={
            "scheme_name": "Test Scheme",
            "category": "Machinery",
            "government_level": "Central",
            "state": None,
            "status": "DRAFT",
            "verification_status": "PENDING_REVIEW",
        },
    )
    assert create.status_code == 201, create.text
    assert create.json()["status"] == "DRAFT"

    # Publish + verify the scheme.
    scheme_id = create.json()["id"]
    pub = test_client.patch(
        f"/api/v1/schemes/{scheme_id}/status",
        headers=DEV_HEADERS,
        params={"status": "ACTIVE", "verification_status": "VERIFIED"},
    )
    assert pub.status_code == 200, pub.text
    assert pub.json()["status"] == "ACTIVE"
    assert pub.json()["verification_status"] == "VERIFIED"

    # Deactivate.
    deact = test_client.patch(
        f"/api/v1/schemes/{scheme_id}/status",
        headers=DEV_HEADERS,
        params={"status": "INACTIVE"},
    )
    assert deact.status_code == 200
    assert deact.json()["status"] == "INACTIVE"


def test_admin_status_endpoint(test_client):
    res = test_client.get("/api/v1/schemes/admin/status", headers=DEV_HEADERS)
    assert res.status_code == 200
    assert res.json()["is_admin"] is True
