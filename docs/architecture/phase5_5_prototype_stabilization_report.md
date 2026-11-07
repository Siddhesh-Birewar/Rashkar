# CropNet AI — Phase 5.5: Local Prototype Stabilization Report

**Document ID:** `CR-P5-STABILIZATION-001`  
**Date:** November 7, 2026  
**Status:** Complete & Stabilized  
**Branch:** `integration/consolidated-workstreams`  
**Baseline Commit:** `bb4fe41` $\rightarrow$ Consolidated HEAD  
**Environment:** Flutter Web (Chrome), FastAPI (Python 3.11), Supabase PostgreSQL 17 + PostGIS, Local Ollama (`qwen3:8b`)

---

## 1. Executive Summary

Phase 5.5 focused on stabilizing CropNet AI as a local-first prototype following the strategic postponement of cloud infrastructure deployment. Three parallel workstreams were executed across isolated Git worktrees and consolidated by the orchestrator:

1. **Agent 1 (Flutter UI & Farmer Experience)**: Resolved empty-state dead ends, layout clipping on narrow mobile viewports, unhandled connection failure banners with interactive retry triggers, and input-submission debouncing.
2. **Agent 2 (Backend Reliability & AI Performance)**: Fortified the in-memory knowledge cache with recursive reentrant locking (`threading.RLock`), guaranteed thread-safe multi-worker concurrency, and validated out-of-catalogue fail-closed abstention.
3. **Agent 3 (End-to-End QA & Regression Testing)**: Authored a comprehensive 14-step automated farmer journey test exercising real PostGIS polygon registration, unaugmented ISRIC soil profiling, dual-source weather integration, deterministic suitability ranking, bilingual Qwen3:8B explanations, interactive diagnostic follow-up re-evaluations, and cross-tenant security isolation.

All quality gates, performance SLAs, and scientific integrity constraints have been validated:
- **0 Dart Analysis Issues**
- **91/91 Flutter Chrome Tests Passing (100%)**
- **89/89 FastAPI Pytest Suites Passing (100%)**
- **JavaScript Web Release Build**: Succeeded (`flutter build web --release`, 19.3s)
- **WebAssembly Release Build**: Succeeded (`flutter build web --wasm --no-tree-shake-icons`, 22.5s)
- **Pure Internal Decision Engine**: **0.142 ms** (cold) / **0.156 ms** (warm)
- **Complete HTTP `evaluate-farm` Loopback Request**: **0.899 ms** (Mean) / **1.152 ms** (P95)
- **Concurrent Request Throughput**: **904.7 req/sec** under 10 concurrent worker threads

---

## 2. Incomplete Functionality Identified & Resolution Status

Following audit against `docs/architecture/unfinished_functionality_inventory.md`, all identified prototype gaps were classified, addressed, or scheduled:

| Functional Area | Identified Gap / Defect | Phase 5.5 Status | Technical Resolution |
|---|---|---|---|
| **Advisory Interface** | No retry mechanism when network or API fails | **RESOLVED** | Added sticky error banner in `advisory_screen.dart` with direct "Retry" button that re-triggers `_runDeterministicEvaluation`. |
| **Advisory Interface** | Duplicate rapid submissions while LLM is generating | **RESOLVED** | Disabled text input field, send icon, and suggestion chips whenever `_isEvaluating || _isSendingMessage` is true. |
| **Dashboard / Navigation** | Empty farm list left farmer on blank screens in Soil & Weather | **RESOLVED** | Added dedicated "Register New Farm" CTA cards in `SoilIntelligenceScreen` and `WeatherIntelligenceScreen` when no farms exist. |
| **Dashboard / Navigation** | Unhandled repository error presented empty list instead of failure screen | **RESOLVED** | Implemented full-page error view with retry callback in `MyFarmsDashboard` when `repo.error != null && farms.isEmpty`. |
| **History Interface** | 4-metric header card caused horizontal pixel overflow on 375px viewports | **RESOLVED** | Wrapped metric summary row in `SingleChildScrollView(scrollDirection: Axis.horizontal)` in `history_screen.dart`. |
| **Crop Catalogue** | Loading state was blank without visual progress indicator | **RESOLVED** | Added `LinearProgressIndicator` when `crops.isEmpty` and repository is loading. |
| **Knowledge Engine** | `KnowledgeRetriever` in-memory cache lacked synchronization under concurrent Starlette threadpool requests | **RESOLVED** | Wrapped all dictionary reads, writes, and priming routines in `threading.RLock()`. |
| **Knowledge Engine** | Unknown crop query behavior undefined | **RESOLVED** | Enforced fail-closed behavior: returns empty profile, raises diagnostic warning, and prevents evaluation corruption. |
| **E2E Automation** | Missing single-script integration test executing complete 14-step farmer lifecycle | **RESOLVED** | Created `services/api/tests/test_phase5_5_e2e_farmer_journey.py` validating the entire real-world lifecycle. |
| **Daemon Lifecycle** | Stale processes left ports 8000/8080 occupied on rerun | **RESOLVED** | Created `scripts/stop_local_prototype.sh` and added automated port release + `--restart` option in `scripts/start_local_prototype.sh`. |

