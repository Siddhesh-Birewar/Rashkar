import uuid
import pytest
from fastapi.testclient import TestClient

from cropnet.services.api.app.main import app
from cropnet.services.api.app.services.weather_providers.openweather import OpenWeatherProvider
from cropnet.services.api.app.services.weather_providers.nasa_power import NASAPowerProvider
from cropnet.services.api.app.services.weather_service import WeatherService

client = TestClient(app)


def test_openweather_provider_data_mapping():
    """
    Unit test OpenWeatherProvider data mapping and fixture generation.
    """
    provider = OpenWeatherProvider()
    farm_id = str(uuid.uuid4())
    obs = provider.get_current_weather(farm_id, 18.18, 74.53)
    assert obs.farm_id == farm_id
    assert obs.data_type == "observed"
    assert obs.temperature_c is not None
    assert obs.humidity_percent is not None
    assert obs.wind_speed_ms is not None
    assert obs.weather_condition is not None

    forecast = provider.get_forecast(farm_id, 18.18, 74.53)
    assert forecast.farm_id == farm_id
    assert forecast.data_type == "forecast"
    assert len(forecast.daily_summaries) >= 3


def test_nasa_power_provider_climatology_and_seasons():
    """
    Unit test NASAPowerProvider 30-year climatological normals and agro-climatic indicators.
    """
    provider = NASAPowerProvider()
    farm_id = str(uuid.uuid4())
    # Baramati (18.18, 74.53)
    climate = provider.get_climate_summary(farm_id, 18.18, 74.53)
    assert climate.farm_id == farm_id
    assert climate.data_type == "historical_reanalysis"
    assert len(climate.monthly_climate) == 12
    assert climate.annual_rainfall_mm > 0.0
    assert climate.monsoon_rainfall_mm > 0.0
    assert climate.monsoon_share_percent > 50.0 # Monsoon dominates in Maharashtra

    # Check Indian Agricultural Seasons (Kharif, Rabi, Zaid)
    season_names = [s.season_name for s in climate.agricultural_seasons]
    assert any("Kharif" in name for name in season_names)
    assert any("Rabi" in name for name in season_names)
    assert any("Zaid" in name for name in season_names)

    # Check deterministic water stress indicator is present
    assert climate.potential_water_stress_indicator is not None
    assert len(climate.potential_water_stress_indicator) > 10


def test_farm_weather_api_lifecycle_caching_and_security():
    """
    End-to-End Test for Phase 3:
    1. Register a farm with centroid in Baramati.
    2. Retrieve current weather via GET /farms/{farm_id}/weather/current.
    3. Verify caching (subsequent request returns is_cached=True).
    4. Retrieve 5-day forecast via GET /farms/{farm_id}/weather/forecast.
    5. Retrieve 30-year agro-climate summary via GET /farms/{farm_id}/weather/climate-summary.
    6. Verify stored history via GET /farms/{farm_id}/weather/history.
    7. Multi-Tenant Authorization Security: User 2 cannot access User 1's weather data (403).
    8. Verify no crop recommendations or yield predictions are introduced.
    """
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())

    # 1. Register Farm in Baramati
    farm_payload = {
        "name": "Baramati Weather Pilot Farm",
        "taluka": "Baramati",
        "district": "Pune",
        "state": "Maharashtra",
        "village": "Supa",
        "irrigation_type": "irrigated",
        "water_source": "canal",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [74.520, 18.170],
                [74.530, 18.170],
                [74.530, 18.180],
                [74.520, 18.180],
                [74.520, 18.170]
            ]]
        }
    }

    create_res = client.post(
        "/api/v1/farms",
        json=farm_payload,
        headers={"X-Dev-User-Id": user1_id}
    )
    assert create_res.status_code == 201
    farm = create_res.json()
    farm_id = farm["id"]

    # 2. GET Current Weather
    cur_res = client.get(
        f"/api/v1/farms/{farm_id}/weather/current",
        headers={"X-Dev-User-Id": user1_id}
    )
    assert cur_res.status_code == 200
    current_data = cur_res.json()
    assert current_data["farm_id"] == farm_id
    assert current_data["data_type"] == "observed"
    assert "temperature_c" in current_data
    assert "humidity_percent" in current_data
    assert "wind_speed_ms" in current_data
    assert "weather_condition" in current_data

    # 3. Verify Caching on Current Weather
    cached_cur_res = client.get(
        f"/api/v1/farms/{farm_id}/weather/current",
        headers={"X-Dev-User-Id": user1_id}
    )
    assert cached_cur_res.status_code == 200
    cached_data = cached_cur_res.json()
    assert cached_data["is_cached"] is True
    assert cached_data["cache_age_seconds"] is not None

    # 4. GET 5-Day Forecast
    fc_res = client.get(
        f"/api/v1/farms/{farm_id}/weather/forecast",
        headers={"X-Dev-User-Id": user1_id}
    )
    assert fc_res.status_code == 200
    fc_data = fc_res.json()
    assert fc_data["farm_id"] == farm_id
    assert fc_data["data_type"] == "forecast"
    assert len(fc_data["daily_summaries"]) >= 3
    assert len(fc_data["hourly_points"]) >= 3

    # 5. GET 30-Year Agro-Climate Summary (NASA POWER)
    clim_res = client.get(
        f"/api/v1/farms/{farm_id}/weather/climate-summary",
        headers={"X-Dev-User-Id": user1_id}
    )
    assert clim_res.status_code == 200
    clim_data = clim_res.json()
    assert clim_data["farm_id"] == farm_id
    assert clim_data["data_type"] == "historical_reanalysis"
    assert clim_data["annual_rainfall_mm"] > 0
    assert clim_data["monsoon_rainfall_mm"] > 0
    assert len(clim_data["monthly_climate"]) == 12
    assert len(clim_data["agricultural_seasons"]) == 3
    assert clim_data["potential_water_stress_indicator"] is not None

    # Verify no crop recommendations or yield prediction fields are present
    assert "recommended_crops" not in clim_data
    assert "predicted_yield" not in clim_data

    # 6. GET Weather History
    hist_res = client.get(
        f"/api/v1/farms/{farm_id}/weather/history",
        headers={"X-Dev-User-Id": user1_id}
    )
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert isinstance(history, list)

    # 7. Multi-Tenant Authorization Security: User 2 cannot access User 1's farm weather
    u2_cur = client.get(
        f"/api/v1/farms/{farm_id}/weather/current",
        headers={"X-Dev-User-Id": user2_id}
    )
    assert u2_cur.status_code == 403

    u2_fc = client.get(
        f"/api/v1/farms/{farm_id}/weather/forecast",
        headers={"X-Dev-User-Id": user2_id}
    )
    assert u2_fc.status_code == 403

    u2_clim = client.get(
        f"/api/v1/farms/{farm_id}/weather/climate-summary",
        headers={"X-Dev-User-Id": user2_id}
    )
    assert u2_clim.status_code == 403

    u2_hist = client.get(
        f"/api/v1/farms/{farm_id}/weather/history",
        headers={"X-Dev-User-Id": user2_id}
    )
    assert u2_hist.status_code == 403
