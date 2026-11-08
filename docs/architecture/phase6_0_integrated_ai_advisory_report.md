# CropNet AI — Phase 6.0 Integrated AI Agricultural Advisory Architecture Report

**Version**: 1.0  
**Date**: November 2026  
**Status**: Implemented, Verified, and Benchmark Validated  
**Component**: `services/api/app/services/llm/`  
**Target LLM Model**: `qwen3:8b` (Local Ollama via GGUF / Metal acceleration) with deterministic offline fallback  
**Deliverable**: Phase 6.0 Integrated AI Agricultural Advisory  

---

## 1. Executive Summary

Phase 6.0 elevates CropNet AI from an isolated single-crop explanation utility into a **unified, multi-domain agricultural conversational intelligence advisory**. Grounded strictly in the **Phase 5.9 Farm Health Snapshot Contract (Version 1.0)**, the upgraded advisory synthesizes evidence across all five institutional agronomic pillars:
1. **Soil Intelligence**: Dual-source laboratory measurements (KVK / ICAR) and SoilGrids spatial estimates with depth stratification.
2. **Water Intelligence**: Source registry (borewell, open well, canal) evaluated against Bureau of Indian Standards **BIS IS 11624:2019** salinity (EC) and sodicity (SAR/RSC) hazard classes.
3. **Satellite Intelligence**: ESA Sentinel-2 L2A optical reflectance (10m GSD) distinguishing pure vegetative canopy (Class 4 NDVI/NDMI) from inter-row bare soil paths.
4. **Weather & Climate**: Real-time agro-meteorological observations, 5-day precipitation forecasts, and long-term scarcity zone rainfall normals.
5. **Crop Feasibility**: Phase 5.1 deterministic decision outcomes (Verified Suitable, Conditionally Suitable, Unsuitable, Abstain) from Mahatma Phule Krishi Vidyapeeth (MPKV) and ICAR rules.

### Core Architectural Principles
- **Absolute Deterministic Authority**: The LLM is strictly a natural-language communication and translation layer. It **never** determines crop suitability, modifies decision states, or computes synthetic aggregate health scores.
- **Compact Token Budgeting (< 1200 Tokens)**: Selective compaction algorithms filter verbose metadata while preserving precision agronomic indicators, ensuring flawless inference within local Qwen3:8B context windows.
- **Multi-Turn Diagnostic Loop**: When a farmer answers follow-up diagnostic questions in free-form English or authentic agricultural Marathi, natural language intent is disambiguated, deterministically re-evaluated through `DeterministicDecisionEngine`, and the answered question is isolated from remaining pending items.
- **Strict Multi-Layered Guardrails**: Automated validation rejects ungrounded numerical values, fabricated fertilizer quantities (e.g., urea kg/ha), chemical spray concentrations (e.g., ml/L), and premature satellite pathogen diagnoses lacking mandatory scientific disclaimers.

---

## 2. Multi-Domain Snapshot Context Architecture

### 2.1 Context Aggregation Pipeline

```
                               ┌────────────────────────────────────────────────────────┐
                               │  Phase 5.9 Farm Health Snapshot (JSON / Pydantic Model) │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │
                                                          ▼
                                      ┌──────────────────────────────────────┐
                                      │  FarmContextBuilder._normalize_snapshot │
                                      └───────────────────┬──────────────────┘
                                                          │
                                                          ▼
                                      ┌──────────────────────────────────────┐
                                      │   FarmContextBuilder.build_farm_context   │
                                      └───────────────────┬──────────────────┘
                                                          │
                                                          ▼
                                      ┌──────────────────────────────────────┐
                                      │ classify_query_domains (Regex + Stems)│
                                      └───────────────────┬──────────────────┘
                                                          │
                                 ┌────────────────────────┴────────────────────────┐
                                 │                                                 │
                                 ▼                                                 ▼
                   [Single-Domain Inquiry]                              [Cross-Domain Synthesis]
               (soil, water, sat, or wx focus)                     (multi-domain query / crop eval)
                                 │                                                 │
                                 ▼                                                 ▼
                   Target Domain Detailed                              All 5 Domains Compacted
                   Other 4 Domains Compact                             Token Budget: ~800–1050 tokens
                                 │                                                 │
                                 └────────────────────────┬────────────────────────┘
                                                          │
                                                          ▼
                                      ┌──────────────────────────────────────┐
                                      │ ExplanationPromptBuilder Grounded Prompts│
                                      └───────────────────┬──────────────────┘
                                                          │
                                                          ▼
                                      ┌──────────────────────────────────────┐
                                      │    Local Qwen3:8B Structured JSON    │
                                      └───────────────────┬──────────────────┘
                                                          │
                                                          ▼
                                      ┌──────────────────────────────────────┐
                                      │ GuardrailValidator & Card Enrichment │
                                      └───────────────────┬──────────────────┘
                                                          │
                                                          ▼
                                      ┌──────────────────────────────────────┐
                                      │ Verified Agricultural Advisory Card  │
                                      └──────────────────────────────────────┘
```

