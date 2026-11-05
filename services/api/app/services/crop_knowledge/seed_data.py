"""
Authoritative agricultural knowledge base data seeded from:
- Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri — Package of Practices (कृषी दैनंदिनी)
- ICAR Research Institutes: IISR (Sugarcane), NRCP (Pomegranate), IISR (Soybean), CICR (Cotton),
  IIMR (Maize & Sorghum), IIWBR (Wheat), AICRP-PearlMillet, IIPR (Chickpea), DGR (Groundnut)
"""

KNOWLEDGE_SOURCES = [
    {
        "id": "mpkv_pop_2023",
        "organization": "Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri",
        "publication_title": "Package of Practices for Field Crops & Agro-Techniques of Western Maharashtra (कृषी दैनंदिनी २०२३-२४)",
        "publication_year": 2023,
        "document_url_or_ref": "https://mpkv.ac.in/extension/package-of-practices",
        "section_or_pages": "Cereals, Pulses, Oilseeds and Cash Crops Recommendations, pp. 24–168",
        "evidence_quality": "verified_authoritative"
    },
    {
        "id": "icar_iisr_sugarcane_2022",
        "organization": "ICAR — Indian Institute of Sugarcane Research (IISR), Lucknow",
        "publication_title": "Good Agricultural Practices in Sugarcane Cultivation for Tropical India",
        "publication_year": 2022,
        "document_url_or_ref": "https://iisr.icar.gov.in/iisr/crop-production-technologies",
        "section_or_pages": "Water management & soil suitability in Peninsular Zone, pp. 12–38",
        "evidence_quality": "verified_authoritative"
    },
    {
        "id": "icar_nrcp_pomegranate_2021",
        "organization": "ICAR — National Research Centre on Pomegranate (NRCP), Solapur",
        "publication_title": "Scientific Pomegranate Production Manual for Semi-Arid Tropics",
        "publication_year": 2021,
        "document_url_or_ref": "https://nrcpomegranate.icar.gov.in/production-technology",
        "section_or_pages": "Soil suitability, Bahar regulation and wilt management, pp. 15–45",
        "evidence_quality": "verified_authoritative"
    },
    {
        "id": "icar_iisr_soybean_2022",
        "organization": "ICAR — Indian Institute of Soybean Research (IISR), Indore",
        "publication_title": "Soybean Production Technologies for Central and Peninsular India",
        "publication_year": 2022,
        "document_url_or_ref": "https://iisrindore.icar.gov.in/technologies",
        "section_or_pages": "Varietal guide and water stress mitigation, pp. 8–24",
        "evidence_quality": "verified_authoritative"
    },
    {
        "id": "icar_cicr_cotton_2022",
        "organization": "ICAR — Central Institute for Cotton Research (CICR), Nagpur",
        "publication_title": "Cotton Production Technology for Rainfed and Irrigated Vertisols of Maharashtra",
        "publication_year": 2022,
        "document_url_or_ref": "https://cicr.icar.gov.in/production-technology",
        "section_or_pages": "Soil depth and drainage criteria for Bt Cotton, pp. 14–32",
        "evidence_quality": "verified_authoritative"
    },
    {
        "id": "icar_iiwbr_wheat_2022",
        "organization": "ICAR — Indian Institute of Wheat and Barley Research (IIWBR), Karnal",
        "publication_title": "Wheat Production Technologies for Peninsular Zone of India",
        "publication_year": 2022,
        "document_url_or_ref": "https://iiwbr.icar.gov.in/peninsular-zone-technologies",
        "section_or_pages": "Thermal constraints and CRI irrigation scheduling, pp. 18–35",
        "evidence_quality": "verified_authoritative"
    },
    {
        "id": "icar_iimr_millets_2022",
        "organization": "ICAR — Indian Institute of Millets Research (IIMR), Hyderabad",
        "publication_title": "Sorghum and Small Millets Production Guide for Dryland Agriculture",
        "publication_year": 2022,
        "document_url_or_ref": "https://millets.res.in/technologies",
        "section_or_pages": "Rabi Jowar Maldandi agronomy in Deccan Vertisols, pp. 22–50",
        "evidence_quality": "verified_authoritative"
    },
    {
        "id": "icar_iipr_pulses_2022",
        "organization": "ICAR — Indian Institute of Pulses Research (IIPR), Kanpur",
        "publication_title": "Chickpea Production Technology and Moisture Conservation in Peninsular Vertisols",
        "publication_year": 2022,
        "document_url_or_ref": "https://iipr.icar.gov.in/chickpea-technologies",
        "section_or_pages": "Rabi chickpea wilt prevention and soil criteria, pp. 10–28",
        "evidence_quality": "verified_authoritative"
    }
]

