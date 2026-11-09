"""Farm-context Heat Risk test (weather forecast mocked for determinism)."""
import uuid

from cropnet.services.api.app.schemas.weather import DailyForecastSummary, FarmWeatherForecastResponse
from cropnet.services.api.app.services import weather_service as weather_module

DEV = {"X-Dev-User-Id": str(uuid.uuid4())}

FARM = {
    "name": "Heat Test Farm",
    "village": "Baramati",
    "taluka": "Baramati",
    "district": "Pune",
    "state": "Maharashtra",
    "irrigation_type": "irrigated",
    "water_source": "canal",
    "geometry": {
        "type": "Polygon",
        "coordinates": [[[74.52, 18.15], [74.53, 18.15], [74.53, 18.16], [74.52, 18.16], [74.52, 18.15]]],
    },
}


def _fake_forecast(self, farm, db=None, force_refresh=False):
    return FarmWeatherForecastResponse(
        farm_id=str(farm["id"]),
        source="MockForecast",
        daily_summaries=[
            DailyForecastSummary(
                date="2026-11-10", day_name="Tue", temp_min_c=24.0, temp_max_c=40.0,
                humidity_percent=55.0, weather_condition="Clear",
                weather_description="clear sky", weather_icon="01d",
                total_rain_mm=0.0, max_pop_pct=0.0,
            ),
            DailyForecastSummary(
                date="2026-11-11", day_name="Wed", temp_min_c=23.0, temp_max_c=37.0,
                humidity_percent=50.0, weather_condition="Clear",
                weather_description="clear sky", weather_icon="01d",
                total_rain_mm=0.0, max_pop_pct=0.0,
            ),
        ],
        hourly_points=[],
    )


def test_farm_heat_risk_endpoint(test_client, monkeypatch):
    monkeypatch.setattr(weather_module.WeatherService, "get_forecast", _fake_forecast)

    created = test_client.post("/api/v1/farms", headers=DEV, json=FARM)
    assert created.status_code == 201, created.text
    farm_id = created.json()["id"]

    res = test_client.post(
        f"/api/v1/heat-risk/farm/{farm_id}",
        headers=DEV,
        json={"crop_code": "soybean", "include_worker_heat": True},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["farm_id"] == farm_id
    assert body["risk_category"] in {"LOW", "MODERATE", "HIGH", "CRITICAL"}
    assert body["weather_source"] == "MockForecast"
    assert len(body["daily_outlook"]) == 2
    assert len(body["interventions"]) >= 1
    assert body["worker_heat"] is not None
    assert body["provenance"]
    assert any("default wind/solar" in lim for lim in body["limitations"])


def test_farm_heat_risk_rejects_other_users(test_client, monkeypatch):
    monkeypatch.setattr(weather_module.WeatherService, "get_forecast", _fake_forecast)
    created = test_client.post("/api/v1/farms", headers=DEV, json=FARM)
    farm_id = created.json()["id"]

    other = {"X-Dev-User-Id": str(uuid.uuid4())}
    res = test_client.post(
        f"/api/v1/heat-risk/farm/{farm_id}",
        headers=other,
        json={"crop_code": "soybean"},
    )
    assert res.status_code in (403, 404)
