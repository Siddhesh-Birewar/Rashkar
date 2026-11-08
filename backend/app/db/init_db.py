from sqlalchemy import text
from backend.app.db.session import engine, Base, SessionLocal
from backend.app.db.models.registry import DatasetRegistryModel
from backend.app.db.models.farm import FarmerModel, FarmModel, FarmPlotModel, CropCycleModel, SoilProfileModel
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
from backend.app.db.models.income import IncomeOpportunityModel, IncomeScenarioModel
from backend.app.db.models.pmfby import CropLossCaseModel
from backend.app.db.models.assistant import AssistantSessionModel, AssistantMessageModel
from datetime import date, datetime

def init_db():
    # Attempt non-destructive column migration for local SQLite
    with engine.connect() as conn:
        for stmt in [
            "ALTER TABLE canonical_crops ADD COLUMN support_level VARCHAR(50) DEFAULT 'data_limited'",
            "ALTER TABLE farms ADD COLUMN total_area_acres FLOAT",
            "ALTER TABLE crop_cycles ADD COLUMN planted_area_acres FLOAT"
        ]:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                pass

    # Create all tables in the engine
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if already seeded or update existing
        if db.query(CanonicalCropMasterModel).count() < 30:
            db.query(CanonicalCropMasterModel).delete()
            seed_canonical_crops(db)
        if db.query(CropStageReferenceModel).count() == 0:
            seed_crop_stages(db)
        if db.query(AgronomicThresholdRegistryModel).count() == 0:
            seed_agronomic_thresholds(db)
        if db.query(AgronomicAdvisoryCatalogueModel).count() == 0:
            seed_advisories(db)
        if db.query(FarmerModel).count() == 0:
            seed_demo_farmer_and_farm(db)
        if db.query(IncomeOpportunityModel).count() == 0:
            seed_income_opportunities(db)
    finally:
        db.close()

