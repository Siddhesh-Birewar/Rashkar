from backend.app.db.session import engine, Base, SessionLocal
from backend.app.db.models.registry import DatasetRegistryModel
from backend.app.db.models.farm import FarmModel, FarmPlotModel, CropCycleModel
from backend.app.db.models.crop_knowledge import (
    CanonicalCropMasterModel,
    CropStageReferenceModel,
    AgronomicThresholdRegistryModel,
    AgronomicAdvisoryCatalogueModel
)
from backend.app.db.models.risk import (
    YieldAssessmentLogModel,
    WorkerHazardAuditLogModel,
    CropHeatAssessmentLogModel
)

def init_db():
    # Create all tables in the engine
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(CanonicalCropMasterModel).count() == 0:
            seed_canonical_crops(db)
            seed_crop_stages(db)
            seed_agronomic_thresholds(db)
            seed_advisories(db)
    finally:
        db.close()

def seed_canonical_crops(db):
    crops = [
        # Pioneer pilot crops
        CanonicalCropMasterModel(
            crop_code="soybean",
            common_name_en="Soybean",
            common_name_mr="सोयाबीन",
            botanical_name="Glycine max",
            crop_category="oilseed",
            standard_season="kharif",
            is_pioneer_pilot_crop=True,
            apy_alias_list=["Soyabean", "Soyabean(Bhat)", "Soybean"]
        ),
        CanonicalCropMasterModel(
            crop_code="cotton",
            common_name_en="Cotton",
            common_name_mr="कापूस",
            botanical_name="Gossypium hirsutum",
            crop_category="fibre",
            standard_season="kharif",
            is_pioneer_pilot_crop=True,
            apy_alias_list=["Cotton", "Cotton(lint)", "Kapas"]
        ),
        CanonicalCropMasterModel(
            crop_code="jowar",
            common_name_en="Jowar / Sorghum",
            common_name_mr="ज्वारी",
            botanical_name="Sorghum bicolor",
            crop_category="cereal",
            standard_season="kharif",
            is_pioneer_pilot_crop=True,
            apy_alias_list=["Jowar", "Sorghum", "Kharif Jowar", "Rabi Jowar"]
        ),
        CanonicalCropMasterModel(
            crop_code="sugarcane",
            common_name_en="Sugarcane",
            common_name_mr="ऊस",
            botanical_name="Saccharum officinarum",
            crop_category="commercial",
            standard_season="perennial",
            is_pioneer_pilot_crop=True,
            apy_alias_list=["Sugarcane", "Cane"]
        ),
        # Major Maharashtra state crops
        CanonicalCropMasterModel(
            crop_code="tur",
            common_name_en="Tur / Pigeon Pea",
            common_name_mr="तूर / अरहर",
            botanical_name="Cajanus cajan",
            crop_category="pulse",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            apy_alias_list=["Arhar/Tur", "Tur", "Pigeon Pea"]
        ),
        CanonicalCropMasterModel(
            crop_code="gram",
            common_name_en="Gram / Chickpea",
            common_name_mr="हरभरा / चणा",
            botanical_name="Cicer arietinum",
            crop_category="pulse",
            standard_season="rabi",
            is_pioneer_pilot_crop=False,
            apy_alias_list=["Gram", "Bengal Gram", "Chana"]
        ),
        CanonicalCropMasterModel(
            crop_code="bajra",
            common_name_en="Bajra / Pearl Millet",
            common_name_mr="बाजरी",
            botanical_name="Pennisetum glaucum",
            crop_category="millet",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            apy_alias_list=["Bajra", "Pearl Millet"]
        ),
        CanonicalCropMasterModel(
            crop_code="rice",
            common_name_en="Rice / Paddy",
            common_name_mr="भात / धान",
            botanical_name="Oryza sativa",
            crop_category="cereal",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            apy_alias_list=["Rice", "Paddy"]
        ),
        CanonicalCropMasterModel(
            crop_code="wheat",
            common_name_en="Wheat",
            common_name_mr="गहू",
            botanical_name="Triticum aestivum",
            crop_category="cereal",
            standard_season="rabi",
            is_pioneer_pilot_crop=False,
            apy_alias_list=["Wheat"]
        ),
        CanonicalCropMasterModel(
            crop_code="onion",
            common_name_en="Onion",
            common_name_mr="कांदा",
            botanical_name="Allium cepa",
            crop_category="vegetable",
            standard_season="rabi",
            is_pioneer_pilot_crop=False,
            apy_alias_list=["Onion"]
        ),
        CanonicalCropMasterModel(
            crop_code="pomegranate",
            common_name_en="Pomegranate",
            common_name_mr="डाळिंब",
            botanical_name="Punica granatum",
            crop_category="fruit",
            standard_season="perennial",
            is_pioneer_pilot_crop=False,
            apy_alias_list=["Pomegranate"]
        ),
        CanonicalCropMasterModel(
            crop_code="grapes",
            common_name_en="Grapes",
            common_name_mr="द्राक्षे",
            botanical_name="Vitis vinifera",
            crop_category="fruit",
            standard_season="perennial",
            is_pioneer_pilot_crop=False,
            apy_alias_list=["Grapes"]
        )
    ]
    db.add_all(crops)
    db.commit()

