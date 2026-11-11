"""Yield Risk, DES APY district baseline, and soil suitability screening engine."""

from datetime import date, datetime
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import uuid
import pandas as pd
from sqlalchemy.orm import Session

from ..data import MAHARASHTRA_APY_CANONICAL_CSV
from ..models import (
    RashkarCanonicalCropModel,
    RashkarCropCycleModel,
    RashkarYieldAssessmentLogModel,
)
from ..schemas.yield_risk import (
    ActionableRecommendation,
    HistoricalYieldBaseline,
    RiskItem,
    SoilSuitabilityAnalysis,
    YieldRiskResponse,
)
from ..timezone import IST_ZONE, UTC_ZONE, now_utc, to_ist_iso
from .crop_stage_service import CropStageService


DISTRICT_IMD_NORMALS_MM: Dict[str, float] = {
    "pune": 722.0,
    "solapur": 561.4,
    "nashik": 692.8,
    "ahmednagar": 501.2,
    "satara": 810.0,
    "sangli": 625.0,
    "kolhapur": 1780.0,
    "nagpur": 1090.0,
    "amravati": 845.0,
    "aurangabad": 675.0,
    "jalna": 688.0,
    "beed": 660.0,
    "latur": 795.0,
    "nanded": 890.0,
}

BUILTIN_APY_ALIAS_MAP: Dict[str, List[str]] = {
    "soybean": ["soyabean", "soybean"],
    "cotton": ["cotton", "cotton(lint)"],
    "jowar": ["jowar", "sorghum"],
    "sugarcane": ["sugarcane"],
    "tur": ["arhar/tur", "tur", "arhar"],
    "gram": ["gram", "chickpea"],
    "chickpea": ["gram", "chickpea"],
    "bajra": ["bajra"],
    "rice": ["rice", "paddy"],
    "wheat": ["wheat"],
    "onion": ["onion"],
}


def _extract_soil_prop(soil_profile: Any, attr: str, default: Any = None) -> Any:
    """Extracts a property from dict, CropNet SoilProfile ORM, or UnifiedSoilProfile."""
    if soil_profile is None:
        return default
    if hasattr(soil_profile, "properties") and isinstance(soil_profile.properties, dict):
        return soil_profile.properties.get(attr, default)
    if isinstance(soil_profile, dict):
        if "properties" in soil_profile and isinstance(soil_profile["properties"], dict):
            return soil_profile["properties"].get(attr, default)
        for alias in (
            attr,
            {
                "ph": "soil_ph",
                "ph_water": "ph_h2o",
                "texture_class": "soil_texture",
                "available_water_capacity": "available_water_capacity_mm_m",
                "depth_cm": "effective_rooting_depth_cm",
            }.get(attr, attr),
            {"ph": "ph_h2o", "cation_exchange_capacity": "cec_cmol_kg"}.get(attr, attr),
        ):
            if alias in soil_profile and soil_profile[alias] is not None:
                return soil_profile[alias]
        return default

    attr_map = {
        "ph": "ph",
        "ph_water": "ph",
        "texture_class": "usda_texture_class",
        "organic_carbon_pct": "organic_carbon_pct",
        "cation_exchange_capacity": "cation_exchange_capacity_cmol_kg",
        "available_water_capacity": "plant_available_water_capacity_mm",
        "depth_cm": "soil_depth_to_bedrock_cm",
    }
    target_attr = attr_map.get(attr, attr)
    for candidate in (target_attr, attr, "ph_h2o", "soil_texture", "cec_cmol_kg", "available_water_capacity_mm_m", "effective_rooting_depth_cm"):
        if candidate == target_attr or candidate == attr or candidate in {
            "ph_h2o",
            "soil_texture",
            "cec_cmol_kg",
            "available_water_capacity_mm_m",
            "effective_rooting_depth_cm",
        }:
            if hasattr(soil_profile, candidate):
                prop = getattr(soil_profile, candidate)
                if prop is None:
                    continue
                if hasattr(prop, "value"):
                    return prop.value
                if hasattr(prop, "value_display") and prop.value_display:
                    return prop.value_display
                if hasattr(prop, "value_code") and prop.value_code:
                    return prop.value_code
                return prop
    return default