def seed_canonical_crops(db):
    crops = [
        # --- Level 1: Rule and Baseline Supported (Pioneer Pilot Crops) ---
        CanonicalCropMasterModel(
            crop_code="soybean",
            common_name_en="Soybean",
            common_name_mr="सोयाबीन",
            botanical_name="Glycine max",
            crop_category="oilseed",
            standard_season="kharif",
            is_pioneer_pilot_crop=True,
            support_level="rule_and_baseline_supported",
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
            support_level="rule_and_baseline_supported",
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
            support_level="rule_and_baseline_supported",
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
            support_level="rule_and_baseline_supported",
            apy_alias_list=["Sugarcane", "Cane"]
        ),

        # --- Level 2: Advisory Only (Major Maharashtra Staples & Cash Crops) ---
        CanonicalCropMasterModel(
            crop_code="tur",
            common_name_en="Tur / Pigeon Pea",
            common_name_mr="तूर / अरहर",
            botanical_name="Cajanus cajan",
            crop_category="pulse",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            support_level="advisory_only",
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
            support_level="advisory_only",
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
            support_level="advisory_only",
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
            support_level="advisory_only",
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
            support_level="advisory_only",
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
            support_level="advisory_only",
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
            support_level="advisory_only",
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
            support_level="advisory_only",
            apy_alias_list=["Grapes"]
        ),

        # --- Level 3: Data Limited (Secondary Field Crops, Oilseeds & Horticulture) ---
        CanonicalCropMasterModel(
            crop_code="groundnut",
            common_name_en="Groundnut / Peanut",
            common_name_mr="भुईमूग",
            botanical_name="Arachis hypogaea",
            crop_category="oilseed",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Groundnut", "Peanut"]
        ),
        CanonicalCropMasterModel(
            crop_code="sunflower",
            common_name_en="Sunflower",
            common_name_mr="सूर्यफूल",
            botanical_name="Helianthus annuus",
            crop_category="oilseed",
            standard_season="rabi",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Sunflower"]
        ),
        CanonicalCropMasterModel(
            crop_code="maize",
            common_name_en="Maize / Corn",
            common_name_mr="मका",
            botanical_name="Zea mays",
            crop_category="cereal",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Maize", "Corn"]
        ),
        CanonicalCropMasterModel(
            crop_code="moong",
            common_name_en="Moong / Green Gram",
            common_name_mr="मूग",
            botanical_name="Vigna radiata",
            crop_category="pulse",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Moong(Green Gram)", "Moong"]
        ),
        CanonicalCropMasterModel(
            crop_code="urad",
            common_name_en="Urad / Black Gram",
            common_name_mr="उडीद",
            botanical_name="Vigna mungo",
            crop_category="pulse",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Urad", "Black Gram"]
        ),
        CanonicalCropMasterModel(
            crop_code="safflower",
            common_name_en="Safflower / Kardi",
            common_name_mr="करडई",
            botanical_name="Carthamus tinctorius",
            crop_category="oilseed",
            standard_season="rabi",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Safflower", "Kardi"]
        ),
        CanonicalCropMasterModel(
            crop_code="sesamum",
            common_name_en="Sesamum / Til",
            common_name_mr="तीळ",
            botanical_name="Sesamum indicum",
            crop_category="oilseed",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Sesamum", "Til"]
        ),
        CanonicalCropMasterModel(
            crop_code="niger",
            common_name_en="Niger Seed / Karale",
            common_name_mr="कारळे",
            botanical_name="Guizotia abyssinica",
            crop_category="oilseed",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Niger seed", "Karale"]
        ),
        CanonicalCropMasterModel(
            crop_code="castor",
            common_name_en="Castor Seed",
            common_name_mr="एरंडी",
            botanical_name="Ricinus communis",
            crop_category="oilseed",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Castor seed"]
        ),
        CanonicalCropMasterModel(
            crop_code="linseed",
            common_name_en="Linseed / Alsi",
            common_name_mr="जवस",
            botanical_name="Linum usitatissimum",
            crop_category="oilseed",
            standard_season="rabi",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Linseed", "Alsi"]
        ),
        CanonicalCropMasterModel(
            crop_code="ragi",
            common_name_en="Finger Millet / Ragi / Nachani",
            common_name_mr="नाचणी / रागी",
            botanical_name="Eleusine coracana",
            crop_category="millet",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Ragi", "Finger Millet", "Nachani"]
        ),
        CanonicalCropMasterModel(
            crop_code="small_millets",
            common_name_en="Small Millets / Vari / Kodra",
            common_name_mr="वरी / कोद्रा / सावा",
            botanical_name="Panicum sumatrense",
            crop_category="millet",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Small millets", "Vari", "Kodra"]
        ),
        CanonicalCropMasterModel(
            crop_code="banana",
            common_name_en="Banana",
            common_name_mr="केळी",
            botanical_name="Musa acuminata",
            crop_category="fruit",
            standard_season="perennial",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Banana"]
        ),
        CanonicalCropMasterModel(
            crop_code="mango",
            common_name_en="Mango / Alphonso",
            common_name_mr="आंबा / हापूस",
            botanical_name="Mangifera indica",
            crop_category="fruit",
            standard_season="perennial",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Mango"]
        ),
        CanonicalCropMasterModel(
            crop_code="sweet_orange",
            common_name_en="Sweet Orange / Mosambi",
            common_name_mr="मोसंबी",
            botanical_name="Citrus sinensis",
            crop_category="fruit",
            standard_season="perennial",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Sweet Orange", "Mosambi", "Citrus"]
        ),
        CanonicalCropMasterModel(
            crop_code="mandarin",
            common_name_en="Mandarin / Nagpur Santra",
            common_name_mr="संत्री",
            botanical_name="Citrus reticulata",
            crop_category="fruit",
            standard_season="perennial",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Orange", "Santra"]
        ),
        CanonicalCropMasterModel(
            crop_code="custard_apple",
            common_name_en="Custard Apple / Sitaphal",
            common_name_mr="सीताफळ",
            botanical_name="Annona squamosa",
            crop_category="fruit",
            standard_season="perennial",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Custard Apple", "Sitaphal"]
        ),
        CanonicalCropMasterModel(
            crop_code="guava",
            common_name_en="Guava / Amrud",
            common_name_mr="पेरू",
            botanical_name="Psidium guajava",
            crop_category="fruit",
            standard_season="perennial",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Guava", "Peru"]
        ),
        CanonicalCropMasterModel(
            crop_code="papaya",
            common_name_en="Papaya",
            common_name_mr="पपई",
            botanical_name="Carica papaya",
            crop_category="fruit",
            standard_season="perennial",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Papaya"]
        ),
        CanonicalCropMasterModel(
            crop_code="tomato",
            common_name_en="Tomato",
            common_name_mr="टोमॅटो",
            botanical_name="Solanum lycopersicum",
            crop_category="vegetable",
            standard_season="rabi",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Tomato"]
        ),
        CanonicalCropMasterModel(
            crop_code="chilli",
            common_name_en="Chilli",
            common_name_mr="मिरची",
            botanical_name="Capsicum annuum",
            crop_category="vegetable",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Chilli", "Chillies"]
        ),
        CanonicalCropMasterModel(
            crop_code="brinjal",
            common_name_en="Brinjal / Eggplant",
            common_name_mr="वांगी",
            botanical_name="Solanum melongena",
            crop_category="vegetable",
            standard_season="kharif",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Brinjal"]
        ),
        CanonicalCropMasterModel(
            crop_code="potato",
            common_name_en="Potato",
            common_name_mr="बटाटा",
            botanical_name="Solanum tuberosum",
            crop_category="vegetable",
            standard_season="rabi",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Potato"]
        ),
        CanonicalCropMasterModel(
            crop_code="ginger",
            common_name_en="Ginger",
            common_name_mr="आले",
            botanical_name="Zingiber officinale",
            crop_category="commercial",
            standard_season="perennial",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Ginger"]
        ),
        CanonicalCropMasterModel(
            crop_code="turmeric",
            common_name_en="Turmeric",
            common_name_mr="हळद",
            botanical_name="Curcuma longa",
            crop_category="commercial",
            standard_season="perennial",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Turmeric"]
        ),
        CanonicalCropMasterModel(
            crop_code="garlic",
            common_name_en="Garlic",
            common_name_mr="लसूण",
            botanical_name="Allium sativum",
            crop_category="vegetable",
            standard_season="rabi",
            is_pioneer_pilot_crop=False,
            support_level="data_limited",
            apy_alias_list=["Garlic"]
        )
    ]
    db.add_all(crops)
    db.commit()
    print(f"[SEEDED] Seeded {len(crops)} canonical crops across Maharashtra with verified support levels.")

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
            stage_id="SOY_POD_FILL",
            crop_code="soybean",
            stage_code="R3_POD_FILLING",
            stage_name_en="Pod Formation & Seed Filling",
            stage_name_mr="शेंगा भरणे व दाणे भरणे",
            sequence_order=3,
            typical_duration_days=35,
            das_start_typical=51,
            das_end_typical=85,
            heat_sensitivity="high",
            drought_sensitivity="critical",
            excess_water_sensitivity="low",
            source_citation="ICAR-IISR Technical Bulletin 44"
        ),
        CropStageReferenceModel(
            stage_id="SOY_MATURITY",
            crop_code="soybean",
            stage_code="R7_MATURITY",
            stage_name_en="Maturity & Harvest",
            stage_name_mr="पक्वता व काढणी",
            sequence_order=4,
            typical_duration_days=15,
            das_start_typical=86,
            das_end_typical=105,
            heat_sensitivity="low",
            drought_sensitivity="low",
            excess_water_sensitivity="high",
            source_citation="ICAR-IISR Technical Bulletin 44"
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
            growth_stage="R3_POD_FILLING",
            environmental_variable="tmax_c",
            unit="celsius",
            critical_threshold=35.0,
            required_exposure_duration_hours=4,
            comparison_operator=">=",
            physiological_impact="Accelerated senescence, reduced seed weight and shrivelled grain",
            source_institution="ICAR-Indian Institute of Soybean Research (IISR) Indore",
            publication_citation="IISR Research Bulletin 52, 2021",
            publication_year=2021,
            evidence_grade="peer_reviewed_experimental",
            verification_status="verified_by_agronomist"
        ),
        # Soil pH Threshold (MPKV Rahuri)
        AgronomicThresholdRegistryModel(
            threshold_id="THRESH_VERTISOL_PH_HIGH",
            crop_code="soybean",
            applicable_variety="all",
            agro_ecological_zone="Maharashtra Vertisols (Black Cotton Soils)",
            growth_stage="all",
            environmental_variable="ph",
            unit="pH_scale",
            critical_threshold=8.5,
            required_exposure_duration_hours=0,
            comparison_operator=">=",
            physiological_impact="Severe lime-induced iron (Fe) and zinc (Zn) deficiency, chlorosis",
            source_institution="Mahatma Phule Krishi Vidyapeeth (MPKV) Rahuri",
            publication_citation="MPKV Soil Science Advisory Manual 2020",
            publication_year=2020,
            evidence_grade="university_package_of_practices",
            verification_status="verified_by_agronomist"
        )
    ]
    db.add_all(thresholds)
    db.commit()

