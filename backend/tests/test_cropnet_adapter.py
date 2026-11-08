import pytest
from backend.app.services.cropnet_service import CropNetService, CropNetServiceException
from backend.app.schemas.soil import SoilVerificationStatus, NumericSoilProperty

def test_cropnet_synthetic_profile():
    profile = CropNetService.get_soil_profile("farm_test_01", "plot_01", taluka="Baramati")

    # Strict requirement: Synthetic test fixtures MUST be explicitly flagged
    assert profile.is_synthetic_test_data is True
    assert profile.spatial_coverage_status == "pilot_taluka_covered"

    # Preserves actual depth intervals and status
    assert profile.ph.depth_interval == "0-15cm"
    assert profile.ph.verification_status == SoilVerificationStatus.MAP_DERIVED_ESTIMATE
    assert profile.ph.value >= 7.0  # Baramati Vertisol is alkaline

    # Categorical property check
    assert profile.usda_texture_class.value_code == "clay"

    # Strict non-inference: unavailable parameters MUST be None
    assert profile.available_nitrogen_kg_ha is None
    assert profile.available_phosphorus_kg_ha is None
    assert profile.available_potassium_kg_ha is None
    assert profile.electrical_conductivity_ds_m is None
    assert profile.soil_depth_to_bedrock_cm is None
    assert profile.plant_available_water_capacity_mm is None

def test_cropnet_non_inference_safety_gate():
    profile = CropNetService.get_soil_profile("farm_test_01", taluka="Baramati")

    # Tamper with profile by inventing an unverified EC estimate
    profile.electrical_conductivity_ds_m = NumericSoilProperty(
        value=1.8,
        unit="dS/m",
        depth_interval="0-15cm",
        verification_status=SoilVerificationStatus.MAP_DERIVED_ESTIMATE,  # VIOLATION: Must only be LAB
        source_id="Fictional_Inference"
    )

    with pytest.raises(CropNetServiceException) as exc_info:
        CropNetService.validate_non_inference_contract(profile)
    assert "Contract Violation" in str(exc_info.value)