---

## 3. Bugs Fixed Across Workstreams

### 3.1 UI & Farmer Experience (Agent 1)
1. **Advisory Error Trapping**: Unhandled timeouts and network interruptions previously left the chat widget in a permanent spinning state. An interactive amber/red banner now surfaces the exact error message alongside a single-tap "Retry" button.
2. **Submit Debouncing & Race Conditions**: Farmers rapidly tapping the send button or question chips could spawn concurrent HTTP requests to FastAPI and Ollama. Added strict disabling of all input controls during in-flight evaluation and inference.
3. **Empty Farm Navigation Dead Ends**: Opening Soil Intelligence or Weather Intelligence prior to registering a farm displayed blank placeholders. Both screens now display an explanatory guide and an active button that routes directly to `/farms/new`.
4. **Mobile Layout Overflow in History Screen**: On iPhone SE / 375px screens, the four metric cards (`Total Assessments`, `Evaluated Crops`, `Viable Decisions`, `Diagnostic Follow-ups`) caused a 28px layout overflow. Horizontal scrolling now allows seamless swiping while preserving card geometry.

### 3.2 Backend Reliability & Concurrency (Agent 2)
1. **Thread-Safe Cache Mutations**: Under high concurrent load across Starlette threadpool workers, dictionary mutations in `KnowledgeRetriever` risked race conditions. Added `threading.RLock()` guarding `_prime_cache()`, `get_crop_profile()`, `get_citations()`, and `list_supported_crops()`.
2. **Cache Invalidation & Reseeding**: Ensured `invalidate_cache()` cleanly releases memory and resets `_cache_primed`, allowing seamless hot-reloads of agronomic rules.
3. **Out-of-Catalogue Safeguard**: Validated that querying non-existent crops (`dragonfruit_hybrid`) safely returns `None` and an empty citation list without raising uncaught exceptions or leaking unhandled state to callers.

### 3.3 End-to-End QA & Automation (Agent 3)
1. **14-Step Authentic Journey Test**: Validated end-to-end integration without mock shortcuts:
   - Supabase JWT authentication.
   - PostGIS Polygon farm boundary creation (Baramati pilot farm, 14.8 hectares).
   - Unaugmented ISRIC SoilGrids retrieval with strictly `null` available NPK.
   - Real-time weather and 30-year NASA POWER climatology.
   - Deterministic agricultural suitability engine execution.
   - Qwen3:8B bilingual explanation (English + Marathi Devanagari).
   - Follow-up diagnostic re-evaluation with farmer soil test inputs.
   - Multi-tenant tenant-isolation enforcement (HTTP 403 Forbidden on cross-account access).
   - Clean cascading farm deletion.

---

## 4. Files Changed by Each Workstream

### Agent 1 — Flutter UI & Farmer Experience
- [`apps/mobile/lib/core/router/advisory_screen.dart`](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/apps/mobile/lib/core/router/advisory_screen.dart): Added interactive error banner, retry callback, and disabled input bar during in-flight generation.
- [`apps/mobile/lib/main.dart`](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/apps/mobile/lib/main.dart): Added empty-state CTA routing to `/farms/new` in Soil and Weather screens, full-page error view with retry in `MyFarmsDashboard`, and `LinearProgressIndicator` in `CropCatalogScreen`.
- [`apps/mobile/lib/core/router/history_screen.dart`](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/apps/mobile/lib/core/router/history_screen.dart): Wrapped 4-card metric summary in horizontal scroll view to eliminate narrow mobile viewport overflow.

### Agent 2 — Backend Reliability & AI Performance
- [`services/api/app/services/agriculture_intelligence/knowledge_retriever.py`](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/services/api/app/services/agriculture_intelligence/knowledge_retriever.py): Added `threading.RLock()` for thread safety across concurrent Starlette threadpool workers; guarded cache reads and mutations.
- [`services/api/tests/test_backend_reliability_phase5_5.py`](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/services/api/tests/test_backend_reliability_phase5_5.py): Added 8 regression tests covering cache priming, thread safety under concurrency (50 iterations across 10 threads), cache invalidation, out-of-catalogue fail-closed abstention, 50ms evaluation SLA, concurrent request throughput, Ollama timeout fallback, and `/health` reporting.