def seed_crop_stages(db):
    stages = [
        # Soybean Stages (MPKV Rahuri / ICAR-IISR)
        CropStageReferenceModel(
            stage_id="SOY_VEG",
            crop_code="soybean",
            stage_code="VEGETATIVE",
            stage_name_en="Vegetative Growth",
            stage_name_mr="शाकीय वाढीची अवस्था",
            sequence_order=1,
            typical_duration_days=30,
            das_start_typical=0,
            das_end_typical=30,
            heat_sensitivity="low",
            drought_sensitivity="medium",
            excess_water_sensitivity="high",
            source_citation="ICAR-IISR Technical Bulletin 44"
        ),
        CropStageReferenceModel(
            stage_id="SOY_FLOWER",
            crop_code="soybean",
            stage_code="R1_FLOWERING",
            stage_name_en="Flowering",
            stage_name_mr="फुलोरा अवस्था",
            sequence_order=2,
            typical_duration_days=20,
            das_start_typical=31,
            das_end_typical=50,
            heat_sensitivity="critical",
            drought_sensitivity="critical",
            excess_water_sensitivity="medium",
            source_citation="ICAR-IISR Technical Bulletin 44"
        ),
        CropStageReferenceModel(
            stage_id="SOY_POD",
            crop_code="soybean",
            stage_code="R3_POD_DEVELOPMENT",
            stage_name_en="Pod Development & Seed Filling",
            stage_name_mr="शेंगा भरणे व दाणे भरणे",
            sequence_order=3,
            typical_duration_days=30,
            das_start_typical=51,
            das_end_typical=80,
            heat_sensitivity="high",
            drought_sensitivity="critical",
            excess_water_sensitivity="medium",
            source_citation="MPKV Rahuri Kharif Crop Advisory 2025"
        ),
        CropStageReferenceModel(
            stage_id="SOY_MATURITY",
            crop_code="soybean",
            stage_code="R7_MATURITY",
            stage_name_en="Physiological Maturity & Harvest",
            stage_name_mr="पक्वता व काढणी अवस्था",
            sequence_order=4,
            typical_duration_days=20,
            das_start_typical=81,
            das_end_typical=100,
            heat_sensitivity="low",
            drought_sensitivity="low",
            excess_water_sensitivity="high",
            source_citation="MPKV Rahuri Kharif Crop Advisory 2025"
        ),
        # Cotton Stages (ICAR-CICR Nagpur / PDKV Akola)
        CropStageReferenceModel(
            stage_id="COT_VEG",
            crop_code="cotton",
            stage_code="VEGETATIVE",
            stage_name_en="Vegetative Growth & Square Formation",
            stage_name_mr="शाकीय वाढ व पाते लागणे",
            sequence_order=1,
            typical_duration_days=50,
            das_start_typical=0,
            das_end_typical=50,
            heat_sensitivity="medium",
            drought_sensitivity="medium",
            excess_water_sensitivity="high",
            source_citation="ICAR-CICR Cotton Production Manual 2023"
        ),
        CropStageReferenceModel(
            stage_id="COT_FLOWER",
            crop_code="cotton",
            stage_code="FLOWERING_BOLL_DEV",
            stage_name_en="Peak Flowering & Boll Development",
            stage_name_mr="फुलोरा व बोंड लागणे",
            sequence_order=2,
            typical_duration_days=60,
            das_start_typical=51,
            das_end_typical=110,
            heat_sensitivity="critical",
            drought_sensitivity="critical",
            excess_water_sensitivity="high",
            source_citation="ICAR-CICR Cotton Production Manual 2023"
        )
    ]
    db.add_all(stages)
    db.commit()

