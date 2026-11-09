"""Heat Risk — deterministic crop & worker heat-stress engines.

Ported from the Rashkar `yeild-and-heat-risk-feature` branch and adapted to the
CropNet architecture. Thresholds are the original published values:
- Crop phenology: Rashkar CropHeatEngine species physiology table.
- Worker heat: ACGIH 2023 TLVs / ISO 7243:2017 screening action limits.
The WBGT solver (Liljegren et al. 2008) and thermal indices live in this package.
"""
import math
from typing import Dict, Any, Optional, List

from cropnet.services.api.app.services.heat_risk.wbgt_solver import calculate_wbgt
from cropnet.services.api.app.services.heat_risk.thermal_indices import (
    calculate_noaa_heat_index,
    calculate_utci_approx,
)

# Crop phenological thermal physiology (Rashkar CropHeatEngine baseline table).
CROP_SPECIES_PHYSIOLOGY: Dict[str, Dict[str, Any]] = {
    "soybean": {
        "common_name": "Soybean",
        "base_temp_c": 10.0,
        "optimal_min": 25.0,
        "optimal_max": 30.0,
        "night_crit_c": 22.0,
        "stages": [
            {"stage_code": "stage_germination", "stage_name": "Germination / Emergence", "das_min": 0, "das_max": 10, "crit_tmax": 38.0},
            {"stage_code": "stage_vegetative", "stage_name": "Vegetative Branching", "das_min": 11, "das_max": 35, "crit_tmax": 39.0},
            {"stage_code": "stage_flowering", "stage_name": "Flowering & Anthesis", "das_min": 36, "das_max": 55, "crit_tmax": 35.0},
            {"stage_code": "stage_pod_development", "stage_name": "Pod Formation & Seed Filling", "das_min": 56, "das_max": 85, "crit_tmax": 36.5},
            {"stage_code": "stage_maturity", "stage_name": "Maturity / Harvest", "das_min": 86, "das_max": 105, "crit_tmax": 42.0},
        ],
    },
    "cotton": {
        "common_name": "Cotton",
        "base_temp_c": 12.0,
        "optimal_min": 26.0,
        "optimal_max": 32.0,
        "night_crit_c": 24.0,
        "stages": [
            {"stage_code": "stage_germination", "stage_name": "Emergence & Seedling", "das_min": 0, "das_max": 20, "crit_tmax": 40.0},
            {"stage_code": "stage_vegetative", "stage_name": "Squaring & Vegetative", "das_min": 21, "das_max": 55, "crit_tmax": 39.0},
            {"stage_code": "stage_flowering", "stage_name": "Peak Flowering", "das_min": 56, "das_max": 90, "crit_tmax": 36.0},
            {"stage_code": "stage_boll_formation", "stage_name": "Boll Formation & Opening", "das_min": 91, "das_max": 150, "crit_tmax": 38.0},
            {"stage_code": "stage_maturity", "stage_name": "Bursting & Harvest", "das_min": 151, "das_max": 180, "crit_tmax": 42.0},
        ],
    },
    "jowar": {
        "common_name": "Sorghum (Jowar)",
        "base_temp_c": 10.0,
        "optimal_min": 26.0,
        "optimal_max": 33.0,
        "night_crit_c": 23.0,
        "stages": [
            {"stage_code": "stage_germination", "stage_name": "Emergence", "das_min": 0, "das_max": 15, "crit_tmax": 40.0},
            {"stage_code": "stage_vegetative", "stage_name": "Vegetative / General Growth", "das_min": 16, "das_max": 45, "crit_tmax": 41.0},
            {"stage_code": "stage_flowering", "stage_name": "Boot & Flowering / Anthesis", "das_min": 46, "das_max": 65, "crit_tmax": 37.0},
            {"stage_code": "stage_grain_filling", "stage_name": "Grain Development / Dough", "das_min": 66, "das_max": 95, "crit_tmax": 38.5},
            {"stage_code": "stage_maturity", "stage_name": "Physiological Maturity", "das_min": 96, "das_max": 115, "crit_tmax": 42.0},
        ],
    },
    "onion": {
        "common_name": "Onion",
        "base_temp_c": 7.0,
        "optimal_min": 20.0,
        "optimal_max": 28.0,
        "night_crit_c": 20.0,
        "stages": [
            {"stage_code": "stage_vegetative", "stage_name": "Foliage / Leaf Development", "das_min": 0, "das_max": 40, "crit_tmax": 35.0},
            {"stage_code": "stage_bulb_initiation", "stage_name": "Bulb Initiation", "das_min": 41, "das_max": 70, "crit_tmax": 33.0},
            {"stage_code": "stage_bulb_development", "stage_name": "Bulb Development & Enlargement", "das_min": 71, "das_max": 105, "crit_tmax": 34.0},
            {"stage_code": "stage_maturity", "stage_name": "Neck Fall & Harvest", "das_min": 106, "das_max": 130, "crit_tmax": 38.0},
        ],
    },
}