### 2.2 Token Compaction Strategy

Local 8B models (such as Qwen3:8B running on consumer Apple Silicon or server CPUs) perform best when prompt context is concise, structured, and free of redundant dictionary nesting. `FarmContextBuilder` enforces domain-specific compaction routines:

| Domain | Detailed Representation (Single Domain Focus) | Compact Representation (Cross-Domain Synthesis) |
|---|---|---|
| **Soil Intelligence** | Full laboratory metadata, test date, all 8 physical/chemical parameters, depth ranges, sample laboratory name, agronomic notes. | `availability_state`, `data_age_days`, `provenance`, essential indicators (`soil_ph`, `organic_carbon_pct`, `electrical_conductivity_ds_m`, `soil_texture`, `drainage`), missing critical parameters. |
| **Water Intelligence** | Source capacity, flow rates, laboratory certificate, all chemical ions ($Cl^-$, $B$, $TDS$), full institutional evaluation guidance. | `availability_state`, `data_age_days`, registered sources summary, primary indicators (`ph`, `electrical_conductivity_ds_m`, `sar`), compact institutional evaluation hazards (`parameter_key`, `hazard_level`, `standard_applied`). |
| **Satellite Intelligence** | Sensor, granule ID, composite mean NDVI, pixel count, cloud coverage %, full agro-interpretation paragraph, mandatory scientific disclaimer. | `availability_state`, `observation_date`, `observation_age_days`, pure canopy Class 4 NDVI (`canopy_ndvi`), canopy moisture (`canopy_ndmi`), bare soil reference (`bare_soil_mean_ndvi`), mandatory scientific disclaimer. |
| **Weather & Climate** | Full hourly forecast, min/max temperatures, humidity, wind vector, seasonal drought indices, full climate normal tables. | `availability_state`, current condition, temperature (°C), precipitation (mm), next 48h rain forecast (mm), annual rainfall normal (mm). |
| **Crop Feasibility** | Complete catalogue outcomes, full rule citations, daily tree drip tables, detailed limiting factors and uncertainty notes. | `availability_state`, `target_season`, top 3 suitable crops (names + decision state), top 3 conditional crops (names + limiting factors), top limiting factors. |

This strategy compresses a complete 5-domain snapshot from > 5,500 characters down to ~2,600–2,800 characters (~750–900 tokens), remaining comfortably beneath the 1,200 token budget.

---

## 3. Bilingual Multi-Domain Dialogue & Grounding

### 3.1 Domain-Specific Prompt Guidance

`ExplanationPromptBuilder` generates tailored instructions depending on the detected query domain:
- **`cross_domain_inquiry`**: Instructs the model to synthesize inter-domain relationships (e.g., explaining how heavy Vertisol clay interacts with borewell water EC 1.85 dS/m to compound salt accumulation in onion root zones).
- **`water_inquiry`**: Enforces strict adherence to **BIS IS 11624:2019** (salinity classes C1–C4, sodium adsorption ratio classes S1–S4, and residual sodium carbonate). Explicitly forbids inventing chemical desalinization treatments for groundwater.
- **`satellite_inquiry`**: Directs the LLM to explain that Sentinel-2 Level-2A reflects 10m optical reflectance and segregates pure vegetative canopy (NDVI 0.68) from bare inter-row soil (NDVI 0.28). Enforces the mandatory scientific disclaimer.
- **`soil_inquiry`**: Directs the LLM to distinguish farmer-verified laboratory test reports from modeled regional SoilGrids data, clearly flagging unmeasured macronutrients.
- **`weather_inquiry`**: Analyzes short-term rain forecasts against seasonal crop water requirements, noting rainfall deficits in scarcity zones.

