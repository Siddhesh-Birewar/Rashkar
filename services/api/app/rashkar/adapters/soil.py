"""Edaphic & climate-normal adapter reading CropNet soil reports and map profiles."""

from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

try:
    from cropnet.services.api.app.models.soil_and_farm import (
        FarmSoilProfileModel,
        SoilParameterModel,
    )
    from cropnet.services.api.app.models.soil_reports import (
        SoilMeasurementModel,
        SoilTestReportModel,
    )
    from cropnet.services.api.app.models.weather import FarmClimateSummaryModel
    from cropnet.services.api.app.services.spatial_extractor import (
        derive_usda_texture_class,
    )
except ImportError:
    from app.models.soil_and_farm import FarmSoilProfileModel, SoilParameterModel
    from app.models.soil_reports import SoilMeasurementModel, SoilTestReportModel
    from app.models.weather import FarmClimateSummaryModel
    from app.services.spatial_extractor import derive_usda_texture_class

from ..schemas.context import RashkarSoilContext


_LAB_KEY_MAP: Dict[str, str] = {
    "soil_ph": "soil_ph",
    "ph": "soil_ph",
    "ph_h2o": "soil_ph",
    "organic_carbon": "organic_carbon_pct",
    "organic_carbon_pct": "organic_carbon_pct",
    "soc": "organic_carbon_pct",
    "clay": "clay_pct",
    "clay_pct": "clay_pct",
    "clay_percent": "clay_pct",
    "sand": "sand_pct",
    "sand_pct": "sand_pct",
    "sand_percent": "sand_pct",
    "silt": "silt_pct",
    "silt_pct": "silt_pct",
    "silt_percent": "silt_pct",
    "cec": "cation_exchange_capacity",
    "cation_exchange_capacity": "cation_exchange_capacity",
    "cec_cmol_kg": "cation_exchange_capacity",
    "bulk_density": "bulk_density_g_cm3",
    "bulk_density_g_cm3": "bulk_density_g_cm3",
    "awc": "available_water_capacity_mm_m",
    "available_water_capacity": "available_water_capacity_mm_m",
    "available_water_capacity_mm_m": "available_water_capacity_mm_m",
    "effective_rooting_depth_cm": "effective_rooting_depth_cm",
    "depth_cm": "effective_rooting_depth_cm",
    "rooting_depth_cm": "effective_rooting_depth_cm",
}

_MAP_KEY_MAP: Dict[str, str] = {
    "ph": "soil_ph",
    "soil_ph": "soil_ph",
    "ph_h2o": "soil_ph",
    "soc": "organic_carbon_pct",
    "organic_carbon": "organic_carbon_pct",
    "organic_carbon_pct": "organic_carbon_pct",
    "clay": "clay_pct",
    "clay_pct": "clay_pct",
    "clay_percent": "clay_pct",
    "sand": "sand_pct",
    "sand_pct": "sand_pct",
    "sand_percent": "sand_pct",
    "silt": "silt_pct",
    "silt_pct": "silt_pct",
    "silt_percent": "silt_pct",
    "cec": "cation_exchange_capacity",
    "cation_exchange_capacity": "cation_exchange_capacity",
    "cec_cmol_kg": "cation_exchange_capacity",
    "bulk_density": "bulk_density_g_cm3",
    "bulk_density_g_cm3": "bulk_density_g_cm3",
    "awc": "available_water_capacity_mm_m",
    "available_water_capacity": "available_water_capacity_mm_m",
    "available_water_capacity_mm_m": "available_water_capacity_mm_m",
    "effective_rooting_depth_cm": "effective_rooting_depth_cm",
    "depth_cm": "effective_rooting_depth_cm",
}

_UNAVAILABLE_STATUSES = {"unavailable", "not_available", "source_unavailable"}


def _extract_measurement_value(meas: SoilMeasurementModel) -> Optional[float]:
    for val in (
        meas.farmer_corrected_value,
        meas.normalized_value,
        meas.original_value,
    ):
        if val is not None:
            return float(val)
    return None


def _is_valid_map_param(param: SoilParameterModel) -> bool:
    avail = str(param.availability_status or "").strip().lower()
    if avail in _UNAVAILABLE_STATUSES:
        return False
    verif = str(param.verification_status or "").strip().lower()
    source = str(param.source or "").strip().lower()
    if "synthetic" in verif or "synthetic" in source:
        return False
    return True


def _extract_map_soil_fields(farm_id: str, db: Session) -> Dict[str, Any]:
    """Extract latest non-synthetic, available parameters from FarmSoilProfileModel."""
    profiles = (
        db.query(FarmSoilProfileModel)
        .filter(FarmSoilProfileModel.farm_id == str(farm_id))
        .order_by(
            FarmSoilProfileModel.version.desc(),
            FarmSoilProfileModel.created_at.desc(),
        )
        .all()
    )

    extracted: Dict[str, Any] = {}
    for profile in profiles:
        params = (
            db.query(SoilParameterModel)
            .filter(SoilParameterModel.profile_id == profile.id)
            .all()
        )
        for p in params:
            if not _is_valid_map_param(p):
                continue
            key = str(p.parameter_key or "").strip().lower()
            if key in ("soil_texture_class", "soil_texture", "texture_class"):
                if "soil_texture" not in extracted and p.scientific_note:
                    extracted["soil_texture"] = str(p.scientific_note).strip()
                continue
            target_field = _MAP_KEY_MAP.get(key)
            if target_field and p.value is not None and target_field not in extracted:
                extracted[target_field] = float(p.value)
        if extracted:
            break
    return extracted


