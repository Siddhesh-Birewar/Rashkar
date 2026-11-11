"""
Soil Intelligence Collector for Farm Health Snapshot.

Combines physical laboratory soil test reports (with farmer confirmation)
and SoilGrids 2.0 250m spatial profiles, applying precedence fusion and freshness rules.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session

from cropnet.services.api.app.schemas.farm_health import (
    DataAvailabilityState,
    SoilDomainSummary,
    SoilKeyIndicators,
)
from cropnet.services.api.app.models.soil_reports import (
    SoilTestReportModel,
    SoilMeasurementModel,
)
from cropnet.services.api.app.schemas.soil_reports import (
    ReviewStatus,
    MeasurementVerificationStatus,
)
from cropnet.services.api.app.models.soil_and_farm import (
    FarmSoilProfileModel,
    SoilParameterModel,
)
from cropnet.services.api.app.services.farm_health.collectors.base import (
    BaseDomainCollector,
    compute_age_days,
    utc_now,
)

logger = logging.getLogger(__name__)

LAB_STALE_THRESHOLD_DAYS = 1095  # 3 years
SPATIAL_STALE_THRESHOLD_DAYS = 365  # 1 year

ALL_CRITICAL_PARAMETERS = [
    "soil_ph",
    "organic_carbon",
    "nitrogen",
    "phosphorus",
    "potassium",
    "texture",
]


class SoilCollector(BaseDomainCollector):
    """
    Collects soil intelligence from physical laboratory tests and SoilGrids spatial profiles.
    """

    @property
    def domain_name(self) -> str:
        return "soil"

    def collect(self, farm: Dict[str, Any], db: Session, **kwargs) -> SoilDomainSummary:
        farm_id = str(farm["id"])
        now = utc_now()

        # 1. Fetch confirmed lab reports and unconfirmed reports
        confirmed_reports = (
            db.query(SoilTestReportModel)
            .filter(
                SoilTestReportModel.farm_id == farm_id,
                SoilTestReportModel.review_status == ReviewStatus.CONFIRMED.value,
            )
            .order_by(
                SoilTestReportModel.report_date.desc(),
                SoilTestReportModel.created_at.desc(),
            )
            .all()
        )

        unconfirmed_reports = (
            db.query(SoilTestReportModel)
            .filter(
                SoilTestReportModel.farm_id == farm_id,
                SoilTestReportModel.review_status != ReviewStatus.CONFIRMED.value,
            )
            .all()
        )

        # 2. Fetch confirmed measurements
        confirmed_measurements = []
        if confirmed_reports:
            confirmed_measurements = (
                db.query(SoilMeasurementModel)
                .join(SoilTestReportModel, SoilMeasurementModel.report_id == SoilTestReportModel.id)
                .filter(
                    SoilMeasurementModel.farm_id == farm_id,
                    SoilTestReportModel.review_status == ReviewStatus.CONFIRMED.value,
                    SoilMeasurementModel.verification_status == MeasurementVerificationStatus.FARMER_CONFIRMED.value,
                )
                .order_by(
                    SoilTestReportModel.report_date.desc(),
                    SoilMeasurementModel.created_at.desc(),
                )
                .all()
            )

        # 3. Fetch latest spatial profile
        spatial_profile = (
            db.query(FarmSoilProfileModel)
            .filter(FarmSoilProfileModel.farm_id == farm_id)
            .order_by(FarmSoilProfileModel.created_at.desc())
            .first()
        )

        # Case A: ZERO soil records exist
        if not confirmed_reports and not unconfirmed_reports and not spatial_profile:
            return SoilDomainSummary(
                availability_state=DataAvailabilityState.NOT_AVAILABLE,
                last_updated=None,
                data_age_days=None,
                provenance=None,
                laboratory_name=None,
                sample_depth=None,
                key_indicators=SoilKeyIndicators(),
                missing_critical_parameters=list(ALL_CRITICAL_PARAMETERS),
                agronomic_notes=[
                    "No soil profile has been generated or uploaded for this farm.",
                    "Action required: Trigger initial SoilGrids spatial analysis or upload a certified laboratory soil test report.",
                ],
            )

        # Case B: Only unconfirmed reports exist (in review) and no spatial profile
        if not confirmed_reports and unconfirmed_reports and not spatial_profile:
            rep = unconfirmed_reports[0]
            rep_date = rep.report_date or rep.upload_timestamp or rep.created_at
            age = compute_age_days(rep_date, now)
            return SoilDomainSummary(
                availability_state=DataAvailabilityState.PARTIALLY_AVAILABLE,
                last_updated=rep_date,
                data_age_days=age,
                provenance="LABORATORY_UNCONFIRMED",
                laboratory_name=rep.laboratory_name or "Pending Verification",
                sample_depth=rep.sample_depth_interval or "Not specified",
                key_indicators=SoilKeyIndicators(),
                missing_critical_parameters=list(ALL_CRITICAL_PARAMETERS),
                agronomic_notes=[
                    "Laboratory soil test report is currently awaiting farmer confirmation in review queue.",
                ],
            )

        # Process spatial parameters if present
        spatial_params: Dict[str, SoilParameterModel] = {}
        if spatial_profile and spatial_profile.parameters:
            for p in spatial_profile.parameters:
                spatial_params[p.parameter_key] = p

        # Map laboratory measurements
        latest_meas_by_param: Dict[str, SoilMeasurementModel] = {}
        for m in confirmed_measurements:
            if m.parameter_key not in latest_meas_by_param:
                latest_meas_by_param[m.parameter_key] = m

        def _val(m: Optional[SoilMeasurementModel]) -> Optional[float]:
            if not m:
                return None
            if m.farmer_corrected_value is not None:
                return float(m.farmer_corrected_value)
            if m.normalized_value is not None:
                return float(m.normalized_value)
            if m.original_value is not None:
                try:
                    return float(m.original_value)
                except (ValueError, TypeError):
                    return None
            return None

        # Build indicators with lab precedence over spatial
        ph_val: Optional[float] = None
        soc_val: Optional[float] = None
        ec_val: Optional[float] = None
        n_val: Optional[float] = None
        p_val: Optional[float] = None
        k_val: Optional[float] = None
        texture_str: Optional[str] = None
        cec_val: Optional[float] = None

        has_lab_data = bool(latest_meas_by_param)
        has_spatial_data = bool(spatial_params)

        # 1. pH
        if "soil_ph" in latest_meas_by_param:
            ph_val = _val(latest_meas_by_param["soil_ph"])
        elif "ph" in latest_meas_by_param:
            ph_val = _val(latest_meas_by_param["ph"])
        elif "soil_ph" in spatial_params and spatial_params["soil_ph"].value is not None:
            ph_val = spatial_params["soil_ph"].value
        elif "ph" in spatial_params and spatial_params["ph"].value is not None:
            ph_val = spatial_params["ph"].value

        # 2. SOC
        if "organic_carbon" in latest_meas_by_param:
            soc_val = _val(latest_meas_by_param["organic_carbon"])
        elif "soc" in latest_meas_by_param:
            soc_val = _val(latest_meas_by_param["soc"])
        elif "organic_matter" in latest_meas_by_param and _val(latest_meas_by_param["organic_matter"]) is not None:
            soc_val = round(_val(latest_meas_by_param["organic_matter"]) / 1.724, 2)
        elif "organic_carbon" in spatial_params and spatial_params["organic_carbon"].value is not None:
            val = spatial_params["organic_carbon"].value
            # SoilGrids SOC unit conversion if in g/kg or >10%
            if getattr(spatial_params["organic_carbon"], "unit", "") == "g/kg" or val > 10.0:
                soc_val = round(val / 10.0, 3)
            else:
                soc_val = round(val, 3)
        elif "soc" in spatial_params and spatial_params["soc"].value is not None:
            val = spatial_params["soc"].value
            if getattr(spatial_params["soc"], "unit", "") == "g/kg" or val > 10.0:
                soc_val = round(val / 10.0, 3)
            else:
                soc_val = round(val, 3)

        # 3. EC
        if "electrical_conductivity" in latest_meas_by_param:
            ec_val = _val(latest_meas_by_param["electrical_conductivity"])
        elif "electrical_conductivity" in spatial_params and spatial_params["electrical_conductivity"].value is not None:
            ec_val = spatial_params["electrical_conductivity"].value

        # 4. NPK
        if "available_nitrogen" in latest_meas_by_param:
            n_val = _val(latest_meas_by_param["available_nitrogen"])
        elif soc_val is not None and soc_val > 0:
            n_val = round(min(max(soc_val * 500.0, 50.0), 1200.0), 1)
        elif "available_nitrogen" in spatial_params and spatial_params["available_nitrogen"].value is not None:
            n_val = spatial_params["available_nitrogen"].value

        if "available_phosphorus" in latest_meas_by_param:
            p_val = _val(latest_meas_by_param["available_phosphorus"])
        elif "phosphorus" in latest_meas_by_param:
            meas_p = latest_meas_by_param["phosphorus"]
            raw_p = _val(meas_p)
            if raw_p is not None:
                p_unit = (getattr(meas_p, "normalized_unit", None) or getattr(meas_p, "original_unit", "") or "").lower()
                p_val = round(raw_p * 2.24, 1) if ("ppm" in p_unit or "mg/kg" in p_unit) else raw_p
        elif "available_phosphorus" in spatial_params and spatial_params["available_phosphorus"].value is not None:
            p_val = spatial_params["available_phosphorus"].value

        if "available_potassium" in latest_meas_by_param:
            k_val = _val(latest_meas_by_param["available_potassium"])
        elif "potassium" in latest_meas_by_param:
            meas_k = latest_meas_by_param["potassium"]
            raw_k = _val(meas_k)
            if raw_k is not None:
                k_unit = (getattr(meas_k, "normalized_unit", None) or getattr(meas_k, "original_unit", "") or "").lower()
                k_val = round(raw_k * 2.24, 1) if ("ppm" in k_unit or "mg/kg" in k_unit) else raw_k
        elif "available_potassium" in spatial_params and spatial_params["available_potassium"].value is not None:
            k_val = spatial_params["available_potassium"].value

        # 5. Texture & CEC
        if "soil_texture" in latest_meas_by_param:
            m_tex = latest_meas_by_param["soil_texture"]
            texture_str = (
                getattr(m_tex, "original_value_text", None)
                or getattr(m_tex, "normalized_unit", None)
                or getattr(m_tex, "original_unit", None)
                or (str(m_tex.original_value) if m_tex.original_value is not None and not isinstance(m_tex.original_value, (int, float)) else None)
            )
        elif "texture" in spatial_params and spatial_params["texture"].display_name:
            texture_str = spatial_params["texture"].display_name
        elif "clay_percent" in spatial_params:
            clay = spatial_params["clay_percent"].value or 0.0
            sand = spatial_params.get("sand_percent", SoilParameterModel(value=0.0)).value or 0.0
            if clay >= 40.0:
                texture_str = "Clay"
            elif clay >= 27.0:
                texture_str = "Clay Loam"
            elif sand >= 70.0:
                texture_str = "Sandy Loam"
            else:
                texture_str = "Loam"

        if "cation_exchange_capacity" in latest_meas_by_param:
            cec_val = _val(latest_meas_by_param["cation_exchange_capacity"])
        elif "cation_exchange_capacity" in spatial_params and spatial_params["cation_exchange_capacity"].value is not None:
            cec_val = spatial_params["cation_exchange_capacity"].value

        key_indicators = SoilKeyIndicators(
            soil_ph=ph_val,
            organic_carbon_pct=soc_val,
            electrical_conductivity_ds_m=ec_val,
            available_nitrogen_kg_ha=n_val,
            available_phosphorus_kg_ha=p_val,
            available_potassium_kg_ha=k_val,
            soil_texture=texture_str,
            cation_exchange_capacity=cec_val,
        )

        # Check missing critical parameters
        missing_critical: List[str] = []
        if ph_val is None:
            missing_critical.append("soil_ph")
        if soc_val is None:
            missing_critical.append("organic_carbon")
        if n_val is None:
            missing_critical.append("nitrogen")
        if p_val is None:
            missing_critical.append("phosphorus")
        if k_val is None:
            missing_critical.append("potassium")
        if texture_str is None:
            missing_critical.append("texture")

        # Provenance, dates, and freshness
        agronomic_notes: List[str] = []
        last_updated: Optional[datetime] = None
        data_age_days: Optional[int] = None
        provenance: str = "SPATIALLY_ESTIMATED_ISRIC"
        lab_name: Optional[str] = None
        sample_depth: Optional[str] = None

        if has_lab_data and confirmed_reports:
            rep = confirmed_reports[0]
            lab_name = rep.laboratory_name or "Certified Laboratory"
            sample_depth = rep.sample_depth_interval or "0-15 cm"
            last_updated = rep.report_date or rep.confirmed_at or rep.upload_timestamp or rep.created_at
            data_age_days = compute_age_days(last_updated, now)

            if has_spatial_data:
                provenance = "MIXED_DUAL_SOURCE"
            else:
                provenance = "LABORATORY_CONFIRMED"

            agronomic_notes.append(f"Farmer-confirmed physical laboratory test from {lab_name}.")
            if soc_val is not None:
                soc_status = "low" if soc_val < 0.5 else ("moderate" if soc_val <= 0.75 else "high")
                agronomic_notes.append(f"Soil organic carbon is {soc_status} ({soc_val}%).")

            # Evaluate state for lab data
            if data_age_days is not None and data_age_days > LAB_STALE_THRESHOLD_DAYS:
                availability_state = DataAvailabilityState.STALE
                agronomic_notes.append(
                    f"Soil laboratory test report is over 3 years old ({data_age_days} days). Soil nutrient and organic carbon levels may have shifted significantly."
                )
                agronomic_notes.append("Recommendation: Collect fresh soil samples and submit for updated Soil Health Card testing.")
            elif missing_critical:
                availability_state = DataAvailabilityState.PARTIALLY_AVAILABLE
            else:
                availability_state = DataAvailabilityState.AVAILABLE

        elif has_spatial_data and spatial_profile:
            provenance = "SPATIALLY_ESTIMATED_ISRIC"
            last_updated = spatial_profile.created_at
            data_age_days = compute_age_days(last_updated, now)
            sample_depth = "0-30 cm"
            agronomic_notes.append("Derived from ISRIC SoilGrids 2.0 250m global digital soil mapping.")

            if data_age_days is not None and data_age_days > SPATIAL_STALE_THRESHOLD_DAYS:
                availability_state = DataAvailabilityState.STALE
                agronomic_notes.append(f"Spatial soil extraction is over 1 year old ({data_age_days} days). Re-extraction recommended.")
            elif missing_critical:
                availability_state = DataAvailabilityState.PARTIALLY_AVAILABLE
            else:
                availability_state = DataAvailabilityState.AVAILABLE
        else:
            availability_state = DataAvailabilityState.NOT_AVAILABLE

        return SoilDomainSummary(
            availability_state=availability_state,
            last_updated=last_updated,
            data_age_days=data_age_days,
            provenance=provenance,
            laboratory_name=lab_name,
            sample_depth=sample_depth,
            key_indicators=key_indicators,
            missing_critical_parameters=missing_critical,
            agronomic_notes=agronomic_notes,
        )
