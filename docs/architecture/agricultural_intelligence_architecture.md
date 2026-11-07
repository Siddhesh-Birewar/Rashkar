# CropNet AI — Agricultural Intelligence Architecture Specification (Phase 5.0)

**Document Version:** 1.0.0  
**Phase:** 5.0 (Intelligence Benchmark & Evaluation Framework)  
**Target Environment:** FastAPI (Python 3.11+) + PostgreSQL 17 / PostGIS 3.5 (Hosted Supabase) + Local LLM Explanation Layer (Qwen3:8B) + Flutter Mobile Client  
**Status:** Approved Architectural Blueprint  

---

## 1. Architectural Philosophy & Core Tenets

CropNet AI’s agricultural intelligence is built upon a fundamental architectural axiom:
> **Agronomic decisions must be deterministic, mathematically transparent, and evidence-grounded. Large Language Models (LLMs) must NEVER serve as unconstrained decision-makers, nor should they directly query the database or fabricate agronomic thresholds.**

The CropNet system strictly isolates **agronomic reasoning** from **linguistic expression**:
1. **The Deterministic Decision Engine** determines crop suitability, environmental violations, irrigation requirements, and risk factors using formal rules derived from verified agricultural literature (ICAR, MPKV, ICRISAT).
2. **The Agricultural Knowledge Retrieval Layer** fetches exact parameters, citations, and uncertainty flags from the Phase 4 PostgreSQL database.
3. **The LLM Explanation Layer** is strictly confined to synthesizing, formatting, explaining, and translating the deterministic findings into accessible, farmer-friendly English and Marathi.
4. **The Output Safety & Guardrail Layer** validates the LLM’s response against the deterministic payload to ensure zero hallucination, zero threshold alteration, and strict citation compliance.

```
+-----------------------------------------------------------------------------------+
|                               Flutter Mobile Client                               |
|               (Crop Selection, Soil Health Cards, Bilingual Advisory)             |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          | HTTPS / REST (JSON)
                                          v
+-----------------------------------------------------------------------------------+
|                        CropNet FastAPI Backend Service                            |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | Layer 1: Input & Context Validation Service                                 |  |
|  |   - Farm geometry validation & Taluka resolution (PostGIS)                  |  |
|  |   - Soil test verification (Lab NPK vs ISRIC proxy)                         |  |
|  |   - Missing parameter detection & Ambiguity classifier                     |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        |                                          |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | Layer 2: Agricultural Knowledge Retrieval Service                           |  |
|  |   - Supabase PostGIS / SQL queries (Crops, Soil, Climate, Water, Sources)   |  |
|  |   - Weather & Climatology ingestion (Open-Meteo 7-day vs 30-year Normals)   |  |
|  |   - Citation & Evidence status tagging (regional_screening / validation)    |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        |                                          |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | Layer 3: Deterministic Agronomic Decision Engine                           |  |
|  |   - Feasibility filter (pH bounds, drainage, thermal thresholds, Bahar)     |  |
|  |   - Stage-specific water balance calculation                                |  |
|  |   - Taluka screening evaluation (Baramati/Indapur vs Maval/Mulshi)          |  |
|  |   - Reason codes & constraint violation generation                          |  |
|  +-------------------------------------+---------------------------------------+  |
|                                        |                                          |
|                                        v                                          |
|  +-----------------------------------------------------------------------------+  |
|  | Layer 4: Evidence & Uncertainty Management Service                          |  |
|  |   - Unverified parameter tracker (Strict NULL handling)                     |  |
|  |   - Abstention trigger (Insufficient data / Contradictory inputs)           |  |
|  |   - Decoupled source conflict resolver (e.g. ICRISAT vs MPKV irrigation)    |  |
|  +-------------------+---------------------------------+-----------------------+  |
|                      |                                 |                          |
|         Payload with |                    Incomplete   | Request Follow-up        |
|         Verdict & DB |                    Inputs       |                          |
|         Citations    v                                 v                          |
|  +-----------------------------------+  +--------------------------------------+  |
|  | Layer 5: LLM Explanation Layer    |  | Layer 6: Follow-up Question Engine   |  |
|  | (Local Qwen3:8B - Read-Only JSON) |  |   - Generates targeted, non-leading  |  |
|  |   - Grounded prompt templating    |  |     agronomic questions (e.g., soil  |  |
|  |   - Bilingual translation (MR/EN) |  |     depth, irrigation source, Bahar) |  |
|  |   - Farmer-friendly analogies     |  +------------------+-------------------+  |
|  +-------------------+---------------+                     |                      |
|                      |                                     |                      |
|                      +------------------+------------------+                      |
|                                         |                                         |
|                                         v                                         |
|  +-----------------------------------------------------------------------------+  |
|  | Layer 7: Output Validation & Guardrail Service                              |  |
|  |   - Numerical threshold diff checker (Zero hallucination policy)            |  |
|  |   - Scientific term verification (e.g., Total N vs Available N)             |  |
|  |   - Citation presence assertion (Must match Layer 2 IDs)                    |  |
|  |   - Cross-lingual semantic invariant check (English == Marathi boundaries)  |  |
|  +-------------------------------------+---------------------------------------+  |
+----------------------------------------|------------------------------------------+
                                         |
                                         | Structured API Response (JSON)
                                         v
+-----------------------------------------------------------------------------------+
|                          Flutter UI Presentation Engine                           |
|        (Visual Health Indicators, Structured Warnings, Follow-up Dialogs)         |
+-----------------------------------------------------------------------------------+
```

