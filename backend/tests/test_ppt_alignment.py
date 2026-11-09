"""
Unit and Integration Tests for Rashkar Official Hackathon PPT Alignment.

Validates:
1. Multi-Index Thermal Safety Suite (NOAA Heat Index & UTCI).
2. Topographic elevation lapse-rate downscaling (11 km -> 1 km).
3. 30-Minute Cadence Forecast Grid Cache & Alert Lifecycle.
4. Explainable 0-100 Personalized Heat Risk Scores (Worker & Crop).
5. ML Forecast & Personalization Staged Pipeline (XGBoost, Random Forest, PyTorch LSTM).
6. PMFBY Multimodal Vision AI Pipeline (Sentinel-2 NDVI/NDWI, YOLOv8, U-Net, ViT, Multimodal Fusion).
7. PMFBY Human Review Queue & 48-Hour SLA Tracking.
"""

import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from backend.app.services.thermal_indices_service import (
    calculate_noaa_heat_index,
    calculate_utci_approx,
    apply_topographic_lapse_downscaling,
    compute_personalized_worker_heat_strain_score,
    compute_crop_heat_vulnerability_score,
)
from backend.app.services.forecast_scheduler import ForecastGridCache
from backend.app.ml.heat_ml_pipeline import heat_ml_pipeline
from backend.app.services.pmfby_vision_service import pmfby_vision_service
from backend.app.core.timezone import now_utc


# --- 1. Multi-Index Thermal Suite Tests ---
def test_noaa_heat_index_calculations():
    # Below 20°C returns air temperature
    assert calculate_noaa_heat_index(18.0, 50.0) == 18.0

    # Warm & humid: 35°C (95°F) at 70% RH produces substantial heat index (> 48°C / 118°F)
    hi_hot = calculate_noaa_heat_index(35.0, 70.0)
    assert hi_hot > 45.0
    assert isinstance(hi_hot, float)

    # Moderate conditions: 28°C at 50% RH
    hi_mod = calculate_noaa_heat_index(28.0, 50.0)
    assert 27.0 <= hi_mod <= 31.0


def test_utci_calculations():
    # Warm sunny condition: 34°C, 60% RH, 2 m/s wind, 700 W/m2 solar
    utci_sun = calculate_utci_approx(temp_c=34.0, rel_humidity_pct=60.0, wind_speed_10m_mps=2.0, solar_radiation_w_m2=700.0)
    # Mean radiant temperature under solar irradiance elevates UTCI
    assert utci_sun > 34.0
    
    # Night/Shade condition: solar = 0
    utci_shade = calculate_utci_approx(temp_c=34.0, rel_humidity_pct=60.0, wind_speed_10m_mps=2.0, solar_radiation_w_m2=0.0)
    assert utci_sun > utci_shade


# --- 2. Topographic Elevation Downscaling Tests ---
def test_topographic_lapse_rate_downscaling():
    # Farm at 600m, grid at 500m -> farm is 100m higher -> cooler by ~0.65°C
    downscaled_t, lapse_adj = apply_topographic_lapse_downscaling(
        base_temp_c=32.0,
        farm_elevation_m=600.0,
        grid_elevation_m=500.0,
        lapse_rate_c_per_km=6.5
    )
    assert lapse_adj == -0.65
    assert downscaled_t == 31.35


# --- 3. 30-Minute Cadence Grid Cache Tests ---
def test_forecast_grid_cache_cadence_and_alerts():
    cache = ForecastGridCache(cache_ttl_seconds=1800)
    lat1, lon1 = 18.524, 73.856
    lat2, lon2 = 18.519, 73.861  # Nearby farm within same 0.1 deg (~11 km) grid bin
    
    # Store for first farm
    cache.store_forecast(lat1, lon1, {"temp_c": 33.5}, source_model="Open-Meteo GFS")
    
    # Second farm retrieves from shared grid cell
    cached = cache.get_cached_forecast(lat2, lon2)
    assert cached is not None
    assert cached["grid_key"] == "grid_18.5_73.9"
    assert cached["refresh_cadence_minutes"] == 30
    assert cached["seconds_until_refresh"] > 0
    assert cached["base_grid_resolution_km"] == 11.0
    assert cached["target_downscaled_resolution_km"] == 1.0

    # Alert state lifecycle
    alert = cache.register_alert(
        farm_id="farm_001",
        alert_type="worker_heat_warning",
        severity_level="HIGH_HEAT_STRAIN",
        message="Shift heavy work to morning",
        score_0_100=72.0,
        valid_until_utc=now_utc() + timedelta(hours=2)
    )
    assert alert["state"] == "generated"
    
    # Update alert state
    updated = cache.update_alert_state(alert["alert_id"], "acknowledged")
    assert updated["state"] == "acknowledged"

    active_alerts = cache.get_farm_active_alerts("farm_001")
    assert len(active_alerts) == 1


