import pytest
from datetime import date
from fastapi.testclient import TestClient

def test_pmfby_draft_save(client: TestClient):
    payload = {
        "farmer_id": "farmer_demo_01",
        "farm_id": "farm_demo_pune_01",
        "crop_code": "soybean",
        "season": "kharif",
        "event_date": "2024-07-20",
        "peril_type": "inundation",
        "damage_estimate_pct": 40.0,
        "affected_area_acres": 2.5,
        "photo_urls": [],
        "is_draft": True
    }
    response = client.post("/v1/pmfby/cases", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"].startswith("case_loss_")
    assert data["dossier_status"] == "draft_saved"
    assert data["peril_type"] == "inundation"
    assert data["damage_estimate_pct"] == 40.0

def test_pmfby_case_submission_and_reviewer_flow(client: TestClient):
    # Step 1: Submit a completed case for review
    submit_payload = {
        "farmer_id": "farmer_demo_01",
        "farm_id": "farm_demo_pune_01",
        "crop_code": "soybean",
        "season": "kharif",
        "event_date": "2024-08-15",
        "peril_type": "drought",
        "damage_estimate_pct": 65.0,
        "affected_area_acres": 3.0,
        "photo_urls": ["file:///data/evidence/drought_plot_01.jpg"],
        "is_draft": False
    }
    sub_res = client.post("/v1/pmfby/cases", json=submit_payload)
    assert sub_res.status_code == 200
    case_data = sub_res.json()
    case_id = case_data["case_id"]
    assert case_data["dossier_status"] == "evidence_submitted"

    # Step 2: Check reviewer queue
    queue_res = client.get("/v1/pmfby/reviewer/queue")
    assert queue_res.status_code == 200
    queue_cases = queue_res.json()
    assert isinstance(queue_cases, list)
    matching = [c for c in queue_cases if c["case_id"] == case_id]
    assert len(matching) == 1
    assert matching[0]["peril_type"] == "drought"

    # Step 3: Human reviewer reviews and approves evidence packet
    review_payload = {
        "reviewer_id": "agronomist_pune_kvk_01",
        "decision": "verified_loss",
        "rationale": "Satellite moisture deficit confirms localized dry spell. Geo-tagged evidence complete.",
        "recommended_compensation_basis": "Mid-season localized adversity PMFBY provision"
    }
    rev_res = client.post(f"/v1/pmfby/cases/{case_id}/review", json=review_payload)
    assert rev_res.status_code == 200
    reviewed_data = rev_res.json()
    assert reviewed_data["case_id"] == case_id
    assert reviewed_data["dossier_status"] == "review_completed"
    assert reviewed_data["reviewer_decision"] == "verified_loss"
    assert "disclaimer" in reviewed_data

def test_pmfby_review_invalid_case(client: TestClient):
    review_payload = {
        "reviewer_id": "reviewer_01",
        "decision": "rejected",
        "rationale": "Missing plot data."
    }
    res = client.post("/v1/pmfby/cases/case_loss_INVALID99/review", json=review_payload)
    assert res.status_code == 404
