"""
Water Intelligence Collector for Farm Health Snapshot.

Gathers farm water sources, confirmed laboratory water test reports,
calculates SAR & RSC, and evaluates institutional BIS IS 11624 / ICAR-CSSRI hazards.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from cropnet.services.api.app.schemas.farm_health import (
    DataAvailabilityState,
    WaterDomainSummary,
    WaterSourceSummaryItem,
    WaterKeyIndicators,
    WaterEvaluationFinding,
)
from cropnet.services.api.app.models.water import (
    WaterSourceModel,
    WaterTestReportModel,
    WaterMeasurementModel,
)
from cropnet.services.api.app.services.water_intelligence.evaluator import (
    calculate_sar_and_rsc,
    WaterQualityEvaluator,
)
from cropnet.services.api.app.services.farm_health.collectors.base import (
    BaseDomainCollector,
    compute_age_days,
    utc_now,
)

logger = logging.getLogger(__name__)

WATER_STALE_THRESHOLD_DAYS = 365  # 1 year


class WaterCollector(BaseDomainCollector):
    """
    Collects irrigation water sources and laboratory quality evaluations.
    """

    @property
    def domain_name(self) -> str:
        return "water"

    def collect(self, farm: Dict[str, Any], db: Session, **kwargs) -> WaterDomainSummary:
        farm_id = str(farm["id"])
        now = utc_now()

        # 1. Fetch active water sources
        sources = (
            db.query(WaterSourceModel)
            .filter(
                WaterSourceModel.farm_id == farm_id,
                WaterSourceModel.is_active == True,
            )
            .order_by(WaterSourceModel.created_at.asc())
            .all()
        )

        source_items = [
            WaterSourceSummaryItem(
                source_id=s.id,
                source_type=s.source_type,
                name=s.name,
                seasonal_availability=s.seasonal_availability,
                reliability=s.reliability,
                irrigation_method=s.irrigation_method,
                measured_capacity_lph=s.measured_capacity_lph,
                capacity_provenance=s.capacity_provenance,
            )
            for s in sources
        ]

        # 2. Fetch confirmed water reports
        confirmed_report = (
            db.query(WaterTestReportModel)
            .filter(
                WaterTestReportModel.farm_id == farm_id,
                WaterTestReportModel.review_status == "CONFIRMED",
            )
            .order_by(
                WaterTestReportModel.confirmed_at.desc(),
                WaterTestReportModel.report_date.desc(),
            )
            .first()
        )

        unconfirmed_report = None
        if not confirmed_report:
            unconfirmed_report = (
                db.query(WaterTestReportModel)
                .filter(WaterTestReportModel.farm_id == farm_id)
                .order_by(WaterTestReportModel.upload_timestamp.desc())
                .first()
            )

        # Case A: ZERO sources and ZERO reports
        if not sources and not confirmed_report and not unconfirmed_report:
            return WaterDomainSummary(
                availability_state=DataAvailabilityState.NOT_AVAILABLE,
                last_updated=None,
                data_age_days=None,
                registered_sources_count=0,
                sources=[],
                laboratory_name=None,
                key_indicators=WaterKeyIndicators(
                    ph=None,
                    electrical_conductivity_ds_m=None,
                    tds_mg_l=None,
                    sar=None,
                    sar_status="UNAVAILABLE",
                    rsc_meq_l=None,
                    rsc_status="UNAVAILABLE",
                    chloride_meq_l=None,
                    boron_mg_l=None,
                ),
                institutional_evaluations=[],
                missing_critical_parameters=[
                    "water_source",
                    "electrical_conductivity",
                    "sar",
                    "rsc",
                ],
            )

        # Case B: Sources exist, but NO confirmed report
        if not confirmed_report:
            rep = unconfirmed_report
            last_updated = (rep.report_date or rep.upload_timestamp) if rep else None
            data_age = compute_age_days(last_updated, now) if last_updated else None
            return WaterDomainSummary(
                availability_state=DataAvailabilityState.PARTIALLY_AVAILABLE,
                last_updated=last_updated,
                data_age_days=data_age,
                registered_sources_count=len(source_items),
                sources=source_items,
                laboratory_name=rep.laboratory_name if rep else None,
                key_indicators=WaterKeyIndicators(
                    sar_status="UNAVAILABLE",
                    rsc_status="UNAVAILABLE",
                ),
                institutional_evaluations=[],
                missing_critical_parameters=[
                    "electrical_conductivity",
                    "sar",
                    "rsc",
                ],
            )

        # Case C: Confirmed report exists
        rep = confirmed_report
        last_updated = rep.report_date or rep.confirmed_at or rep.upload_timestamp
        data_age_days = compute_age_days(last_updated, now)

        # Fetch measurements for confirmed report
        measurements = (
            db.query(WaterMeasurementModel)
            .filter(WaterMeasurementModel.report_id == rep.id)
            .all()
        )

        meas_dict: Dict[str, Dict[str, Any]] = {}
        for m in measurements:
            eff_val = (
                m.farmer_corrected_value
                if m.farmer_corrected_value is not None
                else m.original_value
            )
            meas_dict[m.parameter_key] = {
                "original_value": eff_val,
                "original_unit": m.original_unit,
                "normalized_value": m.normalized_value,
                "normalized_unit": m.normalized_unit,
            }

        # Calculate SAR and RSC
        calc_indices = calculate_sar_and_rsc(meas_dict)

        # Run institutional evaluation
        eval_resp = WaterQualityEvaluator.evaluate(
            measurements=meas_dict,
            farm_id=farm_id,
            water_source_id=rep.water_source_id,
        )

        institutional_findings: List[WaterEvaluationFinding] = []
        for e in eval_resp.evaluations:
            hazard_lvl = e.hazard_level.value if hasattr(e.hazard_level, "value") else str(e.hazard_level)
            std_app = getattr(e, "applicable_standard", getattr(e, "standard_applied", "BIS IS 11624:2019"))
            institutional_findings.append(
                WaterEvaluationFinding(
                    parameter_key=e.parameter_key,
                    parameter_name=e.parameter_name,
                    hazard_level=hazard_lvl,
                    hazard_title=e.hazard_title,
                    standard_applied=std_app,
                    management_guidance=e.management_guidance,
                )
            )

        # Extract indicators
        def _get_val(k: str) -> Optional[float]:
            item = meas_dict.get(k)
            if not item:
                return None
            v = item.get("normalized_value")
            if v is not None:
                return float(v)
            orig = item.get("original_value")
            if orig is not None:
                try:
                    return float(orig)
                except (ValueError, TypeError):
                    return None
            return None

        ph_val = _get_val("ph")
        ec_val = _get_val("electrical_conductivity")
        tds_val = _get_val("tds")
        cl_val = _get_val("chloride")
        boron_val = _get_val("boron")

        key_indicators = WaterKeyIndicators(
            ph=ph_val,
            electrical_conductivity_ds_m=ec_val,
            tds_mg_l=tds_val,
            sar=calc_indices.sar,
            sar_status=calc_indices.sar_status,
            rsc_meq_l=calc_indices.rsc,
            rsc_status=calc_indices.rsc_status,
            chloride_meq_l=cl_val,
            boron_mg_l=boron_val,
        )

        missing_critical: List[str] = []
        if ec_val is None:
            missing_critical.append("electrical_conductivity")
        if calc_indices.sar is None:
            missing_critical.append("sar")
        if calc_indices.rsc is None:
            missing_critical.append("rsc")

        # Determine state
        if data_age_days is not None and data_age_days > WATER_STALE_THRESHOLD_DAYS:
            availability_state = DataAvailabilityState.STALE
        elif missing_critical:
            availability_state = DataAvailabilityState.PARTIALLY_AVAILABLE
        else:
            availability_state = DataAvailabilityState.AVAILABLE

        return WaterDomainSummary(
            availability_state=availability_state,
            last_updated=last_updated,
            data_age_days=data_age_days,
            registered_sources_count=len(source_items),
            sources=source_items,
            laboratory_name=rep.laboratory_name,
            key_indicators=key_indicators,
            institutional_evaluations=institutional_findings,
            missing_critical_parameters=missing_critical,
        )