def seed_advisories(db):
    advisories = [
        AgronomicAdvisoryCatalogueModel(
            action_id="ADV_SOY_DRY_01",
            crop_code="soybean",
            risk_dimension="dry_spell",
            title_en="Protective Supplemental Irrigation for Soybean",
            title_mr="सोयाबीन पिकास संरक्षित पाणी देणे",
            description_en="Apply light protective irrigation (25-30 mm) via sprinkler or drip during critical flowering/pod development to prevent flower drop.",
            description_mr="फुलोरा व शेंगा भरण्याच्या अवस्थेत पावसाचा १० दिवसांपेक्षा जास्त खंड पडल्यास तुषार किंवा ठिबक सिंचनाने एक संरक्षित पाणी द्यावे.",
            evidence_citation="MPKV Rahuri Soybean Package of Practices 2023, p. 14"
        ),
        AgronomicAdvisoryCatalogueModel(
            action_id="ADV_COT_HEAT_01",
            crop_code="cotton",
            risk_dimension="crop_heat",
            title_en="Foliar 2% Potassium Nitrate Spray Alleviation",
            title_mr="२% पोटॅशियम नायट्रेट (१३:०:४५) फवारणी",
            description_en="Spray 2% KNO3 (20 g/L water) in late evening to improve stomatal regulation, reduce canopy temperature, and reduce square dropping.",
            description_mr="उष्णतेमुळे होणारी पातेगळ व फुलगळ रोखण्यासाठी संध्याकाळी २% १३:०:४५ (२० ग्रॅम प्रति लिटर पाणी) ची फवारणी करावी.",
            evidence_citation="ICAR-CICR Cotton Advisory 2023"
        )
    ]
    db.add_all(advisories)
    db.commit()

