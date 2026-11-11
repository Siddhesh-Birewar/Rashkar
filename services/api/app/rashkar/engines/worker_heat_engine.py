"""Worker occupational heat hazard & WBGT screening engine (ISO 7243 / ACGIH)."""

from datetime import datetime, timedelta
import math
from typing import Any, Dict, List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session

from ..models import RashkarWorkerHazardAuditLogModel
from ..schemas.worker_heat import (
    HourlyHeatRiskProjection,
    WorkerHeatAssessmentRequest,
    WorkerHeatAssessmentResponse,
)
from ..timezone import IST_ZONE, UTC_ZONE, now_ist, now_utc, now_utc_naive
from .forecast_scheduler import grid_scheduler_cache
from .heat_ml_pipeline import heat_ml_pipeline
from .thermal_indices import (
    apply_topographic_lapse_downscaling,
    calculate_noaa_heat_index,
    calculate_utci_approx,
    compute_personalized_worker_heat_strain_score,
)
from .wbgt_solver import calculate_wbgt


# ACGIH TLV & ISO 7243:2017 screening action limits (°C WBGT)
WORKLOAD_THRESHOLDS_ACCLIMATISED: Dict[str, float] = {
    "light": 31.0,
    "moderate": 28.0,
    "heavy": 26.0,
    "very_heavy": 25.0,
}

WORKLOAD_THRESHOLDS_UNACCLIMATISED: Dict[str, float] = {
    "light": 28.0,
    "moderate": 25.0,
    "heavy": 23.0,
    "very_heavy": 22.0,
}

# Clothing Adjustment Values (CAV, °C) - ISO 9920 / ACGIH
CLOTHING_ADJUSTMENT_VALUES: Dict[str, float] = {
    "standard_work_clothes": 0.0,
    "coveralls_protective": 2.0,
    "woven_double_layer": 3.0,
    "impermeable_vapor_barrier": 10.0,
}


def calculate_dew_point(t_c: float, rh_pct: float) -> float:
    """Magnus-Tetens formula for dew point calculation."""
    a = 17.27
    b = 237.7
    rh = max(1.0, min(100.0, rh_pct))
    alpha = ((a * t_c) / (b + t_c)) + math.log(rh / 100.0)
    return round((b * alpha) / (a - alpha), 1)


def _extract_hourly_metrics(
    point: Dict[str, Any],
    solar_multiplier: float,
    hour_offset: int,
    extrapolating: bool = False,
) -> Tuple[Optional[float], Optional[float], float, float, List[str]]:
    """Extracts meteorological variables from an hourly point without fabricating temp/RH."""
    missing: List[str] = []
    ta = point.get("air_temp_c", point.get("temp_c"))
    rh = point.get("relative_humidity_pct", point.get("rh_pct"))
    u = point.get("wind_speed_ms", point.get("wind_ms"))
    raw_solar = point.get("solar_irradiance_wm2", point.get("solar_wm2"))

    if ta is None:
        missing.append("air_temp_c")
    if rh is None:
        missing.append("relative_humidity_pct")
    if u is None:
        missing.append("wind_speed_ms")
        u = 1.5  # Standard calm wind neutral baseline for Liljegren denominator bound
    if raw_solar is None:
        missing.append("solar_irradiance_wm2")
        raw_solar = 0.0

    if extrapolating:
        raw_solar = max(0.0, float(raw_solar) - (hour_offset * 20.0))

    sw = max(0.0, float(raw_solar)) * solar_multiplier
    return (
        float(ta) if ta is not None else None,
        float(rh) if rh is not None else None,
        float(u),
        float(sw),
        missing,
    )


