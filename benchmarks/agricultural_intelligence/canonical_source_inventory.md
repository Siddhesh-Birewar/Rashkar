# CropNet AI — Canonical Agricultural Source Inventory (Phase 5.0.1)

**Document Version:** 1.0.0  
**Phase:** 5.0.1 (Benchmark Source Traceability Audit)  
**Database Reference:** Hosted Supabase PostgreSQL 17 (`005_evidence_provenance_updates`)  
**Registry Table:** `agricultural_knowledge_sources`  
**Status:** Canonical Truth Registry  

---

## 1. Official Canonical Source Inventory

The table below catalogs the exact 12 knowledge source records provisioned in the production Supabase database. Every agricultural claim, crop requirement boundary, and benchmark test case must trace directly to this canonical registry.

| # | Canonical Source ID | Official Publication Title | Issuing Organization | Year | Document Type | Key Pages / Tables / Sections | Supported Crops & Agronomic Claims | Evidence Quality Classification |
|---|---|---|---|:---:|---|---|---|:---:|
| 1 | **`mpkv_research_2023`** | *Research Recommendations Released during 2023 by Mahatma Phule Krishi Vidyapeeth, Rahuri* | Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri | 2023 | Annual Research Trial Releases (Joint Agresco) | pp. 1–13 (69 discrete trial releases; Rec. 8, pp. 2–3 for canal Vertisol Rabi scheduling) | Chickpea, Sorghum, Sugarcane, Maize, Soybean. Verifies Vertisol canal-irrigated scheduling (20–25 & 60–65 DAS), Suru drip planting with micro-sprinklers, Sub-montane split N/K. | `verified_authoritative` |
| 2 | **`mpkv_pop_2023`** | *Package of Practices for Field Crops & Agro-Techniques of Western Maharashtra (कृषी दैनंदिनी २०२३-२४)* | Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri | 2023 | Comprehensive Extension Compendium | pp. 24–168 (Cereals, Pulses, Oilseeds, Soil Fertility ratings) | Bajra, Groundnut, Sorghum, Wheat, Chickpea. Standard soil test fertility ratings (Available N < 280 kg/ha = Low; SOC < 0.50% = Low); Kharif sowing rainfall criteria (75–100 mm). | `requires_pop_compendium` |
| 3 | **`icrisat_chickpea_2010`** | *Chickpea Seed Production Manual* | International Crops Research Institute for the Semi-Arid Tropics (ICRISAT), Patancheru | 2010 | Peer-Reviewed Crop & Seed Production Manual | pp. 1–28 (p. 3: thermal thresholds; p. 8: soil texture, pH 6.0–8.0, salinity; p. 11: stage irrigation) | Chickpea. Verifies best-suited soil pH (6.0–8.0), salinity/waterlogging sensitivity, reproductive thermal stress (>35°C max & <15°C mean), branching/pod-filling irrigations. | `verified_authoritative` |
| 4 | **`icar_nrcp_manage_2022`** | *High-tech Pomegranate Production Practices for Export Quality Pomegranate Production and Value Addition* | ICAR-National Research Centre on Pomegranate (NRCP), Solapur & MANAGE, Hyderabad | 2022 | Comprehensive Monograph / Manual (ISBN: 978-93-91668-12-9) | pp. 1–119 (p. 3: Light soil, pH 6.5–7.0, up to 8.5; pp. 45–46: Tables 1–3 daily tree water schedules) | Pomegranate. Verifies "Light soil", pH 6.5–7.0 most suitable, 8.5 qualified upper tolerance, 480 daily water schedule values (L/tree/day by Bahar and tree age), Bacterial Blight (*Xanthomonas*). | `verified_authoritative` |
| 5 | **`icar_nrcp_pomegranate_2021`** | *Scientific Pomegranate Production Manual for Semi-Arid Tropics* | ICAR — National Research Centre on Pomegranate (NRCP), Solapur | 2021 | Extension Manual | pp. 15–45 (Soil suitability, Bahar regulation, wilt management) | Pomegranate. Baseline orchard establishment guidelines (superseded in specific water tables and pH bounds by 2022 manual). | `superseded_by_2022_manual` |
| 6 | **`iisr_brochure_glance`** | *IISR at a Glance* | ICAR — Indian Institute of Sugarcane Research (IISR), Lucknow | 2010 | Institutional & Technology Brochure | pp. 1–8 (Institutional history, sub-tropical varieties, farm machinery) | Sugarcane. General institutional context; does NOT substantiate Maharashtra Vertisol soil or water parameters. | `unverified_bibliographic` |
| 7 | **`icar_iisr_sugarcane_2022`** | *Good Agricultural Practices in Sugarcane Cultivation for Tropical India* | ICAR — Indian Institute of Sugarcane Research (IISR), Lucknow | 2022 | Institutional Technical Bulletin | pp. 12–38 (Water management and tropical soil suitability) | Sugarcane. Tropical sugarcane water requirements (1500–2500 mm), tillering water stress sensitivity, drip irrigation. | `unverified_bibliographic` |
| 8 | **`icar_cicr_cotton_2022`** | *Cotton Production Technology for Rainfed and Irrigated Vertisols of Maharashtra* | ICAR — Central Institute for Cotton Research (CICR), Nagpur | 2022 | Research Bulletin | pp. 14–32 (Vertisol depth and drainage criteria for Bt Cotton) | Cotton. Vertisol suitability, minimum depth requirements (>60 cm), alkalinity tolerance up to pH 8.5, drainage sensitivity. | `requires_pop_compendium` |
| 9 | **`icar_iiwbr_wheat_2022`** | *Wheat Production Technologies for Peninsular Zone of India* | ICAR — Indian Institute of Wheat and Barley Research (IIWBR), Karnal | 2022 | Regional Production Guide | pp. 18–35 (Peninsular thermal constraints and CRI irrigation) | Wheat. Peninsular wheat winter temperature sensitivity (terminal heat stress), Crown Root Initiation (CRI) irrigation, groundwater salinity sensitivity. | `requires_pop_compendium` |
| 10 | **`icar_iisr_soybean_2022`** | *Soybean Production Technologies for Central and Peninsular India* | ICAR — Indian Institute of Soybean Research (IISR), Indore | 2022 | Technical Bulletin | pp. 8–24 (Varietal guide, waterlogging sensitivity, flowering moisture) | Soybean. Waterlogging sensitivity, flowering-stage excessive rainfall risks, nodulation requirements in Vertisols. | `requires_pop_compendium` |
| 11 | **`icar_iimr_millets_2022`** | *Sorghum and Small Millets Production Guide for Dryland Agriculture* | ICAR — Indian Institute of Millets Research (IIMR), Hyderabad | 2022 | Extension Guide | pp. 22–50 (Rabi Jowar Maldandi agronomy, Kharif Bajra sowing) | Bajra, Sorghum. Kharif Bajra sowing window (June 15 – July 15), drought adaptation mechanisms, moisture conservation. | `requires_pop_compendium` |
| 12 | **`icar_iipr_pulses_2022`** | *Chickpea Production Technology and Moisture Conservation in Peninsular Vertisols* | ICAR — Indian Institute of Pulses Research (IIPR), Kanpur | 2022 | Technical Guide | pp. 10–28 (Wilt prevention, seed treatment, moisture conservation) | Chickpea. Complementary pulse agronomy, seed treatment with *Trichoderma*, soil moisture conservation in Vertisols. | `unverified_bibliographic` |

