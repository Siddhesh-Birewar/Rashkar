# Extra Income Engine: Final Personalization, Economic Validation & Browser Acceptance Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rigorously validate and enhance the Extra Income & Farm Diversification Engine so it discovers personalized opportunities from actual farmer resources across 5 distinct profiles, eliminates misleading fit percentages, mathematically reconciles all financial views, verifies realistic zero-cost agronomics, and validates the full farmer journey in the browser.

**Architecture:**
- Deterministic multi-gate feasibility engine in `opportunity_feasibility_engine.py` with dynamic residue calculations and equipment ownership validation.
- Enhanced 12-model knowledge catalog in `income_knowledge_catalog.py` with precise NABARD FY26-27 table/page references and distinct categories for cash income, money saved, and income protected.
- Authoritative calculation service in `income_financial_service.py` supporting assumption tweaking and mathematical reconciliation.
- Farmer-first Flutter UI in `extra_income_screen.dart` replacing fit percentages with 6 descriptive status badges and assumption sliders.
- Real browser validation with Playwright/agent-browser capturing screenshots of Profiles A–E into `docs/screenshots/extra_income/`.

**Spec:** User request for final personalization, economic validation, and browser acceptance.

## Global Constraints
- Target branch: `yeild-and-heat-risk-feature` and `yield-and-heat-risk-feature`. Never merge implementation code into `main`.
- Independent README synchronization: `main` branch README may be updated independently without touching application code.
- Deterministic primacy: calculations must be deterministic; no hallucinated constants or fake fit percentages.
- Support ₹0 budget natively without minimum investment errors.
- Target Flutter Web in Chrome/Edge, keeping backend on FastAPI.

## Review Focus
1. Profile A (₹0 budget, rainfed) must receive Category A (composting/aggregation) as feasible and all capital enterprises as requiring capital.
2. If a farmer does not own a tractor or sprayer, equipment hiring cannot be recommended as feasible income.
3. If a 2+1 goat unit costs ₹18,000 + ₹2,500 working capital, a farmer with ₹15,000 must see an exact shortfall of ₹5,500 and NOT be marked "affordable now".
4. Opportunity card, detail modal, comparison table, and saved plans must show mathematically identical figures.
5. In the browser, all 5 profiles must be loaded, changed, recalculated, and screens captured with zero console crashes.

---

### Task 1: Realistic Agronomic & Ownership Auditing in Multi-Gate Feasibility Engine
**Files:**
- Modify: `backend/app/services/opportunity_feasibility_engine.py`
- Modify: `backend/app/schemas/income.py`
- Create: `backend/tests/test_zero_cost_realistic.py`

- [ ] **Step 1: Write failing tests for residue math, equipment ownership, and working capital shortfall**
- [ ] **Step 2: Run pytest to verify failures**
- [ ] **Step 3: Implement dynamic residue estimation, equipment asset gating, and total outlay shortfall calculation**
- [ ] **Step 4: Verify tests pass**

### Task 2: Exact NABARD FY26-27 Citations & Tri-Partite Return Breakdown
**Files:**
- Modify: `backend/app/services/income_knowledge_catalog.py`
- Modify: `backend/app/services/income_financial_service.py`
- Create: `backend/tests/test_income_citations_and_tripartite.py`

- [ ] **Step 1: Write tests verifying NABARD table citations and cash vs savings vs protected breakdown**
- [ ] **Step 2: Run pytest to verify failures**
- [ ] **Step 3: Update 12 canonical catalog models with page/table numbers and tri-partite returns**
- [ ] **Step 4: Verify tests pass**

### Task 3: 5 Distinct Test Profiles Discovery & Validation Suite
**Files:**
- Create: `backend/tests/test_farmer_personalization_profiles.py`
- Modify: `backend/app/api/v1/endpoints/income.py`

- [ ] **Step 1: Write tests defining Profiles A, B, C, D, E and asserting distinct recommendations**
- [ ] **Step 2: Run pytest to verify failures and assertions**
- [ ] **Step 3: Refine discovery rankings and API endpoint to ensure distinct tailored results**
- [ ] **Step 4: Verify tests pass**

### Task 4: Flutter UI Enhancement — Remove Fit Percentages & Add Status Badges
**Files:**
- Modify: `flutter_client/lib/models/farm_models.dart`
- Modify: `flutter_client/lib/screens/extra_income_screen.dart`

- [ ] **Step 1: Update Flutter models with tri-partite returns and descriptive feasibility status**
- [ ] **Step 2: Replace fit percentage badges with 6 descriptive status badges**
- [ ] **Step 3: Add interactive assumption slider in deep dive view (e.g. market price or batch size)**
- [ ] **Step 4: Verify `flutter analyze` and `flutter test` pass**

### Task 5: Browser Automation & Verification with Screenshot Capture
**Files:**
- Create: `tests/test_browser_journeys.py`
- Directory: `docs/screenshots/extra_income/`

- [ ] **Step 1: Write Playwright browser automation script testing Profiles A–E end-to-end**
- [ ] **Step 2: Execute script against `http://localhost:8080` and `http://127.0.0.1:8000`**
- [ ] **Step 3: Capture and store high-res screenshots for each profile**
- [ ] **Step 4: Verify all browser journeys complete without error**

### Task 6: Final Documentation & Git Synchronization
**Files:**
- Update: `docs/EXTRA_INCOME_ENGINE_METHODOLOGY.md`
- Create: `docs/EXTRA_INCOME_PERSONALIZATION_VALIDATION.md`
- Verify: Full test suite, analyzer, secret scan, and git branch consistency.
