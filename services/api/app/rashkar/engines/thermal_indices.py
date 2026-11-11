"""
RASHKAR — Multi-Index Thermal Safety and Topographic Downscaling Engine.

Calculates:
1. NOAA Heat Index (Rothfusz regression with low/high humidity corrections).
2. Universal Thermal Climate Index (UTCI) operational approximation (Brode et al. 2012).
3. Topographic elevation lapse-rate downscaling from provider grid (~11 km) to plot target (1 km).
4. Explainable 0-100 Personalized Worker Heat Strain Score.
5. Explainable 0-100 Crop Heat Vulnerability Score.
"""

import math
from typing import Any, Dict, Tuple


def calculate_noaa_heat_index(temp_c: float, rel_humidity_pct: float) -> float:
    """
    Computes NOAA National Weather Service Heat Index in Celsius.
    Uses Rothfusz regression equation with standard low/high humidity adjustments.
    Valid for T >= 20C (68F) and RH >= 0%.
    """
    if temp_c < 20.0:
        return round(temp_c, 2)

    t_f = (temp_c * 9.0 / 5.0) + 32.0
    rh = max(0.0, min(100.0, rel_humidity_pct))

    hi_simple = 0.5 * (t_f + 61.0 + ((t_f - 68.0) * 1.2) + (rh * 0.094))

    if hi_simple < 80.0:
        hi_f = hi_simple
    else:
        hi_f = (
            -42.379
            + 2.04901523 * t_f
            + 10.14333127 * rh
            - 0.22475541 * t_f * rh
            - 0.00683783 * (t_f ** 2)
            - 0.05481717 * (rh ** 2)
            + 0.00122874 * (t_f ** 2) * rh
            + 0.00085282 * t_f * (rh ** 2)
            - 0.00000199 * (t_f ** 2) * (rh ** 2)
        )

        if rh < 13.0 and 80.0 <= t_f <= 112.0:
            diff = 17.0 - abs(t_f - 95.0)
            if diff > 0:
                adj = -((13.0 - rh) / 4.0) * math.sqrt(diff / 17.0)
                hi_f += adj
        elif rh > 85.0 and 80.0 <= t_f <= 87.0:
            adj = ((rh - 85.0) / 10.0) * ((87.0 - t_f) / 5.0)
            hi_f += adj

    hi_c = (hi_f - 32.0) * 5.0 / 9.0
    return round(hi_c, 2)


def calculate_utci_approx(
    temp_c: float,
    rel_humidity_pct: float,
    wind_speed_10m_mps: float,
    solar_radiation_w_m2: float = 0.0,
) -> float:
    """
    Operational approximation of Universal Thermal Climate Index (UTCI) in Celsius.
    Models human heat budget based on air temperature, vapor pressure, wind speed,
    and mean radiant temperature (derived from solar irradiance).
    """
    t_a = temp_c
    v_10 = max(0.5, min(30.0, wind_speed_10m_mps))
    rh = max(5.0, min(100.0, rel_humidity_pct))

    e_sat_hpa = 6.112 * math.exp((17.67 * t_a) / (t_a + 243.5))
    e_hpa = e_sat_hpa * (rh / 100.0)
    e_kpa = e_hpa / 10.0

    rad_factor = max(0.0, solar_radiation_w_m2)
    delta_tmrt = (rad_factor * 0.032) / (1.0 + 0.2 * math.sqrt(v_10))
    t_mrt = t_a + delta_tmrt
    d_tmrt = t_mrt - t_a

    utci = (
        t_a
        + 0.6075 * (e_kpa - 1.0)
        + 0.0833 * d_tmrt
        - 1.487 * math.log(v_10) * (1.0 - 0.02 * t_a)
        + 0.0048 * (t_a - 20.0) * (e_kpa - 1.0)
        + 0.0012 * d_tmrt * math.sqrt(v_10)
    )

    if t_a > 30.0 and rh > 60.0:
        utci += 0.05 * (t_a - 30.0) * (rh - 60.0) / 10.0

    return round(utci, 2)


def apply_topographic_lapse_downscaling(
    base_temp_c: float,
    farm_elevation_m: float,
    grid_elevation_m: float,
    lapse_rate_c_per_km: float = 6.5,
) -> Tuple[float, float]:
    """
    Downscales base NWP grid temperature to local farm plot elevation
    using environmental lapse rate delta_T = -(lapse_rate/1000)*(farm_elev - grid_elev).
    """
    elev_diff_m = farm_elevation_m - grid_elevation_m
    lapse_adj_c = -(lapse_rate_c_per_km / 1000.0) * elev_diff_m
    downscaled_temp_c = base_temp_c + lapse_adj_c
    return round(downscaled_temp_c, 2), round(lapse_adj_c, 2)


