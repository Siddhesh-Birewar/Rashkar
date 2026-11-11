"""Idempotent reference-data seeder for RASHKAR canonical knowledge tables.

Intentionally seeds ONLY scientific reference data (crops, stages, thresholds,
advisories, income catalogue) — NEVER demo farmers, demo farms, or fake crops.
"""

from typing import Dict, List, Tuple
from sqlalchemy.orm import Session

from .engines.income import EXTENDED_OPPORTUNITY_CATALOG
from .models import (
    RashkarAdvisoryCatalogueModel,
    RashkarAgronomicThresholdModel,
    RashkarCanonicalCropModel,
    RashkarCropStageModel,
    RashkarIncomeOpportunityModel,
)


CANONICAL_CROPS_DATA: List[
    Tuple[str, str, str, str, str, str, bool, str, List[str]]
] = [
    ("soybean", "Soybean", "सोयाबीन", "Glycine max", "oilseed", "kharif", True, "rule_and_baseline_supported", ["Soyabean", "Soyabean(Bhat)", "Soybean"]),
    ("cotton", "Cotton", "कापूस", "Gossypium hirsutum", "fibre", "kharif", True, "rule_and_baseline_supported", ["Cotton", "Cotton(lint)", "Kapas"]),
    ("jowar", "Jowar / Sorghum", "ज्वारी", "Sorghum bicolor", "cereal", "kharif", True, "rule_and_baseline_supported", ["Jowar", "Sorghum", "Kharif Jowar", "Rabi Jowar"]),
    ("sugarcane", "Sugarcane", "ऊस", "Saccharum officinarum", "commercial", "perennial", True, "rule_and_baseline_supported", ["Sugarcane", "Cane"]),
    ("tur", "Tur / Pigeon Pea", "तूर / अरहर", "Cajanus cajan", "pulse", "kharif", False, "advisory_only", ["Arhar/Tur", "Tur", "Pigeon Pea"]),
    ("gram", "Gram / Chickpea", "हरभरा / चणा", "Cicer arietinum", "pulse", "rabi", False, "advisory_only", ["Gram", "Bengal Gram", "Chana"]),
    ("bajra", "Bajra / Pearl Millet", "बाजरी", "Pennisetum glaucum", "millet", "kharif", False, "advisory_only", ["Bajra", "Pearl Millet"]),
    ("rice", "Rice / Paddy", "भात / धान", "Oryza sativa", "cereal", "kharif", False, "advisory_only", ["Rice", "Paddy"]),
    ("wheat", "Wheat", "गहू", "Triticum aestivum", "cereal", "rabi", False, "advisory_only", ["Wheat"]),
    ("onion", "Onion", "कांदा", "Allium cepa", "vegetable", "rabi", False, "advisory_only", ["Onion"]),
    ("pomegranate", "Pomegranate", "डाळिंब", "Punica granatum", "fruit", "perennial", False, "advisory_only", ["Pomegranate"]),
    ("grapes", "Grapes", "द्राक्षे", "Vitis vinifera", "fruit", "perennial", False, "advisory_only", ["Grapes"]),
    ("groundnut", "Groundnut / Peanut", "भुईमूग", "Arachis hypogaea", "oilseed", "kharif", False, "data_limited", ["Groundnut", "Peanut"]),
    ("sunflower", "Sunflower", "सूर्यफूल", "Helianthus annuus", "oilseed", "rabi", False, "data_limited", ["Sunflower"]),
    ("maize", "Maize / Corn", "मका", "Zea mays", "cereal", "kharif", False, "data_limited", ["Maize", "Corn"]),
    ("moong", "Moong / Green Gram", "मूग", "Vigna radiata", "pulse", "kharif", False, "data_limited", ["Moong(Green Gram)", "Moong"]),
    ("urad", "Urad / Black Gram", "उडीद", "Vigna mungo", "pulse", "kharif", False, "data_limited", ["Urad", "Black Gram"]),
    ("safflower", "Safflower / Kardi", "करडई", "Carthamus tinctorius", "oilseed", "rabi", False, "data_limited", ["Safflower", "Kardi"]),
    ("sesamum", "Sesamum / Til", "तीळ", "Sesamum indicum", "oilseed", "kharif", False, "data_limited", ["Sesamum", "Til"]),
    ("niger", "Niger Seed / Karale", "कारळे", "Guizotia abyssinica", "oilseed", "kharif", False, "data_limited", ["Niger seed", "Karale"]),
    ("castor", "Castor Seed", "एरंडी", "Ricinus communis", "oilseed", "kharif", False, "data_limited", ["Castor seed"]),
    ("linseed", "Linseed / Alsi", "जवस", "Linum usitatissimum", "oilseed", "rabi", False, "data_limited", ["Linseed", "Alsi"]),
    ("ragi", "Finger Millet / Ragi / Nachani", "नाचणी / रागी", "Eleusine coracana", "millet", "kharif", False, "data_limited", ["Ragi", "Finger Millet", "Nachani"]),
    ("small_millets", "Small Millets / Vari / Kodra", "वरी / कोद्रा / सावा", "Panicum sumatrense", "millet", "kharif", False, "data_limited", ["Small millets", "Vari", "Kodra"]),
    ("banana", "Banana", "केळी", "Musa acuminata", "fruit", "perennial", False, "data_limited", ["Banana"]),
    ("mango", "Mango / Alphonso", "आंबा / हापूस", "Mangifera indica", "fruit", "perennial", False, "data_limited", ["Mango"]),
    ("sweet_orange", "Sweet Orange / Mosambi", "मोसंबी", "Citrus sinensis", "fruit", "perennial", False, "data_limited", ["Sweet Orange", "Mosambi", "Citrus"]),
    ("mandarin", "Mandarin / Nagpur Santra", "संत्री", "Citrus reticulata", "fruit", "perennial", False, "data_limited", ["Orange", "Santra"]),
    ("custard_apple", "Custard Apple / Sitaphal", "सीताफळ", "Annona squamosa", "fruit", "perennial", False, "data_limited", ["Custard Apple", "Sitaphal"]),
    ("guava", "Guava / Amrud", "पेरू", "Psidium guajava", "fruit", "perennial", False, "data_limited", ["Guava", "Peru"]),
    ("papaya", "Papaya", "पपई", "Carica papaya", "fruit", "perennial", False, "data_limited", ["Papaya"]),
    ("tomato", "Tomato", "टोमॅटो", "Solanum lycopersicum", "vegetable", "rabi", False, "data_limited", ["Tomato"]),
    ("chilli", "Chilli", "मिरची", "Capsicum annuum", "vegetable", "kharif", False, "data_limited", ["Chilli", "Chillies"]),
    ("brinjal", "Brinjal / Eggplant", "वांगी", "Solanum melongena", "vegetable", "kharif", False, "data_limited", ["Brinjal"]),
    ("potato", "Potato", "बटाटा", "Solanum tuberosum", "vegetable", "rabi", False, "data_limited", ["Potato"]),
    ("ginger", "Ginger", "आले", "Zingiber officinale", "commercial", "perennial", False, "data_limited", ["Ginger"]),
    ("turmeric", "Turmeric", "हळद", "Curcuma longa", "commercial", "perennial", False, "data_limited", ["Turmeric"]),
    ("garlic", "Garlic", "लसूण", "Allium sativum", "vegetable", "rabi", False, "data_limited", ["Garlic"]),
]