# ACGIH TLV & ISO 7243:2017 screening action limits (°C WBGT)
WORKLOAD_THRESHOLDS_ACCLIMATISED = {"light": 31.0, "moderate": 28.0, "heavy": 26.0, "very_heavy": 25.0}
WORKLOAD_THRESHOLDS_UNACCLIMATISED = {"light": 28.0, "moderate": 25.0, "heavy": 23.0, "very_heavy": 22.0}
CLOTHING_ADJUSTMENT_VALUES = {
    "standard_work_clothes": 0.0,
    "coveralls_protective": 2.0,
    "woven_double_layer": 3.0,
    "impermeable_vapor_barrier": 10.0,
}

CROP_EVIDENCE_CITATION = (
    "Rashkar Crop Heat phenological physiology baseline; ICAR-CRIDA / State Agricultural Universities "
    "(SAU) crop-stage thermal thresholds."
)
WORKER_EVIDENCE_CITATION = "ACGIH 2023 TLVs & ISO 7243:2017 screening action limits."


class CropHeatEngine:
    @staticmethod
    def assess(crop_code: str, forecast_tmax_c: float, forecast_tmin_c: float,
               growth_stage: Optional[str] = None, days_after_sowing: Optional[int] = None,
               forecast_sun_hours: Optional[float] = None) -> Dict[str, Any]:
        key = (crop_code or "").strip().lower()
        spec = CROP_SPECIES_PHYSIOLOGY.get(key)
        if spec is None:
            raise ValueError(
                f"Crop heat thresholds are not verified for '{crop_code}'. "
                f"Supported crops: {', '.join(sorted(CROP_SPECIES_PHYSIOLOGY))}."
            )

        stage = None
        if growth_stage:
            stage = next((s for s in spec["stages"] if s["stage_code"] == growth_stage), None)
        if stage is None and days_after_sowing is not None:
            stage = next(
                (s for s in spec["stages"] if s["das_min"] <= days_after_sowing <= s["das_max"]),
                None,
            )
        if stage is None:
            # Default to the most thermally sensitive stage (flowering where present).
            stage = next((s for s in spec["stages"] if "flower" in s["stage_code"]), spec["stages"][0])

        crit_tmax = float(stage["crit_tmax"])
        night_crit = float(spec["night_crit_c"])
        daylight = float(forecast_sun_hours) if forecast_sun_hours else 8.0
        daylight = max(1.0, min(16.0, daylight))

        # First-order thermal exposure estimate: fraction of daylight above the
        # stage-critical maximum, scaled by the day's temperature range.
        diurnal = max(1.0, forecast_tmax_c - forecast_tmin_c)
        hours_above = max(0.0, (forecast_tmax_c - crit_tmax) / diurnal) * daylight
        hours_above = round(min(daylight, hours_above), 2)

        warm_night = forecast_tmin_c > night_crit
        warm_night_penalty = round(max(0.0, forecast_tmin_c - night_crit) * 2.0, 2)
        gdd = round(max(0.0, ((forecast_tmax_c + forecast_tmin_c) / 2.0) - spec["base_temp_c"]), 1)

        if warm_night or hours_above >= 4.0:
            category, label = "CRITICAL", "Critical heat stress"
        elif hours_above >= 2.0:
            category, label = "HIGH", "High heat stress"
        elif hours_above > 0.0:
            category, label = "MODERATE", "Moderate heat stress"
        else:
            category, label = "LOW", "Within thermal tolerance"

        explanation = (
            f"{spec['common_name']} at {stage['stage_name']}: forecast max {forecast_tmax_c:.1f}°C vs "
            f"stage-critical {crit_tmax:.1f}°C, with ~{hours_above:.1f} h above critical. "
            f"Night minimum {forecast_tmin_c:.1f}°C vs warm-night threshold {night_crit:.1f}°C"
            f"{' (warm-night respiration hazard)' if warm_night else ''}."
        )

        return {
            "crop_code": key,
            "growth_stage_code": stage["stage_code"],
            "growth_stage_name": stage["stage_name"],
            "critical_tmax_c": crit_tmax,
            "critical_tmin_c": night_crit,
            "forecast_tmax_c": forecast_tmax_c,
            "forecast_tmin_c": forecast_tmin_c,
            "hours_above_critical": hours_above,
            "warm_night_hazard": warm_night,
            "warm_night_penalty": warm_night_penalty,
            "cumulative_gdd": gdd,
            "risk_category": category,
            "risk_label": label,
            "explanation": explanation,
            "evidence_citation": CROP_EVIDENCE_CITATION,
            "methodology_note": (
                "Hours-above-critical is a first-order daylight exposure estimate derived from the forecast "
                "diurnal range; it is not a sub-daily micrometeorological simulation."
            ),
        }


