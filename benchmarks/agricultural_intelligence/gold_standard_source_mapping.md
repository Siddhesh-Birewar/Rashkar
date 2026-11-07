# CropNet AI — Gold-Standard Source Mapping (Phase 5.0)

**Document Version:** 1.0.0  
**Phase:** 5.0 (Intelligence Benchmark & Evaluation Framework)  
**Database Reference:** Supabase PostgreSQL 17 (`005_evidence_provenance_updates`)  
**Scope:** Complete Cross-Reference of Benchmark Test Cases to Authoritative Literature and Database Schema  

---

## 1. Primary Knowledge Source Registry

Every benchmark test case in `CROPNET-AGRI-BENCH-V1` is strictly grounded in the 12 registered agricultural knowledge sources established in Phase 4.

| Source ID | Organization | Document / Publication Title | Year | Primary Role in Benchmark |
|---|---|---|:---:|---|
| `icar_nrcp_manage_2022` | ICAR-NRCP & MANAGE | High-Tech Pomegranate Production Practices | 2022 | Pomegranate soil texture ("Light soil"), pH 6.5–7.0 (optimum) & 8.5 (upper tolerance), Bahar water tables (Tables 1–3, pp. 45–46), Bacterial Blight (*Xanthomonas*) |
| `icar_nrcp_pomegranate_2021` | ICAR-NRCP | Scientific Pomegranate Production Manual for Semi-Arid Tropics | 2021 | Pomegranate orchard establishment and supplementary nutrient management |
| `icrisat_chickpea_2010` | ICRISAT | Chickpea Seed Production Manual | 2010 | Chickpea best-suited soil pH 6.0–8.0, salinity sensitivity, reproductive thermal stress (>35°C max & <15°C mean, p. 3), physiological stage irrigation (p. 8) |
| `mpkv_research_2023` | MPKV, Rahuri | Research Recommendations Released during 2023 | 2023 | Vertisol cropping systems in Plain/Scarcity Zones (20–25 & 60–65 DAS irrigation), soil fertility classifications (N, P, K, SOC), regional screening criteria |
| `mpkv_pop_2023` | MPKV, Rahuri | Package of Practices for Field Crops & Agro-Techniques (कृषी दैनंदिनी) | 2023 | Maharashtra field crop calendars, sowing windows (Groundnut, Bajra), and water conservation techniques |
| `iisr_brochure_glance` | ICAR-IISR, Lucknow | ICAR-IISR at a Glance | 2010 | Sugarcane agroclimatic requirements, water duration (12–18 months), seasonal water demands |
| `icar_iisr_sugarcane_2022` | ICAR-IISR, Lucknow | Good Agricultural Practices in Sugarcane Cultivation for Tropical India | 2022 | Tropical sugarcane tillering water management and irrigation schedules |
| `icar_cicr_cotton_2022` | ICAR-CICR, Nagpur | Cotton Production Technology for Rainfed and Irrigated Vertisols | 2022 | Cotton Vertisol requirements, regional screening in Baramati/Indapur, drainage and depth constraints |
| `icar_iiwbr_wheat_2022`| ICAR-IIWBR, Karnal | Wheat Production Technologies for Peninsular Zone of India | 2022 | Peninsular wheat irrigation, groundwater salinity sensitivity, winter temperature requirements |
| `icar_iisr_soybean_2022` | ICAR-IISR, Indore | Soybean Production Technologies for Central and Peninsular India | 2022 | Soybean waterlogging sensitivity, flowering rainfall constraints in Western Ghats |
| `icar_iimr_millets_2022` | ICAR-IIMR, Hyderabad | Sorghum and Small Millets Production Guide for Dryland Agriculture | 2022 | Pearl Millet (Bajra) Kharif sowing windows (June 15 – July 15), dryland drought management |
| `icar_iipr_pulses_2022` | ICAR-IIPR, Kanpur | Chickpea Production Technology and Moisture Conservation in Peninsular Vertisols | 2022 | Cross-pulse agronomy, pulse nodulation pH constraints |

---

## 2. Test Case to Database & Literature Mapping