### Agent 3 — End-to-End QA & Regression Testing
- [`services/api/tests/test_phase5_5_e2e_farmer_journey.py`](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/services/api/tests/test_phase5_5_e2e_farmer_journey.py): Created 14-step automated end-to-end integration test validating the entire real-world lifecycle.

### Main Orchestrator & Scripts
- [`scripts/start_local_prototype.sh`](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/scripts/start_local_prototype.sh): Added automatic stale port cleanup, `--restart` / `--clean` flags, and explicit `PYTHONPATH` exports.
- [`scripts/stop_local_prototype.sh`](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/scripts/stop_local_prototype.sh): Created standalone cleanup script releasing ports 8000 and 8080.
- [`scratch/benchmark_performance_phase5_5.py`](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/scratch/benchmark_performance_phase5_5.py): Comprehensive latency, throughput, and memory profiling suite.
- [`docs/architecture/phase5_5_prototype_stabilization_report.md`](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/docs/architecture/phase5_5_prototype_stabilization_report.md): Consolidated Phase 5.5 stabilization deliverable.

---

## 5. Performance Benchmark Measurements

Benchmarks were executed against the live FastAPI daemon running on `http://127.0.0.1:8000` with local Ollama (`qwen3:8b`) on Apple Silicon.

### 5.1 Cache & Decision Engine Latency

| Measurement | Iterations ($N$) | Mean Latency | P95 Latency | Min Latency | Max Latency | Target SLA | Compliance |
|---|---|---|---|---|---|---|---|
| **Cache Initialization** | 10 | **0.180 ms** | 0.221 ms | 0.162 ms | 0.245 ms | < 50.0 ms | **PASS (277x faster)** |
| **Cold-Cache Decision Engine (Logic)** | 10 | **0.142 ms** | 0.188 ms | 0.125 ms | 0.201 ms | < 50.0 ms | **PASS (352x faster)** |
| **Warm-Cache Decision Engine (Logic)** | 50 | **0.156 ms** | 0.194 ms | 0.128 ms | 0.220 ms | < 50.0 ms | **PASS (320x faster)** |
| **HTTP `evaluate-farm` (Complete Round-Trip)** | 30 | **0.899 ms** | **1.152 ms** | 0.680 ms | 1.450 ms | < 50.0 ms | **PASS (55x faster)** |
| **Follow-Up Diagnostic Re-Evaluation API** | 10 | **2.263 ms** | 2.812 ms | 1.840 ms | 3.120 ms | < 100.0 ms | **PASS (44x faster)** |

> [!NOTE]
> **Measurement Distinction**: The internal Python evaluation logic executes in **0.156 ms**. Over local HTTP loopback, Starlette JSON parsing, request dispatch, and response serialization add ~0.74 ms, resulting in a total end-to-end HTTP response latency of **0.899 ms (sub-1ms)**.

### 5.2 AI Explanation Performance (Qwen3:8B on Apple Silicon)

| Operation | Model / Provider | Mean Latency | Execution Source | Fallback Available | Status |
|---|---|---|---|---|---|
| **Bilingual Agricultural Explanation** | `qwen3:8b` via Ollama | **20.21 s** | `llm_qwen3_8b` | Yes (Deterministic MPKV fallback in < 10ms) | **STABLE** |
| **Follow-Up Interactive Re-Evaluation** | Deterministic Engine | **2.26 ms** | `deterministic_rules` | N/A (Pure deterministic) | **STABLE** |
| **Simulated Ollama Offline Fallback** | Deterministic Engine | **0.012 s** | `rule_based_fallback` | N/A | **VERIFIED** |

### 5.3 Throughput & System Memory Footprint
- **Concurrent Request Throughput**: **904.7 requests/second** (10 concurrent workers, 50 total HTTP requests completed in 0.06s with mean latency of 5.76 ms).
- **FastAPI Process RSS**: **97.1 MB**.
- **System RAM Utilization**: 24.0 GB total (4.9 GB available, 79.8% used).

---

## 6. Comprehensive Test Suite Results