class WorkerHeatEngine:
    @staticmethod
    def assess(air_temp_c: float, relative_humidity_pct: float, wind_speed_ms: float = 1.5,
               solar_irradiance_wm2: float = 600.0, workload_category: str = "moderate",
               clothing_type: str = "standard_work_clothes", is_acclimatised: bool = True,
               sun_exposure: str = "direct_sun") -> Dict[str, Any]:
        in_sun = (sun_exposure or "").lower() != "shade"
        wbgt = calculate_wbgt(
            temp_c=air_temp_c,
            rh_pct=relative_humidity_pct,
            wind_speed_ms=wind_speed_ms,
            solar_irradiance_wm2=solar_irradiance_wm2,
            in_sun=in_sun,
        )
        wbgt_c = float(wbgt["wbgt_estimated_c"])

        cav = CLOTHING_ADJUSTMENT_VALUES.get((clothing_type or "").lower(), 0.0)
        wbgt_effective = round(wbgt_c + cav, 2)

        table = WORKLOAD_THRESHOLDS_ACCLIMATISED if is_acclimatised else WORKLOAD_THRESHOLDS_UNACCLIMATISED
        workload = (workload_category or "moderate").lower()
        threshold = float(table.get(workload, 28.0))

        diff = wbgt_effective - threshold
        if diff >= 3.0:
            hazard, cycle = "EXTREME", "Stop outdoor work; move to cool shelter"
        elif diff >= 0.0:
            hazard, cycle = "HIGH", "15 min work / 45 min rest in deep shade"
        elif diff >= -2.0:
            hazard, cycle = "MODERATE", "45 min work / 15 min rest with water"
        else:
            hazard, cycle = "LOW", "Continuous work with regular hydration"

        recommendation = (
            f"Effective WBGT {wbgt_effective:.1f}°C is {'above' if diff >= 0 else 'below'} the "
            f"{threshold:.1f}°C {workload} threshold by {abs(diff):.1f}°C. {cycle}."
        )

        return {
            "wbgt_c": wbgt_c,
            "wbgt_effective_c": wbgt_effective,
            "threshold_c": threshold,
            "hazard_level": hazard,
            "exceeds_threshold": diff >= 0.0,
            "work_rest_cycle": cycle,
            "heat_index_c": round(calculate_noaa_heat_index(air_temp_c, relative_humidity_pct), 2),
            "utci_c": round(
                calculate_utci_approx(
                    temp_c=air_temp_c,
                    rel_humidity_pct=relative_humidity_pct,
                    wind_speed_10m_mps=wind_speed_ms,
                    solar_radiation_w_m2=solar_irradiance_wm2,
                ),
                2,
            ),
            "recommendation": recommendation,
            "methodology_note": (
                "WBGT estimated via the Liljegren et al. (2008) numerical solver; effective WBGT includes "
                "ISO 9920 / ACGIH clothing adjustment. " + WORKER_EVIDENCE_CITATION
            ),
        }


