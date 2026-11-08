import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.timezone import now_utc, to_ist_iso, now_ist
from backend.app.services.wbgt_solver import calculate_wbgt
from backend.app.services.weather_service import WeatherService
from backend.app.db.models.risk import WorkerHazardAuditLogModel
from backend.app.schemas.worker_heat import (
    WorkerHeatAssessmentRequest,
    WorkerHeatAssessmentResponse,
    HourlyHeatRiskProjection
)

# ACGIH TLV & ISO 7243:2017 screening action limits (°C WBGT)
WORKLOAD_THRESHOLDS_ACCLIMATISED = {
    "light": 31.0,
    "moderate": 28.0,
    "heavy": 26.0,
    "very_heavy": 25.0
}

WORKLOAD_THRESHOLDS_UNACCLIMATISED = {
    "light": 28.0,
    "moderate": 25.0,
    "heavy": 23.0,
    "very_heavy": 22.0
}

# Clothing Adjustment Values (CAV, °C) - ISO 9920 / ACGIH
CLOTHING_ADJUSTMENT_VALUES = {
    "standard_work_clothes": 0.0,
    "coveralls_protective": 2.0,
    "woven_double_layer": 3.0,
    "impermeable_vapor_barrier": 10.0
}

class WorkerHeatEngine:
    @staticmethod
    def assess_worker_heat_hazard(
        request: WorkerHeatAssessmentRequest,
        db: Optional[Session] = None,
        weather_hourly_override: Optional[List[Dict[str, float]]] = None
    ) -> WorkerHeatAssessmentResponse:
        session_id = f"whs_{uuid.uuid4().hex[:12]}"
        now_dt_utc = now_utc()
        now_dt_ist = now_ist()

        # 1. Clothing CAV
        cav = CLOTHING_ADJUSTMENT_VALUES.get(request.clothing_type.lower(), 0.0)

        # 2. Workload screening threshold
        threshold_table = (
            WORKLOAD_THRESHOLDS_ACCLIMATISED
            if request.is_acclimatised
            else WORKLOAD_THRESHOLDS_UNACCLIMATISED
        )
        threshold_c = threshold_table.get(request.workload_category.lower(), 28.0)

        # 3. Retrieve or process 0-6 hour forecast sequence via WeatherService
        hourly_projections: List[HourlyHeatRiskProjection] = []
        in_sun = (request.sun_exposure.lower() == "direct_sun")

        if weather_hourly_override:
            hourly_feed = weather_hourly_override
            provider_name = "Provided Meteorological Hourly Feed"
            data_quality_label = "VERIFIED"
        else:
            fc = WeatherService.get_hourly_forecast(request.latitude, request.longitude, horizon_hours=6)
            hourly_feed = fc.get("hourly_points", [])
            provider_name = fc.get("provider", "IMD 0.25° Gridded Climatological Normal Calibration")
            data_quality_label = fc.get("data_quality", "LIMITED")

        for h in range(7):  # 0 to 6 hours (always full 6-hour horizon)
            if hourly_feed and h < len(hourly_feed):
                w = hourly_feed[h]
                ta = w.get("air_temp_c", 32.0)
                rh = w.get("relative_humidity_pct", w.get("rh_pct", 55.0))
                u = w.get("wind_speed_ms", 1.8)
                raw_solar = w.get("solar_irradiance_wm2", 600.0)
                sw = raw_solar if in_sun else 0.0
            elif hourly_feed:
                # Extrapolate beyond short feed
                last_w = hourly_feed[-1]
                ta = last_w.get("air_temp_c", 32.0)
                rh = last_w.get("relative_humidity_pct", last_w.get("rh_pct", 55.0))
                u = last_w.get("wind_speed_ms", 1.8)
                raw_solar = max(0.0, last_w.get("solar_irradiance_wm2", 0.0) - (h * 20.0))
                sw = raw_solar if in_sun else 0.0
            else:
                ta = 32.0 + (h * 0.4)
                rh = max(30.0, 55.0 - (h * 1.5))
                u = 1.8
                sw = max(0.0, 600.0 - (h * 30.0)) if in_sun else 0.0

            wbgt_res = calculate_wbgt(
                temp_c=ta,
                rh_pct=rh,
                wind_speed_ms=u,
                solar_irradiance_wm2=sw,
                in_sun=in_sun
            )

            wbgt_est = wbgt_res["wbgt_estimated_c"]
            wbgt_eff = round(wbgt_est + cav, 2)

            # Determine hazard level against screening limit
            diff = wbgt_eff - threshold_c
            if diff >= 2.5:
                lvl = "extreme"
            elif diff >= 0.0:
                lvl = "high"
            elif diff >= -2.0:
                lvl = "moderate"
            else:
                lvl = "low"

            proj_time_ist = (now_dt_ist + timedelta(hours=h)).strftime("%Y-%m-%d %H:%M:%S IST")

            hourly_projections.append(HourlyHeatRiskProjection(
                forecast_hour_offset=h,
                valid_time_ist=proj_time_ist,
                air_temp_c=round(ta, 1),
                relative_humidity_pct=round(rh, 1),
                wind_speed_ms=round(u, 1),
                solar_irradiance_wm2=round(sw, 1),
                wbgt_estimated_c=wbgt_est,
                wbgt_effective_c=wbgt_eff,
                hazard_level=lvl,
                exceeds_screening_threshold=(wbgt_eff >= threshold_c),
                threshold_limit_c=threshold_c
            ))

        # Overall summary
        current_hazard = hourly_projections[0].hazard_level
        max_wbgt_eff = max(p.wbgt_effective_c for p in hourly_projections)
        hazard_ranks = {"low": 1, "moderate": 2, "high": 3, "extreme": 4}
        max_hazard = max(hourly_projections, key=lambda p: hazard_ranks.get(p.hazard_level, 1)).hazard_level

        # Hydration guidance (NIOSH standard)
        hydration = {
            "rate_recommended": "1 cup (250 ml) every 20 minutes under active exertion",
            "max_hourly_rate": "Do not exceed 1 litre (4 cups) per hour to prevent water intoxication / hyponatremia",
            "electrolytes_note": "If sweating heavily for over 2 hours, supplement with light electrolyte or oral rehydration fluids",
            "temperature_note": "Cool water (10-15°C) is absorbed more rapidly than ice-cold water"
        }

        # Safety cautions
        cautions = [
            "Maintain continuous access to shaded, ventilated recovery areas within 2 minutes walk.",
            "Operate buddy system: immediately check co-workers for confusion, slurred speech, profuse sweating followed by dry hot skin, or dizziness.",
            "Schedule heavy labour (digging, spraying, lifting) for cooler morning hours before 10:30 AM or after 4:00 PM."
        ]
        if max_hazard in ["high", "extreme"]:
            cautions.append("High heat hazard projected in the 0-6 hour window: Increase shaded rest frequency and actively monitor unacclimatised workers.")

        disclaimer = (
            "NOTICE: WBGT values are cloud-modeled estimates based on atmospheric data and the "
            "Liljegren et al. (2008) formulation; they are not on-site physical sensor measurements. "
            "This tool provides conservative screening advice aligned with ISO 7243 and ACGIH standards "
            "and does not mandate work-stoppages. Work-rest decisions must remain flexible and subject "
            "to farm manager oversight and individual medical/health conditions."
        )

        audit_saved = False
        if db:
            try:
                audit_record = WorkerHazardAuditLogModel(
                    session_id=session_id,
                    generated_at_utc=now_dt_utc,
                    latitude_rounded=round(request.latitude, 3),
                    longitude_rounded=round(request.longitude, 3),
                    taluka=request.taluka,
                    workload_category=request.workload_category,
                    sun_exposure=request.sun_exposure,
                    is_acclimatised=request.is_acclimatised,
                    max_estimated_wbgt_c=max_wbgt_eff,
                    hazard_level=max_hazard,
                    weather_provider="IMD_GFS_OPERATIONAL_BLENDED",
                    weather_observation_time_utc=now_dt_utc
                )
                db.add(audit_record)
                db.commit()
                audit_saved = True
            except Exception:
                db.rollback()
                audit_saved = False

        return WorkerHeatAssessmentResponse(
            session_id=session_id,
            generated_at_ist=now_dt_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            time_horizon="0_to_6_hours",
            recalculation_cadence_minutes=30,
            workload_category=request.workload_category,
            clothing_cav_c=cav,
            is_acclimatised=request.is_acclimatised,
            sun_exposure=request.sun_exposure,
            current_hazard_level=current_hazard,
            max_hazard_level_in_window=max_hazard,
            max_wbgt_effective_c=max_wbgt_eff,
            screening_threshold_c=threshold_c,
            disclaimer=disclaimer,
            safety_cautions=cautions,
            hydration_guidance=hydration,
            hourly_projections=hourly_projections,
            audit_logged=audit_saved
        )