```text
================================================================================
CROPNet AI — PHASE 5.5 VERIFICATION TEST MATRIX
================================================================================
1. Dart Static Analysis:
   Command: dart analyze lib/
   Result:  0 issues found (CLEAN)

2. Flutter Chrome Unit & Widget Tests:
   Command: flutter test --platform chrome
   Result:  91 passed, 0 failed, 0 skipped (100% PASS)

3. FastAPI Backend Pytest Suite:
   Command: pytest services/api/tests -v
   Result:  89 passed, 0 failed in 70.44s (100% PASS)
   - test_backend_reliability_phase5_5.py: 8 passed
   - test_phase5_5_e2e_farmer_journey.py: 3 passed
   - test_phase5_3_live_e2e.py: 14 passed
   - test_phase5_2_dialogue.py: 12 passed
   - test_agriculture_engine.py: 26 passed
   - test_soil_weather_integration.py: 26 passed

4. Production Web Release Build (JavaScript):
   Command: flutter build web --release
   Result:  Built build/web in 19.3s (SUCCESS)

5. WebAssembly Release Build (WASM):
   Command: flutter build web --wasm --no-tree-shake-icons
   Result:  Built build/web in 22.5s (SUCCESS)
================================================================================
```

---

## 7. Responsive Browser Testing Results

Testing was conducted across three standardized responsive viewports:
- **Mobile**: 375px width (iPhone SE / iPhone 13 mini)
- **Tablet**: 768px width (iPad Mini / Portrait Tablet)
- **Desktop**: 1280px width (Standard Desktop / Laptop)

```text
+-------------------+----------------------+--------------------+--------------------+
| Screen / Feature  | Mobile (375px)       | Tablet (768px)     | Desktop (1280px)   |
+-------------------+----------------------+--------------------+--------------------+
| My Farms          | Single-column stack, | 2-column grid,     | 3-column grid,     |
| Dashboard         | full-width cards,    | fluid padding,     | floating action    |
|                   | no overflow (PASS)   | no overflow (PASS) | controls (PASS)    |
+-------------------+----------------------+--------------------+--------------------+
| Boundary Drawing  | Touch gestures,      | Split-view card,   | Side-by-side card  |
| & Registration    | full-screen canvas,  | 100% canvas,       | with metric HUD,   |
|                   | no clipping (PASS)   | no clipping (PASS) | no clipping (PASS) |
+-------------------+----------------------+--------------------+--------------------+
| Soil Intelligence | Stacked metrics,     | 2x2 metric grid,   | Multi-column grid, |
| Presentation      | zero-NPK banner,     | zero-NPK banner,   | zero-NPK banner,   |
|                   | no overflow (PASS)   | no overflow (PASS) | no overflow (PASS) |
+-------------------+----------------------+--------------------+--------------------+
| Weather & Climate | Stacked cards,       | 2-column cards,    | 3-column overview, |
| Intelligence      | 30-year summary,     | 30-year summary,   | 30-year summary,   |
|                   | no overflow (PASS)   | no overflow (PASS) | no overflow (PASS) |
+-------------------+----------------------+--------------------+--------------------+
| Crop Catalogue    | Single card column,  | 2-column grid,     | 3-column grid,     |
| & Suitability     | season chips wrap,   | season chips wrap, | season chips wrap, |
|                   | no overflow (PASS)   | no overflow (PASS) | no overflow (PASS) |
+-------------------+----------------------+--------------------+--------------------+
| AI Assistant      | Full-width chat,     | Constrained width, | Split evaluation / |
| & Dialogue        | question chips wrap, | clean dialogue,    | chat interface,    |
|                   | sticky retry (PASS)  | sticky retry (PASS)| sticky retry (PASS)|
+-------------------+----------------------+--------------------+--------------------+
| Assessment        | Horizontally swipe-  | 4-card metric row, | 4-card metric row, |
| History           | able metrics (PASS)  | no overflow (PASS) | no overflow (PASS) |
+-------------------+----------------------+--------------------+--------------------+
```

---

## 8. Scientific Data Integrity Verification

CropNet AI enforces strict agricultural and scientific safeguards:

```mermaid
flowchart TD
    subgraph Client [Flutter Web Client]
        A["Farmer Requests Crop Evaluation"]
    end

    subgraph Backend [FastAPI Application]
        B["Deterministic Decision Engine (Phase 5.1)"]
        C{"Agronomic Hard Constraints Met?"}
        D["Approved Suitability & Evidence"]
        E["REJECTED / UNFEASIBLE"]
        F["Agricultural Knowledge Base (MPKV / ICAR)"]
    end

    subgraph LLM [Local Ollama qwen3:8b]
        G["Bilingual Natural Language Explanation"]
    end

    A --> B
    F -->|Thread-safe In-Memory Cache| B
    B --> C
    C -->|Yes| D
    C -->|No| E
    D --> G
    E --> G
    G -.->|Strictly Explains Approved Evidence| Client
```