### 3.2 Authentic Vernacular Marathi Dialect & Terminology

The advisory prompt provides authentic agricultural Marathi terminology (`SYSTEM_PROMPT_MR`), avoiding unnatural machine-translated phrasing:

| English Agronomic Term | Machine-Translated (Avoided) | Authentic Marathi (CropNet Standard) |
|---|---|---|
| Soil pH | मातीचा पीएच | जमिनीचा सामू (pH) |
| Soil Organic Carbon | सेंद्रिय कार्बन | सेंद्रिय कर्ब (SOC) |
| Drainage | पाण्याचा निचरा होणे | पाण्याचा निचरा (Drainage) |
| Electrical Conductivity (EC) | विद्युत प्रवाह | विद्युत वाहकता / क्षारता (EC) |
| Sodium Adsorption Ratio (SAR) | सोडियम शोषण प्रमाण | सोडियम शोषण गुणोत्तर (SAR) |
| Waterlogging | पाणी साचणे | पाणी साचणे / पाणथळ अवस्था |
| Pure Canopy NDVI | कॅनोपी एनडीव्हीआय | निव्वळ पिकाची हिरवळ (Canopy NDVI) |
| Scientific Disclaimer | वैज्ञानिक अस्वीकरण | वैज्ञानिक इशारा (Scientific Disclaimer) |
| Bacterial Blight | जिवाणू करपा | तेलकट डाग / जिवाणूजन्य करपा |
| Root Rot / Wilt | मूळ सडणे | मूळकुजव्या / कॉलर रॉट / उकळा |

---

## 4. Agronomic Guardrails & Safeguards

CropNet AI enforces a four-tier automated guardrail verification system on every LLM generation before delivering output to the mobile client or API consumer:

```
[Generated Advisory Text / JSON]
           │
           ├─► 1. Decision State Integrity Check
           │     └─► Rejects inversion: disqualified crops cannot be claimed suitable.
           │
           ├─► 2. Numerical Grounding Check
           │     └─► Rejects unauthorized numbers not present in decision/farm snapshot.
           │
           ├─► 3. Agrochemical & Fertilizer Guardrail
           │     ├─► Rejects invented fertilizer dosages (kg urea, DAP, MOP per ha/acre).
           │     └─► Rejects invented pesticide/fungicide spray measurements (ml/L, gm/L).
           │
           └─► 4. Satellite Pathogen Diagnosis Guardrail
                 └─► Rejects pathogen claims (wilt, blight) lacking scientific disclaimer.
```

### Guardrail Specifications
1. **Decision State Non-Reversal**: Verified suitable crops cannot be labeled unsuitable, and disqualified crops cannot be recommended.
2. **Strict Numerical Grounding**: All numerical values in generated prose must exist in the authoritative snapshot payload, verified farm context, or benign integer list (ordinals, hours, years). Hallucinated numbers trigger automatic rejection and fallback to deterministic templates.
3. **Chemical Fertilizer & Spray Dosage Prohibition**: CropNet AI strictly prohibits generating arbitrary fertilizer applications (e.g., `"Apply 120 kg urea and 60 kg DAP"`) or spray concentrations (`"Spray 2.5 ml/L chlorpyrifos"`), directing farmers instead to certified package of practices (MPKV PoP 2023).
4. **Mandatory Satellite Optical Disclaimer**: If satellite imagery or NDVI is discussed alongside disease pathogens, the model must issue the scientific disclaimer:
   > *"Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses."*

---