# --- 4. Explainable 0-100 Risk Scores Tests ---
def test_worker_heat_strain_score_decomposition():
    # Mild conditions
    score_low = compute_personalized_worker_heat_strain_score(
        effective_wbgt_c=20.0,
        iso_threshold_c=28.0,
        metabolic_workload="light",
        is_acclimatized=True,
    )
    assert 0.0 <= score_low["score_0_100"] < 35.0
    assert score_low["severity_level"] == "LOW_RISK"
    assert "sub_indices" in score_low

    # Extreme conditions: exceeding threshold, heavy work, unacclimatized, elderly, long shift
    score_extreme = compute_personalized_worker_heat_strain_score(
        effective_wbgt_c=32.0,
        iso_threshold_c=25.0,
        metabolic_workload="very_heavy",
        is_acclimatized=False,
        worker_age=55,
        continuous_shift_hours=7.0,
        hydration_access=False
    )
    assert score_extreme["score_0_100"] >= 80.0
    assert score_extreme["severity_level"] == "EXTREME_LIFE_THREATENING"
    assert score_extreme["indicator_color"] == "red"


def test_crop_heat_vulnerability_score_decomposition():
    # Flowering soybean under extreme 40°C heat with dry soil
    crop_score = compute_crop_heat_vulnerability_score(
        max_temp_c=40.0,
        optimum_temp_c=30.0,
        critical_temp_c=36.0,
        growth_stage_code="flowering",
        soil_moisture_status="severe_deficit",
        is_irrigated=False
    )
    assert crop_score["score_0_100"] >= 75.0
    assert crop_score["vulnerability_level"] in ["CRITICAL_PHENOLOGICAL_STRESS", "SEVERE_CROP_BURN_RISK"]
    assert "thermal_exceedance_points" in crop_score["sub_indices"]


# --- 5. Machine Learning Pipeline Tests ---
def test_heat_ml_pipeline_benchmarking():
    summary = heat_ml_pipeline.run_full_pipeline_benchmarking()
    assert summary["status"] == "TRAINED_AND_BENCHMARKED"
    assert "Liljegren" in summary["reference_baseline"]
    
    xgb_m = summary["models"]["xgboost_wbgt_forecast"]
    assert xgb_m["r2_score"] >= 0.95
    assert xgb_m["mae_c"] < 0.50
    assert "temp_c" in xgb_m["feature_importances"]

    rf_m = summary["models"]["rf_worker_personalization"]
    assert rf_m["accuracy"] > 0.85

    lstm_m = summary["models"]["lstm_wbgt_trajectory"]
    assert lstm_m["mae_c"] < 1.0


