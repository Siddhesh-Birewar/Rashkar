"""
Authoritative agricultural knowledge base data seeded from:
- Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri — Research Recommendations (2023)
- International Crops Research Institute for the Semi-Arid Tropics (ICRISAT) — Chickpea Manual (2010)
- ICAR-NRCP & MANAGE — High-tech Pomegranate Production Practices (2022)
- ICAR Research Institutes: IISR, CICR, IIMR, IIWBR, IIPR, DGR
"""

KNOWLEDGE_SOURCES = [
    {
        "id": "mpkv_research_2023",
        "organization": "Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri",
        "publication_title": "Research Recommendations Released during 2023 by Mahatma Phule Krishi Vidyapeeth, Rahuri",
        "publication_year": 2023,
        "document_url_or_ref": "Joint Agresco 2023, MPKV Rahuri",
        "section_or_pages": "69 experimental recommendations across field crops, pp. 1–13",
        "evidence_quality": "verified_authoritative"
    },
    {
        "id": "icrisat_chickpea_2010",
        "organization": "International Crops Research Institute for the Semi-Arid Tropics (ICRISAT), Patancheru",
        "publication_title": "Chickpea Seed Production Manual",
        "publication_year": 2010,
        "document_url_or_ref": "ICRISAT / Gaur et al., 28 pp.",
        "section_or_pages": "Agronomy, temperature thresholds, irrigation stages, seed standards, pp. 1–28",
        "evidence_quality": "verified_authoritative"
    },
    {
        "id": "icar_nrcp_manage_2022",
        "organization": "ICAR-National Research Centre on Pomegranate (NRCP), Solapur & MANAGE, Hyderabad",
        "publication_title": "High-tech Pomegranate Production Practices for Export Quality Pomegranate Production and Value Addition",
        "publication_year": 2022,
        "document_url_or_ref": "ISBN: 978-93-91668-12-9",
        "section_or_pages": "Chapters 1–17: Soil pH, tree-age daily drip water tables, bahar regulation, pp. 1–119",
        "evidence_quality": "verified_authoritative"
    },
    {
        "id": "iisr_brochure_glance",
        "organization": "ICAR — Indian Institute of Sugarcane Research (IISR), Lucknow",
        "publication_title": "IISR at a Glance",
        "publication_year": 2010,
        "document_url_or_ref": "Compiled by A.K. Sharma et al., IISR Lucknow",
        "section_or_pages": "Institutional & technology brochure, pp. 1–8",
        "evidence_quality": "unverified_bibliographic"
    },
    {
        "id": "mpkv_pop_2023",
        "organization": "Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri",
        "publication_title": "Package of Practices for Field Crops & Agro-Techniques of Western Maharashtra (कृषी दैनंदिनी २०२३-२४)",
        "publication_year": 2023,
        "document_url_or_ref": "https://mpkv.ac.in/extension/package-of-practices",
        "section_or_pages": "Cereals, Pulses, Oilseeds and Cash Crops Recommendations, pp. 24–168",
        "evidence_quality": "requires_pop_compendium"
    },
    {
        "id": "icar_iisr_sugarcane_2022",
        "organization": "ICAR — Indian Institute of Sugarcane Research (IISR), Lucknow",
        "publication_title": "Good Agricultural Practices in Sugarcane Cultivation for Tropical India",
        "publication_year": 2022,
        "document_url_or_ref": "https://iisr.icar.gov.in/iisr/crop-production-technologies",
        "section_or_pages": "Water management & soil suitability in Peninsular Zone, pp. 12–38",
        "evidence_quality": "unverified_bibliographic"
    },
    {
        "id": "icar_nrcp_pomegranate_2021",
        "organization": "ICAR — National Research Centre on Pomegranate (NRCP), Solapur",
        "publication_title": "Scientific Pomegranate Production Manual for Semi-Arid Tropics",
        "publication_year": 2021,
        "document_url_or_ref": "https://nrcpomegranate.icar.gov.in/production-technology",
        "section_or_pages": "Soil suitability, Bahar regulation and wilt management, pp. 15–45",
        "evidence_quality": "superseded_by_2022_manual"
    },
    {
        "id": "icar_iisr_soybean_2022",
        "organization": "ICAR — Indian Institute of Soybean Research (IISR), Indore",
        "publication_title": "Soybean Production Technologies for Central and Peninsular India",
        "publication_year": 2022,
        "document_url_or_ref": "https://iisrindore.icar.gov.in/technologies",
        "section_or_pages": "Varietal guide and water stress mitigation, pp. 8–24",
        "evidence_quality": "requires_pop_compendium"
    },
    {
        "id": "icar_cicr_cotton_2022",
        "organization": "ICAR — Central Institute for Cotton Research (CICR), Nagpur",
        "publication_title": "Cotton Production Technology for Rainfed and Irrigated Vertisols of Maharashtra",
        "publication_year": 2022,
        "document_url_or_ref": "https://cicr.icar.gov.in/production-technology",
        "section_or_pages": "Soil depth and drainage criteria for Bt Cotton, pp. 14–32",
        "evidence_quality": "requires_pop_compendium"
    },
    {
        "id": "icar_iiwbr_wheat_2022",
        "organization": "ICAR — Indian Institute of Wheat and Barley Research (IIWBR), Karnal",
        "publication_title": "Wheat Production Technologies for Peninsular Zone of India",
        "publication_year": 2022,
        "document_url_or_ref": "https://iiwbr.icar.gov.in/peninsular-zone-technologies",
        "section_or_pages": "Thermal constraints and CRI irrigation scheduling, pp. 18–35",
        "evidence_quality": "requires_pop_compendium"
    },
    {
        "id": "icar_iimr_millets_2022",
        "organization": "ICAR — Indian Institute of Millets Research (IIMR), Hyderabad",
        "publication_title": "Sorghum and Small Millets Production Guide for Dryland Agriculture",
        "publication_year": 2022,
        "document_url_or_ref": "https://millets.res.in/technologies",
        "section_or_pages": "Rabi Jowar Maldandi agronomy in Deccan Vertisols, pp. 22–50",
        "evidence_quality": "requires_pop_compendium"
    },
    {
        "id": "icar_iipr_pulses_2022",
        "organization": "ICAR — Indian Institute of Pulses Research (IIPR), Kanpur",
        "publication_title": "Chickpea Production Technology and Moisture Conservation in Peninsular Vertisols",
        "publication_year": 2022,
        "document_url_or_ref": "https://iipr.icar.gov.in/chickpea-technologies",
        "section_or_pages": "Rabi chickpea wilt prevention and soil criteria, pp. 10–28",
        "evidence_quality": "unverified_bibliographic"
    }
]