---

## 2. Institutional Evidence Quality Hierarchy

CropNet enforces a 4-tier evidence hierarchy to govern whether a claim may be treated as verified or conditional:

1. **`verified_authoritative` (Tier 1):** Directly verified from primary peer-reviewed manuals or official university research releases (`mpkv_research_2023`, `icrisat_chickpea_2010`, `icar_nrcp_manage_2022`). Fully supports numerical thresholds and disqualification logic.
2. **`requires_pop_compendium` (Tier 2):** Comprehensive institutional recommendations from national ICAR institutes or state university packages of practices (`mpkv_pop_2023`, `icar_cicr_cotton_2022`, `icar_iiwbr_wheat_2022`, `icar_iisr_soybean_2022`, `icar_iimr_millets_2022`). Supports general crop rules and regional screening, but requires full compendium cross-reference for edge-case thresholds.
3. **`unverified_bibliographic` (Tier 3):** Institutional brochures or national guides that lack localized Maharashtra Vertisol experimental trials (`iisr_brochure_glance`, `icar_iisr_sugarcane_2022`, `icar_iipr_pulses_2022`). Claims supported only by Tier 3 are classified as `CONDITIONALLY_SUPPORTED` and cannot be used to certify categorical taluka unsuitability.
4. **`superseded_by_2022_manual` (Tier 4):** Older institutional manuals (`icar_nrcp_pomegranate_2021`) whose parameters have been officially updated or refined by newer publications.
Path: file:///Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/benchmarks/agricultural_intelligence/canonical_source_inventory.md