| Test ID | Domain | Database Table & Columns Queried | Primary Document & Section | Verified Scientific Rule / Ground Truth |
|---|---|---|---|---|
| `AGRI-BENCH-001` | Soil | `soil_parameters` (`parameter_name`, `value`), `farm_soil_profiles` | MPKV (2023), Soil Testing Chapter | Total N (~0.05%) != Available N (185 kg/ha). Available N < 280 kg/ha is 'Low'. Fertilizer N application is mandatory. |
| `AGRI-BENCH-002` | Soil | `crop_soil_requirements` (`ph_best_suited_min/max`, `drainage_type`, `waterlogging_sensitivity`) | ICAR-NRCP & MANAGE (2022), p. 3 | pH 6.8 is optimum, but shallow depth (20 cm) and poor drainage/waterlogging disqualify pomegranate unconditionally. |
| `AGRI-BENCH-003` | Soil | `farm_soil_profiles`, `soil_parameters` (`organic_carbon`) | MPKV (2023), Soil Chemistry Section | SOC 0.38% is 'Low' (< 0.50% threshold for semi-arid Vertisols). Requires FYM/compost incorporation. |
| `AGRI-BENCH-004` | Soil | `crop_soil_requirements` (`salinity_tolerance`, `texture`), `crop_catalog` | ICRISAT (2010), p. 8 | Chickpea is highly sensitive to soil salinity and waterlogging. Canal zone requires EC verification before certification. |
| `AGRI-BENCH-005` | Soil | `crop_soil_requirements` (`best_suited_soil_textures`, `ph_best_suited_min/max`, `ph_tolerable_max`) | ICAR-NRCP & MANAGE (2022), p. 3 | "Light soil" with pH 6.5–7.0 is most suitable. Upper tolerance is 8.5 (well-managed). Lower tolerable pH is NULL. |
| `AGRI-BENCH-006` | Suitability | `crop_regional_suitability` (`regional_status`, `suitability_class`, `taluka`) | ICRISAT (2010) & MPKV (2023) | Maval is `requires_regional_validation`; Western Ghats humidity promotes Ascochyta/Botrytis and vegetative excess. |
| `AGRI-BENCH-007` | Suitability | `crop_water_requirements` (`annual_water_requirement_mm_min/max`, `waterlogging_sensitivity`) | ICAR-IISR (2021) | Sugarcane requires 1500–2500 mm and peak irrigation during summer tillering. Seasonal well dry by Feb is disqualifying. |
| `AGRI-BENCH-008` | Suitability | `crop_regional_suitability` (`regional_status`, `notes`), `agricultural_knowledge_sources` | MPKV (2023) & ICAR-CICR (2022) | `regional_screening` is a zonal agroecological filter, NOT a farm-level verification. Local testing remains essential. |
| `AGRI-BENCH-009` | Suitability | `crop_season_requirements` (`season_name`, `sowing_window_start`, `sowing_window_end`) | MPKV (2023) & ICAR-IIMR (2022) | Kharif Bajra optimum sowing is June 15 to July 15 with monsoon onset. |
| `AGRI-BENCH-010` | Suitability | `crop_regional_suitability` (`taluka`, `regional_status`), `crop_climate_requirements` | MPKV (2023) & ICAR-IISR (2022) | Mulshi is `requires_regional_validation`; high rainfall (>2000 mm) causes severe flower abortion and fungal collar rot. |
| `AGRI-BENCH-011` | Decision | `crop_regional_suitability`, `crop_catalog` | CropNet Architectural Standard (Phase 5) | Agronomic suitability measures biological feasibility; market profitability is decoupled and cannot be guaranteed. |
| `AGRI-BENCH-012` | Decision | `crop_soil_requirements` (`texture`, `drainage_type`) | Soil Physics Principles / MPKV (2023) | Physical contradiction: Coarse sand cannot hold standing water for 14 days without subsoil hardpan or runoff depression. |
| `AGRI-BENCH-013` | Decision | `crop_soil_requirements` (`ph_optimum_min/max`), `soil_parameters` | MPKV (2023) & ICAR-CICR (2022) | pH 8.3 is alkaline/calcareous, not acidic. Applying lime (CaCO3) is prohibited; induces severe micronutrient lockout. |
| `AGRI-BENCH-014` | Decision | All Phase 4 tables | CropNet Safety & Governance Specification | Zero context query must trigger formal abstention and structured follow-up questions. |
| `AGRI-BENCH-015` | Decision | `crop_soil_requirements` (`ph_tolerable_min`, `ph_optimum_min/max`) | ICAR-NRCP & MANAGE (2022), p. 3 | 6.0 lower tolerable pH is unverified in literature. Value is preserved as NULL in database; must reject 6.0 claim. |
| `AGRI-BENCH-016` | Decision | `crop_water_requirements` (`annual_water_requirement_mm_min/max`, `daily_water_table`) | ICAR-NRCP & MANAGE (2022), pp. 45–46 | Annual mm is unsupported/NULL. Pomegranate water is specified exclusively in liters/tree/day by Bahar and age. |
| `AGRI-BENCH-017` | Irrigation | `crop_water_requirements` (`daily_water_table`) | ICAR-NRCP & MANAGE (2022), Table 1, p. 45 | 4-year-old tree in October under Mrig Bahar requires 28.3 to 34.2 L/tree/day (Met Weeks 40–44). |
| `AGRI-BENCH-018` | Irrigation | `crop_water_requirements` (`irrigation_stages_detail`, `critical_stages`) | ICRISAT (2010), p. 8 vs MPKV (2023) | Decoupled preservation: ICRISAT stage-based (branching/pod) vs MPKV calendar-based (20–25 & 60–65 DAS). No 4-irrigation blend. |
| `AGRI-BENCH-019` | Irrigation | `crop_water_requirements` (`waterlogging_sensitivity`), `farm_weather_snapshots` | ICRISAT (2010) & MPKV (2023) | Chickpea in Vertisols dies from waterlogging and collar rot. Suspend irrigation when 50 mm heavy rain is forecast. |
| `AGRI-BENCH-020` | Irrigation | `crop_soil_requirements` (`salinity_tolerance`), `crop_catalog` | MPKV (2023) & ICAR-IIWBR (2022) | Semi-arid Vertisol groundwater frequently has EC > 1.5 dS/m and high SAR. Water testing is mandatory. |
| `AGRI-BENCH-021` | Weather | `farm_climate_summaries` vs `farm_weather_snapshots` | MPKV (2023) & MPKV (2023) | 30-year June normal (115 mm) != real-time forecast. Sowing without monsoon arrival causes dry seed desiccation. |
| `AGRI-BENCH-022` | Weather | `crop_climate_requirements` (`temp_reproductive_max_c`, `thermal_threshold_context`) | ICRISAT (2010), p. 3 | >35°C daily max during reproductive stage causes flower drop and reduced pod set. Qualified as reproductive threshold. |
| `AGRI-BENCH-023` | Weather | `crop_climate_requirements` (`temp_reproductive_min_mean_c`, `thermal_threshold_context`) | ICRISAT (2010), p. 3 | Mean of max and min <15°C during reproductive stage causes flower abortion and delayed pod setting. |
| `AGRI-BENCH-024` | Retrieval | `crop_regional_suitability` (`regional_status`), `agricultural_knowledge_sources` | MPKV (2023), Chickpea Section | Inapplicable retrieval: MPKV recommendation for deep Vertisols under canal irrigation does not apply to Maval shallow gravel. |
| `AGRI-BENCH-025` | Retrieval | `agricultural_knowledge_sources`, `crop_soil_requirements`, `crop_water_requirements` | ICRISAT (2010) & MPKV (2023) | Multi-source attribution: ICRISAT for pH 6.0–8.0 & physiological irrigation; MPKV for Vertisol DAS irrigation. |
| `AGRI-BENCH-026` | Retrieval | `crop_catalog` | CropNet Phase 4 10-Crop Taxonomy | Dragon Fruit is outside the 10 priority crops. System must abstain and notify catalogue boundaries. |
| `AGRI-BENCH-027` | Marathi | `crop_soil_requirements` (`waterlogging_sensitivity`, `best_suited_soil_textures`) | ICAR-NRCP & MANAGE (2022), p. 3 | Marathi vernacular: 'तेलकट डाग / जिवाणूजन्य करपा' (*Xanthomonas*), 'पाण्याचा निचरा', 'हलकी जमीन'. |
| `AGRI-BENCH-028` | Marathi | `crop_climate_requirements` (`temp_reproductive_max_c`) | ICRISAT (2010), p. 3 | Marathi scientific terms: 'पुनरुत्पादन अवस्था', 'कमाल तापमान ३५°C', 'फूल गळ', 'घाटे धारणा'. |
| `AGRI-BENCH-029` | Marathi | `crop_soil_requirements`, `crop_regional_suitability` | ICRISAT (2010) & MPKV (2023) | English and Marathi outputs must have 100% numerical parity (pH 7.8 in 6.0–8.0) and identical caveats. |
| `AGRI-BENCH-030` | Marathi | `crop_water_requirements` (`daily_water_table`) | ICAR-NRCP & MANAGE (2022), pp. 45–46 | Hasta Bahar ('हस्त बहार') avoids summer water scarcity (Feb-March harvest); Ambia Bahar requires peak summer water. |

