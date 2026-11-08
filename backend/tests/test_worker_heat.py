import pytest

def test_worker_heat_assessment_endpoint(client):
    payload = {
        "latitude": 18.1512,
        "longitude": 74.5768,
        "taluka": "Baramati",
        "workload_category": "heavy",
        "clothing_type": "standard_work_clothes",
        "is_acclimatised": True,
        "sun_exposure": "direct_sun"
    }

    res = client.post("/v1/heat-risk/worker-hazard", json=payload)
    assert res.status_code == 200
    data = res.json()

    # Core response structure
    assert data["time_horizon"] == "0_to_6_hours"
    assert data["recalculation_cadence_minutes"] == 30
    assert data["workload_category"] == "heavy"
    assert data["clothing_cav_c"] == 0.0
    assert data["is_acclimatised"] is True
    assert data["screening_threshold_c"] == 26.0  # ACGIH heavy acclimatised limit

    # Assert 7 hourly projections (0 to 6 hours)
    assert len(data["hourly_projections"]) == 7
    first_hour = data["hourly_projections"][0]
    assert "wbgt_estimated_c" in first_hour
    assert "hazard_level" in first_hour
    assert first_hour["threshold_limit_c"] == 26.0

    # Safety and non-medical disclaimer presence
    assert "NOTICE: WBGT values are cloud-modeled estimates" in data["disclaimer"]
    assert "does not mandate work-stoppages" in data["disclaimer"]

    # Hydration guidance adhering to NIOSH limits
    assert "Do not exceed 1 litre" in data["hydration_guidance"]["max_hourly_rate"]
    assert len(data["safety_cautions"]) >= 3

    # Audit logging confirmed
    assert data["audit_logged"] is True

def test_worker_heat_unacclimatised_stricter_threshold(client):
    payload = {
        "latitude": 18.1512,
        "longitude": 74.5768,
        "taluka": "Baramati",
        "workload_category": "heavy",
        "clothing_type": "standard_work_clothes",
        "is_acclimatised": False,  # Unacclimatised worker
        "sun_exposure": "direct_sun"
    }
    res = client.post("/v1/heat-risk/worker-hazard", json=payload)
    assert res.status_code == 200
    data = res.json()
    # Unacclimatised heavy screening threshold is 23.0°C (3°C lower than acclimatised)
    assert data["screening_threshold_c"] == 23.0