# --- 6. PMFBY Multimodal Vision AI Pipeline Tests ---
def test_pmfby_multimodal_vision_service():
    # Spectral calculations
    indices = pmfby_vision_service.compute_spectral_indices(b2_blue=0.05, b4_red=0.08, b8_nir=0.52, b11_swir=0.18)
    assert 0.70 <= indices["ndvi"] <= 0.76
    assert indices["ndwi"] > 0.40

    # Sentinel-2 timeseries
    sat = pmfby_vision_service.analyze_sentinel2_timeseries(18.52, 73.85, "2024-09-10", "unseasonal_rainfall")
    assert sat["satellite_platform"] == "Sentinel-2 MSI Level-2A (ESA Copernicus)"
    assert sat["delta_ndvi"] < 0.0
    assert sat["vegetation_loss_pct"] > 0.0

    # Vision inference
    vis = pmfby_vision_service.run_computer_vision_inference(["dossier_photo1.jpg"], "unseasonal_rainfall", 45.0)
    assert len(vis["yolov8_detections"]) > 0
    assert vis["unet_segmentation"]["plot_boundary_detected"] is True
    assert vis["vit_feature_extraction"]["embedding_dimension"] == 768

    # Multimodal evidence fusion
    fusion = pmfby_vision_service.fuse_multimodal_evidence(
        farmer_claimed_loss_pct=45.0,
        satellite_ndvi_loss_pct=sat["vegetation_loss_pct"],
        vision_detected_loss_pct=vis["vision_damage_pct"],
        weather_anomaly_verified=True
    )
    assert 0.0 <= fusion["verified_damage_pct"] <= 100.0
    assert 0.0 <= fusion["confidence_score"] <= 100.0
    assert fusion["sla_target_hours"] == 48


# --- 7. PMFBY End-to-End API and Reviewer Workflow Tests ---
def test_pmfby_claim_and_reviewer_flow_e2e(client: TestClient):
    # Register isolated farm
    farm_res = client.post("/v1/farms/guided-registration", json={
        "farmer_name": "Sanjay Jagtap",
        "phone_number": "9822998877",
        "taluka": "Haveli",
        "district": "Pune",
        "village": "Wagholi",
        "farm_name": "Jagtap Organic Farm",
        "total_area_acres": 3.5,
        "latitude": 18.58,
        "longitude": 73.98,
        "crop_code": "soybean",
        "season": "kharif",
        "sowing_date": "2024-07-01",
        "irrigation_type": "drip",
        "planted_area_acres": 3.0
    })
    assert farm_res.status_code == 200
    farm_id = farm_res.json()["farm_id"]
    farmer_id = farm_res.json()["farmer_id"]

    # Submit PMFBY Claim with geotagged photo
    claim_payload = {
        "farmer_id": farmer_id,
        "farm_id": farm_id,
        "crop_code": "soybean",
        "season": "kharif",
        "event_date": "2024-09-12",
        "peril_type": "unseasonal_rainfall",
        "damage_estimate_pct": 50.0,
        "affected_area_acres": 2.5,
        "photo_urls": ["https://storage.rashkar.local/evidence/photo_01.jpg"],
        "gps_latitude": 18.58,
        "gps_longitude": 73.98
    }
    claim_res = client.post("/v1/pmfby/cases", json=claim_payload)
    assert claim_res.status_code == 200
    claim_data = claim_res.json()
    case_id = claim_data["case_id"]
    assert claim_data["dossier_status"] == "evidence_submitted"
    assert claim_data["sla_target_hours"] == 48
    assert claim_data["sla_remaining_hours"] > 47.0
    assert "satellite_evidence_summary" in claim_data
    assert "vision_evidence_summary" in claim_data
    assert "multimodal_fusion_summary" in claim_data

    # Check Reviewer Queue contains the newly submitted claim
    queue_res = client.get("/v1/pmfby/reviewer/queue")
    assert queue_res.status_code == 200
    queue = queue_res.json()
    matching = [c for c in queue if c["case_id"] == case_id]
    assert len(matching) == 1
    assert matching[0]["multimodal_fusion_summary"]["confidence_score"] > 0

    # Reviewer decision submission (within 48 hours SLA)
    review_res = client.post(f"/v1/pmfby/cases/{case_id}/review", json={
        "reviewer_id": "surveyor_pune_04",
        "decision": "verified_loss",
        "rationale": "Multimodal convergence verified. Sentinel-2 NDVI drop and field photos confirm lodging loss.",
        "recommended_compensation_basis": "PMFBY Post-Harvest / Localized Calamity Clause 21.2"
    })
    assert review_res.status_code == 200
    reviewed_data = review_res.json()
    assert reviewed_data["dossier_status"] == "review_completed"
    assert reviewed_data["reviewer_decision"] == "verified_loss"
