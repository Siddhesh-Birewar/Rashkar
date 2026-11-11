"""Security, ownership isolation, input validation, and fail-closed outage tests for RASHKAR APIs."""

import uuid
import httpx
import pytest

from cropnet.services.api.app.models.soil_and_farm import FarmModel
from cropnet.services.api.app.rashkar.adapters import weather as weather_adapter


@pytest.fixture(autouse=True)
def _clear_cache():
    weather_adapter.clear_weather_cache()
    yield
    weather_adapter.clear_weather_cache()


def _create_farm_for_user(test_client, user_id: str, name: str = "Baramati Plot") -> str:
    payload = {
        "name": name,
        "taluka": "Baramati",
        "district": "Pune",
        "state": "Maharashtra",
        "village": "Malegaon",
        "irrigation_type": "irrigated",
        "water_source": "canal",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [74.525, 18.175],
                    [74.535, 18.175],
                    [74.535, 18.185],
                    [74.525, 18.185],
                    [74.525, 18.175],
                ]
            ],
        },
    }
    resp = test_client.post(
        "/api/v1/farms",
        json=payload,
        headers={"X-Dev-User-Id": user_id},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def test_all_rashkar_endpoints_reject_unauthenticated_401(test_client):
    sample_farm = str(uuid.uuid4())
    sample_cycle = str(uuid.uuid4())

    checks = [
        ("GET", "/api/v1/rashkar/crops", None),
        ("GET", f"/api/v1/rashkar/farms/{sample_farm}/overview", None),
        ("GET", f"/api/v1/rashkar/farms/{sample_farm}/crop-cycles", None),
        ("POST", f"/api/v1/rashkar/farms/{sample_farm}/crop-cycle", {"crop_code": "soybean"}),
        ("PATCH", f"/api/v1/rashkar/farms/{sample_farm}/crop-cycle/{sample_cycle}", {"variety_name": "JS-335"}),
        ("POST", f"/api/v1/rashkar/farms/{sample_farm}/crop-cycle/confirm-stage", {"stage_code": "flowering"}),
        ("POST", "/api/v1/rashkar/worker-heat/assess", {"latitude": 18.18, "longitude": 74.53}),
        ("GET", f"/api/v1/rashkar/worker-heat/farms/{sample_farm}/history", None),
        ("POST", "/api/v1/rashkar/crop-heat/assess", {"farm_id": sample_farm}),
        ("GET", f"/api/v1/rashkar/crop-heat/farms/{sample_farm}/history", None),
        ("GET", f"/api/v1/rashkar/yield/farms/{sample_farm}/assessment", None),
        ("GET", f"/api/v1/rashkar/yield/farms/{sample_farm}/history", None),
        ("GET", "/api/v1/rashkar/yield/baseline?district=Pune&crop_code=soybean", None),
        ("GET", "/api/v1/rashkar/income/opportunities", None),
        ("GET", "/api/v1/rashkar/income/opportunities/azolla_unit", None),
        ("GET", f"/api/v1/rashkar/income/farms/{sample_farm}/profile", None),
        ("PUT", f"/api/v1/rashkar/income/farms/{sample_farm}/profile", {}),
        ("POST", f"/api/v1/rashkar/income/farms/{sample_farm}/discover", None),
        ("POST", f"/api/v1/rashkar/income/farms/{sample_farm}/calculate-scenario", {"opportunity_id": "azolla_unit"}),
        ("POST", "/api/v1/rashkar/income/calculate-scenario", {"opportunity_id": "azolla_unit"}),
        ("POST", "/api/v1/rashkar/income/compare-opportunities", {"opportunity_ids": ["azolla_unit"]}),
        ("GET", f"/api/v1/rashkar/income/farms/{sample_farm}/plans", None),
        ("POST", f"/api/v1/rashkar/income/farms/{sample_farm}/plans", {"opportunity_id": "azolla_unit", "chosen_budget_inr": 2500}),
        ("DELETE", f"/api/v1/rashkar/income/farms/{sample_farm}/plans/plan_fake", None),
    ]

    for method, url, body in checks:
        resp = test_client.request(method, url, json=body)
        assert resp.status_code == 401, f"{method} {url} returned {resp.status_code}: {resp.text}"


def test_cross_owner_isolation_returns_403(test_client, monkeypatch):
    monkeypatch.setattr(
        weather_adapter,
        "fetch_open_meteo_forecast",
        lambda *args, **kwargs: (_ for _ in ()).throw(httpx.ConnectError("mock offline")),
    )

    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    farm_a = _create_farm_for_user(test_client, user_a, name="Owner A Farm")

    # Owner A creates a cycle, gets opportunity id, and saves a plan
    c_resp = test_client.post(
        f"/api/v1/rashkar/farms/{farm_a}/crop-cycle",
        json={"crop_code": "soybean"},
        headers={"X-Dev-User-Id": user_a},
    )
    assert c_resp.status_code == 201
    cycle_a = c_resp.json()["id"]

    opps = test_client.get(
        "/api/v1/rashkar/income/opportunities",
        headers={"X-Dev-User-Id": user_a},
    ).json()
    opp_id = opps[0]["opportunity_id"]

    plan_resp = test_client.post(
        f"/api/v1/rashkar/income/farms/{farm_a}/plans",
        json={"opportunity_id": opp_id, "chosen_budget_inr": 5000.0},
        headers={"X-Dev-User-Id": user_a},
    )
    assert plan_resp.status_code == 201
    plan_a = plan_resp.json()["plan_id"]

    headers_b = {"X-Dev-User-Id": user_b}
    forbidden_calls = [
        ("GET", f"/api/v1/rashkar/farms/{farm_a}/overview", None),
        ("GET", f"/api/v1/rashkar/farms/{farm_a}/crop-cycles", None),
        ("POST", f"/api/v1/rashkar/farms/{farm_a}/crop-cycle", {"crop_code": "cotton"}),
        ("PATCH", f"/api/v1/rashkar/farms/{farm_a}/crop-cycle/{cycle_a}", {"variety_name": "Tampered"}),
        ("POST", f"/api/v1/rashkar/farms/{farm_a}/crop-cycle/confirm-stage", {"stage_code": "flowering"}),
        ("POST", "/api/v1/rashkar/worker-heat/assess", {"farm_id": farm_a}),
        ("GET", f"/api/v1/rashkar/worker-heat/farms/{farm_a}/history", None),
        ("POST", "/api/v1/rashkar/crop-heat/assess", {"farm_id": farm_a}),
        ("GET", f"/api/v1/rashkar/crop-heat/farms/{farm_a}/history", None),
        ("GET", f"/api/v1/rashkar/yield/farms/{farm_a}/assessment", None),
        ("GET", f"/api/v1/rashkar/yield/farms/{farm_a}/history", None),
        ("GET", f"/api/v1/rashkar/income/farms/{farm_a}/profile", None),
        ("PUT", f"/api/v1/rashkar/income/farms/{farm_a}/profile", {"available_investment_inr": 9999}),
        ("POST", f"/api/v1/rashkar/income/farms/{farm_a}/discover", None),
        ("POST", f"/api/v1/rashkar/income/farms/{farm_a}/calculate-scenario", {"opportunity_id": opp_id}),
        ("POST", "/api/v1/rashkar/income/calculate-scenario", {"opportunity_id": opp_id, "farm_id": farm_a}),
        ("GET", f"/api/v1/rashkar/income/farms/{farm_a}/plans", None),
        ("POST", f"/api/v1/rashkar/income/farms/{farm_a}/plans", {"opportunity_id": opp_id, "chosen_budget_inr": 1000}),
        ("DELETE", f"/api/v1/rashkar/income/farms/{farm_a}/plans/{plan_a}", None),
    ]

    for method, url, body in forbidden_calls:
        resp = test_client.request(method, url, json=body, headers=headers_b)
        assert resp.status_code == 403, f"Cross-owner {method} {url} returned {resp.status_code}: {resp.text}"


def test_unknown_resources_404_and_invalid_inputs_422(test_client, isolated_test_session):
    user_id = str(uuid.uuid4())
    headers = {"X-Dev-User-Id": user_id}
    farm_id = _create_farm_for_user(test_client, user_id)
    missing_uuid = str(uuid.uuid4())

    assert test_client.get(f"/api/v1/rashkar/farms/{missing_uuid}/overview", headers=headers).status_code == 404
    assert test_client.get("/api/v1/rashkar/farms/not-a-uuid/overview", headers=headers).status_code == 422
    assert test_client.patch(
        f"/api/v1/rashkar/farms/{farm_id}/crop-cycle/{missing_uuid}",
        json={"variety_name": "JS-335"},
        headers=headers,
    ).status_code == 404
    assert test_client.get("/api/v1/rashkar/income/opportunities/does_not_exist", headers=headers).status_code == 404
    assert test_client.delete(
        f"/api/v1/rashkar/income/farms/{farm_id}/plans/plan_missing",
        headers=headers,
    ).status_code == 404

    # Crop heat requires farm_id; worker heat requires farm_id OR both lat & lon
    assert test_client.post("/api/v1/rashkar/crop-heat/assess", json={}, headers=headers).status_code == 422
    assert test_client.post("/api/v1/rashkar/worker-heat/assess", json={"latitude": 18.18}, headers=headers).status_code == 422

    # Farm without centroid AND without geometry raises 422
    coordless_id = str(uuid.uuid4())
    coordless_farm = FarmModel(
        id=coordless_id,
        owner_id=user_id,
        name="No Coordinates Farm",
        taluka="Baramati",
        district="Pune",
        state="Maharashtra",
        geometry_geojson={},
        calculated_area_hectares=1.0,
        calculated_area_acres=2.47,
        centroid_latitude=None,
        centroid_longitude=None,
    )
    isolated_test_session.add(coordless_farm)
    isolated_test_session.commit()

    resp = test_client.get(f"/api/v1/rashkar/farms/{coordless_id}/overview", headers=headers)
    assert resp.status_code == 422


def test_open_meteo_outage_fails_closed_and_never_fabricates_soybean(test_client, monkeypatch):
    def _fail_open_meteo(*args, **kwargs):
        raise httpx.ConnectError("Simulated Open-Meteo outage")

    monkeypatch.setattr(weather_adapter, "fetch_open_meteo_forecast", _fail_open_meteo)

    user_id = str(uuid.uuid4())
    headers = {"X-Dev-User-Id": user_id}
    farm_id = _create_farm_for_user(test_client, user_id, name="Clean Unplanted Plot")

    # Overview without crop cycle + weather outage
    ov = test_client.get(f"/api/v1/rashkar/farms/{farm_id}/overview", headers=headers)
    assert ov.status_code == 200
    ov_data = ov.json()
    assert ov_data["has_active_crop"] is False
    assert ov_data["active_crop_cycle"] is None
    assert ov_data["weather"]["status"] == "WEATHER_UNAVAILABLE"

    # Worker heat outage -> WEATHER_UNAVAILABLE with zero temperature fabrication
    wh = test_client.post("/api/v1/rashkar/worker-heat/assess", json={"farm_id": farm_id}, headers=headers)
    assert wh.status_code == 200
    wh_data = wh.json()
    assert wh_data["status"] == "WEATHER_UNAVAILABLE"
    assert wh_data["current_air_temp_c"] is None
    assert wh_data["audit_logged"] is False

    # Income profile with zero crop registered -> NEVER fabricates "soybean"
    prof = test_client.get(f"/api/v1/rashkar/income/farms/{farm_id}/profile", headers=headers)
    assert prof.status_code == 200
    assert prof.json()["current_crop_code"] is None

    # Crop heat & yield without crop cycle -> NO_ACTIVE_CROP (never fabricates "soybean")
    ch_no_crop = test_client.post("/api/v1/rashkar/crop-heat/assess", json={"farm_id": farm_id}, headers=headers)
    assert ch_no_crop.status_code == 200
    assert ch_no_crop.json()["status"] == "NO_ACTIVE_CROP"
    assert ch_no_crop.json()["crop_code"] is None

    yld_no_crop = test_client.get(f"/api/v1/rashkar/yield/farms/{farm_id}/assessment", headers=headers)
    assert yld_no_crop.status_code == 200
    assert yld_no_crop.json()["status"] == "NO_ACTIVE_CROP"
    assert yld_no_crop.json()["crop_code"] is None

    # Register an active crop -> CropHeat & Yield fail closed with WEATHER_UNAVAILABLE
    cyc = test_client.post(
        f"/api/v1/rashkar/farms/{farm_id}/crop-cycle",
        json={"crop_code": "cotton"},
        headers=headers,
    )
    assert cyc.status_code == 201

    ch_outage = test_client.post("/api/v1/rashkar/crop-heat/assess", json={"farm_id": farm_id}, headers=headers)
    assert ch_outage.status_code == 200
    assert ch_outage.json()["status"] == "WEATHER_UNAVAILABLE"
    assert ch_outage.json()["tmax_forecast_c"] is None
    assert ch_outage.json()["audit_logged"] is False

    yld_outage = test_client.get(f"/api/v1/rashkar/yield/farms/{farm_id}/assessment", headers=headers)
    assert yld_outage.status_code == 200
    assert yld_outage.json()["status"] == "WEATHER_UNAVAILABLE"
    assert yld_outage.json()["audit_logged"] is False