CROPS_DATA = [
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
        "recommended_varieties": [
            "Co 86032 (Nira)",
            "CoM 0265 (Phule 265)",
            "MS 10001 (Phule 10001)",
            "VSI 08005"
        ],
        "source_id": "mpkv_research_2023",
        "soil": {
            "preferred_textures": [
                "Clay",
                "Clay Loam",
                "Deep Black Vertisol"
            ],
            "acceptable_textures": [
                "Sandy Clay Loam",
                "Loam"
            ],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 7.8,
            "ph_tolerable_min": 6.0,
            "ph_tolerable_max": 8.5,
            "drainage_requirement": "Well-drained; highly sensitive to prolonged waterlogging (> 48 hrs reduces tillering)",
            "salinity_sensitivity": "Moderately Sensitive (EC < 2.0 dS/m; yield drops 10% per dS/m increase above threshold)",
            "min_soil_depth_cm": 90.0,
            "optimum_organic_carbon_g_kg": 7.5,
            "water_holding_capacity_pref": "High (Deep Vertisols with > 50% clay retain essential moisture)",
            "source_id": "icar_iisr_sugarcane_2022",
            "evidence_status": "derived",
            "unverified_parameters": None
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
            "source_id": "icar_iisr_sugarcane_2022",
            "evidence_status": "derived"
        },
        "seasons": [
            {
                "season_name": "Adsali",
                "is_primary_season": True,
                "planting_window_maharashtra": "15 July to 15 August",
                "harvesting_window_maharashtra": "November to January (after 16–18 months)",
                "duration_days_min": 480,
                "duration_days_max": 540,
                "planting_calendar_by_region": {
                    "Baramati": "15 July - 10 August",
                    "Indapur": "15 July - 15 August"
                },
                "source_id": "mpkv_pop_2023"
            },
            {
                "season_name": "Pre-seasonal",
                "is_primary_season": False,
                "planting_window_maharashtra": "15 October to 15 November",
                "harvesting_window_maharashtra": "December to February (after 14–15 months)",
                "duration_days_min": 420,
                "duration_days_max": 450,
                "planting_calendar_by_region": {
                    "Baramati": "15 October - 15 November",
                    "Indapur": "20 October - 20 November"
                },
                "source_id": "mpkv_pop_2023"
            },
            {
                "season_name": "Suru",
                "is_primary_season": False,
                "planting_window_maharashtra": "15 January to 15 February",
                "harvesting_window_maharashtra": "January to March (after 12 months)",
                "duration_days_min": 360,
                "duration_days_max": 380,
                "planting_calendar_by_region": {
                    "Baramati": "15 January - 15 February",
                    "Indapur": "15 January - 20 February"
                },
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
            "source_id": "icar_iisr_sugarcane_2022",
            "evidence_status": "derived",
            "daily_water_table": None,
            "irrigation_stages_detail": [
                {
                    "source_id": "mpkv_research_2023",
                    "source_citation": "MPKV Research Recommendations 2023, Recommendation 3, p. 2",
                    "scope": "Suru Sugarcane Microclimate",
                    "recommendation": "Planting of Suru Sugarcane with drip irrigation and inverted modular micro-sprinkler creates optimal microclimate and improves water use efficiency in Western Maharashtra."
                }
            ]
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Deep black Vertisols with Nira canal irrigation command create optimal conditions for high-recovery varieties Co 86032 and Phule 265.",
                "limiting_factors": [
                    "Over-irrigation in flat terrain causes soil salinity / water table rise"
                ],
                "source_id": "mpkv_research_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Bhima river basin and canal commands combined with medium-to-deep black soils support intensive Adsali and Pre-seasonal sugarcane.",
                "limiting_factors": [
                    "Summer water shortages when reservoir storages deplete"
                ],
                "source_id": "mpkv_research_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "High rainfall (> 1500 mm) Western Ghats zone with acidic lateritic gravelly soils; lower winter temperatures prolong maturity and depress cane recovery.",
                "limiting_factors": [
                    "Acidic laterite soils (pH < 6.0)",
                    "Excessive monsoon waterlogging",
                    "Sub-optimal sugar recovery"
                ],
                "source_id": "mpkv_research_2023",
                "evidence_status": "requires_regional_validation"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Extreme monsoon downpours (> 2000 mm), steep terrace topography, and acidic soils are agronomically unsuited for commercial sugarcane farming.",
                "limiting_factors": [
                    "Severe monsoon waterlogging",
                    "Topographic slope unsuitable for cane haulage",
                    "High disease incidence"
                ],
                "source_id": "mpkv_research_2023",
                "evidence_status": "requires_regional_validation"
            }
        ]
    },
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
        "recommended_varieties": [
            "Bhagwa (Kesar / Shendari)",
            "Arakta",
            "Ganesh",
            "Solapur Lal"
        ],
        "source_id": "icar_nrcp_manage_2022",
        "soil": {
            "preferred_textures": [
                "Sandy Clay Loam",
                "Clay Loam",
                "Loam",
                "Light to Medium Black"
            ],
            "acceptable_textures": [
                "Gravelly Loam",
                "Sandy Loam"
            ],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 7.0,
            "ph_tolerable_min": None,
            "ph_tolerable_max": 8.5,
            "ph_context_notes": "Optimum pH 6.5–7.0 is most suitable; tolerates up to 8.5 under good soil and nutrient management (ICAR-NRCP & MANAGE 2022, p. 9). Lower tolerable limit is unverified.",
            "drainage_requirement": "Excellent drainage mandatory; light soil on 3-5% slope. Highly intolerant of water stagnation / wet feet",
            "salinity_sensitivity": "Moderately Tolerant (EC up to 3.0 dS/m tolerable; Boron toxicity above 1.5 ppm)",
            "min_soil_depth_cm": 60.0,
            "optimum_organic_carbon_g_kg": 6.0,
            "water_holding_capacity_pref": "Moderate; heavy soils with poor internal drainage trigger wilt",
            "source_id": "icar_nrcp_manage_2022",
            "evidence_status": "verified_authoritative",
            "unverified_parameters": [
                "ph_tolerable_min",
                "min_soil_depth_cm"
            ]
        },
        "climate": {
            "temp_optimum_min_c": 25.0,
            "temp_optimum_max_c": 35.0,
            "temp_tolerable_min_c": 10.0,
            "temp_tolerable_max_c": 44.0,
            "annual_rainfall_min_mm": 500.0,
            "annual_rainfall_max_mm": 700.0,
            "humidity_preference": "Low atmospheric humidity (< 60%) during fruit development; high RH (> 50%) promotes bacterial blight",
            "frost_sensitivity": "Moderately Tolerant; dormant trees withstand light cold",
            "heat_sensitivity": "High tolerance; dry sunny weather promotes high sweetness (TSS > 15° Brix)",
            "solar_radiation_requirement": "High sunlight requirement; shading reduces flowering and fruit coloration",
            "source_id": "icar_nrcp_manage_2022",
            "evidence_status": "verified_authoritative"
        },
        "seasons": [
            {
                "season_name": "Hasta Bahar",
                "is_primary_season": True,
                "planting_window_maharashtra": "September to October (Flowering induction via moisture stress)",
                "harvesting_window_maharashtra": "February to April",
                "duration_days_min": 150,
                "duration_days_max": 180,
                "planting_calendar_by_region": {
                    "Baramati": "15 Sept - 15 Oct",
                    "Indapur": "15 Sept - 15 Oct"
                },
                "source_id": "icar_nrcp_manage_2022"
            },
            {
                "season_name": "Ambe Bahar",
                "is_primary_season": False,
                "planting_window_maharashtra": "January to February",
                "harvesting_window_maharashtra": "June to August",
                "duration_days_min": 160,
                "duration_days_max": 180,
                "planting_calendar_by_region": {
                    "Baramati": "15 Jan - 15 Feb",
                    "Indapur": "15 Jan - 15 Feb"
                },
                "source_id": "icar_nrcp_manage_2022"
            }
        ],
        "water": {
            "annual_water_requirement_mm_min": None,
            "annual_water_requirement_mm_max": None,
            "rainfed_suitable": False,
            "irrigation_dependency": "Critical via Micro-Irrigation (Drip mandatory for water control and bahar regulation)",
            "critical_growth_stages": [
                "Flowering and fruit setting phase (30–60 days after bahar release)",
                "Fruit development and aril pigmentation phase (90–140 days)"
            ],
            "waterlogging_sensitivity": "Extremely High; stagnant water induces root asphyxiation and Ceratocystis wilt",
            "drought_sensitivity": "High drought hardiness during stress regulation; sensitive during fruit sizing",
            "source_id": "icar_nrcp_manage_2022",
            "evidence_status": "verified_authoritative",
            "daily_water_table": {
                "unit": "liters_per_tree_per_day",
                "citation": "ICAR-NRCP & MANAGE 2022, Chapter 9, pp. 45–46, Tables 1–3",
                "description": "Granular daily water application (lit/day/tree) by tree age (1st to 5th year) and Meteorological Week (MW) for Mrig, Hasta, and Ambia Bahar",
                "summary_ranges_by_year": {
                    "year_1": "2 - 6",
                    "year_2": "3 - 20",
                    "year_3": "3 - 36",
                    "year_4": "5 - 56",
                    "year_5_and_above": "6 - 70"
                },
                "mrig_bahar": {
                    "table_name": "Table 1. Water to be applied (lit/day) for one to five years old pomegranate tree during Mirg bahar (p. 45)",
                    "period": "June to 2nd week of January (MW 23 to MW 02)",
                    "schedule": [
                        {
                            "months": "June",
                            "mw": 23,
                            "year_1": 3,
                            "year_2": 5,
                            "year_3": 6,
                            "year_4": 8,
                            "year_5": 11
                        },
                        {
                            "months": "June",
                            "mw": 24,
                            "year_1": 3,
                            "year_2": 5,
                            "year_3": 6,
                            "year_4": 8,
                            "year_5": 13
                        },
                        {
                            "months": "June",
                            "mw": 25,
                            "year_1": 3,
                            "year_2": 5,
                            "year_3": 7,
                            "year_4": 11,
                            "year_5": 16
                        },
                        {
                            "months": "June",
                            "mw": 26,
                            "year_1": 3,
                            "year_2": 5,
                            "year_3": 8,
                            "year_4": 13,
                            "year_5": 17
                        },
                        {
                            "months": "July to 1st week of September",
                            "mw": 27,
                            "year_1": 3,
                            "year_2": 6,
                            "year_3": 9,
                            "year_4": 15,
                            "year_5": 20
                        },
                        {
                            "months": "July to 1st week of September",
                            "mw": 28,
                            "year_1": 3,
                            "year_2": 6,
                            "year_3": 10,
                            "year_4": 16,
                            "year_5": 22
                        },
                        {
                            "months": "July to 1st week of September",
                            "mw": 29,
                            "year_1": 2,
                            "year_2": 7,
                            "year_3": 11,
                            "year_4": 18,
                            "year_5": 23
                        },
                        {
                            "months": "July to 1st week of September",
                            "mw": 30,
                            "year_1": 2,
                            "year_2": 7,
                            "year_3": 10,
                            "year_4": 17,
                            "year_5": 23
                        },
                        {
                            "months": "July to 1st week of September",
                            "mw": 31,
                            "year_1": 2,
                            "year_2": 7,
                            "year_3": 12,
                            "year_4": 19,
                            "year_5": 25
                        },
                        {
                            "months": "July to 1st week of September",
                            "mw": 32,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 13,
                            "year_4": 21,
                            "year_5": 27
                        },
                        {
                            "months": "July to 1st week of September",
                            "mw": 33,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 14,
                            "year_4": 22,
                            "year_5": 29
                        },
                        {
                            "months": "July to 1st week of September",
                            "mw": 34,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 14,
                            "year_4": 23,
                            "year_5": 29
                        },
                        {
                            "months": "July to 1st week of September",
                            "mw": 35,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 15,
                            "year_4": 25,
                            "year_5": 31
                        },
                        {
                            "months": "July to 1st week of September",
                            "mw": 36,
                            "year_1": 2,
                            "year_2": 9,
                            "year_3": 16,
                            "year_4": 25,
                            "year_5": 32
                        },
                        {
                            "months": "2nd week of September to October",
                            "mw": 37,
                            "year_1": 3,
                            "year_2": 9,
                            "year_3": 17,
                            "year_4": 26,
                            "year_5": 33
                        },
                        {
                            "months": "2nd week of September to October",
                            "mw": 38,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 16,
                            "year_4": 24,
                            "year_5": 31
                        },
                        {
                            "months": "2nd week of September to October",
                            "mw": 39,
                            "year_1": 2,
                            "year_2": 9,
                            "year_3": 16,
                            "year_4": 25,
                            "year_5": 31
                        },
                        {
                            "months": "2nd week of September to October",
                            "mw": 40,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 15,
                            "year_4": 24,
                            "year_5": 30
                        },
                        {
                            "months": "2nd week of September to October",
                            "mw": 41,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 16,
                            "year_4": 24,
                            "year_5": 30
                        },
                        {
                            "months": "2nd week of September to October",
                            "mw": 42,
                            "year_1": 3,
                            "year_2": 9,
                            "year_3": 16,
                            "year_4": 25,
                            "year_5": 32
                        },
                        {
                            "months": "2nd week of September to October",
                            "mw": 43,
                            "year_1": 3,
                            "year_2": 9,
                            "year_3": 18,
                            "year_4": 27,
                            "year_5": 34
                        },
                        {
                            "months": "2nd week of September to October",
                            "mw": 44,
                            "year_1": 3,
                            "year_2": 9,
                            "year_3": 17,
                            "year_4": 26,
                            "year_5": 33
                        },
                        {
                            "months": "November to 2nd week of January",
                            "mw": 45,
                            "year_1": 3,
                            "year_2": 9,
                            "year_3": 17,
                            "year_4": 26,
                            "year_5": 33
                        },
                        {
                            "months": "November to 2nd week of January",
                            "mw": 46,
                            "year_1": 3,
                            "year_2": 8,
                            "year_3": 16,
                            "year_4": 25,
                            "year_5": 32
                        },
                        {
                            "months": "November to 2nd week of January",
                            "mw": 47,
                            "year_1": 3,
                            "year_2": 8,
                            "year_3": 15,
                            "year_4": 24,
                            "year_5": 30
                        },
                        {
                            "months": "November to 2nd week of January",
                            "mw": 48,
                            "year_1": 3,
                            "year_2": 7,
                            "year_3": 15,
                            "year_4": 23,
                            "year_5": 29
                        },
                        {
                            "months": "November to 2nd week of January",
                            "mw": 49,
                            "year_1": 3,
                            "year_2": 7,
                            "year_3": 14,
                            "year_4": 23,
                            "year_5": 29
                        },
                        {
                            "months": "November to 2nd week of January",
                            "mw": 50,
                            "year_1": 3,
                            "year_2": 6,
                            "year_3": 13,
                            "year_4": 21,
                            "year_5": 27
                        },
                        {
                            "months": "November to 2nd week of January",
                            "mw": 51,
                            "year_1": 3,
                            "year_2": 6,
                            "year_3": 13,
                            "year_4": 21,
                            "year_5": 26
                        },
                        {
                            "months": "November to 2nd week of January",
                            "mw": 52,
                            "year_1": 3,
                            "year_2": 6,
                            "year_3": 12,
                            "year_4": 20,
                            "year_5": 25
                        },
                        {
                            "months": "November to 2nd week of January",
                            "mw": 1,
                            "year_1": 3,
                            "year_2": 5,
                            "year_3": 12,
                            "year_4": 19,
                            "year_5": 24
                        },
                        {
                            "months": "November to 2nd week of January",
                            "mw": 2,
                            "year_1": 3,
                            "year_2": 6,
                            "year_3": 12,
                            "year_4": 20,
                            "year_5": 26
                        }
                    ]
                },
                "hasta_bahar": {
                    "table_name": "Table 2. Water to be applied (lit/day) for one to five years old pomegranate tree during Hasta bahar (pp. 45–46)",
                    "period": "September to March (MW 36 to MW 15)",
                    "schedule": [
                        {
                            "months": "September",
                            "mw": 36,
                            "year_1": 2,
                            "year_2": 3,
                            "year_3": 4,
                            "year_4": 5,
                            "year_5": 6
                        },
                        {
                            "months": "September",
                            "mw": 37,
                            "year_1": 2,
                            "year_2": 3,
                            "year_3": 4,
                            "year_4": 6,
                            "year_5": 9
                        },
                        {
                            "months": "September",
                            "mw": 38,
                            "year_1": 2,
                            "year_2": 4,
                            "year_3": 5,
                            "year_4": 8,
                            "year_5": 11
                        },
                        {
                            "months": "September",
                            "mw": 39,
                            "year_1": 2,
                            "year_2": 4,
                            "year_3": 6,
                            "year_4": 10,
                            "year_5": 13
                        },
                        {
                            "months": "1st week of October to 3rd week of December",
                            "mw": 40,
                            "year_1": 2,
                            "year_2": 4,
                            "year_3": 7,
                            "year_4": 11,
                            "year_5": 15
                        },
                        {
                            "months": "1st week of October to 3rd week of December",
                            "mw": 41,
                            "year_1": 2,
                            "year_2": 5,
                            "year_3": 8,
                            "year_4": 13,
                            "year_5": 18
                        },
                        {
                            "months": "1st week of October to 3rd week of December",
                            "mw": 42,
                            "year_1": 2,
                            "year_2": 6,
                            "year_3": 9,
                            "year_4": 15,
                            "year_5": 20
                        },
                        {
                            "months": "1st week of October to 3rd week of December",
                            "mw": 43,
                            "year_1": 2,
                            "year_2": 7,
                            "year_3": 11,
                            "year_4": 18,
                            "year_5": 24
                        },
                        {
                            "months": "1st week of October to 3rd week of December",
                            "mw": 44,
                            "year_1": 2,
                            "year_2": 7,
                            "year_3": 12,
                            "year_4": 19,
                            "year_5": 25
                        },
                        {
                            "months": "1st week of October to 3rd week of December",
                            "mw": 45,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 13,
                            "year_4": 21,
                            "year_5": 28
                        },
                        {
                            "months": "1st week of October to 3rd week of December",
                            "mw": 46,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 14,
                            "year_4": 22,
                            "year_5": 29
                        },
                        {
                            "months": "1st week of October to 3rd week of December",
                            "mw": 47,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 14,
                            "year_4": 23,
                            "year_5": 30
                        },
                        {
                            "months": "1st week of October to 3rd week of December",
                            "mw": 48,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 15,
                            "year_4": 24,
                            "year_5": 31
                        },
                        {
                            "months": "1st week of October to 3rd week of December",
                            "mw": 49,
                            "year_1": 2,
                            "year_2": 9,
                            "year_3": 16,
                            "year_4": 25,
                            "year_5": 32
                        },
                        {
                            "months": "1st week of October to 3rd week of December",
                            "mw": 50,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 16,
                            "year_4": 24,
                            "year_5": 30
                        },
                        {
                            "months": "1st week of October to 3rd week of December",
                            "mw": 51,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 16,
                            "year_4": 24,
                            "year_5": 30
                        },
                        {
                            "months": "4th week of December to 2nd week of February",
                            "mw": 52,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 16,
                            "year_4": 24,
                            "year_5": 30
                        },
                        {
                            "months": "4th week of December to 2nd week of February",
                            "mw": 1,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 15,
                            "year_4": 23,
                            "year_5": 29
                        },
                        {
                            "months": "4th week of December to 2nd week of February",
                            "mw": 2,
                            "year_1": 2,
                            "year_2": 8,
                            "year_3": 16,
                            "year_4": 24,
                            "year_5": 30
                        },
                        {
                            "months": "4th week of December to 2nd week of February",
                            "mw": 3,
                            "year_1": 3,
                            "year_2": 9,
                            "year_3": 16,
                            "year_4": 25,
                            "year_5": 31
                        },
                        {
                            "months": "4th week of December to 2nd week of February",
                            "mw": 4,
                            "year_1": 3,
                            "year_2": 10,
                            "year_3": 18,
                            "year_4": 28,
                            "year_5": 35
                        },
                        {
                            "months": "4th week of December to 2nd week of February",
                            "mw": 5,
                            "year_1": 3,
                            "year_2": 10,
                            "year_3": 19,
                            "year_4": 29,
                            "year_5": 37
                        },
                        {
                            "months": "4th week of December to 2nd week of February",
                            "mw": 6,
                            "year_1": 3,
                            "year_2": 10,
                            "year_3": 20,
                            "year_4": 31,
                            "year_5": 39
                        },
                        {
                            "months": "4th week of December to 2nd week of February",
                            "mw": 7,
                            "year_1": 4,
                            "year_2": 11,
                            "year_3": 21,
                            "year_4": 33,
                            "year_5": 41
                        },
                        {
                            "months": "3rd week of February to March",
                            "mw": 8,
                            "year_1": 4,
                            "year_2": 11,
                            "year_3": 23,
                            "year_4": 35,
                            "year_5": 44
                        },
                        {
                            "months": "3rd week of February to March",
                            "mw": 9,
                            "year_1": 4,
                            "year_2": 12,
                            "year_3": 24,
                            "year_4": 37,
                            "year_5": 47
                        },
                        {
                            "months": "3rd week of February to March",
                            "mw": 10,
                            "year_1": 5,
                            "year_2": 12,
                            "year_3": 24,
                            "year_4": 39,
                            "year_5": 49
                        },
                        {
                            "months": "3rd week of February to March",
                            "mw": 11,
                            "year_1": 5,
                            "year_2": 12,
                            "year_3": 25,
                            "year_4": 39,
                            "year_5": 49
                        },
                        {
                            "months": "3rd week of February to March",
                            "mw": 12,
                            "year_1": 6,
                            "year_2": 12,
                            "year_3": 25,
                            "year_4": 41,
                            "year_5": 52
                        },
                        {
                            "months": "3rd week of February to March",
                            "mw": 13,
                            "year_1": 6,
                            "year_2": 12,
                            "year_3": 25,
                            "year_4": 41,
                            "year_5": 52
                        },
                        {
                            "months": "3rd week of February to March",
                            "mw": 14,
                            "year_1": 6,
                            "year_2": 12,
                            "year_3": 25,
                            "year_4": 41,
                            "year_5": 52
                        },
                        {
                            "months": "3rd week of February to March",
                            "mw": 15,
                            "year_1": 6,
                            "year_2": 12,
                            "year_3": 26,
                            "year_4": 43,
                            "year_5": 54
                        }
                    ]
                },
                "ambia_bahar": {
                    "table_name": "Table 3. Water to be applied (lit/day) for one to five years old pomegranate tree during Ambia bahar (p. 46)",
                    "period": "January to 1st week of August (MW 01 to MW 32)",
                    "schedule": [
                        {
                            "months": "January",
                            "mw": 1,
                            "year_1": 2,
                            "year_2": 3,
                            "year_3": 3,
                            "year_4": 5,
                            "year_5": 6
                        },
                        {
                            "months": "January",
                            "mw": 2,
                            "year_1": 2,
                            "year_2": 3,
                            "year_3": 4,
                            "year_4": 5,
                            "year_5": 8
                        },
                        {
                            "months": "January",
                            "mw": 3,
                            "year_1": 2,
                            "year_2": 4,
                            "year_3": 5,
                            "year_4": 8,
                            "year_5": 11
                        },
                        {
                            "months": "January",
                            "mw": 4,
                            "year_1": 2,
                            "year_2": 5,
                            "year_3": 7,
                            "year_4": 11,
                            "year_5": 15
                        },
                        {
                            "months": "January",
                            "mw": 5,
                            "year_1": 2,
                            "year_2": 6,
                            "year_3": 8,
                            "year_4": 13,
                            "year_5": 18
                        },
                        {
                            "months": "February to March",
                            "mw": 6,
                            "year_1": 3,
                            "year_2": 7,
                            "year_3": 10,
                            "year_4": 17,
                            "year_5": 23
                        },
                        {
                            "months": "February to March",
                            "mw": 7,
                            "year_1": 3,
                            "year_2": 8,
                            "year_3": 12,
                            "year_4": 20,
                            "year_5": 27
                        },
                        {
                            "months": "February to March",
                            "mw": 8,
                            "year_1": 3,
                            "year_2": 9,
                            "year_3": 15,
                            "year_4": 25,
                            "year_5": 33
                        },
                        {
                            "months": "February to March",
                            "mw": 9,
                            "year_1": 4,
                            "year_2": 11,
                            "year_3": 18,
                            "year_4": 30,
                            "year_5": 39
                        },
                        {
                            "months": "February to March",
                            "mw": 10,
                            "year_1": 4,
                            "year_2": 12,
                            "year_3": 21,
                            "year_4": 34,
                            "year_5": 45
                        },
                        {
                            "months": "February to March",
                            "mw": 11,
                            "year_1": 4,
                            "year_2": 13,
                            "year_3": 24,
                            "year_4": 38,
                            "year_5": 50
                        },
                        {
                            "months": "February to March",
                            "mw": 12,
                            "year_1": 4,
                            "year_2": 15,
                            "year_3": 28,
                            "year_4": 44,
                            "year_5": 57
                        },
                        {
                            "months": "February to March",
                            "mw": 13,
                            "year_1": 5,
                            "year_2": 16,
                            "year_3": 30,
                            "year_4": 48,
                            "year_5": 60
                        },
                        {
                            "months": "February to March",
                            "mw": 14,
                            "year_1": 5,
                            "year_2": 17,
                            "year_3": 32,
                            "year_4": 49,
                            "year_5": 62
                        },
                        {
                            "months": "February to March",
                            "mw": 15,
                            "year_1": 5,
                            "year_2": 18,
                            "year_3": 33,
                            "year_4": 51,
                            "year_5": 64
                        },
                        {
                            "months": "February to March",
                            "mw": 16,
                            "year_1": 5,
                            "year_2": 19,
                            "year_3": 35,
                            "year_4": 54,
                            "year_5": 68
                        },
                        {
                            "months": "3rd week of April to 2nd week of June",
                            "mw": 17,
                            "year_1": 5,
                            "year_2": 19,
                            "year_3": 35,
                            "year_4": 54,
                            "year_5": 68
                        },
                        {
                            "months": "3rd week of April to 2nd week of June",
                            "mw": 18,
                            "year_1": 6,
                            "year_2": 20,
                            "year_3": 36,
                            "year_4": 56,
                            "year_5": 70
                        },
                        {
                            "months": "3rd week of April to 2nd week of June",
                            "mw": 19,
                            "year_1": 6,
                            "year_2": 19,
                            "year_3": 36,
                            "year_4": 56,
                            "year_5": 70
                        },
                        {
                            "months": "3rd week of April to 2nd week of June",
                            "mw": 20,
                            "year_1": 6,
                            "year_2": 19,
                            "year_3": 36,
                            "year_4": 56,
                            "year_5": 70
                        },
                        {
                            "months": "3rd week of April to 2nd week of June",
                            "mw": 21,
                            "year_1": 6,
                            "year_2": 19,
                            "year_3": 35,
                            "year_4": 54,
                            "year_5": 67
                        },
                        {
                            "months": "3rd week of April to 2nd week of June",
                            "mw": 22,
                            "year_1": 5,
                            "year_2": 18,
                            "year_3": 33,
                            "year_4": 51,
                            "year_5": 65
                        },
                        {
                            "months": "3rd week of April to 2nd week of June",
                            "mw": 23,
                            "year_1": 4,
                            "year_2": 14,
                            "year_3": 27,
                            "year_4": 42,
                            "year_5": 53
                        },
                        {
                            "months": "3rd week of April to 2nd week of June",
                            "mw": 24,
                            "year_1": 4,
                            "year_2": 12,
                            "year_3": 24,
                            "year_4": 37,
                            "year_5": 47
                        },
                        {
                            "months": "3rd week of June to 1st week of August",
                            "mw": 25,
                            "year_1": 4,
                            "year_2": 11,
                            "year_3": 22,
                            "year_4": 33,
                            "year_5": 42
                        },
                        {
                            "months": "3rd week of June to 1st week of August",
                            "mw": 26,
                            "year_1": 4,
                            "year_2": 10,
                            "year_3": 19,
                            "year_4": 30,
                            "year_5": 38
                        },
                        {
                            "months": "3rd week of June to 1st week of August",
                            "mw": 27,
                            "year_1": 4,
                            "year_2": 9,
                            "year_3": 18,
                            "year_4": 29,
                            "year_5": 37
                        },
                        {
                            "months": "3rd week of June to 1st week of August",
                            "mw": 28,
                            "year_1": 4,
                            "year_2": 8,
                            "year_3": 17,
                            "year_4": 27,
                            "year_5": 34
                        },
                        {
                            "months": "3rd week of June to 1st week of August",
                            "mw": 29,
                            "year_1": 3,
                            "year_2": 7,
                            "year_3": 15,
                            "year_4": 25,
                            "year_5": 32
                        },
                        {
                            "months": "3rd week of June to 1st week of August",
                            "mw": 30,
                            "year_1": 3,
                            "year_2": 6,
                            "year_3": 13,
                            "year_4": 22,
                            "year_5": 27
                        },
                        {
                            "months": "3rd week of June to 1st week of August",
                            "mw": 31,
                            "year_1": 3,
                            "year_2": 6,
                            "year_3": 13,
                            "year_4": 21,
                            "year_5": 27
                        },
                        {
                            "months": "3rd week of June to 1st week of August",
                            "mw": 32,
                            "year_1": 3,
                            "year_2": 6,
                            "year_3": 13,
                            "year_4": 21,
                            "year_5": 27
                        }
                    ]
                },
                "management_notes": "Water regulation (stress period) precedes bahar flowering induction. Drip system with 4 drippers per tree.",
                "reference_adjustment_note": "Water requirement depends on several factors: climate and weather, soil type, organic content, plant age, plant size, plant stage and crop load, hence, will vary from orchard to orchard (ICAR-NRCP/MANAGE 2022, p. 47). Standardize using 24-hr fist-feel soil moisture test at 15–20 cm depth in root zone; flush manifolds and laterals to remove sediment."
            },
            "irrigation_stages_detail": None
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Semi-arid rain shadow, low humidity, and well-drained light-to-medium Vertisols provide textbook conditions for premium Bhagwa cultivation.",
                "limiting_factors": [
                    "Bacterial blight (Xanthomonas axonopodis) during wet spells"
                ],
                "source_id": "icar_nrcp_manage_2022",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Dry micro-climate, high sunshine hours, and well-drained soils allow excellent Hasta Bahar regulation and export quality fruit.",
                "limiting_factors": [
                    "Nematode infestation in sandy patches"
                ],
                "source_id": "icar_nrcp_manage_2022",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "High monsoon rainfall and high RH (> 50%) elevate risk of bacterial blight (Xanthomonas axonopodis) and root rot; requires protected microclimates and regional field validation.",
                "limiting_factors": [
                    "High atmospheric humidity",
                    "Bacterial blight (Xanthomonas)",
                    "Fruit cracking and decay"
                ],
                "source_id": "icar_nrcp_manage_2022",
                "evidence_status": "requires_regional_validation"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Extreme monsoon downpours (> 2000 mm) and high humidity create severe bacterial blight and wilt pressure; classified provisionally pending local micro-climate validation.",
                "limiting_factors": [
                    "Torrential rainfall",
                    "Continuous cloudiness",
                    "Root rot (Ceratocystis)"
                ],
                "source_id": "icar_nrcp_manage_2022",
                "evidence_status": "requires_regional_validation"
            }
        ]
    },
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
        "recommended_varieties": [
            "Phule Sangam (KDS 726)",
            "Phule Kimaya (KDS 753)",
            "JS 335",
            "DSb 21"
        ],
        "source_id": "icar_iisr_soybean_2022",
        "soil": {
            "preferred_textures": [
                "Clay Loam",
                "Clay",
                "Medium Black Vertisol"
            ],
            "acceptable_textures": [
                "Loam",
                "Silt Loam"
            ],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 7.5,
            "ph_tolerable_min": 6.0,
            "ph_tolerable_max": 8.0,
            "drainage_requirement": "Well-drained; seed germination and nodulation fail under waterlogging",
            "salinity_sensitivity": "Sensitive (EC < 1.5 dS/m; salt stress drastically reduces nodulation)",
            "min_soil_depth_cm": 45.0,
            "optimum_organic_carbon_g_kg": 6.5,
            "water_holding_capacity_pref": "Moderate to High",
            "source_id": "icar_iisr_soybean_2022",
            "evidence_status": "derived",
            "unverified_parameters": None
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
            "source_id": "icar_iisr_soybean_2022",
            "evidence_status": "derived"
        },
        "seasons": [
            {
                "season_name": "Kharif",
                "is_primary_season": True,
                "planting_window_maharashtra": "20 June to 10 July (after receiving 75–100 mm monsoon rain)",
                "harvesting_window_maharashtra": "October",
                "duration_days_min": 95,
                "duration_days_max": 110,
                "planting_calendar_by_region": {
                    "Baramati": "25 June - 10 July",
                    "Maval": "20 June - 05 July"
                },
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
            "source_id": "icar_iisr_soybean_2022",
            "evidence_status": "derived",
            "daily_water_table": None,
            "irrigation_stages_detail": [
                {
                    "source_id": "mpkv_research_2023",
                    "source_citation": "MPKV Research Recommendations 2023, Recommendation 12, p. 3",
                    "scope": "Sub-montane Zone Fertilizer & Water Efficiency",
                    "recommendation": "Application of 50% nitrogen and potassium at sowing and 50% at 35 DAS along with full phosphorus is recommended for higher yield and moisture use efficiency in Sub-montane zone light soils."
                }
            ]
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "High-yielding rainfed Kharif crop with protective irrigation backup; varieties Phule Sangam and Phule Kimaya yield up to 25–30 q/ha.",
                "limiting_factors": [
                    "Dry spell during pod development"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Excellent fit for Kharif on medium-to-deep Vertisols followed by Rabi wheat or chickpea.",
                "limiting_factors": [
                    "Rust incidence during prolonged humid overcast weather"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Moderately Suitable",
                "agronomic_rationale": "Performs well on sloped plateaus with free drainage; excessive rain in flat valleys causes seed rot.",
                "limiting_factors": [
                    "Waterlogging in lowlands",
                    "Harvesting difficulties under late monsoon showers"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "requires_regional_validation"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "Excessive monsoon downpours (> 2000 mm) cause severe pod rot, poor nodulation, and harvesting losses.",
                "limiting_factors": [
                    "Continuous torrential rainfall",
                    "Soil acidity"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "requires_regional_validation"
            }
        ]
    },
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
        "recommended_varieties": [
            "Phule Yamuna",
            "PKV Hy 2",
            "Ajeet 155 (Bt)",
            "RCH 2 (Bt)"
        ],
        "source_id": "icar_cicr_cotton_2022",
        "soil": {
            "preferred_textures": [
                "Deep Black Vertisol",
                "Clay",
                "Clay Loam"
            ],
            "acceptable_textures": [
                "Medium Black",
                "Silt Loam"
            ],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 8.0,
            "ph_tolerable_min": 5.8,
            "ph_tolerable_max": 8.5,
            "drainage_requirement": "Good internal drainage mandatory despite clay texture",
            "salinity_sensitivity": "Moderately Tolerant (EC up to 4.0 dS/m during established growth)",
            "min_soil_depth_cm": 90.0,
            "optimum_organic_carbon_g_kg": 5.5,
            "water_holding_capacity_pref": "High; requires stored moisture in subsoil for boll maturation",
            "source_id": "icar_cicr_cotton_2022",
            "evidence_status": "derived",
            "unverified_parameters": None
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
            "source_id": "icar_cicr_cotton_2022",
            "evidence_status": "derived"
        },
        "seasons": [
            {
                "season_name": "Kharif",
                "is_primary_season": True,
                "planting_window_maharashtra": "15 June to 30 June",
                "harvesting_window_maharashtra": "November to January",
                "duration_days_min": 150,
                "duration_days_max": 180,
                "planting_calendar_by_region": {
                    "Baramati": "15 June - 30 June",
                    "Indapur": "15 June - 05 July"
                },
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
            "source_id": "icar_cicr_cotton_2022",
            "evidence_status": "derived",
            "daily_water_table": None,
            "irrigation_stages_detail": None
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Moderately Suitable",
                "agronomic_rationale": "Suitable on deep black Vertisols with supplemental drip irrigation; requires pink bollworm monitoring.",
                "limiting_factors": [
                    "Sucking pest complex in early stages"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Moderately Suitable",
                "agronomic_rationale": "Grown in non-waterlogged medium-to-deep black soils with good post-monsoon sunshine.",
                "limiting_factors": [
                    "Moisture stress during late boll development"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Heavy monsoon rains and continuous high humidity trigger severe boll rotting, square shedding, and rank vegetative growth.",
                "limiting_factors": [
                    "Continuous rainfall",
                    "Boll rot",
                    "Lack of boll opening sunshine"
                ],
                "source_id": "icar_cicr_cotton_2022",
                "evidence_status": "requires_regional_validation"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Extreme Western Ghats rainfall and acid soils completely prevent commercial cotton production.",
                "limiting_factors": [
                    "Excessive rainfall",
                    "Cloudiness",
                    "Boll rot"
                ],
                "source_id": "icar_cicr_cotton_2022",
                "evidence_status": "requires_regional_validation"
            }
        ]
    },
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
        "recommended_varieties": [
            "Pinnacle (30V92)",
            "Ganga 11",
            "DKC 9108",
            "Phule Rajarshi"
        ],
        "source_id": "mpkv_pop_2023",
        "soil": {
            "preferred_textures": [
                "Clay Loam",
                "Loam",
                "Sandy Clay Loam",
                "Medium Black"
            ],
            "acceptable_textures": [
                "Clay",
                "Silt Loam"
            ],
            "ph_optimum_min": 6.0,
            "ph_optimum_max": 7.5,
            "ph_tolerable_min": 5.5,
            "ph_tolerable_max": 8.0,
            "drainage_requirement": "Well-drained; extremely sensitive to standing water (even 24 hrs reduces yield by 30%)",
            "salinity_sensitivity": "Moderately Sensitive (EC < 1.7 dS/m)",
            "min_soil_depth_cm": 60.0,
            "optimum_organic_carbon_g_kg": 6.0,
            "water_holding_capacity_pref": "Moderate",
            "source_id": "mpkv_pop_2023",
            "evidence_status": "derived",
            "unverified_parameters": None
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
            "source_id": "mpkv_pop_2023",
            "evidence_status": "derived"
        },
        "seasons": [
            {
                "season_name": "Kharif",
                "is_primary_season": True,
                "planting_window_maharashtra": "15 June to 15 July",
                "harvesting_window_maharashtra": "September to October",
                "duration_days_min": 90,
                "duration_days_max": 105,
                "planting_calendar_by_region": {
                    "Baramati": "15 June - 10 July",
                    "Maval": "20 June - 10 July"
                },
                "source_id": "mpkv_pop_2023"
            },
            {
                "season_name": "Rabi",
                "is_primary_season": False,
                "planting_window_maharashtra": "15 October to 15 November",
                "harvesting_window_maharashtra": "February to March",
                "duration_days_min": 105,
                "duration_days_max": 120,
                "planting_calendar_by_region": {
                    "Baramati": "15 Oct - 15 Nov",
                    "Indapur": "15 Oct - 15 Nov"
                },
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
            "source_id": "mpkv_pop_2023",
            "evidence_status": "derived",
            "daily_water_table": None,
            "irrigation_stages_detail": None
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Thrives across Kharif, Rabi, and summer under well/canal irrigation; high demand for poultry feed and fodder.",
                "limiting_factors": [
                    "Fall Armyworm (Spodoptera frugiperda) monitoring required"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "High grain and green fodder productivity in Rabi under canal irrigation.",
                "limiting_factors": [
                    "Moisture stress during grain fill in tail-end canals"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Moderately Suitable",
                "agronomic_rationale": "Suitable in Kharif on elevated uplands with free drainage.",
                "limiting_factors": [
                    "Waterlogging in lowland plains during heavy monsoon"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "requires_regional_validation"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "Torrential rain causes severe water stagnation and nutrient leaching on flat lands.",
                "limiting_factors": [
                    "Excessive rainfall",
                    "Fungal stalk rot"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "requires_regional_validation"
            }
        ]
    },
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
        "recommended_varieties": [
            "Phule Samadhan (NIAW 1994)",
            "Trimbak (NIAW 301)",
            "Tapovan (NIAW 917)",
            "MACS 6222"
        ],
        "source_id": "icar_iiwbr_wheat_2022",
        "soil": {
            "preferred_textures": [
                "Clay",
                "Clay Loam",
                "Deep Black Vertisol"
            ],
            "acceptable_textures": [
                "Loam",
                "Silt Loam"
            ],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 7.8,
            "ph_tolerable_min": 6.0,
            "ph_tolerable_max": 8.2,
            "drainage_requirement": "Well-drained; moderate waterlogging tolerance during tillering",
            "salinity_sensitivity": "Moderately Tolerant (EC up to 4.0 dS/m; variety KRL 210 for saline patches)",
            "min_soil_depth_cm": 60.0,
            "optimum_organic_carbon_g_kg": 6.0,
            "water_holding_capacity_pref": "High",
            "source_id": "icar_iiwbr_wheat_2022",
            "evidence_status": "derived",
            "unverified_parameters": None
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
            "source_id": "icar_iiwbr_wheat_2022",
            "evidence_status": "derived"
        },
        "seasons": [
            {
                "season_name": "Rabi",
                "is_primary_season": True,
                "planting_window_maharashtra": "01 November to 20 November (Timely Sown)",
                "harvesting_window_maharashtra": "February to March",
                "duration_days_min": 105,
                "duration_days_max": 125,
                "planting_calendar_by_region": {
                    "Baramati": "01 Nov - 15 Nov",
                    "Indapur": "05 Nov - 20 Nov"
                },
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
            "source_id": "icar_iiwbr_wheat_2022",
            "evidence_status": "derived",
            "daily_water_table": None,
            "irrigation_stages_detail": [
                {
                    "source_id": "mpkv_research_2023",
                    "source_citation": "MPKV Research Recommendations 2023, Recommendation 8, pp. 2–3",
                    "scope": "Canal Irrigated Plain Zone Vertisols (Relative Profitability)",
                    "recommendation": "If only two canal irrigations are available during Rabi season in Vertisols of Plain Zone of Maharashtra, Gram or Sorghum is more profitable than Wheat."
                }
            ]
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Deep black soils with assured canal/well irrigation provide optimal conditions for high-yielding Phule Samadhan.",
                "limiting_factors": [
                    "Terminal heat stress if sowing delayed past 25 November"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "High yields achieved on Vertisols under timely November sowing.",
                "limiting_factors": [
                    "Terminal heat in February if sown late"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "Short winter window and high morning fog/humidity promote brown rust.",
                "limiting_factors": [
                    "High winter humidity",
                    "Foliar rust diseases"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "requires_regional_validation"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "Micro-climate too humid in valleys with acidic laterite soils.",
                "limiting_factors": [
                    "Soil acidity",
                    "Rust susceptibility"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "requires_regional_validation"
            }
        ]
    },
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
        "recommended_varieties": [
            "Maldandi (M 35-1)",
            "Phule Suchitra",
            "Phule Yashodha",
            "Phule Revati",
            "Phule Vasudha"
        ],
        "source_id": "icar_iimr_millets_2022",
        "soil": {
            "preferred_textures": [
                "Deep Black Vertisol",
                "Clay",
                "Clay Loam"
            ],
            "acceptable_textures": [
                "Medium Black",
                "Sandy Clay Loam"
            ],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 8.0,
            "ph_tolerable_min": 5.5,
            "ph_tolerable_max": 8.5,
            "drainage_requirement": "Well-drained; handles heavy clay exceptionally well by extracting deep subsoil moisture",
            "salinity_sensitivity": "Moderately Tolerant (EC up to 4.0 dS/m)",
            "min_soil_depth_cm": 60.0,
            "optimum_organic_carbon_g_kg": 5.0,
            "water_holding_capacity_pref": "Very High; deep Vertisols store receding monsoon rains for winter grain growth",
            "source_id": "icar_iimr_millets_2022",
            "evidence_status": "derived",
            "unverified_parameters": None
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
            "source_id": "icar_iimr_millets_2022",
            "evidence_status": "derived"
        },
        "seasons": [
            {
                "season_name": "Rabi",
                "is_primary_season": True,
                "planting_window_maharashtra": "15 September to 15 October (Hast Nakshatra)",
                "harvesting_window_maharashtra": "January to February",
                "duration_days_min": 115,
                "duration_days_max": 135,
                "planting_calendar_by_region": {
                    "Baramati": "15 Sept - 10 Oct",
                    "Indapur": "20 Sept - 15 Oct"
                },
                "source_id": "mpkv_pop_2023"
            },
            {
                "season_name": "Kharif",
                "is_primary_season": False,
                "planting_window_maharashtra": "15 June to 30 June",
                "harvesting_window_maharashtra": "October",
                "duration_days_min": 105,
                "duration_days_max": 115,
                "planting_calendar_by_region": {
                    "Baramati": "15 June - 30 June"
                },
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
            "source_id": "icar_iimr_millets_2022",
            "evidence_status": "derived",
            "daily_water_table": None,
            "irrigation_stages_detail": [
                {
                    "source_id": "mpkv_research_2023",
                    "source_citation": "MPKV Research Recommendations 2023, Recommendation 8, pp. 2–3",
                    "scope": "Canal Irrigated Plain Zone Vertisols",
                    "recommendation": "Cultivation of Rabi Sorghum under two canal irrigations with first canal irrigation at 20-25 DAS and second canal irrigation at 60-65 DAS is recommended for Plain Zone of Maharashtra in Vertisols."
                }
            ]
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Agro-climatic heartland for Rabi Maldandi Jowar. MPKV 2023 Rec. 8 confirms profitability on Plain Zone Vertisols with two canal irrigations (20-25 & 60-65 DAS). Represents regional screening for deep black moisture-retentive Vertisols, not taluka-wide verification across shallow upland soils.",
                "limiting_factors": [
                    "Shoot fly in early sown or delayed crops"
                ],
                "source_id": "mpkv_research_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Major rainfed and canal-irrigated staple on medium-to-deep black soils aligning with MPKV 2023 Rec. 8 Plain Zone Vertisol criteria. Regional screening status applies to moisture-conserving Vertisols, without claiming taluka-wide verification.",
                "limiting_factors": [
                    "Fall Armyworm attack in early vegetative stage"
                ],
                "source_id": "mpkv_research_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Excessive monsoon rainfall causes severe grain mold in Kharif; soils are too shallow/acidic for Rabi moisture retention.",
                "limiting_factors": [
                    "Grain mold (Curvularia/Fusarium)",
                    "Soil acidity"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "requires_regional_validation"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "Heavy downpours completely prevent grain setting and trigger head blight.",
                "limiting_factors": [
                    "Continuous rainfall",
                    "Grain mold"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "requires_regional_validation"
            }
        ]
    },
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
        "recommended_varieties": [
            "Dhanshakti (High Iron/Zinc)",
            "Phule Aadishakti",
            "Shraddha",
            "Saburi"
        ],
        "source_id": "mpkv_pop_2023",
        "soil": {
            "preferred_textures": [
                "Sandy Loam",
                "Loam",
                "Light to Medium Black",
                "Sandy Clay Loam"
            ],
            "acceptable_textures": [
                "Gravelly Loam",
                "Clay Loam"
            ],
            "ph_optimum_min": 6.5,
            "ph_optimum_max": 7.8,
            "ph_tolerable_min": 5.5,
            "ph_tolerable_max": 8.5,
            "drainage_requirement": "Must be freely draining; completely intolerant of standing water",
            "salinity_sensitivity": "Moderately Tolerant (EC up to 3.5 dS/m)",
            "min_soil_depth_cm": 30.0,
            "optimum_organic_carbon_g_kg": 4.5,
            "water_holding_capacity_pref": "Low to Moderate; thrives on light, shallow, gravelly soils",
            "source_id": "mpkv_pop_2023",
            "evidence_status": "derived",
            "unverified_parameters": None
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
            "source_id": "mpkv_pop_2023",
            "evidence_status": "derived"
        },
        "seasons": [
            {
                "season_name": "Kharif",
                "is_primary_season": True,
                "planting_window_maharashtra": "15 June to 15 July",
                "harvesting_window_maharashtra": "September",
                "duration_days_min": 75,
                "duration_days_max": 85,
                "planting_calendar_by_region": {
                    "Baramati": "15 June - 10 July",
                    "Indapur": "20 June - 15 July"
                },
                "source_id": "mpkv_pop_2023"
            },
            {
                "season_name": "Summer (Zaid)",
                "is_primary_season": False,
                "planting_window_maharashtra": "15 January to 15 February",
                "harvesting_window_maharashtra": "April to May",
                "duration_days_min": 80,
                "duration_days_max": 90,
                "planting_calendar_by_region": {
                    "Baramati": "15 Jan - 15 Feb"
                },
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
            "source_id": "mpkv_pop_2023",
            "evidence_status": "derived",
            "daily_water_table": None,
            "irrigation_stages_detail": None
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Ideal fit on light-to-medium upland soils in low rainfall pockets; biofortified Dhanshakti provides high nutrition.",
                "limiting_factors": [
                    "Downy mildew during overcast humid weather"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Excellent short-duration crop in Kharif drought-prone areas.",
                "limiting_factors": [
                    "Bird damage during maturity"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "High rainfall causes severe waterlogging, poor pollen viability, and heavy downy mildew / ergot attacks.",
                "limiting_factors": [
                    "Excessive moisture",
                    "Ergot disease",
                    "Downy mildew"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "requires_regional_validation"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "High monsoon humidity and precipitation completely incompatible with bajra flowering.",
                "limiting_factors": [
                    "Continuous rainfall",
                    "Crop failure due to ergot"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "requires_regional_validation"
            }
        ]
    },
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
        "recommended_varieties": [
            "Vijay (Wilt resistant)",
            "Digvijay",
            "Vishal (Bold seeded)",
            "Phule Vikram (Mechanized harvest)"
        ],
        "source_id": "icrisat_chickpea_2010",
        "soil": {
            "preferred_textures": [
                "Clay Loam",
                "Clay",
                "Medium Black Vertisol"
            ],
            "acceptable_textures": [
                "Loam",
                "Silt Loam"
            ],
            "ph_optimum_min": 6.0,
            "ph_optimum_max": 8.0,
            "ph_tolerable_min": None,
            "ph_tolerable_max": 8.5,
            "ph_context_notes": "Soil pH range 6.0–8.0 is specifically documented by ICRISAT 2010 (p. 8) as the 'best-suited' range for deep loams or silty clay loams, rather than a universal agronomic optimum or physiological ceiling across all soil textures. Chickpea is successfully cultivated in soils from coarse sands to fine-textured Vertisols (tolerating up to pH 8.5). Saline soils and fields with a high water table are unsuitable.",
            "best_suited_soil_textures": [
                "Deep Loam",
                "Silty Clay Loam"
            ],
            "drainage_requirement": "Loose tilth and good drainage; highly sensitive to poor aeration, waterlogging and collar rot (ICRISAT 2010, p. 8).",
            "salinity_sensitivity": "Sensitive; saline soils and fields with high water tables are not suitable (ICRISAT 2010, p. 8).",
            "min_soil_depth_cm": 45.0,
            "optimum_organic_carbon_g_kg": 5.5,
            "water_holding_capacity_pref": "High (conserved subsoil moisture from monsoon rains supports maturity)",
            "source_id": "icrisat_chickpea_2010",
            "evidence_status": "verified_authoritative",
            "unverified_parameters": [
                "ph_tolerable_min"
            ]
        },
        "climate": {
            "temp_optimum_min_c": 15.0,
            "temp_optimum_max_c": 25.0,
            "temp_tolerable_min_c": 10.0,
            "temp_tolerable_max_c": 35.0,
            "annual_rainfall_min_mm": 300.0,
            "annual_rainfall_max_mm": 450.0,
            "humidity_preference": "Cool, dry and bright weather; cloudy humid days induce pod borer (Helicoverpa) and Botrytis",
            "frost_sensitivity": "Low-temperature sensitivity during reproductive stage: mean of maximum and minimum daily temperatures < 15°C causes flower drop and reduced pod set (ICRISAT 2010, p. 3).",
            "heat_sensitivity": "High-temperature sensitivity during reproductive stage: maximum daily temperature > 35°C causes flower drop and reduced pod set (ICRISAT 2010, p. 3). Not a universal crop mortality threshold; vegetative plants tolerate higher temperatures under adequate soil moisture.",
            "thermal_threshold_context": "Sensitivity thresholds (>35°C daily max and <15°C mean of daily max and min) specifically apply during the reproductive stage causing flower drop and reduced pod set (ICRISAT 2010, p. 3), rather than representing universal vegetative mortality limits.",
            "solar_radiation_requirement": "Bright sunny days enhance branching and pod set",
            "source_id": "icrisat_chickpea_2010",
            "evidence_status": "verified_authoritative"
        },
        "seasons": [
            {
                "season_name": "Rabi",
                "is_primary_season": True,
                "planting_window_maharashtra": "10 October to 10 November",
                "harvesting_window_maharashtra": "January to February",
                "duration_days_min": 95,
                "duration_days_max": 115,
                "planting_calendar_by_region": {
                    "Baramati": "15 Oct - 05 Nov",
                    "Indapur": "20 Oct - 10 Nov"
                },
                "source_id": "mpkv_research_2023"
            }
        ],
        "water": {
            "annual_water_requirement_mm_min": 250.0,
            "annual_water_requirement_mm_max": 350.0,
            "rainfed_suitable": True,
            "irrigation_dependency": "Low to Supplemental (rainfed crop; two irrigations at branching and pod filling stages recommended)",
            "critical_growth_stages": [
                "Branching stage",
                "Pod filling stage"
            ],
            "waterlogging_sensitivity": "High; stagnant moisture induces Fusarium oxysporum wilt and collar rot",
            "drought_sensitivity": "Moderate; deep taproot extracts subsoil moisture; moisture stress with >30°C favors dry root rot",
            "source_id": "icrisat_chickpea_2010",
            "evidence_status": "verified_authoritative",
            "daily_water_table": None,
            "irrigation_stages_detail": [
                {
                    "source_id": "icrisat_chickpea_2010",
                    "source_citation": "ICRISAT Chickpea Seed Production Manual 2010, p. 11",
                    "scope": "General Seed & Grain Production",
                    "recommendation": "Chickpea is generally grown as a rainfed crop, but two irrigations, one each at branching and pod filling stages, are recommended for higher yield. Excess irrigation in heavy soils leads to excessive vegetative growth."
                },
                {
                    "source_id": "mpkv_research_2023",
                    "source_citation": "MPKV Research Recommendations 2023, Recommendation 8, pp. 2–3",
                    "scope": "Canal Irrigated Plain Zone Vertisols",
                    "recommendation": "Under two canal irrigations in Rabi season on Vertisols of Plain Zone of Maharashtra, first canal irrigation at 20-25 days after sowing (DAS) and second canal irrigation at 60-65 days after sowing is recommended for Gram/Chickpea."
                }
            ]
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Major Rabi pulse in crop rotations following early Kharif crops. MPKV 2023 Rec. 8 confirms two canal irrigations (20-25 & 60-65 DAS) provide high profitability in Plain Zone Vertisols. Regional screening classification applies specifically to medium-to-deep black Vertisols with assured canal or conserved moisture; does not establish taluka-wide suitability across non-Vertisol tracts or rainfed uplands.",
                "limiting_factors": [
                    "Pod borer (Helicoverpa armigera) during pod development"
                ],
                "source_id": "mpkv_research_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "Adapted to conserved subsoil moisture in deep black soils with 1-2 canal irrigations per MPKV 2023 Rec. 8 Plain Zone Vertisol criteria. Regional screening applies to canal-command Vertisol tracts; does not imply taluka-wide verification across light soils or tail-end irrigation deficit areas.",
                "limiting_factors": [
                    "Excess vegetative growth if over-irrigated"
                ],
                "source_id": "mpkv_research_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "Acidic soils and high post-monsoon humidity promote fungal root rot and collar rot; provisional classification requiring localized field validation.",
                "limiting_factors": [
                    "Fungal root rot in acid soils",
                    "Fog induced flower drop"
                ],
                "source_id": "icrisat_chickpea_2010",
                "evidence_status": "requires_regional_validation"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Unsuitable / High Disease Risk",
                "agronomic_rationale": "High residual soil moisture and acidic laterite soils cause collar rot risk; provisional rating requiring regional validation.",
                "limiting_factors": [
                    "Soil acidity (pH < 6.0)",
                    "Collar rot disease"
                ],
                "source_id": "icrisat_chickpea_2010",
                "evidence_status": "requires_regional_validation"
            }
        ]
    },
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
        "recommended_varieties": [
            "Phule Unnati",
            "Phule Morana",
            "TAG 24",
            "JL 501"
        ],
        "source_id": "mpkv_pop_2023",
        "soil": {
            "preferred_textures": [
                "Sandy Clay Loam",
                "Loam",
                "Sandy Loam",
                "Light to Medium Loam"
            ],
            "acceptable_textures": [
                "Clay Loam"
            ],
            "ph_optimum_min": 6.0,
            "ph_optimum_max": 7.2,
            "ph_tolerable_min": 5.5,
            "ph_tolerable_max": 7.8,
            "drainage_requirement": "Well-drained, loose friable soil mandatory for easy peg penetration and pod lifting",
            "salinity_sensitivity": "Sensitive (EC < 1.5 dS/m)",
            "min_soil_depth_cm": 45.0,
            "optimum_organic_carbon_g_kg": 6.0,
            "water_holding_capacity_pref": "Moderate; heavy, sticky cracking clay impedes peg entry and pod harvest",
            "source_id": "mpkv_pop_2023",
            "evidence_status": "derived",
            "unverified_parameters": None
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
            "source_id": "mpkv_pop_2023",
            "evidence_status": "derived"
        },
        "seasons": [
            {
                "season_name": "Summer (Zaid)",
                "is_primary_season": True,
                "planting_window_maharashtra": "15 January to 15 February",
                "harvesting_window_maharashtra": "May to June",
                "duration_days_min": 110,
                "duration_days_max": 125,
                "planting_calendar_by_region": {
                    "Baramati": "15 Jan - 15 Feb",
                    "Indapur": "20 Jan - 15 Feb"
                },
                "source_id": "mpkv_pop_2023"
            },
            {
                "season_name": "Kharif",
                "is_primary_season": False,
                "planting_window_maharashtra": "15 June to 10 July",
                "harvesting_window_maharashtra": "October",
                "duration_days_min": 105,
                "duration_days_max": 115,
                "planting_calendar_by_region": {
                    "Baramati": "20 June - 10 July"
                },
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
            "source_id": "mpkv_pop_2023",
            "evidence_status": "derived",
            "daily_water_table": None,
            "irrigation_stages_detail": None
        },
        "regional": [
            {
                "taluka": "Baramati",
                "district": "Pune",
                "suitability_status": "Highly Suitable",
                "agronomic_rationale": "High profitability as a summer crop under drip irrigation in medium friable soils; TAG 24 and Phule Unnati produce high oil content.",
                "limiting_factors": [
                    "Tikka leaf spot disease in late summer"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Indapur",
                "district": "Pune",
                "suitability_status": "Moderately Suitable",
                "agronomic_rationale": "Well-suited on sandy loam patches along river/canal belts; avoids heavy cracking clays.",
                "limiting_factors": [
                    "Heavy cracking soils make pod harvest labor intensive"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "regional_screening"
            },
            {
                "taluka": "Maval",
                "district": "Pune",
                "suitability_status": "Moderately Suitable",
                "agronomic_rationale": "Can be grown in Kharif on elevated gentle slopes with liming to counter soil acidity.",
                "limiting_factors": [
                    "Soil acidity impairs calcium uptake needed for pod filling",
                    "Waterlogging in heavy rains"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "requires_regional_validation"
            },
            {
                "taluka": "Mulshi",
                "district": "Pune",
                "suitability_status": "Marginal / High Input",
                "agronomic_rationale": "High rainfall causes pod rot in soil and washes away calcium necessary for shell formation.",
                "limiting_factors": [
                    "Severe pod rot in wet soils",
                    "Calcium deficiency causing empty pods (pops)"
                ],
                "source_id": "mpkv_pop_2023",
                "evidence_status": "requires_regional_validation"
            }
        ]
    }
]