CROP_STAGES_DATA: List[Dict[str, object]] = [
    {
        "crop_code": "soybean",
        "stage_code": "VEGETATIVE",
        "stage_name_en": "Vegetative Growth",
        "stage_name_mr": "शाकीय वाढीची अवस्था",
        "sequence_order": 1,
        "typical_das_start": 0,
        "typical_das_end": 30,
        "description": "Heat: low | Drought: medium | Excess water: high | ICAR-IISR Technical Bulletin 44",
    },
    {
        "crop_code": "soybean",
        "stage_code": "R1_FLOWERING",
        "stage_name_en": "Flowering",
        "stage_name_mr": "फुलोरा अवस्था",
        "sequence_order": 2,
        "typical_das_start": 31,
        "typical_das_end": 50,
        "description": "Heat: critical | Drought: critical | Excess water: medium | ICAR-IISR Technical Bulletin 44",
    },
    {
        "crop_code": "soybean",
        "stage_code": "R3_POD_FILLING",
        "stage_name_en": "Pod Formation & Seed Filling",
        "stage_name_mr": "शेंगा भरणे व दाणे भरणे",
        "sequence_order": 3,
        "typical_das_start": 51,
        "typical_das_end": 85,
        "description": "Heat: high | Drought: critical | Excess water: low | ICAR-IISR Technical Bulletin 44",
    },
    {
        "crop_code": "soybean",
        "stage_code": "R7_MATURITY",
        "stage_name_en": "Maturity & Harvest",
        "stage_name_mr": "पक्वता व काढणी",
        "sequence_order": 4,
        "typical_das_start": 86,
        "typical_das_end": 105,
        "description": "Heat: low | Drought: low | Excess water: high | ICAR-IISR Technical Bulletin 44",
    },
    {
        "crop_code": "cotton",
        "stage_code": "VEGETATIVE",
        "stage_name_en": "Vegetative Growth & Square Formation",
        "stage_name_mr": "शाकीय वाढ व पाते लागणे",
        "sequence_order": 1,
        "typical_das_start": 0,
        "typical_das_end": 50,
        "description": "Heat: medium | Drought: medium | Excess water: high | ICAR-CICR Cotton Production Manual 2023",
    },
    {
        "crop_code": "cotton",
        "stage_code": "FLOWERING_BOLL_DEV",
        "stage_name_en": "Peak Flowering & Boll Development",
        "stage_name_mr": "फुलोरा व बोंड लागणे",
        "sequence_order": 2,
        "typical_das_start": 51,
        "typical_das_end": 110,
        "description": "Heat: critical | Drought: critical | Excess water: high | ICAR-CICR Cotton Production Manual 2023",
    },
]