def seed_agronomic_thresholds(db):
    thresholds = [
        # Cotton Heat Thresholds (ICAR-CICR Nagpur)
        AgronomicThresholdRegistryModel(
            threshold_id="THRESH_COT_HEAT_FLOWER",
            crop_code="cotton",
            applicable_variety="all",
            agro_ecological_zone="Maharashtra Statewide",
            growth_stage="FLOWERING_BOLL_DEV",
            environmental_variable="tmax_c",
            unit="celsius",
            critical_threshold=38.0,
            required_exposure_duration_hours=3,
            comparison_operator=">=",
            physiological_impact="Pollen desiccation and square/young boll shedding",
            source_institution="ICAR-Central Institute for Cotton Research (CICR) Nagpur",
            publication_citation="CICR Annual Scientific Report 2023, p. 58",
            publication_year=2023,
            evidence_grade="peer_reviewed_experimental",
            verification_status="verified_by_agronomist"
        ),
        AgronomicThresholdRegistryModel(
            threshold_id="THRESH_COT_WARM_NIGHT",
            crop_code="cotton",
            applicable_variety="all",
            agro_ecological_zone="Maharashtra Statewide",
            growth_stage="FLOWERING_BOLL_DEV",
            environmental_variable="tmin_c",
            unit="celsius",
            critical_threshold=24.0,
            required_exposure_duration_hours=6,
            comparison_operator=">=",
            physiological_impact="Elevated dark respiration consuming plant carbohydrates and inducing square abortion",
            source_institution="ICAR-CICR Nagpur",
            publication_citation="CICR Technical Bulletin 2022",
            publication_year=2022,
            evidence_grade="extension_publication",
            verification_status="verified_by_agronomist"
        ),
        # Soybean Heat Thresholds (ICAR-IISR Indore)
        AgronomicThresholdRegistryModel(
            threshold_id="THRESH_SOY_HEAT_POD",
            crop_code="soybean",
            applicable_variety="all",
            agro_ecological_zone="Maharashtra Statewide",
            growth_stage="R1_FLOWERING",
            environmental_variable="tmax_c",
            unit="celsius",
            critical_threshold=35.0,
            required_exposure_duration_hours=4,
            comparison_operator=">=",
            physiological_impact="Stigma drying, poor fertilization, and flower abortion",
            source_institution="ICAR-Indian Institute of Soybean Research (IISR) Indore",
            publication_citation="IISR Technical Bulletin 44, 2021",
            publication_year=2021,
            evidence_grade="peer_reviewed_experimental",
            verification_status="verified_by_agronomist"
        ),
        # Sugarcane Heat Threshold (VSI Pune)
        AgronomicThresholdRegistryModel(
            threshold_id="THRESH_SUG_HEAT_TILLER",
            crop_code="sugarcane",
            applicable_variety="all",
            agro_ecological_zone="Western Maharashtra (Pune/Solapur)",
            growth_stage="TILLERING",
            environmental_variable="tmax_c",
            unit="celsius",
            critical_threshold=40.0,
            required_exposure_duration_hours=5,
            comparison_operator=">=",
            physiological_impact="High evaporative demand, leaf scorching, and reduced tiller survival",
            source_institution="Vasantdada Sugar Institute (VSI) Pune",
            publication_citation="VSI Agronomy Extension Guidelines 2022",
            publication_year=2022,
            evidence_grade="extension_publication",
            verification_status="verified_by_agronomist"
        )
    ]
    db.add_all(thresholds)
    db.commit()

def seed_advisories(db):
    advisories = [
        AgronomicAdvisoryCatalogueModel(
            action_id="ACT_SOY_DRY_01",
            crop_code="soybean",
            risk_dimension="dry_spell",
            title_en="Protective Irrigation or Straw Mulching",
            title_mr="संरक्षित पाणी किंवा सेंद्रिय आच्छादन",
            description_en="Provide one protective irrigation at flowering/pod development to prevent flower/pod abortion. If water is limited, apply crop residue or straw mulch to reduce soil evaporative loss.",
            description_mr="फुलोरा किंवा शेंगा धरण्याच्या अवस्थेत संरक्षित पाणी द्यावे. पाणी कमी असल्यास जमिनीतील ओलावा टिकवण्यासाठी सेंद्रिय आच्छादनाचा वापर करावा.",
            evidence_citation="MPKV Rahuri Kharif Crop Advisory 2025, p. 42",
            expert_reviewer="Dr. Agronomy, MPKV"
        ),
        AgronomicAdvisoryCatalogueModel(
            action_id="ACT_COT_HEAT_01",
            crop_code="cotton",
            risk_dimension="crop_heat",
            title_en="Light Evening Irrigation & Potassium Spray",
            title_mr="हलके पाणी व पोटॅशियम फवारणी",
            description_en="Apply light evening irrigation to reduce canopy temperature. In areas with high heat stress during flowering, spray 1% Potassium Nitrate (13:0:45) to enhance cellular osmotic regulation.",
            description_mr="पिकाचे तापमान कमी करण्यासाठी संध्याकाळी हलके पाणी द्यावे. उष्णतेच्या ताणापासून बचावासाठी १% पोटॅशियम नायट्रेट (१३:०:४५) फवारावे.",
            evidence_citation="ICAR-CICR Cotton Advisory 2024",
            expert_reviewer="CICR Scientist"
        )
    ]
    db.add_all(advisories)
    db.commit()
