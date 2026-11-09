"""Tests for consolidated features: Heat Risk, Crop Doctor, Income Diversification."""
import io


def test_heat_risk_supported_crops(test_client):
    res = test_client.get("/api/v1/heat-risk/crops")
    assert res.status_code == 200
    crops = {c["crop_code"] for c in res.json()["crops"]}
    assert {"soybean", "cotton", "jowar", "onion"} <= crops


def test_crop_heat_assessment(test_client):
    res = test_client.post(
        "/api/v1/heat-risk/crop",
        json={"crop_code": "soybean", "forecast_tmax_c": 40.0, "forecast_tmin_c": 24.0},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["risk_category"] in {"LOW", "MODERATE", "HIGH", "CRITICAL"}
    assert body["warm_night_hazard"] is True
    assert body["hours_above_critical"] > 0
    assert body["evidence_citation"]


def test_crop_heat_unsupported_crop(test_client):
    res = test_client.post(
        "/api/v1/heat-risk/crop",
        json={"crop_code": "banana", "forecast_tmax_c": 38.0, "forecast_tmin_c": 22.0},
    )
    assert res.status_code == 422


def test_worker_heat_assessment(test_client):
    res = test_client.post(
        "/api/v1/heat-risk/worker",
        json={
            "air_temp_c": 38.0,
            "relative_humidity_pct": 60.0,
            "wind_speed_ms": 1.0,
            "solar_irradiance_wm2": 800.0,
            "workload_category": "heavy",
            "is_acclimatised": True,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["wbgt_c"] > 0
    assert body["wbgt_effective_c"] >= body["wbgt_c"]
    assert body["hazard_level"] in {"LOW", "MODERATE", "HIGH", "EXTREME"}
    assert body["threshold_c"] == 26.0  # acclimatised heavy-work ACGIH limit


def test_crop_doctor_status_and_graceful_absence(test_client):
    status_res = test_client.get("/api/v1/crop-doctor/status")
    assert status_res.status_code == 200
    assert "loaded" in status_res.json()

    # A 1x1 PNG; model stack may be absent -> 503, or present -> 200.
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000d49444154789c6360000002000100e221bc330000000049454e44ae426082"
    )
    res = test_client.post(
        "/api/v1/crop-doctor/predict",
        files={"file": ("leaf.png", io.BytesIO(png), "image/png")},
    )
    assert res.status_code in (200, 503), res.text
    if res.status_code == 200:
        assert "diagnosis" in res.json()


def test_income_opportunities(test_client):
    res = test_client.get("/api/v1/income/opportunities")
    assert res.status_code == 200, res.text
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "opportunity_id" in data[0]
