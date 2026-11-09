# Implementation Plan: Personalized Income Intelligence, Issue-First Dashboard, and Real Ollama AI Assistant

**Document Location:** `docs/superpowers/plans/2026-11-09-income-dashboard-ollama-assistant.md`  
**Date:** 9 November 2026  
**Active Branch:** `yeild-and-heat-risk-feature`  

---

## 1. Architectural Overview & Requirements Breakdown

This plan implements four integrated capabilities:
1. **Farmer Age & Work Preferences Personalization**:
   - Add age ranges, work preferences, payback horizons, and family management roles to `FarmerResourceProfile`.
   - Age is never treated as physical ability or automatic disqualification; it is combined with explicit work preferences and time horizons.
   - Crop diversification validation: Sunflower is treated as an agronomic crop, not generic extra income. Missing agronomic context produces `NEEDS_VERIFICATION`.
   - Opportunity classification into 5 distinct groups:
     - `CAN_TRY_WITH_WHAT_YOU_HAVE`
     - `CAN_TRY_WITH_SMALL_ADDITIONAL_AMOUNT`
     - `NEEDS_MORE_MONEY`
     - `NEEDS_MORE_INFORMATION`
     - `NOT_SUITABLE_CURRENTLY`
2. **Issue-First Farmer Dashboard (`DashboardIssueService`)**:
   - Centralized aggregation endpoint `GET /v1/dashboard/issues` combining Worker Heat, Crop Heat, Yield Risk, Weather alerts, and Season integrity.
   - Severity-based prioritization (`URGENT_ATTENTION`, `NEEDS_ATTENTION`, `KEEP_AN_EYE_ON`, `INFORMATION`).
   - Clean farmer-first UI with 1-tap navigation directly into the problem-solving feature.
3. **Real Local Ollama AI Assistant (`qwen3:8b`)**:
   - Backend service communicating with local Ollama (`http://127.0.0.1:11434`).
   - Automatic farm context extraction (Farmer, Farm, Crop, Soil, Weather, Worker Heat, Crop Heat, Yield Risk, Income Feasibility).
   - Tool-grounded synthesis to prevent hallucinations.
   - Streaming SSE endpoint and non-streaming fallback.
   - Resilient offline state indicator when Ollama is unavailable.
4. **Simple Farmer UI Redesign**:
   - Guided Extra Income flow: Intro $\rightarrow$ About You $\rightarrow$ Farm Resources $\rightarrow$ Top 3 Opportunities $\rightarrow$ Structured Detail View $\rightarrow$ Compare & Save Plan.
   - Dashboard: Greeting & Farm identity $\rightarrow$ Needs Attention Today $\rightarrow$ Today's Weather $\rightarrow$ Primary Action Buttons.
   - Ask Rashkar: Context indicator chip $\rightarrow$ Streaming chat $\rightarrow$ Suggested prompts.

---

## 2. File Structure

### Backend Modules to Modify / Create:
- `backend/app/schemas/income.py` (add age range, work preferences, payback horizon, family role, 5 status categories)
- `backend/app/services/opportunity_feasibility_engine.py` (incorporate age preferences, sunflower agronomic validation, verified byproducts)
- `backend/app/services/income_knowledge_catalog.py` (add provenance citations, update sunflower constraints, ensure exact data)
- `backend/app/schemas/dashboard.py` (NEW: DashboardIssue, DashboardIssueSummary, Priority categories)
- `backend/app/services/dashboard_issue_service.py` (NEW: Centralized multi-module issue aggregator)
- `backend/app/api/v1/endpoints/dashboard.py` (NEW: `/v1/dashboard/issues` endpoint)
- `backend/app/schemas/assistant.py` (enrich with context fields, streaming schemas)
- `backend/app/services/ollama_agent_service.py` (NEW: Direct Ollama local connector with context injection & tools)
- `backend/app/api/v1/endpoints/assistant.py` (integrate Ollama streaming & non-streaming endpoints)
- `backend/app/api/v1/router.py` (mount dashboard endpoint)

### Tests to Modify / Create:
- `backend/tests/test_farmer_age_and_preferences.py` (NEW: tests for age, work preferences, payback horizons, sunflower verification)
- `backend/tests/test_dashboard_issues.py` (NEW: tests for multi-module issue detection, prioritization, and no-issue state)
- `backend/tests/test_ollama_agent.py` (NEW: tests for Ollama connectivity, context retrieval, tool execution, offline handling)

### Frontend (Flutter Web) Modules to Modify:
- `flutter_client/lib/models/farm_models.dart` (add age range, preferences, dashboard issue models)
- `flutter_client/lib/services/api_service.dart` (add dashboard issues API, Ollama chat streaming / non-streaming)
- `flutter_client/lib/screens/home_screen.dart` (issue-first priority layout, weather summary, action buttons)
- `flutter_client/lib/screens/extra_income_screen.dart` (step-by-step guided flow, top 3 ranking, simple cards)
- `flutter_client/lib/screens/ask_rashkar_screen.dart` (farm context chip, streaming responses, offline indicator)

---

## 3. Step-by-Step Execution Plan

### Step 1: Update Schemas and Feasibility Engine for Age & Agronomic Sunflower Validation
- Add `age_range`, `work_preference`, `payback_horizon`, `family_management_role` to `FarmerResourceProfile`.
- Implement preference matching in `OpportunityFeasibilityEngine`:
  - Heavy manual activities require `daily_physical` or `family_help` or `hire_labor`.
  - Fast return requirements filter out long gestation enterprises.
  - Sunflower requires active crop calendar inspection; returns `NEEDS_VERIFICATION` if timing/rotation incompatible.
  - Compost requires verified livestock or cow dung.

### Step 2: Build Issue-First Dashboard Backend (`DashboardIssueService`)
- Aggregate Worker Heat, Crop Heat, Yield Risk, Weather alerts, and Crop Season status.
- Sort into `URGENT_ATTENTION`, `NEEDS_ATTENTION`, `KEEP_AN_EYE_ON`, `INFORMATION`.
- Return clean structured list with target route (`heat_safety`, `my_crop`, `income`, `crop_loss`).

### Step 3: Implement Real Ollama AI Assistant Engine (`OllamaAgentService`)
- Connect to `http://127.0.0.1:11434` with model `qwen3:8b`.
- Construct comprehensive farm context dynamically.
- Implement tool retrieval for grounded farm data.
- Expose streaming endpoint `POST /v1/assistant/chat-stream` and standard `POST /v1/assistant/chat`.

### Step 4: Redesign Frontend UI (Home, Extra Income, Ask Rashkar)
- Rebuild `home_screen.dart` with issue-first priority layout.
- Rebuild `extra_income_screen.dart` with guided multi-step wizard and top 3 simple cards.
- Rebuild `ask_rashkar_screen.dart` with live Ollama connection, context indicator chip, and streaming chat.

### Step 5: Verification & Quality Gates
- Run complete test suite (`pytest`).
- Capture browser journey screenshots with Playwright.
- Create all 5 requested documentation files.