CROPS_DATA = [
    # 1. Sugarcane
    {
        "id": "sugarcane",
        "common_name": "Sugarcane",
        "scientific_name": "Saccharum officinarum L.",
        "marathi_name": "ऊस",
        "hindi_name": "गन्ना",
        "category": "Cash Crop",
        "crop_type": "Semi-perennial (12-18 months)",
        "typical_duration_days_min": 360,
        "typical_duration_days_max": 540,
        "recommended_varieties": ["Co 86032 (Nira)", "CoM 0265 (Phule 265)", "MS 10001 (Phule 10001)", "VSI 08005"],
        "source_id": "mpkv_pop_2023",
        "soil": {
            "preferred_textures": ["Clay", "Clay Loam", "Deep Black Vertisol"],
            "acceptable_textures": ["Sandy Clay Loam", "Loam"],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 7.8,
            "ph_tolerable_min": 6.0,
            "ph_tolerable_max": 8.5,
            "drainage_requirement": "Well-drained; highly sensitive to prolonged waterlogging (> 48 hrs reduces tillering)",
            "salinity_sensitivity": "Moderately Sensitive (EC < 2.0 dS/m; yield drops 10% per dS/m increase above threshold)",
            "min_soil_depth_cm": 90.0,
            "optimum_organic_carbon_g_kg": 7.5,
            "water_holding_capacity_pref": "High (Deep Vertisols with > 50% clay retain essential moisture)",
            "source_id": "icar_iisr_sugarcane_2022"
        },
        "climate": {
            "temp_optimum_min_c": 24.0,
            "temp_optimum_max_c": 34.0,
            "temp_tolerable_min_c": 15.0,
            "temp_tolerable_max_c": 40.0,
            "annual_rainfall_min_mm": 1500.0,
            "annual_rainfall_max_mm": 2500.0,
            "humidity_preference": "High relative humidity (65–85%) during formative & elongation stages",
            "frost_sensitivity": "Highly Sensitive; frost stops elongation and damages terminal buds",
            "heat_sensitivity": "Moderate; temperatures > 38°C slow tillering unless frequent irrigation supplied",
            "solar_radiation_requirement": "High sunlight requirement; C4 photosynthetic pathway",
            "source_id": "icar_iisr_sugarcane_2022"
        },
        "seasons": [
            {
                "season_name": "Adsali",
                "is_primary_season": True,
                "planting_window_maharashtra": "15 July to 15 August",
                "harvesting_window_maharashtra": "November to January (after 16–18 months)",
                "duration_days_min": 480,
                "duration_days_max": 540,
                "planting_calendar_by_region": {"Baramati": "15 July - 10 August", "Indapur": "15 July - 15 August"},
                "source_id": "mpkv_pop_2023"
            },
            {
                "season_name": "Pre-seasonal",
                "is_primary_season": False,
                "planting_window_maharashtra": "15 October to 15 November",
                "harvesting_window_maharashtra": "December to February (after 14–15 months)",
                "duration_days_min": 420,
                "duration_days_max": 450,
                "planting_calendar_by_region": {"Baramati": "15 October - 15 November", "Indapur": "20 October - 20 November"},
                "source_id": "mpkv_pop_2023"
            },
            {
                "season_name": "Suru",
                "is_primary_season": False,
                "planting_window_maharashtra": "15 January to 15 February",
                "harvesting_window_maharashtra": "January to March (after 12 months)",
                "duration_days_min": 360,
                "duration_days_max": 380,
                "planting_calendar_by_region": {"Baramati": "15 January - 15 February", "Indapur": "15 January - 20 February"},
                "source_id": "mpkv_pop_2023"
            }
        ],
        "water": {
            "annual_water_requirement_mm_min": 1800.0,
            "annual_water_requirement_mm_max": 2500.0,
            "rainfed_suitable": False,
            "irrigation_dependency": "Critical / High (requires 25–35 irrigations under furrow, or daily drip)",
            "critical_growth_stages": [
                "Germination phase (0–35 DAP)",
                "Formative / Tillering stage (60–130 DAP) — Peak water requirement",
                "Grand growth phase (130–250 DAP)"
            ],
            "waterlogging_sensitivity": "Moderately Tolerant, but water stagnation > 48 hrs reduces tillering and sugar recovery",
            "drought_sensitivity": "High during tillering stage; moisture stress causes pith formation and stunted stalks",
            "source_id": "icar_iisr_sugarcane_2022"
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Deep black Vertisols with Nira canal irrigation command create optimal conditions for high-recovery varieties Co 86032 and Phule 265.",
                "limiting_factors": ["Over-irrigation in flat terrain causes soil salinity / water table rise"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Bhima river basin and canal commands combined with medium-to-deep black soils support intensive Adsali and Pre-seasonal sugarcane.",
                "limiting_factors": ["Summer water shortages when reservoir storages deplete"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "High rainfall (> 1500 mm) Western Ghats zone with acidic lateritic gravelly soils; lower winter temperatures prolong maturity and depress cane recovery.",
                "limiting_factors": ["Acidic laterite soils (pH < 6.0)", "Excessive monsoon waterlogging", "Sub-optimal sugar recovery"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Extreme monsoon downpours (> 2000 mm), steep terrace topography, and acidic soils are agronomically unsuited for commercial sugarcane farming.",
                "limiting_factors": ["Severe monsoon waterlogging", "Topographic slope unsuitable for cane haulage", "High disease incidence"],
                "source_id": "mpkv_pop_2023"
            }
        ]
    },

    # 2. Pomegranate
    {
        "id": "pomegranate",
        "common_name": "Pomegranate",
        "scientific_name": "Punica granatum L.",
        "marathi_name": "डाळिंब",
        "hindi_name": "अनार",
        "category": "Horticulture",
        "crop_type": "Perennial Fruit Tree (20-25 yrs)",
        "typical_duration_days_min": 150,
        "typical_duration_days_max": 180,
        "recommended_varieties": ["Bhagwa (Kesar / Shendari)", "Arakta", "Ganesh", "Solapur Lal"],
        "source_id": "icar_nrcp_pomegranate_2021",
        "soil": {
            "preferred_textures": ["Sandy Clay Loam", "Clay Loam", "Loam", "Light to Medium Black"],
            "acceptable_textures": ["Gravelly Loam", "Sandy Loam"],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 7.8,
            "ph_tolerable_min": 5.5,
            "ph_tolerable_max": 8.2,
            "drainage_requirement": "Excellent drainage mandatory; highly intolerant of water stagnation / wet feet",
            "salinity_sensitivity": "Moderately Tolerant (EC up to 3.0 dS/m tolerable; Boron toxicity above 1.5 ppm)",
            "min_soil_depth_cm": 60.0,
            "optimum_organic_carbon_g_kg": 6.0,
            "water_holding_capacity_pref": "Moderate; heavy soils with poor internal drainage trigger wilt",
            "source_id": "icar_nrcp_pomegranate_2021"
        },
        "climate": {
            "temp_optimum_min_c": 25.0,
            "temp_optimum_max_c": 35.0,
            "temp_tolerable_min_c": 10.0,
            "temp_tolerable_max_c": 44.0,
            "annual_rainfall_min_mm": 500.0,
            "annual_rainfall_max_mm": 700.0,
            "humidity_preference": "Low atmospheric humidity (< 60%) during fruit development ensures brilliant rind color",
            "frost_sensitivity": "Moderately Tolerant; dormant trees withstand light cold",
            "heat_sensitivity": "High tolerance; dry sunny weather promotes high sweetness (TSS > 15° Brix)",
            "solar_radiation_requirement": "High sunlight requirement; shading reduces flowering and fruit coloration",
            "source_id": "icar_nrcp_pomegranate_2021"
        },
        "seasons": [
            {
                "season_name": "Hasta Bahar",
                "is_primary_season": True,
                "planting_window_maharashtra": "September to October (Flowering induction via moisture stress)",
                "harvesting_window_maharashtra": "February to April",
                "duration_days_min": 150,
                "duration_days_max": 180,
                "planting_calendar_by_region": {"Baramati": "15 Sept - 15 Oct", "Indapur": "15 Sept - 15 Oct"},
                "source_id": "icar_nrcp_pomegranate_2021"
            },
            {
                "season_name": "Ambe Bahar",
                "is_primary_season": False,
                "planting_window_maharashtra": "January to February",
                "harvesting_window_maharashtra": "June to August",
                "duration_days_min": 160,
                "duration_days_max": 180,
                "planting_calendar_by_region": {"Baramati": "15 Jan - 15 Feb", "Indapur": "15 Jan - 15 Feb"},
                "source_id": "icar_nrcp_pomegranate_2021"
            }
        ],
        "water": {
            "annual_water_requirement_mm_min": 800.0,
            "annual_water_requirement_mm_max": 1100.0,
            "rainfed_suitable": False,
            "irrigation_dependency": "Critical via Micro-Irrigation (Drip mandatory for water control and bahar regulation)",
            "critical_growth_stages": [
                "Flowering and fruit setting phase (30–60 days after bahar release)",
                "Fruit development and aril pigmentation phase (90–140 days)"
            ],
            "waterlogging_sensitivity": "Extremely High; stagnant water induces root asphyxiation and Ceratocystis wilt",
            "drought_sensitivity": "High drought hardiness during stress regulation; sensitive during fruit sizing",
            "source_id": "icar_nrcp_pomegranate_2021"
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Semi-arid rain shadow, low humidity, and well-drained light-to-medium Vertisols provide textbook conditions for premium Bhagwa cultivation.",
                "limiting_factors": ["Bacterial blight (Xanthomonas axonopodis) during wet spells"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Dry micro-climate, high sunshine hours, and well-drained soils allow excellent Hasta Bahar regulation and export quality fruit.",
                "limiting_factors": ["Nematode infestation in sandy patches"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Persistent monsoon humidity (> 85%) and > 1400 mm rainfall cause devastating outbreaks of bacterial blight (telya) and fruit spot.",
                "limiting_factors": ["High atmospheric humidity", "Bacterial blight (Xanthomonas)", "Fruit cracking and decay"],
                "source_id": "icar_nrcp_pomegranate_2021"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Extreme Western Ghats rainfall and poor light in monsoon cause complete loss from bacterial blight and fungal root rot.",
                "limiting_factors": ["Torrential rainfall", "Continuous cloudiness", "Root rot (Ceratocystis)"],
                "source_id": "icar_nrcp_pomegranate_2021"
            }
        ]
    },

    # 3. Soybean
    {
        "id": "soybean",
        "common_name": "Soybean",
        "scientific_name": "Glycine max (L.) Merr.",
        "marathi_name": "सोयाबीन",
        "hindi_name": "सोयाबीन",
        "category": "Oilseed",
        "crop_type": "Annual Kharif",
        "typical_duration_days_min": 95,
        "typical_duration_days_max": 110,
        "recommended_varieties": ["Phule Sangam (KDS 726)", "Phule Kimaya (KDS 753)", "JS 335", "DSb 21"],
        "source_id": "icar_iisr_soybean_2022",
        "soil": {
            "preferred_textures": ["Clay Loam", "Clay", "Medium Black Vertisol"],
            "acceptable_textures": ["Loam", "Silt Loam"],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 7.5,
            "ph_tolerable_min": 6.0,
            "ph_tolerable_max": 8.0,
            "drainage_requirement": "Well-drained; seed germination and nodulation fail under waterlogging",
            "salinity_sensitivity": "Sensitive (EC < 1.5 dS/m; salt stress drastically reduces nodulation)",
            "min_soil_depth_cm": 45.0,
            "optimum_organic_carbon_g_kg": 6.5,
            "water_holding_capacity_pref": "Moderate to High",
            "source_id": "icar_iisr_soybean_2022"
        },
        "climate": {
            "temp_optimum_min_c": 22.0,
            "temp_optimum_max_c": 30.0,
            "temp_tolerable_min_c": 15.0,
            "temp_tolerable_max_c": 35.0,
            "annual_rainfall_min_mm": 600.0,
            "annual_rainfall_max_mm": 900.0,
            "humidity_preference": "Moderate (60–75%) during pod formation",
            "frost_sensitivity": "Sensitive",
            "heat_sensitivity": "Moderate; temperatures > 35°C during flowering cause flower drop and poor pod set",
            "solar_radiation_requirement": "Short-day photoperiod sensitive",
            "source_id": "icar_iisr_soybean_2022"
        },
        "seasons": [
            {
                "season_name": "Kharif",
                "is_primary_season": True,
                "planting_window_maharashtra": "20 June to 10 July (after receiving 75–100 mm monsoon rain)",
                "harvesting_window_maharashtra": "October",
                "duration_days_min": 95,
                "duration_days_max": 110,
                "planting_calendar_by_region": {"Baramati": "25 June - 10 July", "Maval": "20 June - 05 July"},
                "source_id": "mpkv_pop_2023"
            }
        ],
        "water": {
            "annual_water_requirement_mm_min": 450.0,
            "annual_water_requirement_mm_max": 650.0,
            "rainfed_suitable": True,
            "irrigation_dependency": "Supplemental (1–2 protective irrigations during dry spells ensure high yield)",
            "critical_growth_stages": [
                "Flowering stage (35–45 DAP)",
                "Pod development and seed filling phase (55–75 DAP)"
            ],
            "waterlogging_sensitivity": "High; stagnant water > 24 hours induces seedling damping-off and root rot",
            "drought_sensitivity": "High during flowering and pod fill; moisture stress reduces seed weight",
            "source_id": "icar_iisr_soybean_2022"
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "High-yielding rainfed Kharif crop with protective irrigation backup; varieties Phule Sangam and Phule Kimaya yield up to 25–30 q/ha.",
                "limiting_factors": ["Dry spell during pod development"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Excellent fit for Kharif on medium-to-deep Vertisols followed by Rabi wheat or chickpea.",
                "limiting_factors": ["Rust incidence during prolonged humid overcast weather"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Moderately Suitable",
                "agronomic_rationale": "Performs well on sloped plateaus with free drainage; excessive rain in flat valleys causes seed rot.",
                "limiting_factors": ["Waterlogging in lowlands", "Harvesting difficulties under late monsoon showers"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "Excessive monsoon downpours (> 2000 mm) cause severe pod rot, poor nodulation, and harvesting losses.",
                "limiting_factors": ["Continuous torrential rainfall", "Soil acidity"],
                "source_id": "mpkv_pop_2023"
            }
        ]
    },

    # 4. Cotton
    {
        "id": "cotton",
        "common_name": "Cotton",
        "scientific_name": "Gossypium hirsutum L.",
        "marathi_name": "कापूस",
        "hindi_name": "कपास",
        "category": "Fiber",
        "crop_type": "Annual Kharif (5-6 months)",
        "typical_duration_days_min": 150,
        "typical_duration_days_max": 180,
        "recommended_varieties": ["Phule Yamuna", "PKV Hy 2", "Ajeet 155 (Bt)", "RCH 2 (Bt)"],
        "source_id": "icar_cicr_cotton_2022",
        "soil": {
            "preferred_textures": ["Deep Black Vertisol", "Clay", "Clay Loam"],
            "acceptable_textures": ["Medium Black", "Silt Loam"],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 8.0,
            "ph_tolerable_min": 5.8,
            "ph_tolerable_max": 8.5,
            "drainage_requirement": "Good internal drainage mandatory despite clay texture",
            "salinity_sensitivity": "Moderately Tolerant (EC up to 4.0 dS/m during established growth)",
            "min_soil_depth_cm": 90.0,
            "optimum_organic_carbon_g_kg": 5.5,
            "water_holding_capacity_pref": "High; requires stored moisture in subsoil for boll maturation",
            "source_id": "icar_cicr_cotton_2022"
        },
        "climate": {
            "temp_optimum_min_c": 24.0,
            "temp_optimum_max_c": 34.0,
            "temp_tolerable_min_c": 16.0,
            "temp_tolerable_max_c": 40.0,
            "annual_rainfall_min_mm": 650.0,
            "annual_rainfall_max_mm": 1000.0,
            "humidity_preference": "Moderate during vegetative, dry warm weather during boll opening",
            "frost_sensitivity": "Highly Sensitive; frost kills growing tips",
            "heat_sensitivity": "Moderate; temperatures > 38°C cause square and boll shedding",
            "solar_radiation_requirement": "Abundant bright sunshine hours needed for boll opening",
            "source_id": "icar_cicr_cotton_2022"
        },
        "seasons": [
            {
                "season_name": "Kharif",
                "is_primary_season": True,
                "planting_window_maharashtra": "15 June to 30 June",
                "harvesting_window_maharashtra": "November to January",
                "duration_days_min": 150,
                "duration_days_max": 180,
                "planting_calendar_by_region": {"Baramati": "15 June - 30 June", "Indapur": "15 June - 05 July"},
                "source_id": "mpkv_pop_2023"
            }
        ],
        "water": {
            "annual_water_requirement_mm_min": 650.0,
            "annual_water_requirement_mm_max": 850.0,
            "rainfed_suitable": True,
            "irrigation_dependency": "Supplemental (2–3 protective irrigations during post-monsoon flowering/boll fill)",
            "critical_growth_stages": [
                "Square formation / early branching (45–60 DAP)",
                "Peak flowering stage (70–90 DAP)",
                "Boll development stage (90–120 DAP)"
            ],
            "waterlogging_sensitivity": "High; water stagnation > 36 hours induces square drop and root asphyxiation",
            "drought_sensitivity": "Moderate; deep taproot extracts moisture, but water stress causes boll abortion",
            "source_id": "icar_cicr_cotton_2022"
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Moderately Suitable",
                "agronomic_rationale": "Suitable on deep black Vertisols with supplemental drip irrigation; requires pink bollworm monitoring.",
                "limiting_factors": ["Sucking pest complex in early stages"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Moderately Suitable",
                "agronomic_rationale": "Grown in non-waterlogged medium-to-deep black soils with good post-monsoon sunshine.",
                "limiting_factors": ["Moisture stress during late boll development"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Heavy monsoon rains and continuous high humidity trigger severe boll rotting, square shedding, and rank vegetative growth.",
                "limiting_factors": ["Continuous rainfall", "Boll rot", "Lack of boll opening sunshine"],
                "source_id": "icar_cicr_cotton_2022"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Extreme Western Ghats rainfall and acid soils completely prevent commercial cotton production.",
                "limiting_factors": ["Excessive rainfall", "Cloudiness", "Boll rot"],
                "source_id": "icar_cicr_cotton_2022"
            }
        ]
    },

    # 5. Maize
    {
        "id": "maize",
        "common_name": "Maize (Corn)",
        "scientific_name": "Zea mays L.",
        "marathi_name": "मका",
        "hindi_name": "मक्का",
        "category": "Cereal",
        "crop_type": "Annual (Kharif / Rabi / Summer)",
        "typical_duration_days_min": 90,
        "typical_duration_days_max": 115,
        "recommended_varieties": ["Pinnacle (30V92)", "Ganga 11", "DKC 9108", "Phule Rajarshi"],
        "source_id": "mpkv_pop_2023",
        "soil": {
            "preferred_textures": ["Clay Loam", "Loam", "Sandy Clay Loam", "Medium Black"],
            "acceptable_textures": ["Clay", "Silt Loam"],
            "ph_optimum_min": 6.0,
            "ph_optimum_max": 7.5,
            "ph_tolerable_min": 5.5,
            "ph_tolerable_max": 8.0,
            "drainage_requirement": "Well-drained; extremely sensitive to standing water (even 24 hrs reduces yield by 30%)",
            "salinity_sensitivity": "Moderately Sensitive (EC < 1.7 dS/m)",
            "min_soil_depth_cm": 60.0,
            "optimum_organic_carbon_g_kg": 6.0,
            "water_holding_capacity_pref": "Moderate",
            "source_id": "mpkv_pop_2023"
        },
        "climate": {
            "temp_optimum_min_c": 21.0,
            "temp_optimum_max_c": 30.0,
            "temp_tolerable_min_c": 12.0,
            "temp_tolerable_max_c": 38.0,
            "annual_rainfall_min_mm": 500.0,
            "annual_rainfall_max_mm": 800.0,
            "humidity_preference": "Moderate relative humidity",
            "frost_sensitivity": "Highly Sensitive",
            "heat_sensitivity": "High; temperatures > 38°C during tasseling/silking dessicate pollen",
            "solar_radiation_requirement": "High sunlight requirement; C4 photosynthetic efficiency",
            "source_id": "mpkv_pop_2023"
        },
        "seasons": [
            {
                "season_name": "Kharif",
                "is_primary_season": True,
                "planting_window_maharashtra": "15 June to 15 July",
                "harvesting_window_maharashtra": "September to October",
                "duration_days_min": 90,
                "duration_days_max": 105,
                "planting_calendar_by_region": {"Baramati": "15 June - 10 July", "Maval": "20 June - 10 July"},
                "source_id": "mpkv_pop_2023"
            },
            {
                "season_name": "Rabi",
                "is_primary_season": False,
                "planting_window_maharashtra": "15 October to 15 November",
                "harvesting_window_maharashtra": "February to March",
                "duration_days_min": 105,
                "duration_days_max": 120,
                "planting_calendar_by_region": {"Baramati": "15 Oct - 15 Nov", "Indapur": "15 Oct - 15 Nov"},
                "source_id": "mpkv_pop_2023"
            }
        ],
        "water": {
            "annual_water_requirement_mm_min": 500.0,
            "annual_water_requirement_mm_max": 700.0,
            "rainfed_suitable": True,
            "irrigation_dependency": "Irrigated in Rabi; Rainfed with supplemental irrigation in Kharif",
            "critical_growth_stages": [
                "Tasseling stage (45–55 DAP)",
                "Silking and pollination phase (55–65 DAP)",
                "Grain milk and dough stage (70–85 DAP)"
            ],
            "waterlogging_sensitivity": "Extremely High; standing water causes root chlorosis and severe stunting",
            "drought_sensitivity": "Critical during flowering; 2 days of wilting at silking reduces grain count by 50%",
            "source_id": "mpkv_pop_2023"
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Thrives across Kharif, Rabi, and summer under well/canal irrigation; high demand for poultry feed and fodder.",
                "limiting_factors": ["Fall Armyworm (Spodoptera frugiperda) monitoring required"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "High grain and green fodder productivity in Rabi under canal irrigation.",
                "limiting_factors": ["Moisture stress during grain fill in tail-end canals"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Moderately Suitable",
                "agronomic_rationale": "Suitable in Kharif on elevated uplands with free drainage.",
                "limiting_factors": ["Waterlogging in lowland plains during heavy monsoon"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "Torrential rain causes severe water stagnation and nutrient leaching on flat lands.",
                "limiting_factors": ["Excessive rainfall", "Fungal stalk rot"],
                "source_id": "mpkv_pop_2023"
            }
        ]
    },

    # 6. Wheat
    {
        "id": "wheat",
        "common_name": "Wheat",
        "scientific_name": "Triticum aestivum L.",
        "marathi_name": "गहू",
        "hindi_name": "गेहूं",
        "category": "Cereal",
        "crop_type": "Annual Rabi",
        "typical_duration_days_min": 105,
        "typical_duration_days_max": 125,
        "recommended_varieties": ["Phule Samadhan (NIAW 1994)", "Trimbak (NIAW 301)", "Tapovan (NIAW 917)", "MACS 6222"],
        "source_id": "icar_iiwbr_wheat_2022",
        "soil": {
            "preferred_textures": ["Clay", "Clay Loam", "Deep Black Vertisol"],
            "acceptable_textures": ["Loam", "Silt Loam"],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 7.8,
            "ph_tolerable_min": 6.0,
            "ph_tolerable_max": 8.2,
            "drainage_requirement": "Well-drained; moderate waterlogging tolerance during tillering",
            "salinity_sensitivity": "Moderately Tolerant (EC up to 4.0 dS/m; variety KRL 210 for saline patches)",
            "min_soil_depth_cm": 60.0,
            "optimum_organic_carbon_g_kg": 6.0,
            "water_holding_capacity_pref": "High",
            "source_id": "icar_iiwbr_wheat_2022"
        },
        "climate": {
            "temp_optimum_min_c": 15.0,
            "temp_optimum_max_c": 24.0,
            "temp_tolerable_min_c": 8.0,
            "temp_tolerable_max_c": 30.0,
            "annual_rainfall_min_mm": 350.0,
            "annual_rainfall_max_mm": 550.0,
            "humidity_preference": "Low atmospheric humidity; heavy dew and high humidity induce leaf rust",
            "frost_sensitivity": "Moderately Tolerant",
            "heat_sensitivity": "High; temperatures > 30°C during grain filling cause terminal heat stress and shriveled grains",
            "solar_radiation_requirement": "Cool, bright sunny winter days accelerate tillering",
            "source_id": "icar_iiwbr_wheat_2022"
        },
        "seasons": [
            {
                "season_name": "Rabi",
                "is_primary_season": True,
                "planting_window_maharashtra": "01 November to 20 November (Timely Sown)",
                "harvesting_window_maharashtra": "February to March",
                "duration_days_min": 105,
                "duration_days_max": 125,
                "planting_calendar_by_region": {"Baramati": "01 Nov - 15 Nov", "Indapur": "05 Nov - 20 Nov"},
                "source_id": "mpkv_pop_2023"
            }
        ],
        "water": {
            "annual_water_requirement_mm_min": 400.0,
            "annual_water_requirement_mm_max": 550.0,
            "rainfed_suitable": False,
            "irrigation_dependency": "Critical (requires 4–6 irrigations at key growth stages)",
            "critical_growth_stages": [
                "Crown Root Initiation (CRI) stage (18–21 DAS) — Non-negotiable",
                "Late tillering stage (40–45 DAS)",
                "Jointing / Booting stage (60–65 DAS)",
                "Flowering / Heading stage (75–80 DAS)",
                "Milk to soft dough stage (90–95 DAS)"
            ],
            "waterlogging_sensitivity": "Moderate",
            "drought_sensitivity": "High; water stress at CRI reduces ear-bearing tillers by up to 40%",
            "source_id": "icar_iiwbr_wheat_2022"
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Deep black soils with assured canal/well irrigation provide optimal conditions for high-yielding Phule Samadhan.",
                "limiting_factors": ["Terminal heat stress if sowing delayed past 25 November"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "High yields achieved on Vertisols under timely November sowing.",
                "limiting_factors": ["Terminal heat in February if sown late"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "Short winter window and high morning fog/humidity promote brown rust.",
                "limiting_factors": ["High winter humidity", "Foliar rust diseases"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "Micro-climate too humid in valleys with acidic laterite soils.",
                "limiting_factors": ["Soil acidity", "Rust susceptibility"],
                "source_id": "mpkv_pop_2023"
            }
        ]
    },

    # 7. Sorghum (Jowar)
    {
        "id": "sorghum",
        "common_name": "Sorghum (Jowar)",
        "scientific_name": "Sorghum bicolor (L.) Moench",
        "marathi_name": "ज्वारी",
        "hindi_name": "ज्वार",
        "category": "Cereal",
        "crop_type": "Annual (Kharif / Rabi)",
        "typical_duration_days_min": 110,
        "typical_duration_days_max": 135,
        "recommended_varieties": ["Maldandi (M 35-1)", "Phule Suchitra", "Phule Yashodha", "Phule Revati", "Phule Vasudha"],
        "source_id": "icar_iimr_millets_2022",
        "soil": {
            "preferred_textures": ["Deep Black Vertisol", "Clay", "Clay Loam"],
            "acceptable_textures": ["Medium Black", "Sandy Clay Loam"],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 8.0,
            "ph_tolerable_min": 5.5,
            "ph_tolerable_max": 8.5,
            "drainage_requirement": "Well-drained; handles heavy clay exceptionally well by extracting deep subsoil moisture",
            "salinity_sensitivity": "Moderately Tolerant (EC up to 4.0 dS/m)",
            "min_soil_depth_cm": 60.0,
            "optimum_organic_carbon_g_kg": 5.0,
            "water_holding_capacity_pref": "Very High; deep Vertisols store receding monsoon rains for winter grain growth",
            "source_id": "icar_iimr_millets_2022"
        },
        "climate": {
            "temp_optimum_min_c": 24.0,
            "temp_optimum_max_c": 32.0,
            "temp_tolerable_min_c": 15.0,
            "temp_tolerable_max_c": 38.0,
            "annual_rainfall_min_mm": 400.0,
            "annual_rainfall_max_mm": 650.0,
            "humidity_preference": "Low to moderate humidity; dry sunny weather during grain ripening prevents grain mold",
            "frost_sensitivity": "Sensitive",
            "heat_sensitivity": "Low; outstanding heat and drought tolerance (C4 photosynthetic mechanism)",
            "solar_radiation_requirement": "High sunlight requirement",
            "source_id": "icar_iimr_millets_2022"
        },
        "seasons": [
            {
                "season_name": "Rabi",
                "is_primary_season": True,
                "planting_window_maharashtra": "15 September to 15 October (Hast Nakshatra)",
                "harvesting_window_maharashtra": "January to February",
                "duration_days_min": 115,
                "duration_days_max": 135,
                "planting_calendar_by_region": {"Baramati": "15 Sept - 10 Oct", "Indapur": "20 Sept - 15 Oct"},
                "source_id": "mpkv_pop_2023"
            },
            {
                "season_name": "Kharif",
                "is_primary_season": False,
                "planting_window_maharashtra": "15 June to 30 June",
                "harvesting_window_maharashtra": "October",
                "duration_days_min": 105,
                "duration_days_max": 115,
                "planting_calendar_by_region": {"Baramati": "15 June - 30 June"},
                "source_id": "mpkv_pop_2023"
            }
        ],
        "water": {
            "annual_water_requirement_mm_min": 350.0,
            "annual_water_requirement_mm_max": 500.0,
            "rainfed_suitable": True,
            "irrigation_dependency": "Low / Rainfed (1 protective irrigation at flowering doubles grain yield in drought years)",
            "critical_growth_stages": [
                "Booting / Flag leaf stage (50–55 DAP)",
                "Flowering phase (65–70 DAP)",
                "Grain milky to dough stage (80–90 DAP)"
            ],
            "waterlogging_sensitivity": "Moderate",
            "drought_sensitivity": "Extremely drought-tolerant; enters temporary dormancy during severe moisture deficit",
            "source_id": "icar_iimr_millets_2022"
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Iconic cultural and agro-climatic heartland for Rabi Maldandi Jowar; deep black Vertisols retain monsoon moisture.",
                "limiting_factors": ["Shoot fly in early sown or delayed crops"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Premier rainfed staple crop on medium-to-deep black soils; exceptional roti quality and dry fodder value.",
                "limiting_factors": ["Fall Armyworm attack in early vegetative stage"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Excessive monsoon rainfall causes severe grain mold in Kharif; soils are too shallow/acidic for Rabi moisture retention.",
                "limiting_factors": ["Grain mold (Curvularia/Fusarium)", "Soil acidity"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Heavy downpours completely prevent grain setting and trigger head blight.",
                "limiting_factors": ["Continuous rainfall", "Grain mold"],
                "source_id": "mpkv_pop_2023"
            }
        ]
    },

    # 8. Pearl Millet (Bajra)
    {
        "id": "bajra",
        "common_name": "Pearl Millet (Bajra)",
        "scientific_name": "Pennisetum glaucum (L.) R. Br.",
        "marathi_name": "बाजरी",
        "hindi_name": "बाजरा",
        "category": "Cereal",
        "crop_type": "Annual Kharif / Summer",
        "typical_duration_days_min": 75,
        "typical_duration_days_max": 85,
        "recommended_varieties": ["Dhanshakti (High Iron/Zinc)", "Phule Aadishakti", "Shraddha", "Saburi"],
        "source_id": "mpkv_pop_2023",
        "soil": {
            "preferred_textures": ["Sandy Loam", "Loam", "Light to Medium Black", "Sandy Clay Loam"],
            "acceptable_textures": ["Gravelly Loam", "Clay Loam"],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 7.8,
            "ph_tolerable_min": 5.5,
            "ph_tolerable_max": 8.5,
            "drainage_requirement": "Must be freely draining; completely intolerant of standing water",
            "salinity_sensitivity": "Moderately Tolerant (EC up to 3.5 dS/m)",
            "min_soil_depth_cm": 30.0,
            "optimum_organic_carbon_g_kg": 4.5,
            "water_holding_capacity_pref": "Low to Moderate; thrives on light, shallow, gravelly soils",
            "source_id": "mpkv_pop_2023"
        },
        "climate": {
            "temp_optimum_min_c": 25.0,
            "temp_optimum_max_c": 34.0,
            "temp_tolerable_min_c": 18.0,
            "temp_tolerable_max_c": 42.0,
            "annual_rainfall_min_mm": 350.0,
            "annual_rainfall_max_mm": 550.0,
            "humidity_preference": "Low atmospheric humidity",
            "frost_sensitivity": "Highly Sensitive",
            "heat_sensitivity": "Extremely Low; thrives in high summer heat up to 42°C",
            "solar_radiation_requirement": "High sunlight requirement; C4 photosynthetic system",
            "source_id": "mpkv_pop_2023"
        },
        "seasons": [
            {
                "season_name": "Kharif",
                "is_primary_season": True,
                "planting_window_maharashtra": "15 June to 15 July",
                "harvesting_window_maharashtra": "September",
                "duration_days_min": 75,
                "duration_days_max": 85,
                "planting_calendar_by_region": {"Baramati": "15 June - 10 July", "Indapur": "20 June - 15 July"},
                "source_id": "mpkv_pop_2023"
            },
            {
                "season_name": "Summer (Zaid)",
                "is_primary_season": False,
                "planting_window_maharashtra": "15 January to 15 February",
                "harvesting_window_maharashtra": "April to May",
                "duration_days_min": 80,
                "duration_days_max": 90,
                "planting_calendar_by_region": {"Baramati": "15 Jan - 15 Feb"},
                "source_id": "mpkv_pop_2023"
            }
        ],
        "water": {
            "annual_water_requirement_mm_min": 250.0,
            "annual_water_requirement_mm_max": 350.0,
            "rainfed_suitable": True,
            "irrigation_dependency": "Low / Rainfed in Kharif; 3–4 irrigations in summer",
            "critical_growth_stages": [
                "Tillering stage (25–30 DAP)",
                "Booting and flowering stage (45–50 DAP)",
                "Grain development phase (60–65 DAP)"
            ],
            "waterlogging_sensitivity": "Very High; even brief waterlogging leads to ergot and downy mildew",
            "drought_sensitivity": "Extremely drought-resilient; highest water-use efficiency among all cereals",
            "source_id": "mpkv_pop_2023"
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Ideal fit on light-to-medium upland soils in low rainfall pockets; biofortified Dhanshakti provides high nutrition.",
                "limiting_factors": ["Downy mildew during overcast humid weather"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Excellent short-duration crop in Kharif drought-prone areas.",
                "limiting_factors": ["Bird damage during maturity"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "High rainfall causes severe waterlogging, poor pollen viability, and heavy downy mildew / ergot attacks.",
                "limiting_factors": ["Excessive moisture", "Ergot disease", "Downy mildew"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "High monsoon humidity and precipitation completely incompatible with bajra flowering.",
                "limiting_factors": ["Continuous rainfall", "Crop failure due to ergot"],
                "source_id": "mpkv_pop_2023"
            }
        ]
    },

    # 9. Chickpea (Chana)
    {
        "id": "chickpea",
        "common_name": "Chickpea (Bengal Gram / Chana)",
        "scientific_name": "Cicer arietinum L.",
        "marathi_name": "हरभरा",
        "hindi_name": "चना",
        "category": "Pulse",
        "crop_type": "Annual Rabi",
        "typical_duration_days_min": 95,
        "typical_duration_days_max": 115,
        "recommended_varieties": ["Vijay (Wilt resistant)", "Digvijay", "Vishal (Bold seeded)", "Phule Vikram (Mechanized harvest)"],
        "source_id": "icar_iipr_pulses_2022",
        "soil": {
            "preferred_textures": ["Clay Loam", "Clay", "Medium Black Vertisol"],
            "acceptable_textures": ["Loam", "Silt Loam"],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 7.8,
            "ph_tolerable_min": 6.0,
            "ph_tolerable_max": 8.2,
            "drainage_requirement": "Well-drained; susceptible to collar rot and Fusarium wilt under excess wetness",
            "salinity_sensitivity": "Sensitive to Moderately Sensitive (EC < 1.5 dS/m)",
            "min_soil_depth_cm": 45.0,
            "optimum_organic_carbon_g_kg": 5.5,
            "water_holding_capacity_pref": "High (conserved subsoil moisture from monsoon rains supports maturity)",
            "source_id": "icar_iipr_pulses_2022"
        },
        "climate": {
            "temp_optimum_min_c": 15.0,
            "temp_optimum_max_c": 25.0,
            "temp_tolerable_min_c": 10.0,
            "temp_tolerable_max_c": 32.0,
            "annual_rainfall_min_mm": 300.0,
            "annual_rainfall_max_mm": 450.0,
            "humidity_preference": "Cool, dry weather; cloudy humid days induce pod borer (Helicoverpa) and Botrytis",
            "frost_sensitivity": "Sensitive during flowering",
            "heat_sensitivity": "High; temperatures > 30°C cause flower drop and forced premature maturity",
            "solar_radiation_requirement": "Bright sunny days enhance branching and pod set",
            "source_id": "icar_iipr_pulses_2022"
        },
        "seasons": [
            {
                "season_name": "Rabi",
                "is_primary_season": True,
                "planting_window_maharashtra": "10 October to 10 November",
                "harvesting_window_maharashtra": "January to February",
                "duration_days_min": 95,
                "duration_days_max": 115,
                "planting_calendar_by_region": {"Baramati": "15 Oct - 05 Nov", "Indapur": "20 Oct - 10 Nov"},
                "source_id": "mpkv_pop_2023"
            }
        ],
        "water": {
            "annual_water_requirement_mm_min": 250.0,
            "annual_water_requirement_mm_max": 350.0,
            "rainfed_suitable": True,
            "irrigation_dependency": "Low to Supplemental (1 protective irrigation at pod development stage increases yield by 40%)",
            "critical_growth_stages": [
                "Pre-flowering branching stage (30–35 DAP)",
                "Pod initiation and filling phase (60–65 DAP)"
            ],
            "waterlogging_sensitivity": "High; stagnant moisture induces Fusarium oxysporum wilt",
            "drought_sensitivity": "Moderate; deep root system extracts subsoil moisture",
            "source_id": "icar_iipr_pulses_2022"
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Major Rabi pulse on medium-to-deep black soils after early Kharif soybean or bajra; Vijay and Digvijay varieties show high wilt resistance.",
                "limiting_factors": ["Pod borer (Helicoverpa armigera) during pod development"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "High yields achieved on conserved moisture in deep black soils with 1 light irrigation.",
                "limiting_factors": ["Excess vegetative growth if over-irrigated"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "Acidic soils and high post-monsoon relative humidity promote root rot and collar rot.",
                "limiting_factors": ["Fungal root rot in acid soils", "Fog induced flower drop"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "High residual moisture and acidic laterites cause severe seedling mortality and wilt.",
                "limiting_factors": ["Soil acidity (pH < 6.0)", "Collar rot disease"],
                "source_id": "mpkv_pop_2023"
            }
        ]
    },

    # 10. Groundnut
    {
        "id": "groundnut",
        "common_name": "Groundnut (Peanut)",
        "scientific_name": "Arachis hypogaea L.",
        "marathi_name": "भुईमूग",
        "hindi_name": "मूंगफली",
        "category": "Oilseed",
        "crop_type": "Annual (Kharif / Summer)",
        "typical_duration_days_min": 105,
        "typical_duration_days_max": 125,
        "recommended_varieties": ["Phule Unnati", "Phule Morana", "TAG 24", "JL 501"],
        "source_id": "mpkv_pop_2023",
        "soil": {
            "preferred_textures": ["Sandy Clay Loam", "Loam", "Sandy Loam", "Light to Medium Loam"],
            "acceptable_textures": ["Clay Loam"],
            "ph_optimum_min": 6.0,
            "ph_optimum_max": 7.2,
            "ph_tolerable_min": 5.5,
            "ph_tolerable_max": 7.8,
            "drainage_requirement": "Well-drained, loose friable soil mandatory for easy peg penetration and pod lifting",
            "salinity_sensitivity": "Sensitive (EC < 1.5 dS/m)",
            "min_soil_depth_cm": 45.0,
            "optimum_organic_carbon_g_kg": 6.0,
            "water_holding_capacity_pref": "Moderate; heavy, sticky cracking clay impedes peg entry and pod harvest",
            "source_id": "mpkv_pop_2023"
        },
        "climate": {
            "temp_optimum_min_c": 24.0,
            "temp_optimum_max_c": 32.0,
            "temp_tolerable_min_c": 18.0,
            "temp_tolerable_max_c": 38.0,
            "annual_rainfall_min_mm": 500.0,
            "annual_rainfall_max_mm": 750.0,
            "humidity_preference": "Moderate relative humidity; dry weather during pod maturity",
            "frost_sensitivity": "Highly Sensitive",
            "heat_sensitivity": "Moderate",
            "solar_radiation_requirement": "High sunlight requirement",
            "source_id": "mpkv_pop_2023"
        },
        "seasons": [
            {
                "season_name": "Summer (Zaid)",
                "is_primary_season": True,
                "planting_window_maharashtra": "15 January to 15 February",
                "harvesting_window_maharashtra": "May to June",
                "duration_days_min": 110,
                "duration_days_max": 125,
                "planting_calendar_by_region": {"Baramati": "15 Jan - 15 Feb", "Indapur": "20 Jan - 15 Feb"},
                "source_id": "mpkv_pop_2023"
            },
            {
                "season_name": "Kharif",
                "is_primary_season": False,
                "planting_window_maharashtra": "15 June to 10 July",
                "harvesting_window_maharashtra": "October",
                "duration_days_min": 105,
                "duration_days_max": 115,
                "planting_calendar_by_region": {"Baramati": "20 June - 10 July"},
                "source_id": "mpkv_pop_2023"
            }
        ],
        "water": {
            "annual_water_requirement_mm_min": 450.0,
            "annual_water_requirement_mm_max": 650.0,
            "rainfed_suitable": True,
            "irrigation_dependency": "Critical in Summer (drip or sprinkler irrigation every 8–10 days)",
            "critical_growth_stages": [
                "Flowering phase (20–30 DAP)",
                "Pegging stage (40–50 DAP) — Crucial for subterranean pod formation",
                "Pod development and seed filling (60–80 DAP)"
            ],
            "waterlogging_sensitivity": "High; stagnant moisture induces pod rot (Aspergillus/Rhizoctonia)",
            "drought_sensitivity": "Critical at pegging; dry crust on topsoil prevents peg entry into soil",
            "source_id": "mpkv_pop_2023"
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "High profitability as a summer crop under drip irrigation in medium friable soils; TAG 24 and Phule Unnati produce high oil content.",
                "limiting_factors": ["Tikka leaf spot disease in late summer"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Moderately Suitable",
                "agronomic_rationale": "Well-suited on sandy loam patches along river/canal belts; avoids heavy cracking clays.",
                "limiting_factors": ["Heavy cracking soils make pod harvest labor intensive"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Moderately Suitable",
                "agronomic_rationale": "Can be grown in Kharif on elevated gentle slopes with liming to counter soil acidity.",
                "limiting_factors": ["Soil acidity impairs calcium uptake needed for pod filling", "Waterlogging in heavy rains"],
                "source_id": "mpkv_pop_2023"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "High rainfall causes pod rot in soil and washes away calcium necessary for shell formation.",
                "limiting_factors": ["Severe pod rot in wet soils", "Calcium deficiency causing empty pods (pops)"],
                "source_id": "mpkv_pop_2023"
            }
        ]
    }
]
