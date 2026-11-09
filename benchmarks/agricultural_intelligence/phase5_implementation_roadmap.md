# CropNet AI — Phase 5 Implementation Roadmap (Agricultural Intelligence)

**Roadmap Version:** 1.0.0  
**Phase Scope:** Phase 5.0 through Phase 5.4  
**Target Architecture:** FastAPI Backend + Hosted Supabase (PG17/PostGIS 3.5) + Local Qwen3:8B Explanation Layer + Flutter Mobile Client  
**Execution Guardrail:** Strictly Sequential Gates; Each Subphase Validated Against Benchmark Standards Before Proceeding  

---

## 1. Phase Progression Overview

```
+-----------------------------------------------------------------------------------+
| Phase 5.0: Benchmark & Evaluation Framework (CURRENT GATE - PLANNING ONLY)        |
| - 30-case gold-standard dataset & adversarial test specifications                 |
| - Dual independent evaluation tracks (Track A: Retrieval, Track B: Reasoning)     |
| - Layered architecture & model-independent evaluation runner design               |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Phase 5.1: Deterministic Decision Engine & Retrieval Orchestrator                |
| - Implement Layer 1 (Input Validation) & Layer 2 (Knowledge Retrieval Service)    |
| - Implement Layer 3 (Deterministic Engine: Feasibility, Scoring, Bahar Balancer)  |
| - Implement Layer 4 (Evidence & Uncertainty Manager: Strict NULL & Abstention)    |
| - Unit tests for deterministic logic against 30 benchmark ground truths           |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Phase 5.2: LLM Explanation Layer & Multilingual Safety Guardrails                |
| - Implement Layer 5 (Local Qwen3:8B Prompt Pipeline - Structured JSON In/Out)     |
| - Implement Layer 6 (Follow-Up Question Engine)                                  |
| - Implement Layer 7 (Output Guardrail & Numerical Diff Validator)                 |
| - Bilingual Marathi terminology injection and cross-lingual parity assertion      |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Phase 5.3: Benchmark Evaluation Execution & Performance Calibration               |
| - Execute CropNetAgriEvalRunner across all 30 benchmark test cases                |
| - Calculate Track A (Retrieval) and Track B (Reasoning) metrics independently     |
| - Audit all 9 adversarial failure archetypes (Zero hallucination policy)          |
| - Calibrate prompt engineering and fallback circuit-breakers if needed            |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
| Phase 5.4: Flutter Mobile Client Integration & Field Presentation                 |
| - Connect mobile client to `/api/v1/intelligence/advisory` FastAPI endpoints      |
| - Implement bilingual Marathi/English advisory UI with collapsible source pills   |
| - Render interactive Bahar water schedule visualizer (liters/tree/day)            |
| - Integrate follow-up clarification modal dialogs for missing farm data           |
+-----------------------------------------------------------------------------------+
```

---

## 2. Detailed Subphase Work Breakdown

### Phase 5.0: Benchmark & Evaluation Framework (Current Phase)
- **Goal:** Establish empirical evaluation criteria, gold-standard benchmark datasets, adversarial failure models, and architectural specifications before any AI code is written.
- **Key Deliverables:**
  - `agricultural_intelligence_architecture.md`
  - `benchmark_dataset.json` & `benchmark_dataset.md` (30 test cases)
  - `gold_standard_source_mapping.md`
  - `evaluation_metrics_and_scoring.md`
  - `adversarial_test_specification.md`
  - `experiment_execution_plan.md`
  - `known_evidence_gaps_and_limitations.md`
- **Exit Criteria:** All 30 test cases validated against Phase 4 database ground truth; zero code written modifying production or fine-tuning models.