## 5. Multi-Turn Diagnostic Loop & Follow-up Question Isolation

### 5.1 Architecture of the Diagnostic Conversation

When an initial farm evaluation reveals diagnostic data gaps (e.g., unknown field drainage or unmeasured groundwater salinity), `DeterministicDecisionEngine` tags the outcome as `CONDITIONALLY_SUITABLE_PENDING_DATA` or `REGIONAL_SCREENING_ONLY` and generates structured `FollowUpQuestion` items.

In subsequent dialogue turns:
1. **Intent Disambiguation (`AgriculturalExplanationService.detect_answer_intent`)**:
   - Analyzes farmer input against pending questions.
   - Accurately classifies conversational expressions (e.g., `"Water stays standing for 2 days after irrigation"` $\rightarrow$ `drainage = "poor"`, `water_table_depth = "shallow"`).
   - Correctly prioritizes negations (e.g., `"There is no standing water, it drains quickly"` $\rightarrow$ `drainage = "good"`).
   - Disambiguates soil depth (`"जमीन काळी भारी आणि खोल आहे"` $\rightarrow$ `soil_depth_cm = 75.0`), salinity (`"पाणी थोडे क्षारयुक्त व खारट आहे"` $\rightarrow$ `electrical_conductivity_ds_m = 2.5`), and irrigation types.
2. **Deterministic Engine Re-Evaluation**:
   - `AgriculturalExplanationService.handle_conversation` invokes `engine.process_followup_answers(decision_id, detected_answers)`.
   - The deterministic engine re-runs constraint validation rules against the updated farm context.
   - For example, when poor drainage is confirmed on heavy Vertisol clay for pomegranate, ICAR-NRCP site-selection constraint rules execute, adding critical root rot risk limiting factors.
3. **Follow-Up Question Isolation**:
   - The answered question is removed from the pending question queue.
   - Only truly unresolved diagnostic questions remain in `resp.follow_up_questions`.
4. **Guidance Synchronization**:
   - The updated decision is passed into `ExplanationPromptBuilder` alongside multi-domain snapshot evidence.
   - The generated `StructuredAdvisoryCard` reflects the newly updated deterministic state.

---

## 6. Verification & Automated Benchmark Results

The Phase 6.0 Integrated AI Agricultural Advisory test suite provides comprehensive test coverage across all features, edge cases, and guardrail constraints:

### 6.1 Test Suite Summary (`test_integrated_ai_advisory.py`)