def compute_personalized_worker_heat_strain_score(
    effective_wbgt_c: float,
    iso_threshold_c: float,
    metabolic_workload: str = "heavy",
    is_acclimatized: bool = True,
    worker_age: int = 35,
    continuous_shift_hours: float = 4.0,
    hydration_access: bool = True,
) -> Dict[str, Any]:
    """Computes an explainable, calibrated 0-100 Worker Heat Strain Score."""
    diff_from_thresh = effective_wbgt_c - iso_threshold_c
    if diff_from_thresh <= -6.0:
        base_thermal = max(0.0, 15.0 + (diff_from_thresh + 6.0) * 2.5)
    elif diff_from_thresh <= 0.0:
        base_thermal = 15.0 + ((diff_from_thresh + 6.0) / 6.0) * 30.0
    else:
        base_thermal = min(60.0, 45.0 + (diff_from_thresh / 3.0) * 15.0)

    workload_map = {
        "light": 2.0,
        "moderate": 6.0,
        "heavy": 10.0,
        "very_heavy": 15.0,
    }
    workload_points = workload_map.get(metabolic_workload.lower(), 8.0)

    vuln_points = 0.0
    if not is_acclimatized:
        vuln_points += 10.0
    if worker_age >= 50:
        vuln_points += 5.0
    elif worker_age >= 40:
        vuln_points += 2.0

    duration_points = 0.0
    if continuous_shift_hours >= 6.0:
        duration_points += 5.0
    elif continuous_shift_hours >= 4.0:
        duration_points += 2.5
    if not hydration_access:
        duration_points += 5.0

    raw_score = base_thermal + workload_points + vuln_points + duration_points
    score_0_100 = round(max(0.0, min(100.0, raw_score)), 1)

    if score_0_100 < 35.0:
        severity = "LOW_RISK"
        color = "green"
        action_summary = (
            "Normal agricultural operations safe with standard hourly water intake."
        )
    elif score_0_100 < 60.0:
        severity = "MODERATE_HEAT_STRAIN"
        color = "yellow"
        action_summary = (
            "Active heat monitoring required. Enforce 15-min rest per hour in shade."
        )
    elif score_0_100 < 80.0:
        severity = "HIGH_HEAT_STRAIN"
        color = "orange"
        action_summary = (
            "Dangerous heat stress. Shift heavy labor to early morning/evening. "
            "30-min rest per hour."
        )
    else:
        severity = "EXTREME_LIFE_THREATENING"
        color = "red"
        action_summary = (
            "Immediate cessation of intense physical field labor. "
            "Mandatory hydration and cool recovery."
        )

    return {
        "score_0_100": score_0_100,
        "severity_level": severity,
        "indicator_color": color,
        "sub_indices": {
            "base_thermal_exceedance_points": round(base_thermal, 1),
            "metabolic_workload_points": round(workload_points, 1),
            "vulnerability_points": round(vuln_points, 1),
            "duration_hydration_points": round(duration_points, 1),
        },
        "action_summary": action_summary,
        "iso_threshold_c": iso_threshold_c,
        "effective_wbgt_c": effective_wbgt_c,
        "wbgt_exceedance_c": round(diff_from_thresh, 2),
    }


def compute_crop_heat_vulnerability_score(
    max_temp_c: float,
    optimum_temp_c: float,
    critical_temp_c: float,
    growth_stage_code: str = "flowering",
    soil_moisture_status: str = "moderate",
    is_irrigated: bool = True,
) -> Dict[str, Any]:
    """Computes an explainable, calibrated 0-100 Crop Heat Vulnerability Score."""
    if max_temp_c <= optimum_temp_c:
        base_thermal = max(0.0, 10.0 * (max_temp_c / max(1.0, optimum_temp_c)))
    elif max_temp_c <= critical_temp_c:
        fraction = (max_temp_c - optimum_temp_c) / max(
            1.0, (critical_temp_c - optimum_temp_c)
        )
        base_thermal = 10.0 + fraction * 35.0
    else:
        excess = max_temp_c - critical_temp_c
        base_thermal = min(55.0, 45.0 + excess * 3.0)

    stage_weights = {
        "pollination": 25.0,
        "flowering": 25.0,
        "anthesis": 25.0,
        "grain_filling": 18.0,
        "pod_development": 18.0,
        "vegetative": 8.0,
        "seedling": 12.0,
        "maturity": 5.0,
    }
    stage_code_str = (growth_stage_code or "unknown").lower()
    stage_points = stage_weights.get(stage_code_str, 10.0)

    if soil_moisture_status in ("severe_deficit", "dry"):
        moisture_points = 20.0 if not is_irrigated else 10.0
    elif soil_moisture_status in ("mild_deficit", "moderate"):
        moisture_points = 10.0 if not is_irrigated else 4.0
    else:
        moisture_points = 0.0

    raw_score = base_thermal + stage_points + moisture_points
    score_0_100 = round(max(0.0, min(100.0, raw_score)), 1)

    if score_0_100 < 30.0:
        status = "OPTIMAL_GROWTH"
        color = "green"
        recommendation = (
            "Canopy temperatures remain within safe metabolic range. "
            "Continue scheduled irrigation."
        )
    elif score_0_100 < 55.0:
        status = "MILD_HEAT_STRESS"
        color = "yellow"
        recommendation = (
            "Moderate thermal load. Consider light pre-dawn irrigation to maintain "
            "canopy transpiration cooling."
        )
    elif score_0_100 < 75.0:
        status = "CRITICAL_PHENOLOGICAL_STRESS"
        color = "orange"
        recommendation = (
            "High risk of pollen sterility or flower drop. Apply foliar "
            "potassium/calcium spray and schedule night irrigation."
        )
    else:
        status = "SEVERE_CROP_BURN_RISK"
        color = "red"
        recommendation = (
            "Acute thermal shock imminent. Mandatory emergency micro-sprinkler "
            "misting or soil saturation to avoid permanent yield abort."
        )

    return {
        "score_0_100": score_0_100,
        "vulnerability_level": status,
        "indicator_color": color,
        "sub_indices": {
            "thermal_exceedance_points": round(base_thermal, 1),
            "phenological_sensitivity_points": round(stage_points, 1),
            "moisture_deficit_points": round(moisture_points, 1),
        },
        "action_recommendation": recommendation,
        "max_temp_c": max_temp_c,
        "optimum_temp_c": optimum_temp_c,
        "critical_temp_c": critical_temp_c,
    }
