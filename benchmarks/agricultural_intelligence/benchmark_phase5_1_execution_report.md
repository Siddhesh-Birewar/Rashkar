# CropNet AI — Phase 5.1 Benchmark Execution Report

- **Execution Timestamp**: 2026-11-07T11:13:37.694875Z
- **Total Benchmark Cases**: 30
- **Passed Cases**: 30
- **Failed Cases**: 0
- **Overall Pass Rate**: 100.0%
- **Track A Retrieval Score**: 100.0%
- **Track B Reasoning Score**: 100.0%

## Detailed Case Results

| Test ID | Domain | Track A (Retrieval) | Track B (Reasoning) | Status | Notes |
|---------|--------|---------------------|---------------------|--------|-------|
| AGRI-BENCH-001 | Soil Intelligence | 1.00 | 1.00 | PASS | Correctly separated Total N from Available N (< 280 kg/ha low flagged) |
| AGRI-BENCH-002 | Soil Intelligence | 1.00 | 1.00 | PASS | Correctly disqualified pomegranate on poor drainage and flagged shallow depth pit planting advisory |
| AGRI-BENCH-003 | Soil Intelligence | 1.00 | 1.00 | PASS | Flagged low soil organic carbon |
| AGRI-BENCH-004 | Soil Intelligence | 1.00 | 1.00 | PASS | Correctly withheld unconditional suitability pending EC data |
| AGRI-BENCH-005 | Soil Intelligence | 1.00 | 1.00 | PASS | Verified pomegranate soil requirements: Light soil, pH 6.5-7.0 optimum, 8.5 max |
| AGRI-BENCH-006 | Crop Suitability | 1.00 | 1.00 | PASS | Correctly marked Maval chickpea as REQUIRES_REGIONAL_VALIDATION |
| AGRI-BENCH-007 | Crop Suitability | 1.00 | 1.00 | PASS | Correctly disqualified sugarcane due to summer water exhaustion post-February |
| AGRI-BENCH-008 | Crop Suitability | 1.00 | 1.00 | PASS | Correctly treated regional screening as macro-filter, requiring soil validation |
| AGRI-BENCH-009 | Crop Suitability | 1.00 | 1.00 | PASS | Preserved optimum June 15 - July 15 sowing window |
| AGRI-BENCH-010 | Crop Suitability | 1.00 | 1.00 | PASS | Correctly marked Mulshi soybean as REQUIRES_REGIONAL_VALIDATION |
| AGRI-BENCH-011 | Agricultural Decision Reasoning | 1.00 | 1.00 | PASS | Agronomically suitable without financial speculation |
| AGRI-BENCH-012 | Agricultural Decision Reasoning | 1.00 | 1.00 | PASS | Detected physical contradiction between coarse sand and 14 days waterlogging |
| AGRI-BENCH-013 | Agricultural Decision Reasoning | 1.00 | 1.00 | PASS | Detected chemical contradiction: pH 8.3 is alkaline/calcareous, refused lime recommendation |
| AGRI-BENCH-014 | Agricultural Decision Reasoning | 1.00 | 1.00 | PASS | Abstained from ungrounded recommendations on zero farm context |
| AGRI-BENCH-015 | Agricultural Decision Reasoning | 1.00 | 1.00 | PASS | Preserved lower tolerable pH as NULL without fabrication |
| AGRI-BENCH-016 | Agricultural Decision Reasoning | 1.00 | 1.00 | PASS | Preserved annual water requirement as NULL, defined in L/tree/day |
| AGRI-BENCH-017 | Irrigation Intelligence | 1.00 | 1.00 | PASS | Indexed ICAR-NRCP Table 1 Mrig Bahar daily water table |
| AGRI-BENCH-018 | Irrigation Intelligence | 1.00 | 1.00 | PASS | Decoupled ICRISAT (physiological) and MPKV (calendar) irrigation frameworks |
| AGRI-BENCH-019 | Irrigation Intelligence | 1.00 | 1.00 | PASS | Advised postponement and suspension of chickpea irrigation due to heavy rainfall forecast |
| AGRI-BENCH-020 | Irrigation Intelligence | 1.00 | 1.00 | PASS | Flagged electrical conductivity and salinity testing requirement |
| AGRI-BENCH-021 | Weather and Climate Intelligence | 1.00 | 1.00 | PASS | Gated sowing until 75-100 mm monsoon soaking rainfall received |
| AGRI-BENCH-022 | Weather and Climate Intelligence | 1.00 | 1.00 | PASS | Triggered reproductive thermal warning: > 35°C causes flower drop and reduced pod set |
| AGRI-BENCH-023 | Weather and Climate Intelligence | 1.00 | 1.00 | PASS | Triggered reproductive thermal warning: < 15°C mean causes flower abortion and delayed pod set |
| AGRI-BENCH-024 | Agricultural Knowledge Retrieval | 1.00 | 1.00 | PASS | Identified contextual inapplicability of plain Vertisol recommendations to Maval |
| AGRI-BENCH-025 | Agricultural Knowledge Retrieval | 1.00 | 1.00 | PASS | Dual institutional citations retrieved: ICRISAT 2010 and MPKV 2023 |
| AGRI-BENCH-026 | Agricultural Knowledge Retrieval | 1.00 | 1.00 | PASS | Strictly abstained from advice on unregistered crop (dragon_fruit) |
| AGRI-BENCH-027 | Multilingual Communication | 1.00 | 1.00 | PASS | Accurate Marathi terminology for bacterial blight and poor drainage disqualification |
| AGRI-BENCH-028 | Multilingual Communication | 1.00 | 1.00 | PASS | Accurate Marathi terminology for reproductive heat stress (फूल गळ, घाटे धारणा) |
| AGRI-BENCH-029 | Multilingual Communication | 1.00 | 1.00 | PASS | Cross-lingual agronomic parity: English and Marathi yield identical decision state |
| AGRI-BENCH-030 | Multilingual Communication | 1.00 | 1.00 | PASS | Accurate Marathi recommendation of Hasta Bahar over Ambia Bahar under water scarcity |
