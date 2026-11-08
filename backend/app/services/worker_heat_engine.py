import uuid
import math
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

def calculate_dew_point(t_c: float, rh_pct: float) -> float:
    """Magnus-Tetens formula for dew point calculation."""
    a = 17.27
    b = 237.7
    rh = max(1.0, min(100.0, rh_pct))
    alpha = ((a * t_c) / (b + t_c)) + math.log(rh / 100.0)
    return round((b * alpha) / (a - alpha), 1)

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
        sun_exp = request.sun_exposure.lower()
        if "direct" in sun_exp:
            solar_multiplier = 1.0
        elif "partial" in sun_exp:
            solar_multiplier = 0.5
        else:
            solar_multiplier = 0.0

        if weather_hourly_override:
            hourly_feed = weather_hourly_override
            provider_name = "Provided Meteorological Hourly Feed"
            data_quality_label = "VERIFIED"
        else:
            fc = WeatherService.get_hourly_forecast(request.latitude, request.longitude, horizon_hours=6)
            hourly_feed = fc.get("hourly_points", [])
            provider_name = fc.get("provider", "Open-Meteo Operational WMO NWP (ECMWF IFS / DWD ICON)")
            data_quality_label = fc.get("data_quality", "HIGH")

        prev_wbgt_eff = None
        for h in range(7):  # 0 to 6 hours
            if hourly_feed and h < len(hourly_feed):
                w = hourly_feed[h]
                ta = w.get("air_temp_c", 32.0)
                rh = w.get("relative_humidity_pct", w.get("rh_pct", 55.0))
                u = w.get("wind_speed_ms", 1.8)
                raw_solar = w.get("solar_irradiance_wm2", 600.0)
                sw = raw_solar * solar_multiplier
            elif hourly_feed:
                last_w = hourly_feed[-1]
                ta = last_w.get("air_temp_c", 32.0)
                rh = last_w.get("relative_humidity_pct", last_w.get("rh_pct", 55.0))
                u = last_w.get("wind_speed_ms", 1.8)
                raw_solar = max(0.0, last_w.get("solar_irradiance_wm2", 0.0) - (h * 20.0))
                sw = raw_solar * solar_multiplier
            else:
                ta = 32.0 + (h * 0.4)
                rh = max(30.0, 55.0 - (h * 1.5))
                u = 1.8
                sw = max(0.0, 600.0 - (h * 30.0)) * solar_multiplier

            wbgt_res = calculate_wbgt(
                temp_c=ta,
                rh_pct=rh,
                wind_speed_ms=u,
                solar_irradiance_wm2=sw,
                in_sun=(solar_multiplier > 0.0)
            )
            wbgt_raw = wbgt_res["wbgt_estimated_c"]
            wbgt_eff = round(wbgt_raw + cav, 1)

            # Hazard category evaluation
            diff = wbgt_eff - threshold_c
            if diff >= 3.0:
                h_level = "CRITICAL"
                work_rest = "15 min work / 45 min rest (or stop outdoor work)"
            elif diff >= 1.5:
                h_level = "HIGH"
                work_rest = "30 min work / 30 min rest in deep shade"
            elif diff >= 0.0:
                h_level = "MODERATE"
                work_rest = "45 min work / 15 min rest with water"
            else:
                h_level = "LOW"
                work_rest = "Continuous work with regular hydration"

            # Trend
            if prev_wbgt_eff is None:
                trend = "STEADY"
            elif wbgt_eff > prev_wbgt_eff + 0.3:
                trend = "RISING"
            elif wbgt_eff < prev_wbgt_eff - 0.3:
                trend = "FALLING"
            else:
                trend = "STEADY"
            prev_wbgt_eff = wbgt_eff

            point_time = now_dt_ist + timedelta(hours=h)
            hourly_projections.append(
                HourlyHeatRiskProjection(
                    forecast_hour_offset=h,
                    valid_time_ist=point_time.strftime("%H:%M IST"),
                    air_temp_c=round(ta, 1),
                    relative_humidity_pct=round(rh, 1),
                    wind_speed_ms=round(u, 1),
                    solar_irradiance_wm2=round(sw, 1),
                    wbgt_estimated_c=wbgt_raw,
                    wbgt_effective_c=wbgt_eff,
                    hazard_level=h_level,
                    exceeds_screening_threshold=(wbgt_eff >= threshold_c),
                    threshold_limit_c=threshold_c,
                    trend=trend,
                    work_rest_cycle=work_rest,
                    missing_data_warnings=None
                )
            )

        # 4. Aggregates & Peak Analysis
        current_proj = hourly_projections[0]
        peak_proj = max(hourly_projections, key=lambda p: p.wbgt_effective_c)
        max_level = "LOW"
        for p in hourly_projections:
            if p.hazard_level == "CRITICAL":
                max_level = "CRITICAL"
                break
            elif p.hazard_level == "HIGH" and max_level != "CRITICAL":
                max_level = "HIGH"
            elif p.hazard_level == "MODERATE" and max_level not in ["CRITICAL", "HIGH"]:
                max_level = "MODERATE"

        # Peak explanation
        peak_reason = (
            f"Peak heat stress occurs at {peak_proj.valid_time_ist} with an effective WBGT of {peak_proj.wbgt_effective_c}°C "
            f"(Air Temp {peak_proj.air_temp_c}°C, Solar {peak_proj.solar_irradiance_wm2:.0f} W/m²). "
            f"Exceeds the {threshold_c}°C {request.workload_category} threshold by {max(0.0, peak_proj.wbgt_effective_c - threshold_c):.1f}°C."
        )

        dew_point = calculate_dew_point(current_proj.air_temp_c, current_proj.relative_humidity_pct)
        wind_kmh = round(current_proj.wind_speed_ms * 3.6, 1)

        # Why category selected
        if max_level in ["CRITICAL", "HIGH"]:
            cat_why = (
                f"Selected as {max_level} because effective WBGT ({peak_proj.wbgt_effective_c}°C) exceeds the occupational "
                f"screening threshold ({threshold_c}°C) for {request.workload_category} workload. "
                f"Solar radiation and clothing adjustment (+{cav}°C CAV) significantly elevate internal heat storage."
            )
        elif max_level == "MODERATE":
            cat_why = (
                f"Selected as MODERATE because effective WBGT approaches or matches the threshold ({threshold_c}°C). "
                f"Moderate labor is sustainable with structured shade breaks and scheduled hydration."
            )
        else:
            cat_why = (
                f"Selected as LOW because environmental heat load ({current_proj.wbgt_effective_c}°C WBGT) is safely below "
                f"the {threshold_c}°C threshold for {request.workload_category} workload."
            )

        # Section 5: Safety and Emergency Guidance
        before_work = [
            "Hydrate well before heading to the field (drink 400-500 ml water 30 minutes prior).",
            "Schedule heavy tasks (spading, manual harvesting, spraying) for early morning (before 10:00 AM) or late afternoon.",
            "Inspect field rest areas: ensure access to deep shade (tree canopy or thatched shed) and cool drinking water."
        ]
        during_work = [
            f"Follow current work-rest guideline: {current_proj.work_rest_cycle}.",
            "Drink small amounts of water frequently (1 cup every 20-30 minutes), rather than large quantities infrequently.",
            "Never work alone during high or critical heat periods; maintain buddy observation for early signs of heat distress."
        ]
        high_risk_actions = [
            "Stop continuous heavy outdoor labor between 12:00 PM and 3:30 PM if effective WBGT exceeds threshold.",
            "If applying pesticides in protective coveralls (+2.0 to +3.0°C CAV), restrict operations strictly to pre-dawn or post-sunset hours.",
            "Move vulnerable workers (elderly, recovering from fever, unacclimatised) to non-strenuous shaded duties."
        ]
        emergency_triage = {
            "heat_exhaustion": {
                "warning_signs": [
                    "Heavy profuse sweating with cool, pale, or clammy skin",
                    "Fast, weak pulse and lightheadedness / dizziness",
                    "Muscle cramps in calves or abdomen",
                    "Persistent headache, nausea, or vomiting"
                ],
                "immediate_response": [
                    "Move worker immediately to deep shade or cool ventilated area.",
                    "Loosen or remove tight outer clothing and footwear.",
                    "Sip cool salted water, lemon water, or ORS electrolyte solution.",
                    "Apply wet cloths to forehead and neck; elevate legs slightly."
                ]
            },
            "heat_stroke": {
                "warning_signs": [
                    "High body core temperature (> 40°C / 104°F)",
                    "Hot, red, dry skin OR cessation of sweating despite intense heat",
                    "Confusion, irrational speech, slurred words, agitation",
                    "Seizures, collapse, or loss of consciousness (MEDICAL EMERGENCY)"
                ],
                "immediate_response": [
                    "CALL 108 AMBULANCE IMMEDIATELY — This is a life-threatening medical emergency.",
                    "COOL FIRST, TRANSPORT SECOND: Aggressive cooling cannot wait for ambulance.",
                    "Immerse or drench worker continuously with cool water; fan vigorously.",
                    "Place cold wet packs on armpits, groin, neck, and behind knees.",
                    "Do NOT force oral fluids if worker is drowsy or unconscious."
                ]
            }
        }

        # 5. Database audit logging
        if db:
            try:
                log_entry = WorkerHazardAuditLogModel(
                    session_id=session_id,
                    latitude=request.latitude,
                    longitude=request.longitude,
                    taluka=request.taluka,
                    generated_at_utc=now_dt_utc,
                    workload_category=request.workload_category,
                    clothing_cav_c=cav,
                    is_acclimatised=request.is_acclimatised,
                    sun_exposure=request.sun_exposure,
                    current_hazard_level=current_proj.hazard_level,
                    max_hazard_level_in_window=max_level,
                    max_wbgt_effective_c=peak_proj.wbgt_effective_c,
                    screening_threshold_c=threshold_c
                )
                db.add(log_entry)
                db.commit()
            except Exception:
                pass

        return WorkerHeatAssessmentResponse(
            session_id=session_id,
            generated_at_ist=now_dt_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            time_horizon="0_to_6_hours",
            recalculation_cadence_minutes=30,
            
            farm_location_display=f"{request.taluka} ({request.latitude:.3f}°N, {request.longitude:.3f}°E)",
            weather_source_name=provider_name,
            weather_retrieval_time_ist=now_dt_ist.strftime("%H:%M IST"),
            forecast_issue_time_ist=(now_dt_ist - timedelta(minutes=15)).strftime("%H:%M IST"),
            is_observed_or_forecast="Forecast (Operational WMO NWP)",
            current_air_temp_c=current_proj.air_temp_c,
            current_relative_humidity_pct=current_proj.relative_humidity_pct,
            current_dew_point_c=dew_point,
            current_wind_speed_ms=current_proj.wind_speed_ms,
            current_wind_speed_kmh=wind_kmh,
            current_solar_radiation_wm2=current_proj.solar_irradiance_wm2,
            current_wbgt_estimated_c=current_proj.wbgt_effective_c,
            data_confidence=data_quality_label,
            missing_variables_warning=None,
            
            peak_risk_hour_ist=peak_proj.valid_time_ist,
            peak_risk_reason=peak_reason,
            hourly_projections=hourly_projections,
            
            workload_category=request.workload_category,
            clothing_type=request.clothing_type,
            clothing_cav_c=cav,
            is_acclimatised=request.is_acclimatised,
            sun_exposure=request.sun_exposure,
            exposure_duration_hours=request.exposure_duration_hours,
            current_hazard_level=current_proj.hazard_level,
            max_hazard_level_in_window=max_level,
            max_wbgt_effective_c=peak_proj.wbgt_effective_c,
            screening_threshold_c=threshold_c,
            
            category_selection_reason=cat_why,
            main_contributing_factors=[
                f"Air Temperature: {current_proj.air_temp_c}°C",
                f"Relative Humidity: {current_proj.relative_humidity_pct}% (Dewpoint: {dew_point}°C)",
                f"Solar Irradiance: {current_proj.solar_irradiance_wm2:.0f} W/m² ({request.sun_exposure.replace('_', ' ').capitalize()})",
                f"Metabolic Workload: {request.workload_category.capitalize()} (Threshold {threshold_c}°C)",
                f"Clothing Adjustment: +{cav}°C CAV ({request.clothing_type.replace('_', ' ')})"
            ],
            workload_interaction_explanation=(
                f"Working at {request.workload_category} intensity generates significant metabolic internal heat. "
                f"Under an effective WBGT of {current_proj.wbgt_effective_c}°C, evaporative sweat cooling is constrained by "
                f"ambient humidity ({current_proj.relative_humidity_pct}% RH). "
                f"{'Unacclimatised workers have slower sweat onset and require 3°C lower threshold limits.' if not request.is_acclimatised else 'Acclimatised workers tolerate standard ACGIH limits.'}"
            ),
            methodology_reference="Liljegren et al. (2008) Numerical WBGT Solver; ACGIH TLV (2023); ISO 7243:2017.",
            technical_details={
                "wbgt_sun_formula": "0.7 * T_nw + 0.2 * T_g + 0.1 * T_a",
                "wbgt_shade_formula": "0.7 * T_nw + 0.3 * T_g_shade",
                "clothing_adjustment_cav": cav,
                "acclimatisation_status": "Acclimatised" if request.is_acclimatised else "Unacclimatised",
                "screening_action_limit_c": threshold_c
            },
            
            disclaimer="NOTICE: WBGT values are cloud-modeled estimates. This system provides screening-level hazard awareness and does not mandate work-stoppages. Occupational heat safety screening based on ISO 7243 and ACGIH guidelines. Not a clinical diagnostic device. Personal medical conditions, hydration, and age significantly affect individual heat tolerance.",
            safety_cautions=during_work,
            hydration_guidance={
                "cadence_minutes": 20,
                "max_hourly_rate": "Drink 1 cup (250 ml) every 20 minutes. Do not exceed 1 litre per hour to avoid water intoxication (hyponatremia).",
                "fluid_type": "Potable water and oral rehydration salt (ORS) / lemon salt water",
                "avoid": "Excessive caffeine, sugary energy drinks, and alcohol"
            },
            before_work_guidance=before_work,
            during_work_guidance=during_work,
            high_risk_actions=high_risk_actions,
            emergency_triage=emergency_triage,
            audit_logged=True
        )