def _extract_optional_float(soil_profile: Any, *attrs: str) -> Optional[float]:
    for attr in attrs:
        val = _extract_soil_prop(soil_profile, attr, default=None)
        if val is not None:
            try:
                return float(val)
            except (TypeError, ValueError):
                continue
    return None


def _compute_composite_risk(risks: List[Dict[str, Any]]) -> tuple[float, str]:
    weights = {
        "low": 15.0,
        "moderate": 45.0,
        "high": 75.0,
        "extreme": 95.0,
        "critical": 95.0,
    }
    scores = [weights.get(str(r.get("risk_level", "low")).lower(), 20.0) for r in risks]
    if not scores:
        return 0.0, "low"
    composite = round(0.4 * max(scores) + 0.6 * (sum(scores) / len(scores)), 1)
    if composite >= 75.0:
        tier = "high"
    elif composite >= 40.0:
        tier = "moderate"
    else:
        tier = "low"
    return composite, tier


class YieldRiskEngine:
    """Computes DES APY crop yield baselines and multi-dimensional biophysical screening."""

    @staticmethod
    def calculate_apy_district_baseline(
        district: str,
        crop_code: str,
        db: Optional[Session] = None,
        apy_csv_path: Optional[Path | str] = None,
    ) -> Dict[str, Any]:
        """
        Calculate historical district yield baseline from cleaned canonical APY CSV.
        Strictly empirical; returns unavailable when CSV is missing (no fake fallback yields).
        """
        apy_file = (
            Path(apy_csv_path)
            if apy_csv_path is not None
            else MAHARASHTRA_APY_CANONICAL_CSV
        )

        if not apy_file.exists():
            return {
                "status": "unavailable",
                "geographical_unit": district,
                "district": district,
                "crop_code": crop_code,
                "season": "Kharif / Rabi",
                "data_period": "Unavailable",
                "sample_seasons_count": 0,
                "historical_mean_t_ha": None,
                "historical_median_t_ha": None,
                "historical_p10_t_ha": None,
                "historical_p25_t_ha": None,
                "historical_p90_t_ha": None,
                "min_recorded_t_ha": None,
                "max_recorded_t_ha": None,
                "historical_std_dev": None,
                "disclaimer": (
                    f"Canonical APY dataset not found at {apy_file}; empirical yield "
                    f"baseline unavailable (synthetic fallback disabled)."
                ),
            }

        try:
            df = pd.read_csv(apy_file)

            crop_norm = (crop_code or "").lower()
            aliases = [crop_norm]
            if db is not None:
                crop_rec = (
                    db.query(RashkarCanonicalCropModel)
                    .filter(RashkarCanonicalCropModel.crop_code == crop_norm)
                    .first()
                )
                if crop_rec and crop_rec.apy_alias_list:
                    aliases.extend([str(a).lower() for a in crop_rec.apy_alias_list])

            if crop_norm in BUILTIN_APY_ALIAS_MAP:
                aliases.extend(BUILTIN_APY_ALIAS_MAP[crop_norm])

            aliases = sorted({a for a in aliases if a})
            pattern = "|".join(re.escape(a) for a in aliases)

            crop_filter = df["crop_name_raw"].astype(str).str.lower().str.contains(
                pattern, regex=True
            )
            dist_filter = df["district"].astype(str).str.lower() == district.lower()
            subset = df[crop_filter & dist_filter]

            if subset.empty or len(subset) < 3:
                subset = df[crop_filter]
                geo_unit = f"statewide_maharashtra_{crop_norm}"
            else:
                geo_unit = f"district_{district.lower()}_{crop_norm}"

            yield_col = (
                "calculated_yield_t_ha"
                if "calculated_yield_t_ha" in subset.columns
                else "yield_t_ha"
            )
            yields = subset[yield_col].dropna()
            yields = yields[yields > 0.05]

            if yields.empty:
                return {
                    "status": "insufficient_data",
                    "geographical_unit": geo_unit,
                    "district": district,
                    "crop_code": crop_code,
                    "season": "Kharif / Rabi",
                    "data_period": "N/A",
                    "sample_seasons_count": 0,
                    "historical_mean_t_ha": None,
                    "historical_median_t_ha": None,
                    "historical_p10_t_ha": None,
                    "historical_p25_t_ha": None,
                    "historical_p90_t_ha": None,
                    "min_recorded_t_ha": None,
                    "max_recorded_t_ha": None,
                    "historical_std_dev": None,
                    "disclaimer": "No positive harvest yield records available.",
                }

            mean_val = round(float(yields.mean()), 3)
            median_val = round(float(yields.median()), 3)
            std_val = round(float(yields.std()), 3) if len(yields) > 1 else 0.15
            p10_val = round(float(yields.quantile(0.10)), 3)
            p25_val = round(float(yields.quantile(0.25)), 3)
            p90_val = round(float(yields.quantile(0.90)), 3)
            min_val = round(float(yields.min()), 3)
            max_val = round(float(yields.max()), 3)
            min_yr = (
                int(subset["crop_year"].min()) if "crop_year" in subset.columns else 1997
            )
            max_yr = (
                int(subset["crop_year"].max()) if "crop_year" in subset.columns else 2021
            )

            return {
                "status": "district_historical_baseline",
                "geographical_unit": geo_unit,
                "district": district,
                "crop_code": crop_code,
                "season": "Kharif / Rabi",
                "data_period": f"{min_yr}-{max_yr}",
                "sample_seasons_count": len(yields),
                "historical_mean_t_ha": mean_val,
                "historical_median_t_ha": median_val,
                "historical_p10_t_ha": p10_val,
                "historical_p25_t_ha": p25_val,
                "historical_p90_t_ha": p90_val,
                "min_recorded_t_ha": min_val,
                "max_recorded_t_ha": max_val,
                "historical_std_dev": std_val,
                "disclaimer": (
                    "District-level statistical baseline derived from official APY records "
                    "(1997-2021). Plot-level numerical prediction is disabled pending verified "
                    "harvest labels."
                ),
            }
        except Exception as exc:
            return {
                "status": "error_calculating_baseline",
                "geographical_unit": district,
                "district": district,
                "crop_code": crop_code,
                "season": "Kharif / Rabi",
                "data_period": "N/A",
                "sample_seasons_count": 0,
                "historical_mean_t_ha": None,
                "historical_median_t_ha": None,
                "historical_p10_t_ha": None,
                "historical_p25_t_ha": None,
                "historical_p90_t_ha": None,
                "min_recorded_t_ha": None,
                "max_recorded_t_ha": None,
                "historical_std_dev": None,
                "disclaimer": f"Error calculating baseline: {exc}",
            }

    @staticmethod
    def assess_yield_risk(
        farm_context: Optional[Dict[str, Any]] = None,
        crop_cycle: Optional[RashkarCropCycleModel] = None,
        soil_profile: Optional[Any] = None,
        weather_summary: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
        apy_csv_path: Optional[Path | str] = None,
        farmer_confirmed_stage: Optional[str] = None,
        as_of_utc: Optional[datetime] = None,
    ) -> YieldRiskResponse:
        """Evaluate multi-dimensional biophysical yield risk without silent data fabrication."""
        ctx = farm_context or {}
        if as_of_utc is not None:
            now_dt_utc = (
                as_of_utc.replace(tzinfo=UTC_ZONE)
                if as_of_utc.tzinfo is None
                else as_of_utc.astimezone(UTC_ZONE)
            )
            now_dt_ist = now_dt_utc.astimezone(IST_ZONE)
        else:
            now_dt_utc = now_utc()
            now_dt_ist = now_dt_utc.astimezone(IST_ZONE)

        farm_id = str(ctx.get("farm_id") or "")
        owner_id = str(ctx.get("owner_id") or "")
        farm_name = str(ctx.get("farm_name") or "Registered Farm")
        district = str(ctx.get("district") or "Pune")
        taluka = str(ctx.get("taluka") or district)
        loc_display = f"{taluka}, {district}"

        if crop_cycle is None:
            return YieldRiskResponse(
                status="NO_ACTIVE_CROP",
                has_active_crop=False,
                needs_crop_registration=True,
                message=(
                    "No active crop cycle registered for this farm. Register an active crop "
                    "cycle before running yield baseline and stress risk screening."
                ),
                farm_id=farm_id,
                farm_name=farm_name,
                location_display=loc_display,
                generated_at_utc=to_ist_iso(now_dt_utc),
                provenance={
                    "status": "NO_ACTIVE_CROP",
                    "farm_id": farm_id,
                    "needs_crop_registration": True,
                },
                audit_logged=False,
            )

        crop_code = crop_cycle.crop_code.lower()
        canonical_crop = (
            db.query(RashkarCanonicalCropModel)
            .filter(RashkarCanonicalCropModel.crop_code == crop_code)
            .first()
            if db is not None
            else None
        )
        crop_name = (
            canonical_crop.common_name_en if canonical_crop else crop_code.capitalize()
        )
        acres = (
            crop_cycle.planted_area_acres
            if crop_cycle.planted_area_acres is not None
            else ctx.get("total_area_acres")
        )
        irrigation = str(
            crop_cycle.irrigation_type or ctx.get("irrigation_type") or "unknown"
        )

        if weather_summary is None:
            return YieldRiskResponse(
                status="WEATHER_UNAVAILABLE",
                has_active_crop=True,
                needs_crop_registration=False,
                message=(
                    "Meteorological summary unavailable for yield risk assessment; paused "
                    "without synthetic rainfall or temperature fallback."
                ),
                farm_id=farm_id,
                farm_name=farm_name,
                crop_code=crop_code,
                crop_name=crop_name,
                sowing_date=(
                    crop_cycle.sowing_date.strftime("%Y-%m-%d")
                    if crop_cycle.sowing_date
                    else None
                ),
                total_area_acres=acres,
                irrigation_type=irrigation.capitalize(),
                location_display=loc_display,
                generated_at_utc=to_ist_iso(now_dt_utc),
                provenance={"status": "WEATHER_UNAVAILABLE", "farm_id": farm_id},
                audit_logged=False,
            )

        effective_stage_override = farmer_confirmed_stage or crop_cycle.current_stage_code
        if db is not None:
            stage_info = CropStageService.estimate_crop_stage(
                db=db,
                crop_code=crop_code,
                sowing_date=crop_cycle.sowing_date,
                farmer_confirmed_stage=effective_stage_override,
                as_of_date=now_dt_ist.date(),
            )
        else:
            das_val = (
                max(0, (now_dt_ist.date() - crop_cycle.sowing_date).days)
                if crop_cycle.sowing_date is not None
                else 0
            )
            stage_info = {
                "stage_code": effective_stage_override or "GENERAL_GROWTH",
                "stage_name_en": effective_stage_override or "Vegetative / General Growth",
                "stage_name_mr": "वाढीची अवस्था",
                "days_after_sowing": das_val,
                "stage_source": (
                    "farmer_confirmed" if effective_stage_override else "generic_heuristic"
                ),
                "drought_sensitivity": "medium",
                "heat_sensitivity": "medium",
            }

        consecutive_dry_days = int(weather_summary.get("consecutive_dry_days", 0))
        rolling_3d_rain = float(weather_summary.get("rolling_3d_rain_mm", 0.0))
        recent_rh = float(weather_summary.get("rh_recent_pct", 50.0))
        recent_tmax = float(weather_summary.get("tmax_recent_c", 30.0))
        weather_src = str(weather_summary.get("data_source") or "ProvidedWeatherSummary")

        risks: List[Dict[str, Any]] = []

        # A. Dry Spell / Moisture Deficit
        if consecutive_dry_days >= 10:
            dry_level = (
                "high"
                if stage_info.get("drought_sensitivity") in ("high", "critical")
                else "moderate"
            )
            dry_drivers = [
                f"{consecutive_dry_days} consecutive dry days recorded (< 2.5 mm/day)."
            ]
            if dry_level == "high":
                dry_drivers.append(
                    f"Occurring during moisture-critical {stage_info['stage_name_en']} stage."
                )
        else:
            dry_level = "low"
            dry_drivers = [
                f"Moisture is currently adequate ({consecutive_dry_days} dry days)."
            ]

        risks.append(
            {
                "risk_dimension": "weather_dry_spell",
                "risk_level": dry_level,
                "time_horizon": "next_7_days",
                "impact_severity": (
                    "high"
                    if dry_level == "high"
                    else "moderate"
                    if dry_level == "moderate"
                    else "low"
                ),
                "confidence": "high",
                "drivers": dry_drivers,
                "evidence_provenance": [
                    {"source": weather_src, "variable": "daily_rainfall", "status": "VERIFIED"}
                ],
                "recommended_actions": (
                    [
                        {
                            "title": "Protective Drip Irrigation Scheduling",
                            "description": (
                                "Provide light irrigation at 3-day intervals during morning "
                                "hours to prevent root-zone wilting."
                            ),
                        }
                    ]
                    if dry_level != "low"
                    else []
                ),
            }
        )

        # B. Excess Rainfall / Waterlogging
        waterlog_level = (
            "high"
            if rolling_3d_rain > 65.0
            else "moderate"
            if rolling_3d_rain > 40.0
            else "low"
        )
        risks.append(
            {
                "risk_dimension": "excess_rainfall_waterlogging",
                "risk_level": waterlog_level,
                "time_horizon": "next_72_hours",
                "impact_severity": "high" if waterlog_level == "high" else "low",
                "confidence": "high",
                "drivers": [
                    f"Cumulative 3-day rainfall is {rolling_3d_rain} mm in {taluka}."
                ],
                "evidence_provenance": [
                    {"source": weather_src, "variable": "rainfall_3d_sum", "status": "VERIFIED"}
                ],
                "recommended_actions": [],
            }
        )

        # C. Soil Constraints (zero pH/texture fabrication when missing)
        ph_val = _extract_optional_float(soil_profile, "ph", "soil_ph", "ph_water")
        texture_raw = _extract_soil_prop(soil_profile, "texture_class", default=None)
        texture_name = str(texture_raw) if texture_raw else None

        if ph_val is None:
            ph_status = "Data Not Available"
            soil_level = "low"
            soil_drivers = [
                "Soil pH data is not available from current satellite/ground observations. Soil testing recommended."
            ]
        else:
            ph_status = (
                "Optimal"
                if 6.5 <= ph_val <= 8.2
                else "Moderately Alkaline"
                if ph_val > 8.2
                else "Acidic"
            )
            soil_level = "moderate" if ph_val > 8.3 or ph_val < 6.0 else "low"
            tex_clause = f" Texture: {texture_name}." if texture_name else ""
            soil_drivers = [f"Soil pH is {ph_val:.1f} ({ph_status}).{tex_clause}"]

        risks.append(
            {
                "risk_dimension": "soil_constraint",
                "risk_level": soil_level,
                "time_horizon": "season_long",
                "impact_severity": "moderate" if soil_level == "moderate" else "low",
                "confidence": "high" if ph_val is not None else "low",
                "drivers": soil_drivers,
                "evidence_provenance": [
                    {
                        "source": "CropNet_Soil_Profile_Adapter",
                        "variable": "ph_and_texture",
                        "status": "VERIFIED" if ph_val is not None else "MISSING",
                    }
                ],
                "recommended_actions": [],
            }
        )

        # D. Crop Heat Stress
        heat_level = (
            "high"
            if recent_tmax >= 38.0
            else "moderate"
            if recent_tmax >= 35.0
            else "low"
        )
        risks.append(
            {
                "risk_dimension": "crop_heat_stress",
                "risk_level": heat_level,
                "time_horizon": "next_48_hours",
                "impact_severity": (
                    "high"
                    if heat_level == "high"
                    else "moderate"
                    if heat_level == "moderate"
                    else "low"
                ),
                "confidence": "high",
                "drivers": [f"Daytime maximum temperature reaches {recent_tmax}°C."],
                "evidence_provenance": [
                    {"source": weather_src, "variable": "tmax_2m", "status": "VERIFIED"}
                ],
                "recommended_actions": (
                    [
                        {
                            "title": "Foliar Nutrition / Canopy Cooling",
                            "description": (
                                "Spray 1.5% Potassium Nitrate (KNO3) in early morning "
                                "to reduce leaf transpiration."
                            ),
                        }
                    ]
                    if heat_level != "low"
                    else []
                ),
            }
        )

        # E. Biological / Pest Disease Watch
        pest_level = (
            "moderate" if recent_rh >= 75.0 and recent_tmax <= 32.0 else "low"
        )
        risks.append(
            {
                "risk_dimension": "pest_disease_watch",
                "risk_level": pest_level,
                "time_horizon": "next_7_days",
                "impact_severity": "moderate" if pest_level == "moderate" else "low",
                "confidence": "moderate",
                "drivers": [
                    (
                        f"Relative humidity is {recent_rh}% with temperature {recent_tmax}°C. "
                        f"{'High humidity favors fungal foliar pathogens.' if pest_level == 'moderate' else 'Prevailing weather does not favor severe pest escalation.'}"
                    )
                ],
                "evidence_provenance": [
                    {"source": weather_src, "variable": "rh_and_temp", "status": "VERIFIED"}
                ],
                "recommended_actions": [],
            }
        )

        # 5. Historical District Baseline
        baseline_data = YieldRiskEngine.calculate_apy_district_baseline(
            district=district,
            crop_code=crop_code,
            db=db,
            apy_csv_path=apy_csv_path,
        )

        # 6. Soil Suitability Profile (strictly preserve None for unmeasured values)
        normal_rain = DISTRICT_IMD_NORMALS_MM.get(district.lower())
        oc_val = _extract_optional_float(soil_profile, "organic_carbon_pct")
        cec_val = _extract_optional_float(
            soil_profile, "cation_exchange_capacity", "cec_cmol_kg"
        )
        awc_val = _extract_optional_float(
            soil_profile, "available_water_capacity", "available_water_capacity_mm_m"
        )
        depth_val = _extract_optional_float(
            soil_profile, "depth_cm", "effective_rooting_depth_cm"
        )

        soil_prov = _extract_soil_prop(soil_profile, "data_provenance", default=None)
        if ph_val is None and oc_val is None and cec_val is None and awc_val is None:
            verdict = "Unavailable — Soil profile metrics missing"
            provenance_label = "Soil data unavailable (unsampled farm coordinate)"
        elif ph_val is not None and 6.0 <= ph_val <= 8.3:
            verdict = "Suitable based on available soil measurements"
            provenance_label = str(
                soil_prov or "CropNet Soil Profile & IMD Climate Normals"
            )
        elif ph_val is not None:
            verdict = f"Constraint noted: {ph_status} (pH {ph_val:.1f})"
            provenance_label = str(
                soil_prov or "CropNet Soil Profile & IMD Climate Normals"
            )
        else:
            verdict = "Partial soil data — Soil pH test recommended"
            provenance_label = str(soil_prov or "Partial Farm Soil Record")

        soil_analysis = SoilSuitabilityAnalysis(
            soil_texture=texture_name,
            soil_ph=ph_val,
            ph_status=ph_status,
            organic_carbon_pct=oc_val,
            cation_exchange_capacity=cec_val,
            available_water_capacity_mm_m=awc_val,
            effective_rooting_depth_cm=depth_val,
            climate_normal_rainfall_mm=normal_rain,
            suitability_verdict=verdict,
            data_provenance=provenance_label,
        )

        awc_clause = (
            f"Soil AWC: {awc_val} mm/m." if awc_val is not None else "Soil AWC: unavailable."
        )
        recommendations: List[ActionableRecommendation] = [
            ActionableRecommendation(
                recommendation_id="REC_MOISTURE_MGNT",
                title="Conserve Root-Zone Moisture with Stubble Mulching",
                description=(
                    "Apply 5 cm thick crop residue mulch along crop rows to suppress "
                    "evaporative loss during dry spell."
                ),
                why_recommended=(
                    f"{consecutive_dry_days} consecutive dry days recorded; mulching reduces "
                    f"soil temperature by 3-4°C and retains soil moisture."
                ),
                supporting_data=f"Dry spell: {consecutive_dry_days} days. {awc_clause}",
                evidence_source="ICAR-Central Research Institute for Dryland Agriculture (CRIDA)",
                urgency="High" if dry_level == "high" else "Preventative",
                limitations=(
                    "Effective only when applied before complete root-zone soil moisture exhaustion."
                ),
            ),
            ActionableRecommendation(
                recommendation_id="REC_FOLIAR_POTASSIUM",
                title="Apply 1.5% Potassium Nitrate (KNO3) Foliar Spray",
                description=(
                    "Spray early in the morning when stomata are open. Potassium regulates "
                    "guard cells, preventing excessive wilting under heat."
                ),
                why_recommended=(
                    "Enhances drought and thermal tolerance during sensitive vegetative and flowering phases."
                ),
                supporting_data=(
                    f"Max daytime temperature: {recent_tmax}°C. "
                    f"Crop stage: {stage_info['stage_name_en']}."
                ),
                evidence_source="Vasantrao Naik Marathwada Krishi Vidyapeeth (VNMKV) Agroadvisory",
                urgency="Medium",
                limitations="Avoid spraying during peak noon heat (11:30 AM to 3:30 PM).",
            ),
        ]

        ml_gate = {
            "prediction_status": "REQUIRES_FARM_HARVEST_LABELS",
            "historical_baseline_available": (
                baseline_data.get("historical_mean_t_ha") is not None
            ),
            "farm_level_supervised_model": "LOCKED_PENDING_CCE_LABELS",
            "ethical_safeguard": (
                "Predicting exact farm-level harvest tonnage without verified ground-truth harvest "
                "labels over multiple seasons violates scientific rigor. Rashkar displays auditable "
                "district historical percentiles (P10 to P90) alongside real-time stress screening."
            ),
            "historical_p10_t_ha": baseline_data.get("historical_p10_t_ha"),
            "historical_p25_t_ha": baseline_data.get("historical_p25_t_ha"),
            "historical_mean_t_ha": baseline_data.get("historical_mean_t_ha"),
            "historical_p90_t_ha": baseline_data.get("historical_p90_t_ha"),
        }

        mean_t_ha = baseline_data.get("historical_mean_t_ha")
        if mean_t_ha is not None:
            baseline_clause = (
                f"The historical average yield for this crop in {district} is {mean_t_ha} "
                f"tonnes/ha based on {baseline_data.get('sample_seasons_count', 0)} official "
                f"APY records ({baseline_data.get('data_period', 'N/A')})."
            )
        else:
            baseline_clause = (
                f"Historical APY yield baseline for this crop in {district} is currently unavailable."
            )
        ph_clause = (
            f"Soil pH ({ph_val:.1f}) is {ph_status.lower()}."
            if ph_val is not None
            else "Soil pH measurement is unavailable; soil sampling is recommended."
        )
        narrative = (
            f"Overall agronomic conditions for {crop_code.capitalize()} on {farm_name} in "
            f"{district} are "
            f"{'challenging due to active dry spell stress' if dry_level == 'high' else 'fair with moderate weather stress' if dry_level == 'moderate' else 'favorable'}. "
            f"The crop is currently in the {stage_info['stage_name_en']} stage "
            f"(DAS {stage_info['days_after_sowing']}). "
            f"{baseline_clause} {ph_clause}"
        )

        composite_score, composite_tier = _compute_composite_risk(risks)
        risk_items = [RiskItem(**r) for r in risks]
        provenance_summary = {
            "weather_source": weather_src,
            "soil_provenance": provenance_label,
            "apy_geographical_unit": baseline_data.get("geographical_unit"),
            "apy_status": baseline_data.get("status"),
            "stage_source": stage_info.get("stage_source"),
        }

        audit_logged = False
        if db is not None and farm_id and owner_id:
            benchmark_tier = (
                "unavailable"
                if baseline_data.get("historical_mean_t_ha") is None
                else "statewide"
                if str(baseline_data.get("geographical_unit", "")).startswith("statewide")
                else "district"
            )
            log_entry = RashkarYieldAssessmentLogModel(
                id=f"yra_{uuid.uuid4().hex[:12]}",
                farm_id=farm_id,
                owner_id=owner_id,
                crop_code=crop_code,
                district=district,
                assessed_at_utc=now_dt_utc.replace(tzinfo=None),
                benchmark_tier=benchmark_tier,
                apy_mean_t_ha=baseline_data.get("historical_mean_t_ha"),
                apy_median_t_ha=baseline_data.get("historical_median_t_ha"),
                apy_sample_count=int(baseline_data.get("sample_seasons_count", 0)),
                composite_risk_score=composite_score,
                composite_risk_tier=composite_tier,
                prediction_lock_status="LOCKED_PENDING_CCE_LABELS",
                provenance_summary=provenance_summary,
            )
            db.add(log_entry)
            db.commit()
            audit_logged = True

        return YieldRiskResponse(
            status="OK",
            has_active_crop=True,
            needs_crop_registration=False,
            farm_id=farm_id,
            farm_name=farm_name,
            plot_id=str(ctx.get("plot_id") or crop_cycle.id),
            crop_code=crop_code,
            crop_name=crop_name,
            sowing_date=(
                crop_cycle.sowing_date.strftime("%Y-%m-%d")
                if crop_cycle.sowing_date
                else None
            ),
            days_after_sowing=int(stage_info["days_after_sowing"]),
            total_area_acres=acres,
            irrigation_type=irrigation.capitalize(),
            location_display=loc_display,
            generated_at_utc=to_ist_iso(now_dt_utc),
            timezone="Asia/Kolkata",
            yield_baseline=HistoricalYieldBaseline(**baseline_data),
            suitability_analysis=soil_analysis,
            coverage={
                "crop_status": (
                    canonical_crop.support_level
                    if canonical_crop
                    else "supported_rules_and_baselines"
                ),
                "district": district,
                "taluka": taluka,
                "geographical_unit": baseline_data.get("geographical_unit"),
            },
            crop_stage=stage_info,
            risks=risk_items,
            composite_risk_score=composite_score,
            composite_risk_tier=composite_tier,
            ml_prediction_gate=ml_gate,
            recommendations=recommendations,
            farmer_narrative_explanation=narrative,
            provenance=provenance_summary,
            audit_logged=audit_logged,
        )


__all__ = ["YieldRiskEngine", "DISTRICT_IMD_NORMALS_MM", "BUILTIN_APY_ALIAS_MAP"]