# --- Farm-context helpers (added for the CropNet Heat Risk integration) ---

INTERVENTIONS_BY_CATEGORY = {
    "CRITICAL": [
        ("Emergency irrigation / cooling", "Apply light, frequent irrigation (early morning or evening) to reduce canopy temperature and soil heat load.", "Evaporative cooling lowers leaf temperature and reduces heat-induced flower drop.", "ICAR-CRIDA / SAU crop-stage heat advisories"),
        ("Suspend mid-day field operations", "Avoid spraying, fertilizer application and heavy field work between 12:00 and 16:00.", "Peak WBGT and crop heat load occur in the afternoon.", "ACGIH 2023 / ISO 7243:2017 screening limits"),
        ("Mulch and shade", "Apply crop residue mulch and, where feasible, temporary shade nets for sensitive stages.", "Mulch reduces soil surface temperature and evaporation.", "SAU package of practices"),
    ],
    "HIGH": [
        ("Pre-emptive evening irrigation", "Irrigate in the evening to recharge root-zone moisture before the next hot day.", "Pre-emptive moisture reduces heat-stress severity.", "ICAR-CRIDA heat advisories"),
        ("Reduce afternoon labour", "Shift labour-intensive operations to early morning; increase rest frequency.", "Effective WBGT approaches or exceeds screening limits.", "ACGIH 2023 / ISO 7243:2017"),
        ("Foliar protective sprays (only if locally advised)", "Use only locally recommended protective sprays; do not apply unverified chemical doses.", "Heat stress increases susceptibility; local extension advice governs treatment.", "State Department of Agriculture"),
    ],
    "MODERATE": [
        ("Maintain irrigation schedule", "Keep the normal irrigation schedule and monitor soil moisture.", "Avoid letting the root zone dry out during a warm spell.", "SAU package of practices"),
        ("Monitor crop stage", "Re-check growth stage and re-assess if the forecast warms further.", "Stage-specific sensitivity changes with phenology.", "ICAR-CRIDA crop-stage heat advisories"),
    ],
    "LOW": [
        ("No emergency intervention required", "Continue normal crop management; re-assess when the forecast changes.", "Forecast temperatures are within the verified thermal tolerance for the stage.", "Rashkar Crop Heat baseline"),
    ],
}


def build_interventions(risk_category: str, crop_common_name: str, warm_night: bool) -> List[dict]:
    """Return evidence-linked interventions for the assessed risk category."""
    items = INTERVENTIONS_BY_CATEGORY.get(risk_category, INTERVENTIONS_BY_CATEGORY["LOW"])
    result = [
        {
            "title": title,
            "description": desc,
            "rationale": rationale,
            "evidence": evidence,
            "category": "VERIFIED_AGRONOMIC",
        }
        for (title, desc, rationale, evidence) in items
    ]
    if warm_night:
        result.append({
            "title": "Warm-night respiration mitigation",
            "description": "Avoid late-evening irrigation that raises humidity, and ensure good field ventilation.",
            "rationale": "Night temperatures above the crop's warm-night threshold increase respiration losses.",
            "evidence": "ICAR-CRIDA / SAU crop-stage heat advisories",
            "category": "PREVENTATIVE_MANAGEMENT",
        })
    return result


def assess_daily_outlook(crop_code: str, daily_summaries: List[dict]) -> List[dict]:
    """Assess each forecast day using the crop heat engine."""
    outlook = []
    for day in daily_summaries:
        try:
            res = CropHeatEngine.assess(
                crop_code=crop_code,
                forecast_tmax_c=float(day["temp_max_c"]),
                forecast_tmin_c=float(day["temp_min_c"]),
            )
            outlook.append({
                "date": str(day.get("date", "")),
                "day_name": day.get("day_name"),
                "tmax_c": float(day["temp_max_c"]),
                "tmin_c": float(day["temp_min_c"]),
                "hours_above_critical": res["hours_above_critical"],
                "warm_night_hazard": res["warm_night_hazard"],
                "risk_category": res["risk_category"],
            })
        except (KeyError, TypeError, ValueError):
            continue
    return outlook