| Test Name | Focus Area | Status | Execution Time |
|---|---|---|---|
| `test_farm_context_builder_ingests_full_evidence_snapshot` | Example A Full Snapshot Ingestion (5 Domains Available) | **PASSED** | 0.01s |
| `test_farm_context_builder_ingests_missing_evidence_snapshot` | Example B Zero Evidence Ingestion (5 Domains Not Available, Zero Hallucinated Defaults) | **PASSED** | 0.01s |
| `test_farm_context_builder_ingests_stale_evidence_snapshot` | Example C Stale Evidence Tracking (>30d sat, >1yr water, >3yr soil) | **PASSED** | 0.01s |
| `test_farm_context_builder_compact_token_budget` | Token Compaction Verification (< 1200 tokens across all 5 domains) | **PASSED** | 0.01s |
| `test_farm_context_builder_domain_classification` | Regex Word-Boundary Routing (Soil, Water, Sat, Wx, Crop, Cross-Domain) | **PASSED** | 0.01s |
| `test_explain_decision_with_multi_domain_snapshot` | Grounded Multi-Domain Advisory Card & Observation Pills (pH, EC, NDVI) | **PASSED** | 0.02s |
| `test_explain_decision_marathi_vernacular_with_snapshot` | Authentic Marathi Grounded Explanation (सामू, क्षारता, गहू) | **PASSED** | 0.02s |
| `test_explain_missing_evidence_honest_disclosure` | Honest Disclosure of Missing Lab Tests (Zero Manufactured Data) | **PASSED** | 0.01s |
| `test_guardrail_validator_rejects_suitability_reversal` | Rejection of Suitability State Contradiction / Inversion | **PASSED** | 0.01s |
| `test_guardrail_validator_rejects_fabricated_fertilizer_dosages` | Rejection of Fabricated Fertilizer Quantities (e.g. 120 kg urea) | **PASSED** | 0.01s |
| `test_guardrail_validator_rejects_chemical_spray_measurements` | Rejection of Fabricated Chemical Spray Concentrations (ml/L) | **PASSED** | 0.01s |
| `test_guardrail_validator_rejects_satellite_pathogen_diagnosis_without_disclaimer` | Rejection of Satellite Pathogen Claims Lacking Scientific Disclaimer | **PASSED** | 0.01s |
| `test_guardrail_validator_accepts_satellite_pathogen_with_scientific_disclaimer` | Acceptance of Canopy Indicators with Mandatory Scientific Disclaimer | **PASSED** | 0.01s |
| `test_multiturn_detect_answer_intent_drainage` | Intent Detection on Natural Language Drainage (EN & MR, Negations) | **PASSED** | 0.01s |
| `test_multiturn_detect_answer_intent_salinity_and_depth` | Intent Detection on Salinity, Soil Depth, Well Depth | **PASSED** | 0.01s |
| `test_multiturn_conversation_deterministic_reevaluation_and_question_isolation` | Full Multi-Turn Cycle: Intent Detection $\rightarrow$ Engine Re-eval $\rightarrow$ Question Isolation | **PASSED** | 0.02s |
| `test_multiturn_conversation_marathi_continuity` | Multi-Turn Conversational Cycle in Marathi | **PASSED** | 0.02s |
| `test_qwen3_8b_live_or_verified_fallback` | End-to-End Live Ollama Qwen3:8B Execution & Fallback Parity | **PASSED** | 40.06s (Live) |

### 6.2 Zero-Regression Validation Suite

- **`test_llm_explanation_phase5_2.py`**: **21 / 21 PASSED** (0 failures).
- **`test_ai_intelligence_benchmark_phase5_8_2.py`**: **4 / 4 PASSED** (0 failures, including 30-scenario deterministic fallback benchmark and live Ollama Qwen3:8B benchmark).

---

## 7. Deliverable Artifacts & File Inventory

All work was completed strictly within the assigned worktree (`.worktrees/worktree-agent4-advisory`) and exclusively owned file boundaries:

| File Path | Description of Changes |
|---|---|
| `services/api/app/services/llm/farm_context_builder.py` | Added `_normalize_snapshot`, `classify_query_domains` (word boundary regex & Marathi stems), `_compact_soil`, `_compact_water`, `_compact_satellite`, `_compact_weather`, `_compact_crop`, and enhanced `build_farm_context` to consume snapshot payloads while bounding token consumption (< 1200 tokens). |
| `services/api/app/services/llm/prompt_builder.py` | Enhanced `SYSTEM_PROMPT_EN` and `SYSTEM_PROMPT_MR` with Phase 6.0 multi-domain guidance, BIS IS 11624:2019 water standards, pure canopy NDVI vs bare soil distinctions, and cross-domain synthesis instructions. |
| `services/api/app/services/llm/explanation_service.py` | Upgraded `explain_decision` and `handle_conversation` with snapshot parameter support; implemented `_enrich_card_observations` for multi-domain observation pills; enhanced `detect_answer_intent` for drainage, water table depth, salinity, and depth; expanded `validate_explanation_guardrails` for chemical spray measurements and mandatory satellite pathogen disclaimers. |
| `services/api/tests/test_integrated_ai_advisory.py` | 18 automated integration tests covering snapshot ingestion, cross-domain dialogue in EN/MR, agronomic guardrails, multi-turn diagnostic loop, question isolation, and live Qwen3:8B execution. |
| `docs/architecture/phase6_0_integrated_ai_advisory_report.md` | Comprehensive architectural documentation, benchmark data, and verification methodology. |

*Critical Non-Negotiable Constraint Verified*: The Flutter mobile user interface (`apps/mobile/lib/core/router/advisory_screen.dart`) was untouched, preserving the approved visual layout intact.