def seed_demo_farmer_and_farm(db):
    farmer = FarmerModel(
        farmer_id="farmer_demo_01",
        full_name="Ramesh Patil",
        phone_number="+91 98765 43210",
        state="Maharashtra",
        district="Pune",
        taluka="Baramati",
        village="Malegaon Budruk",
        preferred_language="en"
    )
    db.add(farmer)
    db.flush()

    farm = FarmModel(
        farm_id="farm_demo_pune_01",
        owner_id=farmer.farmer_id,
        farm_name="Patil Krishi Farm",
        total_area_acres=4.5,
        state="Maharashtra",
        district="Pune",
        taluka="Baramati",
        village="Malegaon Budruk",
        latitude=18.151,
        longitude=74.577
    )
    db.add(farm)
    db.flush()

    plot = FarmPlotModel(
        plot_id="plot_demo_01",
        farm_id=farm.farm_id,
        plot_name="Wadgaon Shivar Plot 1",
        area_acres=2.5,
        irrigation_type="rainfed",
        polygon_geojson={
            "type": "Polygon",
            "coordinates": [[[74.576, 18.150], [74.578, 18.150], [74.578, 18.152], [74.576, 18.152], [74.576, 18.150]]]
        }
    )
    db.add(plot)
    db.flush()

    cycle = CropCycleModel(
        cycle_id="cycle_demo_01",
        plot_id=plot.plot_id,
        crop_code="soybean",
        variety_name="JS 335",
        season="kharif",
        sowing_date=date(2024, 6, 15),
        planted_area_acres=2.5,
        current_stage_code="stage_pod_development",
        is_active=True
    )
    db.add(cycle)

    soil = SoilProfileModel(
        soil_id="soil_demo_01",
        farm_id=farm.farm_id,
        depth_interval="0-30cm",
        ph=7.8,
        organic_carbon_pct=0.58,
        clay_pct=52.0,
        sand_pct=18.0,
        silt_pct=30.0,
        bulk_density_g_cm3=1.32,
        cec_cmol_kg=48.5,
        available_water_capacity_mm_m=160.0,
        data_provenance="CropNet_UnifiedSoilProfile_v1",
        is_lab_measured=False
    )
    db.add(soil)
    db.commit()

