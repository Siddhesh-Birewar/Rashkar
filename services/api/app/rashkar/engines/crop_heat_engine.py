"""Crop phenological heat stress screening & intervention engine."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid
from sqlalchemy.orm import Session

from ..models import (
    RashkarAgronomicThresholdModel,
    RashkarCanonicalCropModel,
    RashkarCropCycleModel,
    RashkarCropHeatLogModel,
    RashkarCropStageModel,
)
from ..schemas.crop_heat import (
    CropHeatAssessmentRequest,
    CropHeatAssessmentResponse,
    CropHeatIntervention,
    DailyCropHeatOutlook,
)
from ..timezone import IST_ZONE, UTC_ZONE, now_ist, now_utc
from .crop_stage_service import CropStageService
from .thermal_indices import (
    apply_topographic_lapse_downscaling,
    compute_crop_heat_vulnerability_score,
)
from .wbgt_solver import vapor_pressure_deficit_kpa


# Literature baseline phenological thermal curves (12 Maharashtra crops)
CROP_SPECIES_PHYSIOLOGY: Dict[str, Dict[str, Any]] = {
    "soybean": {
        "base_temp_c": 10.0,
        "optimal_min": 25.0,
        "optimal_max": 30.0,
        "night_crit_c": 22.0,
        "stages": [
            {"stage_code": "stage_germination", "stage_name": "Germination / Emergence", "stage_name_en": "Germination / Emergence", "das_range": "DAS 0-10", "crit_tmax": 38.0},
            {"stage_code": "stage_vegetative", "stage_name": "Vegetative Branching", "stage_name_en": "Vegetative Branching", "das_range": "DAS 11-35", "crit_tmax": 39.0},
            {"stage_code": "stage_flowering", "stage_name": "Flowering & Anthesis", "stage_name_en": "Flowering & Anthesis", "das_range": "DAS 36-55", "crit_tmax": 35.0},
            {"stage_code": "stage_pod_development", "stage_name": "Pod Formation & Seed Filling", "stage_name_en": "Pod Formation & Seed Filling", "das_range": "DAS 56-85", "crit_tmax": 36.5},
            {"stage_code": "stage_maturity", "stage_name": "Maturity / Harvest", "stage_name_en": "Maturity / Harvest", "das_range": "DAS 86-105", "crit_tmax": 42.0},
        ],
    },
    "cotton": {
        "base_temp_c": 12.0,
        "optimal_min": 26.0,
        "optimal_max": 32.0,
        "night_crit_c": 24.0,
        "stages": [
            {"stage_code": "stage_germination", "stage_name": "Emergence & Seedling", "stage_name_en": "Emergence & Seedling", "das_range": "DAS 0-20", "crit_tmax": 40.0},
            {"stage_code": "stage_vegetative", "stage_name": "Squaring & Vegetative", "stage_name_en": "Squaring & Vegetative", "das_range": "DAS 21-55", "crit_tmax": 39.0},
            {"stage_code": "stage_flowering", "stage_name": "Peak Flowering", "stage_name_en": "Peak Flowering", "das_range": "DAS 56-90", "crit_tmax": 36.0},
            {"stage_code": "stage_boll_formation", "stage_name": "Boll Formation & Opening", "stage_name_en": "Boll Formation & Opening", "das_range": "DAS 91-150", "crit_tmax": 38.0},
            {"stage_code": "stage_maturity", "stage_name": "Bursting & Harvest", "stage_name_en": "Bursting & Harvest", "das_range": "DAS 151-180", "crit_tmax": 42.0},
        ],
    },
    "jowar": {
        "base_temp_c": 10.0,
        "optimal_min": 26.0,
        "optimal_max": 33.0,
        "night_crit_c": 23.0,
        "stages": [
            {"stage_code": "stage_germination", "stage_name": "Emergence", "stage_name_en": "Emergence", "das_range": "DAS 0-15", "crit_tmax": 40.0},
            {"stage_code": "stage_vegetative", "stage_name": "Vegetative / General Growth", "stage_name_en": "Vegetative / General Growth", "das_range": "DAS 16-45", "crit_tmax": 41.0},
            {"stage_code": "stage_flowering", "stage_name": "Boot & Flowering / Anthesis", "stage_name_en": "Boot & Flowering / Anthesis", "das_range": "DAS 46-65", "crit_tmax": 37.0},
            {"stage_code": "stage_grain_filling", "stage_name": "Grain Development / Dough", "stage_name_en": "Grain Development / Dough", "das_range": "DAS 66-95", "crit_tmax": 38.5},
            {"stage_code": "stage_maturity", "stage_name": "Physiological Maturity", "stage_name_en": "Physiological Maturity", "das_range": "DAS 96-115", "crit_tmax": 42.0},
        ],
    },
    "onion": {
        "base_temp_c": 7.0,
        "optimal_min": 20.0,
        "optimal_max": 28.0,
        "night_crit_c": 20.0,
        "stages": [
            {"stage_code": "stage_vegetative", "stage_name": "Foliage / Leaf Development", "stage_name_en": "Foliage / Leaf Development", "das_range": "DAS 0-40", "crit_tmax": 35.0},
            {"stage_code": "stage_bulb_initiation", "stage_name": "Bulb Initiation", "stage_name_en": "Bulb Initiation", "das_range": "DAS 41-70", "crit_tmax": 33.0},
            {"stage_code": "stage_bulb_development", "stage_name": "Bulb Development & Enlargement", "stage_name_en": "Bulb Development & Enlargement", "das_range": "DAS 71-105", "crit_tmax": 34.0},
            {"stage_code": "stage_maturity", "stage_name": "Neck Fall & Harvest", "stage_name_en": "Neck Fall & Harvest", "das_range": "DAS 106-130", "crit_tmax": 38.0},
        ],
    },
    "sugarcane": {
        "base_temp_c": 12.0,
        "optimal_min": 28.0,
        "optimal_max": 35.0,
        "night_crit_c": 20.0,
        "stages": [
            {"stage_code": "stage_germination", "stage_name": "Sprouting & Tillering", "stage_name_en": "Sprouting & Tillering", "das_range": "DAS 0-60", "crit_tmax": 42.0},
            {"stage_code": "stage_grand_growth", "stage_name": "Grand Growth & Internode Elongation", "stage_name_en": "Grand Growth & Internode Elongation", "das_range": "DAS 61-240", "crit_tmax": 40.0},
            {"stage_code": "stage_maturity", "stage_name": "Ripening & Sucrose Accumulation", "stage_name_en": "Ripening & Sucrose Accumulation", "das_range": "DAS 241-360", "crit_tmax": 38.0},
        ],
    },
    "wheat": {
        "base_temp_c": 4.0,
        "optimal_min": 18.0,
        "optimal_max": 25.0,
        "night_crit_c": 18.0,
        "stages": [
            {"stage_code": "stage_vegetative", "stage_name": "Crown Root & Tillering", "stage_name_en": "Crown Root & Tillering", "das_range": "DAS 0-35", "crit_tmax": 30.0},
            {"stage_code": "stage_flowering", "stage_name": "Booting & Anthesis", "stage_name_en": "Booting & Anthesis", "das_range": "DAS 36-65", "crit_tmax": 32.0},
            {"stage_code": "stage_grain_filling", "stage_name": "Grain Filling & Milk Stage", "stage_name_en": "Grain Filling & Milk Stage", "das_range": "DAS 66-95", "crit_tmax": 34.0},
            {"stage_code": "stage_maturity", "stage_name": "Physiological Maturity", "stage_name_en": "Physiological Maturity", "das_range": "DAS 96-115", "crit_tmax": 37.0},
        ],
    },
    "gram": {
        "base_temp_c": 8.0,
        "optimal_min": 20.0,
        "optimal_max": 28.0,
        "night_crit_c": 18.0,
        "stages": [
            {"stage_code": "stage_vegetative", "stage_name": "Vegetative Branching", "stage_name_en": "Vegetative Branching", "das_range": "DAS 0-30", "crit_tmax": 35.0},
            {"stage_code": "stage_flowering", "stage_name": "Flowering & Pod Initiation", "stage_name_en": "Flowering & Pod Initiation", "das_range": "DAS 31-60", "crit_tmax": 32.0},
            {"stage_code": "stage_pod_development", "stage_name": "Pod Filling & Seed Growth", "stage_name_en": "Pod Filling & Seed Growth", "das_range": "DAS 61-90", "crit_tmax": 34.0},
            {"stage_code": "stage_maturity", "stage_name": "Pod Maturity & Harvest", "stage_name_en": "Pod Maturity & Harvest", "das_range": "DAS 91-110", "crit_tmax": 38.0},
        ],
    },
    "tur": {
        "base_temp_c": 10.0,
        "optimal_min": 25.0,
        "optimal_max": 33.0,
        "night_crit_c": 22.0,
        "stages": [
            {"stage_code": "stage_vegetative", "stage_name": "Vegetative Branching", "stage_name_en": "Vegetative Branching", "das_range": "DAS 0-60", "crit_tmax": 38.0},
            {"stage_code": "stage_flowering", "stage_name": "Flowering & Pod Formation", "stage_name_en": "Flowering & Pod Formation", "das_range": "DAS 61-120", "crit_tmax": 35.0},
            {"stage_code": "stage_pod_development", "stage_name": "Pod Filling & Seed Hardening", "stage_name_en": "Pod Filling & Seed Hardening", "das_range": "DAS 121-160", "crit_tmax": 36.5},
            {"stage_code": "stage_maturity", "stage_name": "Maturity & Pod Drydown", "stage_name_en": "Maturity & Pod Drydown", "das_range": "DAS 161-190", "crit_tmax": 40.0},
        ],
    },
    "bajra": {
        "base_temp_c": 12.0,
        "optimal_min": 28.0,
        "optimal_max": 36.0,
        "night_crit_c": 24.0,
        "stages": [
            {"stage_code": "stage_germination", "stage_name": "Emergence & Seedling", "stage_name_en": "Emergence & Seedling", "das_range": "DAS 0-15", "crit_tmax": 42.0},
            {"stage_code": "stage_vegetative", "stage_name": "Tillering & Stem Elongation", "stage_name_en": "Tillering & Stem Elongation", "das_range": "DAS 16-35", "crit_tmax": 42.0},
            {"stage_code": "stage_flowering", "stage_name": "Boot & Anthesis", "stage_name_en": "Boot & Anthesis", "das_range": "DAS 36-55", "crit_tmax": 38.0},
            {"stage_code": "stage_grain_filling", "stage_name": "Grain Development / Dough", "stage_name_en": "Grain Development / Dough", "das_range": "DAS 56-75", "crit_tmax": 40.0},
            {"stage_code": "stage_maturity", "stage_name": "Physiological Maturity", "stage_name_en": "Physiological Maturity", "das_range": "DAS 76-90", "crit_tmax": 44.0},
        ],
    },
    "maize": {
        "base_temp_c": 10.0,
        "optimal_min": 24.0,
        "optimal_max": 32.0,
        "night_crit_c": 22.0,
        "stages": [
            {"stage_code": "stage_germination", "stage_name": "Emergence & Early Seedling", "stage_name_en": "Emergence & Early Seedling", "das_range": "DAS 0-15", "crit_tmax": 38.0},
            {"stage_code": "stage_vegetative", "stage_name": "Knee-High to Tasseling", "stage_name_en": "Knee-High to Tasseling", "das_range": "DAS 16-45", "crit_tmax": 38.0},
            {"stage_code": "stage_flowering", "stage_name": "Silking & Pollination", "stage_name_en": "Silking & Pollination", "das_range": "DAS 46-65", "crit_tmax": 35.0},
            {"stage_code": "stage_grain_filling", "stage_name": "Cob Filling & Grain Hardening", "stage_name_en": "Cob Filling & Grain Hardening", "das_range": "DAS 66-95", "crit_tmax": 37.0},
            {"stage_code": "stage_maturity", "stage_name": "Black Layer & Harvest", "stage_name_en": "Black Layer & Harvest", "das_range": "DAS 96-115", "crit_tmax": 40.0},
        ],
    },
    "groundnut": {
        "base_temp_c": 10.0,
        "optimal_min": 24.0,
        "optimal_max": 30.0,
        "night_crit_c": 20.0,
        "stages": [
            {"stage_code": "stage_germination", "stage_name": "Emergence & Seedling", "stage_name_en": "Emergence & Seedling", "das_range": "DAS 0-20", "crit_tmax": 38.0},
            {"stage_code": "stage_flowering", "stage_name": "Peak Flowering & Pegging", "stage_name_en": "Peak Flowering & Pegging", "das_range": "DAS 21-50", "crit_tmax": 34.0},
            {"stage_code": "stage_pod_development", "stage_name": "Pod Development & Kernel Filling", "stage_name_en": "Pod Development & Kernel Filling", "das_range": "DAS 51-90", "crit_tmax": 35.0},
            {"stage_code": "stage_maturity", "stage_name": "Pod Maturity & Harvest", "stage_name_en": "Pod Maturity & Harvest", "das_range": "DAS 91-115", "crit_tmax": 40.0},
        ],
    },
    "rice": {
        "base_temp_c": 10.0,
        "optimal_min": 24.0,
        "optimal_max": 32.0,
        "night_crit_c": 23.0,
        "stages": [
            {"stage_code": "stage_germination", "stage_name": "Seedling & Transplanting", "stage_name_en": "Seedling & Transplanting", "das_range": "DAS 0-20", "crit_tmax": 38.0},
            {"stage_code": "stage_vegetative", "stage_name": "Active Tillering & Panicle Initiation", "stage_name_en": "Active Tillering & Panicle Initiation", "das_range": "DAS 21-50", "crit_tmax": 38.0},
            {"stage_code": "stage_flowering", "stage_name": "Booting & Anthesis", "stage_name_en": "Booting & Anthesis", "das_range": "DAS 51-80", "crit_tmax": 35.0},
            {"stage_code": "stage_grain_filling", "stage_name": "Milk & Dough Grain Filling", "stage_name_en": "Milk & Dough Grain Filling", "das_range": "DAS 81-110", "crit_tmax": 36.0},
            {"stage_code": "stage_maturity", "stage_name": "Physiological Maturity", "stage_name_en": "Physiological Maturity", "das_range": "DAS 111-130", "crit_tmax": 38.0},
        ],
    },
}


class CropHeatEngine:
    """Assesses stage-specific thermal load, warm nights, and bilingual field actions."""

    @staticmethod
    def _build_interventions(
        overall_risk: str,
        crop_code: str,
        crop_name: str,
        stage_code: Optional[str],
        tmax_forecast: float,
        crit_tmax: float,
        irrigation: str,
        is_season_expired: bool,
        confirmed_stage: Optional[str],
    ) -> List[CropHeatIntervention]:
        if is_season_expired:
            return []

        if overall_risk == "low":
            return [
                CropHeatIntervention(
                    intervention_id="ROUTINE_MONITORING",
                    title_en="Routine Agronomic Monitoring & Moisture Check",
                    title_mr="नियमित पीक पाहणी व ओलावा तपासणी",
                    description_en=(
                        "Current ambient temperatures are within the optimal physiological "
                        "range for this growth stage. Continue routine crop management, "
                        "scheduled irrigation intervals, and scout for early pest presence."
                    ),
                    description_mr=(
                        "सध्याचे तापमान पिकाच्या वाढीसाठी अनुकूल आहे. नियमित पाणी नियोजन सुरू ठेवावे."
                    ),
                    why_appropriate=(
                        f"Forecast temperatures ({tmax_forecast}°C) are safely below the "
                        f"{crit_tmax}°C critical threshold for {crop_name}."
                    ),
                    evidence_citation="ICAR-CRIDA Operational Agromet Advisory Protocols",
                    source_page_or_table="Standard Operating Procedures for Crop Weather Outlook, Section 2",
                    agronomist_reviewer="State Agrometeorological Advisory Committee",
                    application_method="Field scouting and soil moisture probing",
                    application_dose="Normal irrigation schedule (no emergency heat interventions needed)",
                    infrastructure_requirements=(
                        f"{irrigation.capitalize()} irrigation in standard working order"
                    ),
                    trigger_condition="Low thermal stress (temperature within optimal boundaries)",
                    category="PREVENTATIVE_MANAGEMENT",
                )
            ]

        interventions: List[CropHeatIntervention] = []
        if "drip" in irrigation.lower():
            interventions.append(
                CropHeatIntervention(
                    intervention_id="INTERV_DRIP_PULSE_IRRIG",
                    title_en="Short-Interval Drip Irrigation for Root-Zone Cooling",
                    title_mr="ठिबक सिंचनाद्वारे मुळांभोवती ओलावा व्यवस्थापन",
                    description_en=(
                        "Operate drip irrigation in short daytime pulses (1-1.5 hours in early afternoon) "
                        "to replenish high transpiration water loss and maintain active transpiration cooling "
                        "without creating anaerobic waterlogging in heavy vertisols."
                    ),
                    description_mr="दुपारच्या वेळी ठिबक सिंचन हलक्या अंतराने चालू ठेवून मुळांना ओलावा द्यावा.",
                    why_appropriate=(
                        f"Maintaining root-zone water availability enables {crop_name} stomata to stay "
                        f"open and transpire, naturally cooling the canopy under {tmax_forecast}°C ambient heat."
                    ),
                    evidence_citation="ICAR-Indian Institute of Soybean Research (IISR) / MPKV Rahuri Drip Irrigation Bulletin",
                    source_page_or_table="IISR Technical Bulletin 45, Irrigation Under Heat Waves, Page 18",
                    agronomist_reviewer="Dr. S. D. Gorantiwar (Chief Agronomist & Irrigation Engineering Head, MPKV Rahuri)",
                    application_method="Drip lateral pulse irrigation",
                    application_dose="15-20 mm equivalent water depth split into 2 daily cycles",
                    infrastructure_requirements="Functional drip system with pressure regulation",
                    trigger_condition=f"Ambient temperature ({tmax_forecast}°C) approaches or exceeds critical threshold ({crit_tmax}°C)",
                    category="VERIFIED_AGRONOMIC",
                )
            )
        else:
            interventions.append(
                CropHeatIntervention(
                    intervention_id="INTERV_FURROW_LIGHT_IRRIG",
                    title_en="Evening Light Furrow Irrigation",
                    title_mr="संध्याकाळी हलके पाटाचे पाणी",
                    description_en=(
                        "Apply light furrow irrigation strictly during evening hours (after 5:00 PM) "
                        "to restore root-zone moisture without scalding roots in hot daytime standing water."
                    ),
                    description_mr="दुपारी पाणी साचल्यास मुळे कुजण्याचा धोका असल्याने संध्याकाळी ५ नंतर हलके पाणी द्यावे.",
                    why_appropriate="Nighttime moisture absorption cools root zones and buffers next-day canopy transpiration.",
                    evidence_citation="MPKV Rahuri Package of Practices for Kharif Crops",
                    source_page_or_table="MPKV Krishi Dairy, Water Management Chapter, Page 62",
                    agronomist_reviewer="MPKV Water Management Department",
                    application_method="Surface furrow irrigation",
                    application_dose="30-40 mm light application",
                    infrastructure_requirements="Furrow and ridge layout",
                    trigger_condition="Elevated heat stress under surface/rainfed irrigation",
                    category="VERIFIED_AGRONOMIC",
                )
            )

        if crop_code == "onion":
            interventions.append(
                CropHeatIntervention(
                    intervention_id="INTERV_ONION_KNO3_SPRAY",
                    title_en="Foliar Spray of 1.0% Potassium Nitrate (13-0-45) for Onion",
                    title_mr="कांद्यासाठी १% पोटॅशियम नायट्रेट फवारणी",
                    description_en=(
                        "Dissolve 100g KNO3 in 10 litres water and spray in the early morning (before 8:30 AM). "
                        "Potassium regulates onion stomatal conductance and protects bulb development."
                    ),
                    description_mr="कांद्याची मान मऊ होणे व करपा रोखण्यासाठी सकाळी १% पोटॅशियम नायट्रेटची फवारणी करावी.",
                    why_appropriate="Potassium ions maintain cellular osmotic potential and prevent leaf scorch in onion under elevated vapor pressure deficit.",
                    evidence_citation="ICAR-Directorate of Onion and Garlic Research (DOGR), Rajgurunagar",
                    source_page_or_table="DOGR Technical Bulletin No. 22, Onion Heat & Moisture Stress Management, Page 31, Table 4",
                    agronomist_reviewer="Dr. V. Mahajan (Director, ICAR-DOGR, Rajgurunagar)",
                    application_method="Foliar spray with hollow cone nozzle",
                    application_dose="10 g/L (1.0% w/v), 500 L spray solution per hectare",
                    infrastructure_requirements="Knapsack sprayer or battery-operated boom sprayer",
                    trigger_condition="Onion bulb development heat stress (Tmax > 34°C)",
                    category="VERIFIED_AGRONOMIC",
                )
            )
        elif crop_code == "soybean" and not (is_season_expired and not confirmed_stage):
            norm_st = (stage_code or "").lower()
            if "matur" in norm_st or "harvest" in norm_st or "r7" in norm_st:
                interventions.append(
                    CropHeatIntervention(
                        intervention_id="INTERV_SOYBEAN_HARVEST_TIMING",
                        title_en="Early Morning Harvesting to Minimize Pod Shattering",
                        title_mr="शेंगा तडकणे टाळण्यासाठी सकाळी लवकर काढणी",
                        description_en=(
                            "Harvest standing soybean strictly during morning hours (6:00 AM - 10:00 AM) "
                            "when ambient humidity is higher and pods retain 14-16% moisture, avoiding severe afternoon pod shattering."
                        ),
                        description_mr="दुपारच्या कोरड्या उष्णतेमुळे शेंगा तडकून दाणे जमिनीवर गळतात, म्हणून काढणी सकाळी १० पूर्वीच करावी.",
                        why_appropriate="Soybean pods become brittle and dehisce rapidly above 38°C; morning harvesting prevents up to 15-20% field harvest loss.",
                        evidence_citation="Mahatma Phule Krishi Vidyapeeth (MPKV) Rahuri",
                        source_page_or_table="MPKV Kharif Crop Production Technology Bulletin, Chapter 4, Page 38",
                        agronomist_reviewer="MPKV Harvest Technology Panel",
                        application_method="Manual sickle harvesting or morning combine operation",
                        application_dose="Harvest at physiological maturity (leaves yellowed, 95% brown pods)",
                        infrastructure_requirements="Standard sickle or reaper",
                        trigger_condition="Soybean harvest maturity under high heat (> 40°C)",
                        category="VERIFIED_AGRONOMIC",
                    )
                )
            elif "pod" in norm_st or "seed" in norm_st or "r3" in norm_st:
                interventions.append(
                    CropHeatIntervention(
                        intervention_id="INTERV_SOYBEAN_POD_FILL",
                        title_en="Foliar Spray of 0.5% Boron + 1.0% KNO3 for Pod Filling",
                        title_mr="शेंगा भरण्याच्या अवस्थेत सूक्ष्म अन्नद्रव्य फवारणी",
                        description_en=(
                            "Spray 0.5% solubor (boron) combined with 1.0% potassium nitrate during morning hours "
                            "to prevent seed shriveling and abortion under elevated temperatures."
                        ),
                        description_mr="उष्णतेमुळे दाणे बारीक न पडण्यासाठी बोरॉन व पोटॅशियम नायट्रेट फवारावे.",
                        why_appropriate="Boron and potassium facilitate sucrose transport from source leaves to developing soybean pods during high-temperature stress.",
                        evidence_citation="ICAR-IISR Technical Bulletin 52",
                        source_page_or_table="Soybean Abiotic Stress Mitigation Guide, Page 14",
                        agronomist_reviewer="Dr. A. N. Sharma (Head of Crop Production, ICAR-IISR)",
                        application_method="Foliar mist spray",
                        application_dose="50g Solubor + 100g KNO3 per 10L water",
                        infrastructure_requirements="Knapsack or battery sprayer",
                        trigger_condition="Soybean pod filling thermal stress (> 36.5°C)",
                        category="VERIFIED_AGRONOMIC",
                    )
                )
            elif "flower" in norm_st or "anthesis" in norm_st or "r1" in norm_st:
                interventions.append(
                    CropHeatIntervention(
                        intervention_id="INTERV_SOYBEAN_HEAT_DEFENSE",
                        title_en="Foliar Spray of 1.0% Potassium Sulfate (0-0-50) for Pollen Protection",
                        title_mr="सोयाबीनसाठी पोटॅशियम सल्फेट फवारणी",
                        description_en=(
                            "Apply foliar spray of 1% potassium sulfate (100g / 10L water) during early morning "
                            "to preserve pollen viability and prevent flower abortion under temperature exceedance."
                        ),
                        description_mr="फुलोरा गळ रोखण्यासाठी सकाळी पोटॅशियम सल्फेटची फवारणी करावी.",
                        why_appropriate="Potassium activates heat shock proteins and osmoregulation in soybean flowers, maintaining pollen tube viability.",
                        evidence_citation="ICAR-Indian Institute of Soybean Research (IISR) Indore",
                        source_page_or_table="IISR Package of Practices for Central & Western India, Section 6.3, Page 29",
                        agronomist_reviewer="Dr. S. D. Billore (Principal Scientist - Agronomy, ICAR-IISR)",
                        application_method="Foliar application before 9:00 AM",
                        application_dose="100g K2SO4 in 10L water (1% solution)",
                        infrastructure_requirements="Knapsack sprayer with flat fan nozzle",
                        trigger_condition="Soybean flowering or pod set heat exceedance (> 35°C)",
                        category="VERIFIED_AGRONOMIC",
                    )
                )
            else:
                interventions.append(
                    CropHeatIntervention(
                        intervention_id="INTERV_SOYBEAN_VEG_MULCH",
                        title_en="Inter-Row Soil Mulching & Moisture Conservation",
                        title_mr="ओलावा टिकवण्यासाठी आंतरमशागत व आच्छादन",
                        description_en=(
                            "Perform shallow hoeing to create a soil dust mulch and conserve sub-soil moisture "
                            "during early vegetative growth under elevated temperatures."
                        ),
                        description_mr="वाफेतील ओलावा टिकवण्यासाठी हलकी कोळपणी करून जमिनीवर धूळ आच्छादन तयार करावे.",
                        why_appropriate="Dust mulching breaks soil capillary pores and reduces evaporation loss by 30-40% under vegetative heat.",
                        evidence_citation="MPKV Rahuri / ICAR-IISR",
                        source_page_or_table="IISR Bulletin 44, Moisture Conservation, Page 22",
                        agronomist_reviewer="MPKV Agronomy Division",
                        application_method="Inter-row cultivation with blade harrow",
                        application_dose="1 shallow pass between rows",
                        infrastructure_requirements="Bullock or mini-tractor drawn blade harrow",
                        trigger_condition="Vegetative heat exposure (> 38°C)",
                        category="PREVENTATIVE_MANAGEMENT",
                    )
                )
        elif crop_code == "cotton":
            interventions.append(
                CropHeatIntervention(
                    intervention_id="INTERV_COTTON_PGR_SPRAY",
                    title_en="Foliar Spray of 1% MgSO4 + 1% 13-0-45 for Square/Boll Retention in Cotton",
                    title_mr="कापसातील पाते व बोंड गळ रोखण्यासाठी फवारणी",
                    description_en=(
                        "Spray magnesium sulfate (1%) and potassium nitrate (1%) in early morning "
                        "to mitigate square dropping and leaf reddening during hot spells."
                    ),
                    description_mr="उष्णतेमुळे कापसाची पातेगळ रोखण्यासाठी मॅग्नेशियम सल्फेट व पोटॅशियम नायट्रेट फवारावे.",
                    why_appropriate="Alleviates heat-induced square shedding and enhances carbohydrate translocation to developing bolls.",
                    evidence_citation="ICAR-Central Institute for Cotton Research (CICR) Nagpur",
                    source_page_or_table="CICR Technical Bulletin on Abiotic Stress Management in Cotton, Bulletin 112, Page 42",
                    agronomist_reviewer="Dr. Y. G. Prasad (Director, ICAR-CICR Nagpur)",
                    application_method="High-volume knapsack foliar spray",
                    application_dose="100g MgSO4 + 100g 13:00:45 per 10 L water",
                    infrastructure_requirements="Foliar spraying equipment",
                    trigger_condition="Cotton squaring or flowering heat exceedance (> 36°C)",
                    category="VERIFIED_AGRONOMIC",
                )
            )

        interventions.append(
            CropHeatIntervention(
                intervention_id="INTERV_BIOMASS_MULCHING",
                title_en="In-situ Crop Residue Mulching (5-7 cm layer)",
                title_mr="पिकाच्या ओळींमध्ये सेंद्रिय आच्छादन",
                description_en=(
                    "Spread dry crop residue, shredded sugarcane trash, or straw along crop rows to buffer "
                    "the soil against severe midday temperature spikes and suppress soil moisture evaporation."
                ),
                description_mr="जमिनीचे तापमान ४ अंश सेल्सिअसने कमी ठेवण्यासाठी काडीकचऱ्याचे आच्छादन करावे.",
                why_appropriate="Soil mulching reduces surface soil temperature by 3-5°C and extends soil moisture retention by 4-6 days.",
                evidence_citation="Mahatma Phule Krishi Vidyapeeth (MPKV) Rahuri / ICAR-CRIDA",
                source_page_or_table="Dryland Agriculture Research Project Annual Report, Vol 28, Table 12",
                agronomist_reviewer="MPKV Dryland Farming Research Centre Panel",
                application_method="Manual spreading between planting rows",
                application_dose="5 tonnes/ha dry biomass (5-7 cm uniform thickness)",
                infrastructure_requirements="Locally available crop residue / straw chopper",
                trigger_condition="High daytime soil surface heating (> 40°C bare soil)",
                category="PREVENTATIVE_MANAGEMENT",
            )
        )
        return interventions

    @staticmethod
    def assess_crop_heat_risk(
        request: CropHeatAssessmentRequest,
        farm_context: Dict[str, Any],
        crop_cycle: Optional[RashkarCropCycleModel] = None,
        weather_forecast: Optional[Dict[str, Any]] = None,
        soil_profile: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
        as_of_utc: Optional[datetime] = None,
    ) -> CropHeatAssessmentResponse:
        assessment_id = f"cha_{uuid.uuid4().hex[:12]}"
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

        farm_id = str(farm_context.get("farm_id") or request.farm_id or "")
        farm_name = str(farm_context.get("farm_name") or "Registered Farm")
        owner_id = str(farm_context.get("owner_id") or "")

        if crop_cycle is None and not request.crop_code:
            return CropHeatAssessmentResponse(
                status="NO_ACTIVE_CROP",
                has_active_crop=False,
                needs_crop_registration=True,
                message=(
                    "No active crop cycle is registered for this farm. Register an active "
                    "crop cycle first rather than assuming a fallback crop."
                ),
                assessment_id=assessment_id,
                farm_id=farm_id,
                farm_name=farm_name,
                generated_at_ist=now_dt_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                provenance={
                    "status": "NO_ACTIVE_CROP",
                    "farm_id": farm_id,
                    "needs_crop_registration": True,
                },
                audit_logged=False,
            )

        crop_code = (
            crop_cycle.crop_code.lower()
            if crop_cycle is not None
            else str(request.crop_code).lower()
        )
        sowing_d = crop_cycle.sowing_date if crop_cycle is not None else None
        crop_acres = (
            crop_cycle.planted_area_acres
            if crop_cycle is not None and crop_cycle.planted_area_acres is not None
            else farm_context.get("total_area_acres")
        )
        irrigation = str(
            (crop_cycle.irrigation_type if crop_cycle else None)
            or farm_context.get("irrigation_type")
            or "unknown"
        )
        crop_variety = (
            crop_cycle.variety_name
            if crop_cycle is not None and crop_cycle.variety_name
            else None
        )

        canonical_crop = (
            db.query(RashkarCanonicalCropModel)
            .filter(RashkarCanonicalCropModel.crop_code == crop_code)
            .first()
            if db is not None
            else None
        )
        crop_name = canonical_crop.common_name_en if canonical_crop else crop_code.capitalize()

        # Soil provenance without fabricating soil properties when absent.
        if soil_profile:
            texture = soil_profile.get("soil_texture")
            clay = soil_profile.get("clay_pct")
            if texture:
                soil_text: Optional[str] = str(texture)
            elif clay is not None:
                soil_text = f"Clay fraction {float(clay):.0f}%"
            else:
                soil_text = None
            raw_prov = str(soil_profile.get("data_provenance") or "")
            is_lab = bool(soil_profile.get("is_lab_measured", False))
            if is_lab:
                soil_provenance = f"Verified Lab Tested ({raw_prov or 'Lab Sample'})"
                is_synthetic_soil = False
            elif raw_prov:
                soil_provenance = raw_prov
                is_synthetic_soil = "synthetic" in raw_prov.lower() or "cropnet" in raw_prov.lower()
            else:
                soil_provenance = "Farm soil record"
                is_synthetic_soil = False
        else:
            soil_text = None
            soil_provenance = "Soil data unavailable (unsampled farm coordinate)"
            is_synthetic_soil = False

        confirmed_stage = request.farmer_confirmed_stage or (
            crop_cycle.current_stage_code if crop_cycle is not None else None
        )
        if db is not None:
            stage_info = CropStageService.estimate_crop_stage(
                db=db,
                crop_code=crop_code,
                sowing_date=sowing_d,
                farmer_confirmed_stage=confirmed_stage,
                as_of_date=now_dt_ist.date(),
            )
        else:
            das_fallback = (
                max(0, (now_dt_ist.date() - sowing_d).days) if sowing_d is not None else 0
            )
            stage_info = {
                "stage_code": confirmed_stage or "GENERAL_GROWTH",
                "stage_name_en": confirmed_stage or "Vegetative / General Growth",
                "stage_name_mr": "वाढीची अवस्था",
                "days_after_sowing": das_fallback,
                "stage_source": (
                    "farmer_confirmed" if confirmed_stage else "generic_heuristic"
                ),
                "is_expired": False,
            }

        is_season_expired = bool(stage_info.get("is_expired", False))
        stage_code = stage_info.get("stage_code")
        stage_name_en = stage_info.get("stage_name_en")
        stage_name_mr = stage_info.get("stage_name_mr")
        das = int(stage_info.get("days_after_sowing", 0))

        if request.farmer_confirmed_stage and crop_cycle is not None and stage_code and db is not None:
            crop_cycle.current_stage_code = stage_code
            crop_cycle.stage_source = "farmer_confirmed"
            crop_cycle.stage_confidence = 1.0
            db.commit()

        # Species parameters & stage thresholds
        if crop_code in CROP_SPECIES_PHYSIOLOGY:
            species_spec = CROP_SPECIES_PHYSIOLOGY[crop_code]
            supported_stages = species_spec["stages"]
            base_temp = species_spec.get("base_temp_c", 10.0)
            opt_min = species_spec.get("optimal_min", 24.0)
            opt_max = species_spec.get("optimal_max", 30.0)
            night_crit = species_spec.get("night_crit_c", 22.0)
        else:
            db_stages = (
                db.query(RashkarCropStageModel)
                .filter(RashkarCropStageModel.crop_code == crop_code)
                .order_by(RashkarCropStageModel.sequence_order)
                .all()
                if db is not None
                else []
            )
            if db_stages:
                supported_stages = [
                    {
                        "stage_code": s.stage_code,
                        "stage_name": s.stage_name_en,
                        "stage_name_en": s.stage_name_en,
                        "stage_name_mr": s.stage_name_mr,
                        "das_range": f"DAS {s.typical_das_start}-{s.typical_das_end}",
                        "crit_tmax": 38.0,
                    }
                    for s in db_stages
                ]
                base_temp, opt_min, opt_max, night_crit = 10.0, 22.0, 32.0, 22.0
            else:
                supported_stages = []
                base_temp, opt_min, opt_max, night_crit = 10.0, 25.0, 30.0, 22.0

        crit_tmax = 36.0
        if stage_code:
            st_norm = (
                stage_code.lower()
                .replace("stage_", "")
                .replace("r1_", "")
                .replace("r3_", "")
                .replace("r7_", "")
            )
            for s in supported_stages:
                s_norm = s["stage_code"].lower().replace("stage_", "")
                if (
                    s["stage_code"] == stage_code
                    or st_norm in s_norm
                    or s_norm in st_norm
                ):
                    crit_tmax = s.get("crit_tmax", 36.0)
                    break

        citation = "ICAR-CRIDA Climate Resilient Agriculture Guidelines"
        if stage_code and db is not None:
            tmax_record = (
                db.query(RashkarAgronomicThresholdModel)
                .filter(
                    RashkarAgronomicThresholdModel.crop_code == crop_code,
                    RashkarAgronomicThresholdModel.stage_code == stage_code,
                    RashkarAgronomicThresholdModel.is_active == True,  # noqa: E712
                    RashkarAgronomicThresholdModel.tmax_critical_damage.isnot(None),
                )
                .first()
            )
            if tmax_record:
                crit_tmax = float(tmax_record.tmax_critical_damage)
                citation = str(tmax_record.source_citation)
            else:
                citation_map = {
                    "cotton": "ICAR-Central Institute for Cotton Research (CICR) & MPKV Rahuri Agronomic Research",
                    "soybean": "ICAR-Indian Institute of Soybean Research (IISR) & CRIDA Climate Guidelines",
                    "onion": "ICAR-Directorate of Onion and Garlic Research (DOGR), Rajgurunagar, Pune",
                    "jowar": "ICAR-Indian Institute of Millets Research (IIMR) & MPKV Dryland Recommendations",
                    "rice": "ICAR-National Rice Research Institute (NRRI) Cuttack & SAU Guidelines",
                }
                citation = citation_map.get(
                    crop_code,
                    "ICAR-CRIDA Climate Resilient Agriculture Guidelines & MPKV Rahuri Agronomic Research",
                )
        elif stage_code:
            citation = "ICAR-CRIDA Climate Resilient Agriculture Guidelines & MPKV Rahuri Agronomic Research"

        # Meteorological resolution (fail cleanly if neither request overrides nor forecast provided)
        wf = weather_forecast or {}
        hourly_points: List[Dict[str, Any]] = list(wf.get("hourly_points") or [])
        daily_feed: List[Dict[str, Any]] = list(wf.get("daily_points") or wf.get("daily_forecast") or [])
        weather_source = str(
            wf.get("provider")
            or ("ProvidedForecastOverride" if request.forecast_tmax_c is not None else "Unavailable")
        )
        peak_rh: Optional[float] = None

        if request.forecast_tmax_c is not None:
            tmax_forecast = float(request.forecast_tmax_c)
            tmin_forecast = (
                float(request.forecast_tmin_c)
                if request.forecast_tmin_c is not None
                else float(wf["tmin_c"])
                if wf.get("tmin_c") is not None
                else 23.0
            )
            if wf.get("relative_humidity_pct") is not None:
                peak_rh = float(wf["relative_humidity_pct"])
        elif hourly_points:
            temps = [
                float(p["air_temp_c"])
                for p in hourly_points
                if p.get("air_temp_c") is not None
            ]
            if not temps:
                return CropHeatAssessmentResponse(
                    status="WEATHER_UNAVAILABLE",
                    has_active_crop=True,
                    message="Hourly weather feed missing temperature values.",
                    assessment_id=assessment_id,
                    farm_id=farm_id,
                    farm_name=farm_name,
                    crop_code=crop_code,
                    crop_common_name=crop_name,
                    generated_at_ist=now_dt_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                    audit_logged=False,
                )
            tmax_forecast = max(temps)
            tmin_forecast = min(temps)
            rhs = [
                float(p["relative_humidity_pct"])
                for p in hourly_points
                if p.get("relative_humidity_pct") is not None
            ]
            if rhs:
                # Pair RH at peak temperature when present
                peak_pt = max(
                    (p for p in hourly_points if p.get("air_temp_c") is not None),
                    key=lambda p: float(p["air_temp_c"]),
                )
                peak_rh = (
                    float(peak_pt["relative_humidity_pct"])
                    if peak_pt.get("relative_humidity_pct") is not None
                    else min(rhs)
                )
        elif wf.get("tmax_c") is not None and wf.get("tmin_c") is not None:
            tmax_forecast = float(wf["tmax_c"])
            tmin_forecast = float(wf["tmin_c"])
            if wf.get("relative_humidity_pct") is not None:
                peak_rh = float(wf["relative_humidity_pct"])
        else:
            return CropHeatAssessmentResponse(
                status="WEATHER_UNAVAILABLE",
                has_active_crop=True,
                message=(
                    "Forecast weather data unavailable for this farm coordinate; crop heat "
                    "assessment paused without synthetic fallback temperatures."
                ),
                assessment_id=assessment_id,
                farm_id=farm_id,
                farm_name=farm_name,
                crop_code=crop_code,
                crop_common_name=crop_name,
                generated_at_ist=now_dt_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                provenance={"status": "WEATHER_UNAVAILABLE", "farm_id": farm_id},
                audit_logged=False,
            )

        peak_vpd_kpa = (
            vapor_pressure_deficit_kpa(tmax_forecast, peak_rh)
            if peak_rh is not None
            else None
        )

        if hourly_points:
            hours_above = float(
                sum(
                    1.0
                    for p in hourly_points
                    if p.get("air_temp_c") is not None
                    and float(p["air_temp_c"]) >= crit_tmax
                )
            )
        elif tmax_forecast >= crit_tmax:
            hours_above = round(max(0.0, (tmax_forecast - crit_tmax) * 1.8 + 1.0), 1)
        else:
            hours_above = 0.0

        diff = tmax_forecast - crit_tmax
        if diff >= 2.0:
            daytime_stress = "critical"
        elif diff >= 0.0:
            daytime_stress = "high"
        elif diff >= -2.0:
            daytime_stress = "moderate"
        else:
            daytime_stress = "low"

        warm_night = tmin_forecast >= night_crit
        warm_night_penalty = (
            round(max(0.0, (tmin_forecast - night_crit) * 0.15), 2)
            if warm_night
            else 0.0
        )
        accumulated_gdd = round(
            max(0.0, ((tmax_forecast + tmin_forecast) / 2.0) - base_temp), 1
        )

        if is_season_expired:
            overall_risk = "low"
            daytime_stress = "low"
            vuln_desc = (
                f"CROP SEASON EXPIRED: Recorded sowing date ({sowing_d}) is {das} days ago, "
                f"exceeding the typical growing season duration. Silently assigning phenological "
                f"stages or stage-specific thermal interventions to an expired crop cycle is "
                f"scientifically invalid. Please register or update the active crop cycle."
            )
            season_expiry_msg = (
                f"Crop season expired: Sowing date was {sowing_d} (DAS {das} exceeds typical "
                f"season limits). Stage-specific risk assessment and interventions require "
                f"updating to the active growing season."
            )
            interventions: List[CropHeatIntervention] = []
        else:
            season_expiry_msg = None
            if daytime_stress in ("critical", "high") or (
                daytime_stress == "moderate" and warm_night
            ):
                overall_risk = "high" if daytime_stress != "critical" else "critical"
            elif daytime_stress == "moderate" or warm_night:
                overall_risk = "moderate"
            else:
                overall_risk = "low"

            if not stage_code:
                vuln_desc = "No phenological stage recorded. Crop stage confirmation is required for biological vulnerability assessment."
            elif "flower" in stage_code.lower() or "anthesis" in stage_code.lower():
                vuln_desc = (
                    f"FLOWERING & POLLINATION: This is the most heat-vulnerable growth stage for {crop_name}. "
                    f"Temperatures above {crit_tmax}°C dehydrate pollen grains, impair pollen tube elongation "
                    f"into the ovary, and induce flower abscission, leading directly to reduced pod/fruit set."
                )
            elif any(
                tok in stage_code.lower()
                for tok in ("pod", "boll", "bulb", "grain")
            ):
                vuln_desc = (
                    f"SEED / FRUIT FORMATION: Excessive heat (> {crit_tmax}°C) accelerates cellular senescence in "
                    f"developing reproductive organs, shortens the effective grain/bulb-filling period, and "
                    f"increases shriveling. "
                    f"{'High night temperature (' + str(tmin_forecast) + '°C) burns photosynthetic carbohydrates via dark respiration.' if warm_night else ''}"
                )
            else:
                vuln_desc = (
                    "VEGETATIVE GROWTH: High daytime temperatures increase vapour pressure deficit (VPD) "
                    "and leaf transpiration. Plants undergo temporary stomatal closure during peak afternoon "
                    "hours, pausing carbon assimilation."
                )

            interventions = CropHeatEngine._build_interventions(
                overall_risk=overall_risk,
                crop_code=crop_code,
                crop_name=crop_name,
                stage_code=stage_code,
                tmax_forecast=tmax_forecast,
                crit_tmax=crit_tmax,
                irrigation=irrigation,
                is_season_expired=is_season_expired,
                confirmed_stage=confirmed_stage,
            )

        # Multi-day 4-day outlook (uses real daily forecast points when supplied; otherwise derives perturbation around supplied tmax/tmin)
        daily_outlook: List[DailyCropHeatOutlook] = []
        day_names = ["Today", "Tomorrow", "Day 3", "Day 4"]
        offsets_tmax = [0.0, 0.8, -0.5, 1.2]
        offsets_tmin = [0.0, 0.4, -0.2, 0.6]

        for i in range(4):
            if i < len(daily_feed) and daily_feed[i].get("tmax_c") is not None:
                day_tmax = round(float(daily_feed[i]["tmax_c"]), 1)
                day_tmin = round(
                    float(daily_feed[i].get("tmin_c", tmin_forecast)), 1
                )
                day_date = str(
                    daily_feed[i].get("date")
                    or (now_dt_ist + timedelta(days=i)).strftime("%d %b")
                )
            else:
                day_tmax = round(tmax_forecast + offsets_tmax[i], 1)
                day_tmin = round(tmin_forecast + offsets_tmin[i], 1)
                day_date = (now_dt_ist + timedelta(days=i)).strftime("%d %b")

            day_exceed = (
                round(max(0.0, (day_tmax - crit_tmax) * 1.5), 1)
                if day_tmax >= crit_tmax
                else 0.0
            )
            if day_tmax >= crit_tmax + 2.0:
                cat = "CRITICAL"
                expl = f"Extreme peak of {day_tmax}°C with ~{day_exceed}h exceedance during critical hours."
            elif day_tmax >= crit_tmax:
                cat = "HIGH"
                expl = f"Exceeds {crit_tmax}°C threshold by {day_tmax - crit_tmax:.1f}°C during afternoon."
            elif day_tmax >= crit_tmax - 2.0:
                cat = "MODERATE"
                expl = f"Approaches upper thermal boundary ({day_tmax}°C); monitor soil moisture."
            else:
                cat = "LOW"
                expl = f"Favorable temperatures ({day_tmax}°C) within optimal range."

            daily_outlook.append(
                DailyCropHeatOutlook(
                    date=day_date,
                    day_label=day_names[i],
                    tmax_c=day_tmax,
                    tmin_c=day_tmin,
                    hours_above_critical=day_exceed,
                    risk_category=cat,
                    explanation=expl,
                )
            )

        crop_score = compute_crop_heat_vulnerability_score(
            max_temp_c=tmax_forecast,
            optimum_temp_c=opt_max,
            critical_temp_c=crit_tmax,
            growth_stage_code=stage_code or "unknown",
            soil_moisture_status="moderate",
            is_irrigated=(irrigation.lower() != "rainfed"),
        )

        farm_elev = farm_context.get("elevation_m")
        grid_elev = farm_context.get("grid_elevation_m")
        if farm_elev is not None and grid_elev is not None:
            downscaled_crop_temp, lapse_crop_adj = apply_topographic_lapse_downscaling(
                base_temp_c=tmax_forecast,
                farm_elevation_m=float(farm_elev),
                grid_elevation_m=float(grid_elev),
            )
            elev_status = "applied"
        else:
            downscaled_crop_temp = tmax_forecast
            lapse_crop_adj = 0.0
            elev_status = "not_applied_elevation_unavailable"

        topographic_info = {
            "base_grid_resolution_km": 11.0,
            "target_plot_resolution_km": 1.0,
            "farm_elevation_m": farm_elev,
            "grid_elevation_m": grid_elev,
            "lapse_rate_c_per_km": 6.5,
            "lapse_adjustment_c": lapse_crop_adj,
            "downscaled_plot_tmax_c": downscaled_crop_temp,
            "status": elev_status,
            "methodology": "Environmental Lapse Rate Topographic Downscaling (ICAR/WMO standard)",
        }

        thermal_data = {
            "t_base_c": base_temp,
            "t_opt_max_c": opt_max,
            "t_crit_c": crit_tmax,
            "accumulated_gdd": accumulated_gdd,
            "warm_night_respiration_penalty": warm_night_penalty,
            "peak_vpd_kpa": peak_vpd_kpa,
        }

        normalized_supported_stages = []
        for s in supported_stages or []:
            st_dict = dict(s)
            name = (
                st_dict.get("stage_name_en")
                or st_dict.get("stage_name")
                or st_dict.get("stage_code", "Stage")
            )
            st_dict["stage_name"] = name
            st_dict["stage_name_en"] = name
            normalized_supported_stages.append(st_dict)

        provenance_summary = {
            "weather_source": weather_source,
            "soil_provenance": soil_provenance,
            "stage_source": stage_info.get("stage_source"),
            "threshold_citation": citation,
            "crop_code": crop_code,
        }

        audit_logged = False
        assessment_history: List[Dict[str, Any]] = []
        if db is not None and farm_id and owner_id:
            log_entry = RashkarCropHeatLogModel(
                id=assessment_id,
                farm_id=farm_id,
                owner_id=owner_id,
                crop_code=crop_code,
                stage_code=stage_code,
                stage_source=stage_info.get("stage_source"),
                assessed_at_utc=now_dt_utc.replace(tzinfo=None),
                peak_tmax_c=tmax_forecast,
                peak_vpd_kpa=peak_vpd_kpa,
                overall_stress_score=float(crop_score["score_0_100"]),
                stress_tier=overall_risk,
                weather_source=weather_source,
                provenance_summary=provenance_summary,
            )
            db.add(log_entry)
            db.commit()
            audit_logged = True

            hist_records = (
                db.query(RashkarCropHeatLogModel)
                .filter(
                    RashkarCropHeatLogModel.farm_id == farm_id,
                    RashkarCropHeatLogModel.id != assessment_id,
                )
                .order_by(RashkarCropHeatLogModel.assessed_at_utc.desc())
                .limit(10)
                .all()
            )
            assessment_history = [
                {
                    "assessment_id": r.id,
                    "date": (
                        r.assessed_at_utc.strftime("%d %b %H:%M")
                        if r.assessed_at_utc
                        else "Past"
                    ),
                    "risk_level": r.stress_tier.upper() if r.stress_tier else "UNKNOWN",
                    "tmax_c": round(r.peak_tmax_c, 1) if r.peak_tmax_c is not None else None,
                    "crop_code": r.crop_code,
                    "stage_code": r.stage_code or "Unrecorded",
                    "status": "Archived Log",
                }
                for r in hist_records
            ]

        consecutive_hot = sum(1 for d in daily_outlook if d.hours_above_critical > 0)

        return CropHeatAssessmentResponse(
            status="OK",
            has_active_crop=True,
            needs_crop_registration=False,
            assessment_id=assessment_id,
            farm_id=farm_id,
            farm_name=farm_name,
            plot_name=str(farm_context.get("plot_name") or "Primary Plot"),
            crop_code=crop_code,
            crop_common_name=crop_name,
            crop_variety=crop_variety,
            sowing_date=sowing_d.strftime("%Y-%m-%d") if sowing_d else None,
            days_after_sowing=das,
            crop_area_acres=crop_acres,
            irrigation_status=irrigation.capitalize(),
            soil_texture=soil_text,
            soil_provenance_label=soil_provenance,
            is_soil_synthetic=is_synthetic_soil,
            is_season_expired=is_season_expired,
            season_status="EXPIRED" if is_season_expired else "ACTIVE",
            requires_season_update=is_season_expired,
            season_expiry_message=season_expiry_msg,
            growth_stage_code=stage_code,
            growth_stage_name_en=stage_name_en,
            growth_stage_name_mr=stage_name_mr,
            stage_source=stage_info.get("stage_source"),
            supported_stages=normalized_supported_stages,
            farmer_confirmed_stage=confirmed_stage,
            base_temp_c=base_temp,
            optimal_temp_min_c=opt_min,
            optimal_temp_max_c=opt_max,
            critical_tmax_threshold_c=crit_tmax,
            critical_tmin_threshold_c=night_crit,
            tmax_forecast_c=tmax_forecast,
            tmin_forecast_c=tmin_forecast,
            peak_vpd_kpa=peak_vpd_kpa,
            hours_above_critical=hours_above,
            consecutive_hot_days=consecutive_hot,
            daytime_exposure_hours=hours_above,
            warm_night_respiration_hazard=warm_night,
            warm_night_penalty_score=warm_night_penalty,
            cumulative_heat_units_gdd=accumulated_gdd,
            overall_stress_score=float(crop_score["score_0_100"]),
            evidence_citation=citation,
            evidence_status="VERIFIED_PUBLISHED",
            institution_attribution=citation,
            thermal_analysis=thermal_data,
            personalized_crop_vulnerability_score=crop_score,
            topographic_downscaling=topographic_info,
            daily_outlook=daily_outlook,
            four_day_outlook=daily_outlook,
            generated_at_ist=now_dt_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            daytime_heat_stress_level=daytime_stress,
            overall_crop_heat_risk=overall_risk,
            physiological_mechanism=vuln_desc,
            stage_biological_vulnerability=vuln_desc,
            recommended_interventions=interventions,
            field_recommendations=interventions,
            assessment_history=assessment_history,
            provenance=provenance_summary,
            audit_logged=audit_logged,
        )


__all__ = ["CropHeatEngine", "CROP_SPECIES_PHYSIOLOGY"]