class WorkerHeatEngine:
    """Assesses 0-6h agricultural worker WBGT hazard with ACGIH/ISO 7243 limits."""

    @staticmethod
    def _build_threshold_comparison(
        effective_wbgt_c: float,
        threshold_c: float,
        workload_category: str,
    ) -> Tuple[str, float, str]:
        diff = round(effective_wbgt_c - threshold_c, 1)
        if diff > 0.05:
            thresh_state = "ABOVE"
            thresh_msg = (
                f"Effective WBGT ({effective_wbgt_c:.1f}°C) exceeds the "
                f"{threshold_c:.1f}°C {workload_category} threshold by {diff:.1f}°C."
            )
        elif abs(diff) <= 0.05:
            thresh_state = "AT_THRESHOLD"
            thresh_msg = (
                f"Effective WBGT ({effective_wbgt_c:.1f}°C) is at the "
                f"{threshold_c:.1f}°C {workload_category} threshold (0.0°C difference)."
            )
        else:
            thresh_state = "BELOW"
            thresh_msg = (
                f"Effective WBGT ({effective_wbgt_c:.1f}°C) is {abs(diff):.1f}°C "
                f"below the {threshold_c:.1f}°C {workload_category} threshold."
            )
        return thresh_msg, diff, thresh_state

    @staticmethod
    def _location_display(
        request: WorkerHeatAssessmentRequest,
        farm_context: Optional[Dict[str, Any]],
    ) -> str:
        ctx = farm_context or {}
        place = (
            request.taluka
            or ctx.get("taluka")
            or ctx.get("district")
            or ctx.get("farm_name")
        )
        if place:
            return f"{place} ({request.latitude:.3f}°N, {request.longitude:.3f}°E)"
        return f"Lat {request.latitude:.3f}°N, Lon {request.longitude:.3f}°E"

    @staticmethod
    def assess_worker_heat_hazard(
        request: WorkerHeatAssessmentRequest,
        farm_context: Optional[Dict[str, Any]] = None,
        weather_hourly: Optional[List[Dict[str, Any]]] = None,
        db: Optional[Session] = None,
        weather_hourly_override: Optional[List[Dict[str, Any]]] = None,
        weather_provider: str = "Provided Meteorological Hourly Feed",
        data_quality: str = "VERIFIED",
        as_of_utc: Optional[datetime] = None,
        ml_benchmark: bool = False,
    ) -> WorkerHeatAssessmentResponse:
        session_id = f"whs_{uuid.uuid4().hex[:12]}"
        if as_of_utc is not None:
            now_dt_utc = (
                as_of_utc.replace(tzinfo=UTC_ZONE)
                if as_of_utc.tzinfo is None
                else as_of_utc.astimezone(UTC_ZONE)
            )
            now_dt_ist = now_dt_utc.astimezone(IST_ZONE)
        else:
            now_dt_utc = now_utc()
            now_dt_ist = now_ist()

        ctx = farm_context or {}
        cav = CLOTHING_ADJUSTMENT_VALUES.get(request.clothing_type.lower(), 0.0)
        threshold_table = (
            WORKLOAD_THRESHOLDS_ACCLIMATISED
            if request.is_acclimatised
            else WORKLOAD_THRESHOLDS_UNACCLIMATISED
        )
        threshold_c = threshold_table.get(request.workload_category.lower(), 28.0)

        hourly_feed = (
            weather_hourly_override
            if weather_hourly_override is not None
            else weather_hourly
        )
        location_display = WorkerHeatEngine._location_display(request, ctx)
        methodology_version = "ACGIH 2023 TLVs & ISO 7243:2017 screening action limits"
        disclaimer_text = (
            "NOTICE: WBGT values are cloud-modeled estimates. This system provides "
            "screening-level hazard awareness and does not mandate work-stoppages. "
            "Occupational heat safety screening based on ISO 7243 and ACGIH guidelines. "
            "Not a clinical diagnostic device. Personal medical conditions, hydration, "
            "and age significantly affect individual heat tolerance."
        )

        # Fail cleanly without fabricating temperature/humidity when hourly feed is missing.
        if not hourly_feed:
            return WorkerHeatAssessmentResponse(
                status="WEATHER_UNAVAILABLE",
                error_message=(
                    "Hourly meteorological forecast is unavailable for these farm "
                    "coordinates; worker WBGT calculation paused without fallback fabrication."
                ),
                session_id=session_id,
                generated_at_ist=now_dt_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                farm_location_display=location_display,
                weather_source_name="Unavailable",
                weather_retrieval_time_ist=now_dt_ist.strftime("%H:%M IST"),
                forecast_issue_time_ist=now_dt_ist.strftime("%H:%M IST"),
                valid_time_ist="Unavailable",
                grid_coordinates=f"Lat {request.latitude:.4f}°N, Lon {request.longitude:.4f}°E",
                data_confidence="UNAVAILABLE",
                missing_variables=[
                    "air_temp_c",
                    "relative_humidity_pct",
                    "wind_speed_ms",
                    "solar_irradiance_wm2",
                ],
                missing_variables_warning=(
                    "Live or cached hourly weather feed missing; no synthetic weather generated."
                ),
                workload_category=request.workload_category,
                clothing_type=request.clothing_type,
                clothing_cav_c=cav,
                is_acclimatised=request.is_acclimatised,
                sun_exposure=request.sun_exposure,
                exposure_duration_hours=request.exposure_duration_hours,
                planned_shift_duration_hours=float(request.exposure_duration_hours),
                current_hazard_level="UNAVAILABLE",
                max_hazard_level_in_window="UNAVAILABLE",
                screening_threshold_c=threshold_c,
                methodology_reference=(
                    "Liljegren et al. (2008) Numerical WBGT Solver; ACGIH TLV (2023); ISO 7243:2017."
                ),
                methodology_standards_version=methodology_version,
                disclaimer=disclaimer_text,
                provenance={
                    "status": "WEATHER_UNAVAILABLE",
                    "farm_id": ctx.get("farm_id") or request.farm_id,
                    "weather_provider": None,
                },
                audit_logged=False,
            )

        sun_exp = request.sun_exposure.lower()
        if "direct" in sun_exp:
            solar_multiplier = 1.0
        elif "partial" in sun_exp:
            solar_multiplier = 0.5
        else:
            solar_multiplier = 0.0

        hourly_projections: List[HourlyHeatRiskProjection] = []
        all_missing_vars: List[str] = []
        prev_wbgt_eff: Optional[float] = None

        for h in range(7):  # 0 to 6 hours
            extrapolating = h >= len(hourly_feed)
            point = hourly_feed[h] if not extrapolating else hourly_feed[-1]
            ta, rh, u, sw, missing_pts = _extract_hourly_metrics(
                point, solar_multiplier, h, extrapolating=extrapolating
            )
            if ta is None or rh is None:
                return WorkerHeatAssessmentResponse(
                    status="WEATHER_UNAVAILABLE",
                    error_message=(
                        f"Hour +{h} forecast missing essential variable(s): {missing_pts}"
                    ),
                    session_id=session_id,
                    generated_at_ist=now_dt_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                    farm_location_display=location_display,
                    weather_source_name=weather_provider,
                    weather_retrieval_time_ist=now_dt_ist.strftime("%H:%M IST"),
                    forecast_issue_time_ist=now_dt_ist.strftime("%H:%M IST"),
                    grid_coordinates=f"Lat {request.latitude:.4f}°N, Lon {request.longitude:.4f}°E",
                    data_confidence="INSUFFICIENT",
                    missing_variables=missing_pts,
                    missing_variables_warning="Incomplete hourly meteorological point.",
                    workload_category=request.workload_category,
                    clothing_type=request.clothing_type,
                    clothing_cav_c=cav,
                    is_acclimatised=request.is_acclimatised,
                    sun_exposure=request.sun_exposure,
                    exposure_duration_hours=request.exposure_duration_hours,
                    planned_shift_duration_hours=float(request.exposure_duration_hours),
                    current_hazard_level="UNAVAILABLE",
                    max_hazard_level_in_window="UNAVAILABLE",
                    screening_threshold_c=threshold_c,
                    methodology_reference=(
                        "Liljegren et al. (2008) Numerical WBGT Solver; ACGIH TLV (2023); ISO 7243:2017."
                    ),
                    methodology_standards_version=methodology_version,
                    disclaimer=disclaimer_text,
                    provenance={"status": "WEATHER_UNAVAILABLE", "missing": missing_pts},
                    audit_logged=False,
                )

            for m in missing_pts:
                if m not in all_missing_vars:
                    all_missing_vars.append(m)

            wbgt_res = calculate_wbgt(
                temp_c=ta,
                rh_pct=rh,
                wind_speed_ms=u,
                solar_irradiance_wm2=sw,
                in_sun=(solar_multiplier > 0.0),
            )
            wbgt_raw = wbgt_res["wbgt_estimated_c"]
            wbgt_eff = round(wbgt_raw + cav, 1)

            hi_val = calculate_noaa_heat_index(temp_c=ta, rel_humidity_pct=rh)
            utci_val = calculate_utci_approx(
                temp_c=ta,
                rel_humidity_pct=rh,
                wind_speed_10m_mps=u,
                solar_radiation_w_m2=sw,
            )

            diff_hour = wbgt_eff - threshold_c
            if diff_hour >= 3.0:
                h_level = "CRITICAL"
                work_rest = "15 min work / 45 min rest (or stop outdoor work)"
            elif diff_hour >= 1.5:
                h_level = "HIGH"
                work_rest = "30 min work / 30 min rest in deep shade"
            elif diff_hour >= 0.0:
                h_level = "MODERATE"
                work_rest = "45 min work / 15 min rest with water"
            else:
                h_level = "LOW"
                work_rest = "Continuous work with regular hydration"

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
                    heat_index_c=hi_val,
                    utci_c=utci_val,
                    hazard_level=h_level,
                    exceeds_screening_threshold=(wbgt_eff >= threshold_c),
                    threshold_limit_c=threshold_c,
                    trend=trend,
                    work_rest_cycle=work_rest,
                    missing_data_warnings=(
                        f"Neutral fallback used for missing {', '.join(missing_pts)}"
                        if missing_pts
                        else None
                    ),
                )
            )

        current_proj = hourly_projections[0]
        peak_proj = max(hourly_projections, key=lambda p: p.wbgt_effective_c)

        severity_order = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}
        max_level = max(
            (p.hazard_level for p in hourly_projections),
            key=lambda lvl: severity_order.get(lvl, 0),
        )

        thresh_msg, diff, thresh_state = WorkerHeatEngine._build_threshold_comparison(
            peak_proj.wbgt_effective_c, threshold_c, request.workload_category
        )

        peak_reason = (
            f"Peak heat stress occurs at {peak_proj.valid_time_ist} with an effective WBGT of "
            f"{peak_proj.wbgt_effective_c}°C (Air Temp {peak_proj.air_temp_c}°C, "
            f"Solar {peak_proj.solar_irradiance_wm2:.0f} W/m²). {thresh_msg}"
        )

        dew_point = calculate_dew_point(
            current_proj.air_temp_c, current_proj.relative_humidity_pct
        )
        wind_kmh = round(current_proj.wind_speed_ms * 3.6, 1)

        planned_shift = float(request.exposure_duration_hours)
        forecast_coverage = 6
        shift_exceeds = planned_shift > float(forecast_coverage)
        coverage_warning = (
            (
                f"Shift Duration Limitation: The meteorological forecast covers a "
                f"{forecast_coverage}-hour window. Your planned shift is {planned_shift:.1f} hours. "
                f"The final {planned_shift - forecast_coverage:.1f} hour(s) are unmonitored by "
                f"this forecast. Risk classification applies strictly to the monitored "
                f"0-{forecast_coverage} hour forecast window."
            )
            if shift_exceeds
            else None
        )

        if max_level in ["CRITICAL", "HIGH"]:
            cat_why = (
                f"Selected as {max_level} because effective WBGT ({peak_proj.wbgt_effective_c}°C) "
                f"exceeds the occupational screening threshold ({threshold_c}°C) for "
                f"{request.workload_category} workload. Solar radiation and clothing adjustment "
                f"(+{cav}°C CAV) significantly elevate internal heat storage."
            )
        elif max_level == "MODERATE":
            cat_why = (
                f"Selected as MODERATE because effective WBGT approaches or matches the "
                f"threshold ({threshold_c}°C). Moderate labor is sustainable with structured "
                f"shade breaks and scheduled hydration."
            )
        else:
            cat_why = (
                f"Selected as LOW because environmental heat load "
                f"({current_proj.wbgt_effective_c}°C WBGT) is safely below the {threshold_c}°C "
                f"threshold for {request.workload_category} workload."
            )

        threshold_meaning = (
            f"The {threshold_c}°C {request.workload_category} threshold represents the upper "
            f"environmental wet-bulb globe thermal load below which nearly all healthy "
            f"{'acclimatised' if request.is_acclimatised else 'unacclimatised'} workers can "
            f"perform sustained labor without exceeding a core body temperature of 38.0°C (100.4°F)."
        )
        safety_disclaimer = (
            "A 'LOW' screening category indicates that environmental thermal conditions are "
            "currently below standard occupational action limits. It is NOT an absolute guarantee "
            "of individual occupational safety. Individual factors including hydration status, "
            "cardiovascular fitness, medications, age, prior illness, and metabolic work rate "
            "can trigger heat-related disorders even below screening limits."
        )

        before_work = [
            "Hydrate well before heading to the field (drink 400-500 ml water 30 minutes prior).",
            "Schedule heavy tasks (spading, manual harvesting, spraying) for early morning (before 10:00 AM) or late afternoon.",
            "Inspect field rest areas: ensure access to deep shade (tree canopy or thatched shed) and cool drinking water.",
        ]
        during_work = [
            f"Follow current work-rest guideline: {current_proj.work_rest_cycle}.",
            "Drink small amounts of water frequently (1 cup every 20-30 minutes), rather than large quantities infrequently.",
            "Never work alone during high or critical heat periods; maintain buddy observation for early signs of heat distress.",
        ]
        high_risk_actions = [
            "Stop continuous heavy outdoor labor between 12:00 PM and 3:30 PM if effective WBGT exceeds threshold.",
            "If applying pesticides in protective coveralls (+2.0 to +3.0°C CAV), restrict operations strictly to pre-dawn or post-sunset hours.",
            "Move vulnerable workers (elderly, recovering from fever, unacclimatised) to non-strenuous shaded duties.",
        ]
        hydration_guidance = {
            "rule_summary": "Drink ~1 cup (250 ml) every 15-20 minutes during moderate to heavy labor under heat strain. For light work or cool conditions, drink according to thirst.",
            "max_hourly_rate": "CRITICAL SAFETY LIMIT: Do not exceed 1 litre (4 cups) per hour or 12 litres per day. Excessive water intake without electrolytes can lead to life-threatening water intoxication (hyponatremia).",
            "electrolyte_advice": "Under heavy sweating lasting > 2 hours, supplement with oral rehydration salts (ORS), lemon water with salt, or buttermilk.",
            "beverage_restrictions": "Avoid alcohol, energy drinks with excessive caffeine, and hypertonic sugary sodas, which accelerate fluid loss.",
        }
        emergency_triage = {
            "heat_exhaustion": {
                "warning_signs": [
                    "Heavy profuse sweating with cool, pale, or clammy skin",
                    "Fast, weak pulse and lightheadedness / dizziness",
                    "Muscle cramps in calves or abdomen",
                    "Persistent headache, nausea, or vomiting",
                ],
                "immediate_response": [
                    "Move worker immediately to deep shade or cool ventilated area.",
                    "Loosen or remove tight outer clothing and footwear.",
                    "Only if fully conscious and able to swallow safely: sip cool salted water, lemon water, or ORS electrolyte solution.",
                    "Apply wet cloths to forehead, neck, and chest; elevate legs slightly.",
                    "If vomiting occurs or symptoms do not improve within 30 minutes, transfer immediately to medical facility.",
                ],
            },
            "heat_stroke": {
                "warning_signs": [
                    "High body core temperature (> 40°C / 104°F)",
                    "Hot, red, dry skin OR profuse sweating with altered mental status",
                    "Confusion, irrational speech, slurred words, agitation, or delirium",
                    "Seizures, collapse, or loss of consciousness (CRITICAL MEDICAL EMERGENCY)",
                ],
                "immediate_response": [
                    "CALL 108 AMBULANCE IMMEDIATELY — This is a life-threatening medical emergency.",
                    "COOL FIRST, TRANSPORT SECOND: Aggressive cooling cannot wait for the ambulance.",
                    "Immerse or drench worker continuously with cool water; fan vigorously.",
                    "Place cold wet packs or ice packs on neck, armpits, and groin.",
                    "CRITICAL SAFETY WARNING: DO NOT give any fluids by mouth if worker is drowsy, confused, unconscious, or vomiting (severe choking/aspiration risk).",
                ],
            },
        }
        local_emergency_contacts = {
            "ambulance_toll_free": "108 (Maharashtra Emergency Medical Services)",
            "national_emergency_helpline": "112",
            "kisan_call_centre": "1800-180-1551",
        }

        personalized_score = compute_personalized_worker_heat_strain_score(
            effective_wbgt_c=current_proj.wbgt_effective_c,
            iso_threshold_c=threshold_c,
            metabolic_workload=request.workload_category,
            is_acclimatized=request.is_acclimatised,
            worker_age=int(ctx.get("worker_age", 35)),
            continuous_shift_hours=planned_shift,
            hydration_access=True,
        )

        farm_elevation_m = ctx.get("elevation_m")
        grid_elevation_m = ctx.get("grid_elevation_m")
        if farm_elevation_m is not None and grid_elevation_m is not None:
            downscaled_temp, lapse_offset = apply_topographic_lapse_downscaling(
                base_temp_c=current_proj.air_temp_c,
                farm_elevation_m=float(farm_elevation_m),
                grid_elevation_m=float(grid_elevation_m),
            )
            elev_status = "applied"
        else:
            downscaled_temp = current_proj.air_temp_c
            lapse_offset = 0.0
            elev_status = "not_applied_elevation_unavailable"

        topographic_info = {
            "base_grid_provider": weather_provider,
            "base_grid_resolution_km": 11.0,
            "target_plot_resolution_km": 1.0,
            "lapse_rate_c_per_km": 6.5,
            "grid_elevation_m": grid_elevation_m,
            "farm_elevation_m": farm_elevation_m,
            "lapse_adjustment_c": lapse_offset,
            "downscaled_plot_temp_c": downscaled_temp,
            "status": elev_status,
            "methodology": "Environmental Lapse Rate Topographic Downscaling (ICAR/WMO standard)",
        }

        if ml_benchmark and not heat_ml_pipeline.metrics:
            heat_ml_pipeline.run_full_pipeline_benchmarking()

        ml_metadata: Dict[str, Any] = {
            "physics_reference_baseline": "Liljegren et al. (2008) verified numerical solver",
            "benchmark_status": (
                "TRAINED_AND_BENCHMARKED"
                if heat_ml_pipeline.metrics
                else "PHYSICS_ONLY_ON_DEMAND"
            ),
        }
        if heat_ml_pipeline.metrics:
            ml_metadata["xgboost_wbgt_predictor"] = heat_ml_pipeline.metrics.get(
                "xgboost_wbgt"
            )
            ml_metadata["rf_personalization"] = heat_ml_pipeline.metrics.get(
                "rf_personalization"
            )
            ml_metadata["lstm_trajectory"] = heat_ml_pipeline.metrics.get(
                "lstm_wbgt_trajectory"
            )

        grid_scheduler_cache.store_forecast(
            latitude=request.latitude,
            longitude=request.longitude,
            raw_weather_data={
                "current_wbgt": current_proj.wbgt_effective_c,
                "current_ta": current_proj.air_temp_c,
            },
            source_model=weather_provider,
            base_grid_resolution_km=11.0,
        )
        next_refresh_ist = (now_dt_ist + timedelta(minutes=30)).strftime("%H:%M IST")

        provenance_summary = {
            "weather_provider": weather_provider,
            "data_quality": data_quality,
            "physics_solver": "Liljegren et al. (2008)",
            "standards": methodology_version,
            "missing_variables": all_missing_vars,
            "farm_id": ctx.get("farm_id") or request.farm_id,
        }

        audit_logged = False
        if db is not None:
            farm_id_val = ctx.get("farm_id") or request.farm_id
            owner_id_val = ctx.get("owner_id")
            log_entry = RashkarWorkerHazardAuditLogModel(
                id=session_id,
                farm_id=farm_id_val,
                owner_id=owner_id_val,
                request_timestamp_utc=now_utc_naive(),
                forecast_target_timestamp_utc=now_dt_utc.replace(tzinfo=None),
                weather_provider=weather_provider,
                air_temp_c=current_proj.air_temp_c,
                relative_humidity_pct=current_proj.relative_humidity_pct,
                wind_speed_kmh=wind_kmh,
                solar_radiation_wm2=current_proj.solar_irradiance_wm2,
                calculated_wbgt_c=current_proj.wbgt_effective_c,
                calculated_heat_index_c=current_proj.heat_index_c,
                risk_tier=max_level,
                workload_class=request.workload_category,
                acclimatization_status=request.is_acclimatised,
                applied_threshold_wbgt_c=threshold_c,
                provenance_summary=provenance_summary,
                advisory_issued_ids=[],
            )
            db.add(log_entry)
            db.commit()
            audit_logged = True

        return WorkerHeatAssessmentResponse(
            status="OK",
            session_id=session_id,
            generated_at_ist=now_dt_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            time_horizon="0_to_6_hours",
            recalculation_cadence_minutes=30,
            farm_location_display=location_display,
            weather_source_name=weather_provider,
            weather_retrieval_time_ist=now_dt_ist.strftime("%H:%M IST"),
            forecast_issue_time_ist=(now_dt_ist - timedelta(minutes=15)).strftime(
                "%H:%M IST"
            ),
            valid_time_ist=(
                f"{hourly_projections[0].valid_time_ist} to "
                f"{hourly_projections[-1].valid_time_ist}"
            ),
            spatial_resolution=(
                "0.1° (~11 km grid resolution) downscaled to 1.0 km plot target"
            ),
            grid_coordinates=(
                f"Lat {request.latitude:.4f}°N, Lon {request.longitude:.4f}°E"
            ),
            is_observed_or_forecast="Forecast (Operational WMO NWP)",
            current_air_temp_c=current_proj.air_temp_c,
            current_relative_humidity_pct=current_proj.relative_humidity_pct,
            current_dew_point_c=dew_point,
            current_wind_speed_ms=current_proj.wind_speed_ms,
            current_wind_speed_kmh=wind_kmh,
            current_solar_radiation_wm2=current_proj.solar_irradiance_wm2,
            current_wbgt_estimated_c=current_proj.wbgt_effective_c,
            current_heat_index_c=current_proj.heat_index_c,
            current_utci_c=current_proj.utci_c,
            personalized_heat_strain_score=personalized_score,
            topographic_downscaling=topographic_info,
            ml_forecast_metadata=ml_metadata,
            next_assessment_refresh_ist=next_refresh_ist,
            data_confidence=data_quality,
            missing_variables=all_missing_vars,
            missing_variables_warning=(
                f"Neutral fallback used for: {', '.join(all_missing_vars)}"
                if all_missing_vars
                else None
            ),
            peak_risk_hour_ist=peak_proj.valid_time_ist,
            peak_risk_reason=peak_reason,
            hourly_projections=hourly_projections,
            workload_category=request.workload_category,
            clothing_type=request.clothing_type,
            clothing_cav_c=cav,
            is_acclimatised=request.is_acclimatised,
            sun_exposure=request.sun_exposure,
            exposure_duration_hours=request.exposure_duration_hours,
            planned_shift_duration_hours=planned_shift,
            forecast_coverage_hours=forecast_coverage,
            shift_exceeds_forecast_coverage=shift_exceeds,
            coverage_limitation_warning=coverage_warning,
            current_hazard_level=current_proj.hazard_level,
            max_hazard_level_in_window=max_level,
            max_wbgt_effective_c=peak_proj.wbgt_effective_c,
            screening_threshold_c=threshold_c,
            threshold_comparison_message=thresh_msg,
            threshold_difference_c=diff,
            threshold_comparison_state=thresh_state,
            category_selection_reason=cat_why,
            main_contributing_factors=[
                f"Air Temperature: {current_proj.air_temp_c}°C",
                (
                    f"Relative Humidity: {current_proj.relative_humidity_pct}% "
                    f"(Dewpoint: {dew_point}°C)"
                ),
                (
                    f"Solar Irradiance: {current_proj.solar_irradiance_wm2:.0f} W/m² "
                    f"({request.sun_exposure.replace('_', ' ').capitalize()})"
                ),
                (
                    f"Metabolic Workload: {request.workload_category.capitalize()} "
                    f"(Threshold {threshold_c}°C)"
                ),
                (
                    f"Clothing Adjustment: +{cav}°C CAV "
                    f"({request.clothing_type.replace('_', ' ')})"
                ),
            ],
            workload_interaction_explanation=(
                f"Working at {request.workload_category} intensity generates significant "
                f"metabolic internal heat. Under an effective WBGT of "
                f"{current_proj.wbgt_effective_c}°C, evaporative sweat cooling is constrained "
                f"by ambient humidity ({current_proj.relative_humidity_pct}% RH). "
                f"{'Unacclimatised workers have slower sweat onset and require 3°C lower threshold limits.' if not request.is_acclimatised else 'Acclimatised workers tolerate standard ACGIH limits.'}"
            ),
            methodology_reference=(
                "Liljegren et al. (2008) Numerical WBGT Solver; ACGIH TLV (2023); ISO 7243:2017."
            ),
            methodology_standards_version=methodology_version,
            threshold_meaning_explanation=threshold_meaning,
            safety_guarantee_disclaimer=safety_disclaimer,
            technical_details={
                "wbgt_sun_formula": "0.7 * T_nw + 0.2 * T_g + 0.1 * T_a",
                "wbgt_shade_formula": "0.7 * T_nw + 0.3 * T_g_shade",
                "clothing_adjustment_cav": cav,
                "acclimatisation_status": (
                    "Acclimatised" if request.is_acclimatised else "Unacclimatised"
                ),
                "screening_action_limit_c": threshold_c,
            },
            disclaimer=disclaimer_text,
            safety_cautions=during_work,
            hydration_guidance=hydration_guidance,
            before_work_guidance=before_work,
            during_work_guidance=during_work,
            high_risk_actions=high_risk_actions,
            emergency_triage=emergency_triage,
            local_emergency_contacts=local_emergency_contacts,
            provenance=provenance_summary,
            audit_logged=audit_logged,
        )


__all__ = [
    "WorkerHeatEngine",
    "WORKLOAD_THRESHOLDS_ACCLIMATISED",
    "WORKLOAD_THRESHOLDS_UNACCLIMATISED",
    "CLOTHING_ADJUSTMENT_VALUES",
    "calculate_dew_point",
]