---

## 2. Detailed Layer Specifications

### Layer 1: Input & Context Validation Service
- **Responsibilities:**
  - Validate inbound GeoJSON coordinates and verify spatial containment within Maharashtra pilot talukas (Baramati, Indapur, Maval, Mulshi).
  - Distinguish between **Laboratory Soil Test Results** (measured available N, P, K, pH, EC) and **ISRIC Coarse Spatial Proxies** (estimated total N, SOC).
  - Run missing parameter detection: identify absence of critical limiting factors (e.g., soil depth, EC, slope, water table depth).
  - Flag input contradictions (e.g., claiming "sandy soil" while reporting "frequent waterlogging", or specifying "pH 8.2" while describing the soil as "acidic").

### Layer 2: Agricultural Knowledge Retrieval Service
- **Responsibilities:**
  - Execute parameter-driven SQL queries against the 7 Phase 4 knowledge tables via SQLAlchemy.
  - Ingest real-time weather forecasts (Open-Meteo 7–14 days) and historical climate summaries (30-year normals).
  - Maintain strict separation: historical climate normals define long-term crop feasibility, whereas short-range weather forecasts determine operational scheduling (sowing, spraying, irrigation).
  - Retrieve bibliographic metadata for every crop parameter from `agricultural_knowledge_sources`.
  - Attach evidence classifications (`verified_regional_evidence`, `regional_screening`, `requires_regional_validation`).

### Layer 3: Deterministic Agronomic Decision Engine
- **Responsibilities:**
  - **Hard Constraint Filtering:** Disqualify crops if soil or climate values exceed tolerable thresholds (e.g., waterlogging-sensitive crops in poorly drained Vertisols; chickpea in saline soil).
  - **Suitability Scoring:** Calculate dimensional suitability scores:
    $$S_{\text{total}} = w_{\text{soil}} S_{\text{soil}} + w_{\text{climate}} S_{\text{climate}} + w_{\text{water}} S_{\text{water}}$$
    *(Where weights are normalized and missing dimensions trigger explicit uncertainty penalties rather than assuming default zeros).*
  - **Stage-Aware Irrigation Calculator:** Compute net irrigation requirement using crop coefficient ($K_c$) or explicit daily water tables (e.g., pomegranate liters/tree/day across Mrig, Hasta, Ambia Bahars).
  - **Reason Code Generation:** Produce structured, deterministic reason codes (e.g., `ERR_PH_EXCEEDS_OPTIMUM`, `WARN_REPRODUCTIVE_HEAT_STRESS_35C`, `INFO_BAHAR_FLOWER_REGULATION_REQUIRED`).

### Layer 4: Evidence & Uncertainty Management Service
- **Responsibilities:**
  - **Strict NULL Handling:** Prevent imputation of unknown values. For example, pomegranate lower tolerable pH and annual water requirement (mm) are unverified in source literature and must remain `NULL`.
  - **Abstention Protocols:** Trigger formal abstention (`status: "ABSTAIN_INSUFFICIENT_DATA"`) when core limiting factors are missing.
  - **Decoupled Source Preservation:** When multiple authoritative sources provide complementary or divergent recommendations (e.g., ICRISAT stage-based irrigation vs. MPKV calendar DAS irrigation for chickpea), present both with distinct source IDs rather than blending them into an unverified composite.

### Layer 5: LLM Explanation Layer (Local Qwen3:8B)
- **Responsibilities:**
  - Receive a structured JSON payload containing:
    1. Deterministic suitability verdict and reason codes.
    2. Verified crop requirements and thresholds.
    3. Retrieved source citations.
    4. Target language (`en` or `mr`).
  - Convert structured results into fluent, empathetic, and culturally appropriate agricultural language.
  - Strictly forbidden from:
    - Altering numerical values (e.g., changing 35°C to 40°C).
    - Promoting disqualified crops based on market popularity.
    - Answering questions outside the provided context payload.