def resolve_farm_soil_context(farm_id: str, db: Session) -> Dict[str, Any]:
    """
    Resolve farm soil parameters with strict provenance and zero synthetic fabrication:
    1) Latest confirmed laboratory SoilTestReportModel (`review_status == 'CONFIRMED'`).
    2) Supplement missing unmeasured keys cleanly from FarmSoilProfileModel.
    3) Attach annual climate normal rainfall from FarmClimateSummaryModel when present.
    """
    farm_id_str = str(farm_id)
    fields: Dict[str, Any] = {}
    lab_measured_keys: set[str] = set()
    map_supplemented_keys: set[str] = set()

    confirmed_reports = (
        db.query(SoilTestReportModel)
        .filter(
            SoilTestReportModel.farm_id == farm_id_str,
            SoilTestReportModel.review_status == "CONFIRMED",
        )
        .order_by(
            SoilTestReportModel.confirmed_at.desc(),
            SoilTestReportModel.report_date.desc(),
            SoilTestReportModel.upload_timestamp.desc(),
        )
        .all()
    )

    lab_name: Optional[str] = None
    for report in confirmed_reports:
        measurements = (
            db.query(SoilMeasurementModel)
            .filter(
                SoilMeasurementModel.report_id == report.id,
                SoilMeasurementModel.farm_id == farm_id_str,
                SoilMeasurementModel.verification_status.in_(
                    ("FARMER_CONFIRMED", "FARMER_CORRECTED")
                ),
            )
            .order_by(SoilMeasurementModel.created_at.desc())
            .all()
        )
        if not measurements:
            continue

        if lab_name is None:
            lab_name = report.laboratory_name or "Confirmed Soil Test"

        for meas in measurements:
            key = str(meas.parameter_key or "").strip().lower()
            if key in ("soil_texture", "texture_class", "soil_texture_class"):
                if "soil_texture" not in fields and meas.original_value_text:
                    fields["soil_texture"] = str(meas.original_value_text).strip()
                    lab_measured_keys.add("soil_texture")
                continue

            target_field = _LAB_KEY_MAP.get(key)
            if not target_field or target_field in fields:
                continue
            val = _extract_measurement_value(meas)
            if val is not None:
                fields[target_field] = val
                lab_measured_keys.add(target_field)

        if lab_measured_keys:
            break

    map_fields = _extract_map_soil_fields(farm_id_str, db)
    for k, v in map_fields.items():
        if k not in fields and v is not None:
            fields[k] = v
            map_supplemented_keys.add(k)

    # Derive USDA texture class deterministically if sand, silt, clay were measured
    if (
        "soil_texture" not in fields
        and fields.get("sand_pct") is not None
        and fields.get("silt_pct") is not None
        and fields.get("clay_pct") is not None
    ):
        derived = derive_usda_texture_class(
            fields["sand_pct"], fields["silt_pct"], fields["clay_pct"]
        )
        if derived:
            fields["soil_texture"] = derived

    climate_normal_rainfall_mm: Optional[float] = None
    climate_summary = (
        db.query(FarmClimateSummaryModel)
        .filter(FarmClimateSummaryModel.farm_id == farm_id_str)
        .order_by(FarmClimateSummaryModel.created_at.desc())
        .first()
    )
    if climate_summary is not None and climate_summary.annual_rainfall_mm is not None:
        climate_normal_rainfall_mm = float(climate_summary.annual_rainfall_mm)

    if lab_measured_keys:
        is_lab_measured = True
        base_prov = f"Laboratory Report ({lab_name or 'Confirmed Soil Test'})"
        if map_supplemented_keys:
            data_provenance = f"{base_prov} + CropNet Map-Derived Soil Profile Supplement"
        else:
            data_provenance = base_prov
    elif map_supplemented_keys:
        is_lab_measured = False
        data_provenance = "CropNet Map-Derived Soil Profile"
    else:
        is_lab_measured = False
        data_provenance = "No farm soil profile or confirmed laboratory soil test on file"

    ctx = RashkarSoilContext(
        soil_texture=fields.get("soil_texture"),
        soil_ph=fields.get("soil_ph"),
        organic_carbon_pct=fields.get("organic_carbon_pct"),
        cation_exchange_capacity=fields.get("cation_exchange_capacity"),
        available_water_capacity_mm_m=fields.get("available_water_capacity_mm_m"),
        effective_rooting_depth_cm=fields.get("effective_rooting_depth_cm"),
        clay_pct=fields.get("clay_pct"),
        sand_pct=fields.get("sand_pct"),
        silt_pct=fields.get("silt_pct"),
        bulk_density_g_cm3=fields.get("bulk_density_g_cm3"),
        climate_normal_rainfall_mm=climate_normal_rainfall_mm,
        data_provenance=data_provenance,
        is_lab_measured=is_lab_measured,
        is_synthetic=False,
    )
    return ctx.model_dump()


__all__ = ["resolve_farm_soil_context"]
