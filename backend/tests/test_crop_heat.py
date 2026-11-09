import pytest

def test_crop_heat_assessment_endpoint(client):
    # 1. Setup Farm & Plot
    farm_res = client.post("/v1/farms/", json={
        "owner_id": "farmer_indapur_02",
        "farm_name": "Indapur Cotton Farm",
        "district": "Pune",
        "taluka": "Indapur",
        "village": "Nimgaon",
        "latitude": 18.1123,
        "longitude": 75.0234
    })
    assert farm_res.status_code == 200
    farm_id = farm_res.json()["farm_id"]

    plot_res = client.post(f"/v1/farms/{farm_id}/plots", json={
        "plot_name": "Cotton Block A",
        "area_acres": 4.5,
        "irrigation_type": "drip"
    })
    assert plot_res.status_code == 200
    plot_id = plot_res.json()["plot_id"]

    # 2. Add Cotton crop cycle during flowering stage
    cycle_res = client.post(f"/v1/farms/{farm_id}/crop-cycles?plot_id={plot_id}", json={
        "crop_code": "cotton",
        "variety_name": "Ajeet-155",
        "season": "kharif",
        "sowing_date": "2024-06-10",
        "farmer_confirmed_stage": "FLOWERING_BOLL_DEV"
    })
    assert cycle_res.status_code == 200

    # 3. Assess Crop Heat Risk with high day temp (39.5°C) and warm night (25.5°C)
    assessment_res = client.post("/v1/heat-risk/crop-heat", json={
        "farm_id": farm_id,
        "plot_id": plot_id,
        "forecast_tmax_c": 39.5,
        "forecast_tmin_c": 25.5
    })
    assert assessment_res.status_code == 200
    data = assessment_res.json()

    # Structural and agronomic assertions
    assert data["farm_id"] == farm_id
    assert data["crop_code"] == "cotton"
    assert data["growth_stage_code"] == "FLOWERING_BOLL_DEV"
    assert data["critical_tmax_threshold_c"] == 38.0
    assert data["critical_tmin_threshold_c"] == 24.0

    # Stress levels
    assert data["daytime_heat_stress_level"] in ["high", "critical"]
    assert data["warm_night_respiration_hazard"] is True
    assert data["overall_crop_heat_risk"] in ["high", "critical"]

    # Evidence traceability
    assert "ICAR-Central Institute for Cotton Research" in data["evidence_citation"]
    assert len(data["recommended_interventions"]) > 0
    assert data["audit_logged"] is True

    # Supported stages assertions (must have non-null, non-empty stage_name_en and stage_code)
    assert "supported_stages" in data
    assert len(data["supported_stages"]) > 0
    for stage in data["supported_stages"]:
        assert stage.get("stage_code") is not None
        assert stage.get("stage_name_en") is not None
        assert len(stage["stage_name_en"].strip()) > 0
        assert "null" not in stage["stage_name_en"].lower()
        assert stage.get("crit_tmax") is not None