AGRONOMIC_THRESHOLDS_DATA: List[Dict[str, object]] = [
    {
        "crop_code": "cotton",
        "stage_code": "FLOWERING_BOLL_DEV",
        "tmin_ideal_low": None,
        "tmax_ideal_high": 32.0,
        "tmax_stress_trigger": 36.0,
        "tmax_critical_damage": 38.0,
        "tmin_cold_trigger": None,
        "vpd_stress_trigger_kpa": None,
        "critical_heat_duration_hrs": 3,
        "evidence_tier": "peer_reviewed_experimental",
        "source_citation": (
            "ICAR-Central Institute for Cotton Research (CICR) Nagpur "
            "(CICR Annual Scientific Report 2023, p. 58)"
        ),
        "is_active": True,
    },
    {
        "crop_code": "cotton",
        "stage_code": "FLOWERING_BOLL_DEV",
        "tmin_ideal_low": 24.0,
        "tmax_ideal_high": None,
        "tmax_stress_trigger": None,
        "tmax_critical_damage": None,
        "tmin_cold_trigger": None,
        "vpd_stress_trigger_kpa": None,
        "critical_heat_duration_hrs": 6,
        "evidence_tier": "extension_publication",
        "source_citation": (
            "ICAR-CICR Nagpur (CICR Technical Bulletin 2022) — Warm night tmin >= 24.0 C"
        ),
        "is_active": True,
    },
    {
        "crop_code": "soybean",
        "stage_code": "R3_POD_FILLING",
        "tmin_ideal_low": None,
        "tmax_ideal_high": 30.0,
        "tmax_stress_trigger": 33.5,
        "tmax_critical_damage": 35.0,
        "tmin_cold_trigger": None,
        "vpd_stress_trigger_kpa": None,
        "critical_heat_duration_hrs": 4,
        "evidence_tier": "peer_reviewed_experimental",
        "source_citation": (
            "ICAR-Indian Institute of Soybean Research (IISR) Indore "
            "(IISR Research Bulletin 52, 2021)"
        ),
        "is_active": True,
    },
    {
        "crop_code": "soybean",
        "stage_code": "all",
        "tmin_ideal_low": None,
        "tmax_ideal_high": None,
        "tmax_stress_trigger": None,
        "tmax_critical_damage": None,
        "tmin_cold_trigger": None,
        "vpd_stress_trigger_kpa": None,
        "critical_heat_duration_hrs": 0,
        "evidence_tier": "university_package_of_practices",
        "source_citation": (
            "Mahatma Phule Krishi Vidyapeeth (MPKV) Rahuri "
            "(MPKV Soil Science Advisory Manual 2020) — Vertisol soil pH >= 8.5"
        ),
        "is_active": True,
    },
]