### Phase 5.1: Deterministic Decision Engine & Retrieval Orchestrator
- **Goal:** Build the mathematically deterministic core that processes farm inputs, checks physical constraints, queries knowledge tables, and computes crop suitability without LLM involvement.
- **Tasks:**
  1. Create `cropnet.services.api.app.services.intelligence.validator`: Validate farm coordinates, detect missing parameters, classify lab vs. proxy soil data.
  2. Create `cropnet.services.api.app.services.intelligence.retriever`: Execute parameterized queries against Phase 4 tables (`crop_soil_requirements`, `crop_climate_requirements`, `crop_water_requirements`, `crop_regional_suitability`, `agricultural_knowledge_sources`).
  3. Create `cropnet.services.api.app.services.intelligence.decision_engine`:
     - Implement hard constraint filters (soil depth, drainage, salinity, temperature extremes).
     - Implement crop suitability scoring and reason code generator.
     - Implement pomegranate Bahar water calculator (480 daily values in liters/tree/day).
     - Implement chickpea decoupled irrigation selector (ICRISAT physiological vs MPKV calendar).
  4. Create `cropnet.services.api.app.services.intelligence.uncertainty`: Strict NULL handling, abstention triggers, and decoupled source preservation.
- **Exit Criteria:** 100% of deterministic unit tests pass against the 30 benchmark ground-truth payloads with zero external LLM dependencies.

### Phase 5.2: LLM Explanation Layer & Multilingual Guardrails
- **Goal:** Integrate local Qwen3:8B to translate structured deterministic payloads into empathetic, clear English and Marathi advisories, wrapped in strict safety guardrails.
- **Tasks:**
  1. Build inference client interfacing with local Qwen3:8B (OpenAI-compatible local API / Ollama).
  2. Design rigid, grounded prompt templates that supply only verified database facts.
  3. Implement Layer 6 (`follow_up_engine`): Formulate structured diagnostic questions for missing or contradictory inputs.
  4. Implement Layer 7 (`guardrail_validator`):
     - Numerical threshold regex extractor: Compare generated numbers against input payload. Discard and fallback if unauthorized numbers are generated.
     - Prohibited claims filter: Ban profit guarantees, unsupported pH limits, and unverified chemical applications.
     - Marathi glossary injector: Ensure vernacular terms (सामू, सेंद्रिय कर्ब, पाणथळ, बहार) are strictly maintained.
- **Exit Criteria:** Guardrail intercepts 100% of simulated hallucinations in unit tests; fallback circuit breaker successfully renders template text on failure.

### Phase 5.3: Benchmark Evaluation Run & Performance Calibration
- **Goal:** Execute the complete end-to-end evaluation runner against the 30-case benchmark.
- **Tasks:**
  1. Run `CropNetAgriEvalRunner` on local environment.
  2. Log all inputs, outputs, latencies, and token metrics.
  3. Compute Track A (Retrieval) and Track B (Reasoning) metrics independently.
  4. Verify that all 9 adversarial failure archetypes pass with 0.00 Hallucination Rate and 1.00 Constraint Adherence.
  5. Generate formal benchmark evaluation report.
- **Exit Criteria:** Track A Precision $\ge 0.95$, Track B Constraint Adherence $= 1.00$, Numerical Hallucination Rate $= 0.00$, $p95$ Latency $\le 3.5\text{ s}$.

### Phase 5.4: Mobile Integration & Flutter UI
- **Goal:** Expose the agricultural intelligence API to the Flutter mobile application and render rich, transparent recommendations for farmers.
- **Tasks:**
  1. Expose `POST /api/v1/intelligence/advisory` in FastAPI.
  2. Implement Flutter mobile bloc/state management for interactive advisory.
  3. Design mobile components:
     - Color-coded suitability cards (Green: High, Yellow: Screening/Conditional, Red: Violation).
     - Expandable citation drawer displaying verified source titles, organizations, and publication years.
     - Interactive pomegranate Bahar water slider (daily liters/tree by month and tree age).
     - Diagnostic follow-up prompt cards when soil parameters are missing.
- **Exit Criteria:** Flutter mobile app seamlessly communicates with FastAPI backend; offline cache gracefully handles degraded modes; Marathi/English toggle functions flawlessly.
Path: file:///Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/benchmarks/agricultural_intelligence/phase5_implementation_roadmap.md