---

## 3. Strict Agronomic Boundary Justifications

1. **Pomegranate Lower Tolerable pH (`ph_tolerable_min: NULL`):**
   - *Literature:* ICAR-NRCP & MANAGE (2022) only certifies 6.5–7.0 (most suitable) and up to 8.5 (upper tolerance). No lower limit is established.
   - *Rule:* The benchmark penalizes any system that invents a lower boundary (e.g. 6.0 or 5.5).
2. **Pomegranate Annual Water Requirement (`annual_water_requirement_mm_min/max: NULL`):**
   - *Literature:* ICAR-NRCP & MANAGE (2022) exclusively reports daily tree water requirements in liters/tree/day (Tables 1–3).
   - *Rule:* Systems that report generic annual rainfall/irrigation millimeters (e.g. 500–1000 mm) fail the benchmark.
3. **Chickpea Upper Tolerable pH (`ph_tolerable_max: NULL`):**
   - *Literature:* ICRISAT (2010, p. 8) defines 6.0–8.0 as "best-suited". No tolerance up to 8.5 is established.
   - *Rule:* The benchmark ensures 8.0 is retained as the upper bound of the best-suited range and penalizes unsupported 8.5 claims.
4. **Chickpea Thermal Thresholds (`temp_reproductive_max_c: 35.0` & `temp_reproductive_min_mean_c: 15.0`):**
   - *Literature:* ICRISAT (2010, p. 3) explicitly restricts these temperatures to the **reproductive stage** (causing flower drop and pod abortion).
   - *Rule:* The benchmark penalizes systems that represent 35°C as a vegetative or universal crop survival limit.
Path: file:///Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/benchmarks/agricultural_intelligence/gold_standard_source_mapping.md