ADVISORY_CATALOGUE_DATA: List[Dict[str, object]] = [
    {
        "advisory_id": "ADV_SOY_DRY_01",
        "domain": "yield_risk",
        "target_crop_code": "soybean",
        "target_stage_code": None,
        "trigger_severity": "dry_spell",
        "title_en": "Protective Supplemental Irrigation for Soybean",
        "title_mr": "सोयाबीन पिकास संरक्षित पाणी देणे",
        "action_steps_en": [
            "Apply light protective irrigation (25-30 mm) via sprinkler or drip during critical flowering/pod development to prevent flower drop."
        ],
        "action_steps_mr": [
            "फुलोरा व शेंगा भरण्याच्या अवस्थेत पावसाचा १० दिवसांपेक्षा जास्त खंड पडल्यास तुषार किंवा ठिबक सिंचनाने एक संरक्षित पाणी द्यावे."
        ],
        "do_not_do_warning": "Avoid heavy flood irrigation in poorly drained Vertisols.",
        "cost_class": "low_cost",
        "lead_time_required_hours": 24,
        "source_attribution": "MPKV Rahuri Soybean Package of Practices 2023, p. 14",
        "is_verified_agronomist": True,
    },
    {
        "advisory_id": "ADV_COT_HEAT_01",
        "domain": "crop_heat",
        "target_crop_code": "cotton",
        "target_stage_code": None,
        "trigger_severity": "crop_heat",
        "title_en": "Foliar 2% Potassium Nitrate Spray Alleviation",
        "title_mr": "२% पोटॅशियम नायट्रेट (१३:०:४५) फवारणी",
        "action_steps_en": [
            "Spray 2% KNO3 (20 g/L water) in late evening to improve stomatal regulation, reduce canopy temperature, and reduce square dropping."
        ],
        "action_steps_mr": [
            "उष्णतेमुळे होणारी पातेगळ व फुलगळ रोखण्यासाठी संध्याकाळी २% १३:०:४५ (२० ग्रॅम प्रति लिटर पाणी) ची फवारणी करावी."
        ],
        "do_not_do_warning": "Do not spray during peak afternoon sunlight to prevent leaf scorch.",
        "cost_class": "low_cost",
        "lead_time_required_hours": 12,
        "source_attribution": "ICAR-CICR Cotton Advisory 2023",
        "is_verified_agronomist": True,
    },
]


def seed_canonical_crops(db: Session) -> int:
    """Idempotently upsert all 38 canonical Maharashtra crops."""
    count = 0
    for row in CANONICAL_CROPS_DATA:
        (
            crop_code,
            name_en,
            name_mr,
            botanical,
            category,
            season,
            is_pilot,
            support,
            aliases,
        ) = row
        existing = (
            db.query(RashkarCanonicalCropModel)
            .filter(RashkarCanonicalCropModel.crop_code == crop_code)
            .first()
        )
        if existing:
            existing.common_name_en = name_en
            existing.common_name_mr = name_mr
            existing.botanical_name = botanical
            existing.crop_category = category
            existing.standard_season = season
            existing.is_pioneer_pilot_crop = is_pilot
            existing.support_level = support
            existing.apy_alias_list = aliases
        else:
            db.add(
                RashkarCanonicalCropModel(
                    crop_code=crop_code,
                    common_name_en=name_en,
                    common_name_mr=name_mr,
                    botanical_name=botanical,
                    crop_category=category,
                    standard_season=season,
                    is_pioneer_pilot_crop=is_pilot,
                    support_level=support,
                    apy_alias_list=aliases,
                )
            )
        count += 1
    db.flush()
    return count


def seed_crop_stages(db: Session) -> int:
    """Idempotently upsert canonical crop phenological stages."""
    count = 0
    for item in CROP_STAGES_DATA:
        existing = (
            db.query(RashkarCropStageModel)
            .filter(
                RashkarCropStageModel.crop_code == item["crop_code"],
                RashkarCropStageModel.stage_code == item["stage_code"],
            )
            .first()
        )
        if existing:
            for field, val in item.items():
                setattr(existing, field, val)
        else:
            db.add(RashkarCropStageModel(**item))
        count += 1
    db.flush()
    return count