### Layer 6: Follow-Up Question Engine
- **Responsibilities:**
  - When Layer 1 detects missing or contradictory data, Layer 6 formulates concise, non-leading clarification questions.
  - Examples:
    - *Soil depth unknown:* "What is the effective depth of your soil? (Shallow <30 cm, Medium 30–60 cm, Deep >60 cm)"
    - *Pomegranate Bahar unselected:* "Which Bahar are you planning to regulate? (Mrig Bahar / June flowering, Hasta Bahar / September flowering, or Ambia Bahar / January flowering)?"

### Layer 7: Output Validation & Guardrail Service
- **Responsibilities:**
  - **Deterministic Diff Assertion:** Extract all numerical values and crop names from the LLM’s generated text; verify that every number and threshold exists within the deterministic payload.
  - **Scientific Terminology Guard:** Ensure terms like "Available Nitrogen" (उपलब्ध नत्र) are never used if the data provided was "Total Nitrogen" (एकूण नत्र).
  - **Citation Verification:** Confirm that every cited reference ID in the text corresponds to a valid record in `agricultural_knowledge_sources`.
  - **Fallback Circuit Breaker:** If the LLM output fails validation, discard the LLM text and return a deterministic template-rendered response.

---

## 3. Communication Contract (Flutter to FastAPI)

The Flutter mobile client communicates exclusively with FastAPI endpoints. The mobile client never interfaces directly with database instances or LLM backends.

```json
// POST /api/v1/intelligence/advisory
// Request Payload
{
  "farm_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "target_season": "rabi",
  "target_year": 2026,
  "language": "mr",
  "user_query": "माझ्या शेतात हरभरा लावला तर चालेल का? पाण्याचे काय नियोजन करावे?",
  "farm_overrides": {
    "irrigation_source": "well",
    "soil_depth_cm": 75,
    "has_salinity_problem": false
  }
}
```

```json
// Response Payload
{
  "advisory_id": "adv_20261107_8f92b",
  "status": "SUCCESS",
  "degraded_mode": false,
  "language": "mr",
  "crop_verdicts": [
    {
      "crop_id": "chickpea",
      "common_name": "हरभरा (चना)",
      "suitability_class": "HIGHLY_SUITABLE",
      "suitability_score": 0.88,
      "regional_status": "regional_screening",
      "limiting_factors": [],
      "reproductive_risk_warnings": [
        "पुनरुत्पादन अवस्थेत (फुलोरा व घाटे भरणे) कमाल तापमान ३५°C पेक्षा जास्त गेल्यास फूल गळ व घाटे धारणा कमी होण्याचा धोका असतो (ICRISAT 2010)."
      ],
      "irrigation_guidance": {
        "strategy": "DECOUPLED_STAGE_AND_DAS",
        "icrisat_recommendation": "फांद्या फुटताना आणि घाटे भरताना १ ते २ हलके पाणी द्यावे. अति पाणी दिल्यास मूळ कुजव्या रोगाचा प्रादुर्भाव होतो.",
        "mpkv_recommendation": "मध्यम ते भारी जमिनीत पेरणीनंतर २०-२५ दिवसांनी आणि ६०-६५ दिवसांनी संरक्षित पाणी द्यावे."
      }
    }
  ],
  "llm_explanation": "तुमच्या बारामती येथील शेतातील खोल काळी जमीन (Vertisol) आणि रब्बी हंगामातील हवामान हरभरा पिकासाठी अतिशय अनुकूल आहे...",
  "citations": [
    {
      "source_id": "icrisat_chickpea_2010",
      "organization": "ICRISAT",
      "publication_title": "Chickpea Seed Production Manual",
      "publication_year": 2010
    },
    {
      "source_id": "mpkv_research_2023",
      "organization": "MPKV, Rahuri",
      "publication_title": "Research Recommendations Released during 2023",
      "publication_year": 2023
    }
  ],
  "follow_up_questions": []
}
```

---

## 4. Operational Boundaries & Architectural Prohibitions

1. **No Microservices:** The engine operates as a modular package (`cropnet.services.api.app.services.intelligence`) within the existing FastAPI backend. No Kafka, Redis streams, or independent microservices are permitted.
2. **No Direct Database Access by LLM:** The LLM prompt is constructed strictly from validated Pydantic schemas. The LLM has no SQL connection, tools, or direct query capability.
3. **No Automatic Fallback to Unsupported Assumptions:** If data is missing (e.g. soil EC), the engine must label it as missing and either solicit clarification or abstain from certifying salt-sensitive crops.
Path: file:///Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/docs/architecture/agricultural_intelligence_architecture.md