def seed_income_opportunities(db):
    opps = [
        IncomeOpportunityModel(
            opportunity_id="OPP_VERMICOMPOST_01",
            title="Farm-Scale Vermicomposting from Crop Residues",
            category="byproduct_utilization",
            target_crops=["soybean", "cotton", "sugarcane"],
            required_resources=["crop_residue", "cow_dung", "shade_net", "water"],
            min_investment_inr=18000.0,
            max_investment_inr=35000.0,
            payback_period_months=4,
            potential_annual_profit_inr=54000.0,
            risk_level="low",
            summary="Convert harvested crop biomass into high-value organic vermicompost for self-farm nutrition and local nursery sales.",
            key_assumptions=[
                "Biomass availability: 2-3 tonnes per season",
                "Compost cycle time: 60-75 days",
                "Local bulk sales price: ₹6 to ₹8 per kg"
            ],
            key_risks=[
                "Moisture management during peak summer heat",
                "Termite infestation if bed is dry"
            ],
            source_attribution="KVK Baramati & ICAR-NIASM Baramati Agri-Allied Practice"
        ),
        IncomeOpportunityModel(
            opportunity_id="OPP_OSMANABADI_GOAT_01",
            title="Osmanabadi Goat Rearing Unit (10+1)",
            category="livestock",
            target_crops=["soybean", "jowar", "bajra"],
            required_resources=["shed", "fodder", "fencing"],
            min_investment_inr=85000.0,
            max_investment_inr=140000.0,
            payback_period_months=12,
            potential_annual_profit_inr=95000.0,
            risk_level="moderate",
            summary="Hardy drought-tolerant indigenous breed reared on farm-grown dry fodders and pulse husks with high meat market demand.",
            key_assumptions=[
                "Twinning rate: ~60-70% for Osmanabadi breed",
                "Kid marketing at 8-10 months (25-30 kg live weight)",
                "Live weight price: ₹300-340 per kg"
            ],
            key_risks=[
                "PPR and enterotoxemia disease outbreaks if vaccinations are missed",
                "Green fodder shortage in April-May"
            ],
            source_attribution="MPKV Rahuri Goat & Sheep Directorate / Pune District KVK"
        ),
        IncomeOpportunityModel(
            opportunity_id="OPP_SOLAR_DRYER_01",
            title="Solar Conduction Dryer for Onion & Chillies",
            category="value_addition",
            target_crops=["onion", "tomato"],
            required_resources=["direct_sunlight", "grading_area", "packaging"],
            min_investment_inr=45000.0,
            max_investment_inr=85000.0,
            payback_period_months=8,
            potential_annual_profit_inr=65000.0,
            risk_level="moderate",
            summary="Prevents distress sales during market gluts by dehydrating surplus produce into shelf-stable flakes and powders.",
            key_assumptions=[
                "Processing capacity: 15-20 kg per batch",
                "Dehydration ratio: 8:1 for onions",
                "Dry onion flake market price: ₹220-280 per kg"
            ],
            key_risks=[
                "Unseasonal cloudy weather or rain during Kharif drying cycles",
                "Moisture-proof packing requirements"
            ],
            source_attribution="ICAR-DOGR (Directorate of Onion and Garlic Research), Rajgurunagar, Pune"
        )
    ]
    db.add_all(opps)
    db.commit()