def seed_agronomic_thresholds(db: Session) -> int:
    """Idempotently upsert evidence-backed thermal thresholds."""
    count = 0
    for item in AGRONOMIC_THRESHOLDS_DATA:
        existing = (
            db.query(RashkarAgronomicThresholdModel)
            .filter(
                RashkarAgronomicThresholdModel.crop_code == item["crop_code"],
                RashkarAgronomicThresholdModel.stage_code == item["stage_code"],
                RashkarAgronomicThresholdModel.source_citation == item["source_citation"],
            )
            .first()
        )
        if existing:
            for field, val in item.items():
                setattr(existing, field, val)
        else:
            db.add(RashkarAgronomicThresholdModel(**item))
        count += 1
    db.flush()
    return count


def seed_advisory_catalogue(db: Session) -> int:
    """Idempotently upsert verified bilingual agronomic advisories."""
    count = 0
    for item in ADVISORY_CATALOGUE_DATA:
        existing = (
            db.query(RashkarAdvisoryCatalogueModel)
            .filter(RashkarAdvisoryCatalogueModel.advisory_id == item["advisory_id"])
            .first()
        )
        if existing:
            for field, val in item.items():
                setattr(existing, field, val)
        else:
            db.add(RashkarAdvisoryCatalogueModel(**item))
        count += 1
    db.flush()
    return count


def seed_income_opportunities(db: Session) -> int:
    """Idempotently upsert all curated Extra Income opportunities."""
    count = 0
    for item in EXTENDED_OPPORTUNITY_CATALOG:
        req_resources = getattr(item, "required_resources", None)
        if req_resources is None:
            space = getattr(item, "required_space_type", "none")
            req_resources = [space] if space and space != "none" else []

        existing = (
            db.query(RashkarIncomeOpportunityModel)
            .filter(
                RashkarIncomeOpportunityModel.opportunity_id == item.opportunity_id
            )
            .first()
        )
        payload = {
            "title": item.title,
            "category": item.category,
            "is_cost_saving": item.is_cost_saving,
            "tagline": item.tagline,
            "target_crops": list(item.target_crops),
            "required_resources": list(req_resources),
            "min_investment_inr": item.min_investment_inr,
            "max_investment_inr": item.max_investment_inr,
            "working_capital_required_inr": item.working_capital_required_inr,
            "payback_period_months": item.payback_period_months,
            "potential_annual_profit_inr": item.potential_annual_profit_inr,
            "potential_annual_savings_inr": item.potential_annual_savings_inr,
            "risk_level": item.risk_level,
            "summary": item.summary,
            "market_commodity": item.market_commodity,
            "market_benchmark_price": item.market_benchmark_price,
            "market_source": item.market_source,
            "key_assumptions": list(item.key_assumptions),
            "key_risks": list(item.key_risks),
            "source_attribution": item.source_attribution,
            "is_active": True,
        }
        if existing:
            for field, val in payload.items():
                setattr(existing, field, val)
        else:
            db.add(
                RashkarIncomeOpportunityModel(
                    opportunity_id=item.opportunity_id, **payload
                )
            )
        count += 1
    db.flush()
    return count


def seed_rashkar_reference_data(db: Session) -> Dict[str, int]:
    """Idempotently seed all RASHKAR canonical reference tables."""
    crops = seed_canonical_crops(db)
    stages = seed_crop_stages(db)
    thresholds = seed_agronomic_thresholds(db)
    advisories = seed_advisory_catalogue(db)
    opportunities = seed_income_opportunities(db)
    db.commit()
    return {
        "canonical_crops": crops,
        "crop_stages": stages,
        "agronomic_thresholds": thresholds,
        "advisory_catalogue": advisories,
        "income_opportunities": opportunities,
    }


__all__ = [
    "CANONICAL_CROPS_DATA",
    "CROP_STAGES_DATA",
    "AGRONOMIC_THRESHOLDS_DATA",
    "ADVISORY_CATALOGUE_DATA",
    "seed_canonical_crops",
    "seed_crop_stages",
    "seed_agronomic_thresholds",
    "seed_advisory_catalogue",
    "seed_income_opportunities",
    "seed_rashkar_reference_data",
]