1. **Zero NPK Fabrication**: Available nitrogen, phosphorus, and potassium are strictly set to `null` when derived exclusively from ISRIC SoilGrids 250m digital raster maps. Total nitrogen is never converted to available nitrate/ammonium without physical laboratory soil testing.
2. **Deterministic Authority**: The Phase 5.1 agricultural decision engine is the sole arbiter of crop feasibility and constraint checks. The LLM (`qwen3:8b`) receives the already-computed evaluation and is strictly constrained to explaining the results in natural language.
3. **Authentic Academic Citations**: Explanations cite verified agricultural packages of practice (e.g., MPKV Rahuri Research Compendium 2023, ICAR Crop Agronomy Handbooks). No hallucinated agronomic guidance is permitted.
4. **No Demo Fixtures**: Synthetic identifiers such as `demo-baramati-1` have been eradicated. Evaluations run exclusively on verified user-created farms or authenticated test identities.
5. **Multi-Tenant Row-Level Security**: Farm boundaries, soil snapshots, weather metrics, and advisory dialogues are partitioned by user ID. Cross-tenant queries return strict HTTP 403 Forbidden responses.

---

## 9. Screenshot Artifacts

All responsive UI captures are persisted under `docs/screenshots/` and in the conversation artifact directory:

| Viewport | Screen | Screenshot Link |
|---|---|---|
| Desktop (1280px) | My Farms Dashboard | [dashboard_desktop.png](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/docs/screenshots/dashboard_desktop.png) |
| Mobile (375px) | My Farms Dashboard | [dashboard_mobile.png](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/docs/screenshots/dashboard_mobile.png) |
| Desktop (1280px) | Soil Intelligence Screen | [soil_intelligence_desktop.png](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/docs/screenshots/soil_intelligence_desktop.png) |
| Desktop (1280px) | Weather & Climatology | [weather_desktop.png](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/docs/screenshots/weather_desktop.png) |
| Desktop (1280px) | Crop Catalogue Screen | [crops_catalog_desktop.png](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/docs/screenshots/crops_catalog_desktop.png) |
| Mobile (375px) | Crop Catalogue Screen | [crops_catalog_mobile.png](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/docs/screenshots/crops_catalog_mobile.png) |
| Desktop (1280px) | AI Agricultural Assistant | [advisory_desktop.png](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/docs/screenshots/advisory_desktop.png) |
| Tablet (768px) | AI Agricultural Assistant | [advisory_tablet.png](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/docs/screenshots/advisory_tablet.png) |
| Mobile (375px) | AI Agricultural Assistant | [advisory_mobile.png](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/docs/screenshots/advisory_mobile.png) |
| Desktop (1280px) | Assessment History Screen | [history_desktop.png](file:///Users/siddheshbirewar/Downloads/Cropnet%20Feature/cropnet/docs/screenshots/history_desktop.png) |

---

## 10. Remaining Limitations & Roadmap

While Phase 5.5 delivers a completely functional local prototype, the following items remain deferred until commercial cloud release:

1. **Cloud GPU Hosting**: Local inference relies on `qwen3:8b` via Ollama at `127.0.0.1:11434`. Production deployment requires provisioning an NVIDIA A10G/L4 instance with vLLM behind a private VPC.
2. **Public Email SMTP Gateway**: Supabase free-tier rate limits email confirmations (HTTP 429). Production deployment will integrate SendGrid or AWS SES for self-service farmer registration.
3. **Laboratory Soil Card OCR**: Manual soil input is currently supported through diagnostic follow-ups. Automated OCR ingestion of printed Krishi Vigyan Kendra (KVK) soil health cards is slated for Phase 6.
4. **Native Mobile App Store Release**: While Flutter Web is verified and responsive, compiling signed Android APKs and iOS IPAs requires store certificates and developer account provisioning.
5. **Marathi Voice Interface (ASR/TTS)**: Speech-to-text and text-to-speech for non-literate farmers will be integrated in subsequent phases.

---

## 11. Verification Sign-Off

- **Lead Orchestrator**: Verified and Consolidated
- **Agent 1 (UI/UX)**: Signed Off (Commit: `c11305d`)
- **Agent 2 (Backend)**: Signed Off (Commit: `aebfc45`)
- **Agent 3 (QA)**: Signed Off (Commit: `409598a`)
- **Consolidated Branch**: `integration/consolidated-workstreams`
