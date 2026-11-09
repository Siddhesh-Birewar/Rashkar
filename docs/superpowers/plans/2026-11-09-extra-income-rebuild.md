# Extra Income & Farm Diversification Engine Complete Rebuild Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the Extra Income feature from an unrealistic catalogue of expensive enterprises into a farmer-first, resource-grounded opportunity discovery engine that starts with ₹0 cash and existing resources, enforces strict financial consistency, and eliminates all arbitrary 98% fit scores.

**Architecture:** Layered architecture featuring:
1. Structured `FarmerResourceProfile` schema and database storage prefilled from farm parcels.
2. Dynamic 5-category opportunity discovery catalogue (`Zero-Cash`, `Very Low Investment`, `Low-to-Moderate Enterprise`, `Alternative Crops`, `External/Group Services`).
3. Multi-gate feasibility engine (Capital, Working Capital, Space, Water, Labour, Market, Season) with transparent suitability scoring and no fake probabilities.
4. Single-source-of-truth financial simulation engine with enterprise-specific cash-flow timelines, true cumulative payback, and reconciled card/table metrics.
5. Simple 7-screen progressive disclosure Flutter Web interface supporting ₹0-to-enterprise budgets with responsive centering and comparison tools.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy, Pydantic v2, Flutter Web (Dart 3), Playwright / pytest.

**Spec:** User prompt: "RASHKAR — COMPLETE EXTRA INCOME & FARM DIVERSIFICATION ENGINE REBUILD"

## Global Constraints
- Support farmers with ₹0 available capital without validation failures or artificial minimums.
- Zero fake financial numbers: All opportunity cards, comparison tables, and scenario views must reconcile to the exact same backend model.
- No static `98% Fit` badges: Use transparent criteria match breakdowns and descriptive status tags.
- Categorize cost-savings (e.g. on-farm composting reducing fertilizer purchases) separately from new cash revenue.
- Secondary crops (e.g. sunflower) must account for opportunity costs of displaced primary crops.
- Preserve Yield Intelligence and Heat Risk modules untouched.

## Review Focus
1. **₹0 Budget Farmer**: A farmer entering ₹0 investment must receive Category A opportunities (byproduct utilization, loss reduction, market linkage) and zero unaffordable enterprise suggestions.
2. **Capital Gate Strictness**: An enterprise costing ₹75,000 (like 10+1 goats) must NEVER be approved or marked as "Capital Match" when the farmer's available setup budget is ₹15,000.
3. **Mushroom Profit Reconciliation**: Annual profit displayed on the opportunity card, detail view, and comparison table must be identical for the same scenario.
4. **Offline Resilience**: When Ollama or external network APIs are unavailable, the deterministic engine must function completely without error.
5. **Responsive Large-Screen Alignment**: Flutter UI must use `ConstrainedBox(maxWidth: 840)` and adaptive sliders/chips that work seamlessly across desktop (1440x900) and mobile (390x844).

---

### Task 1: Comprehensive Backend Data Models & Database Schemas

**Files:**
- Modify: `backend/app/db/models/income.py`
- Modify: `backend/app/schemas/income.py`
- Create: `backend/tests/test_income_models_schema.py`

**Interfaces:**
- Consumes: SQLAlchemy `Base`, `now_utc`
- Produces: `FarmerResourceProfileModel`, `OpportunityCatalogModel`, `SavedIncomePlanModel`, updated Pydantic schemas supporting ₹0 minimums and 5 categories.

- [ ] **Step 1: Write failing schema and model tests**
Test that `FarmerResourceProfile` accepts `available_investment_inr = 0.0`, correctly structures separate setup vs working capital, validates 5 opportunity categories (`zero_cash`, `very_low_cost`, `moderate_enterprise`, `crop_diversification`, `group_external`), and models monthly cash flow timelines.

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_income_models_schema.py -v`
Expected: FAIL (models missing new fields / `ge=5000` validation failure)

- [ ] **Step 3: Implement updated schemas and database models**
Update `backend/app/schemas/income.py` and `backend/app/db/models/income.py` with:
- Zero-minimum support (`ge=0.0`).
- Multi-dimensional resource profiles (space, shed, water months, family vs hired labour, existing tools, byproducts).
- 5-category opportunity taxonomy.
- Reconciled financial scenario output schema with scenario ID, capex, opex, gross revenue, net cash surplus, economic profit, and 12-month timeline.

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_income_models_schema.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add backend/app/schemas/income.py backend/app/db/models/income.py backend/tests/test_income_models_schema.py
git commit -m "feat(income): expand schemas and database models for 5-category opportunity framework"
```

---

### Task 2: Grounded Opportunity Knowledge Catalogue & Byproduct Taxonomy

**Files:**
- Create: `backend/app/services/income_knowledge_catalog.py`
- Modify: `backend/app/db/init_db.py`
- Create: `backend/tests/test_income_catalog.py`

**Interfaces:**
- Consumes: `OpportunityCatalogItem`, crop byproduct mapping (soybean, cotton, jowar, onion, sugarcane)
- Produces: `EXTENDED_OPPORTUNITY_CATALOG` with verified NABARD FY26-27 benchmarks, ICAR/MPKV package of practices, and zero-cash agricultural interventions.

- [ ] **Step 1: Write failing tests for catalogue coverage**
Test that the catalogue contains:
1. Category A Zero-Cash opportunities (Farmyard Composting & Input Cost Saving, Direct APMC/FPO Grain Aggregation, Field Equipment Rental Sharing).
2. Category B Very-Low-Investment opportunities (Field Bund Drumstick/Moringa, Seedling Pro-Tray Raising, Micro-Vermicompost).
3. Category C Scaled Enterprise units (Small 2+1 Goat Unit, 10+1 Goat Unit, Oyster Mushroom Batch, 5-Box Beekeeping).
4. Category D Crop Diversification (Sunflower intercropping with opportunity cost checks).
5. Category E Group & Services (Custom Hiring Services, FPO Collective Procurement).
All items must have valid evidence citations, minimum viable units, and explicit input requirements.

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_income_catalog.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement `income_knowledge_catalog.py`**
Define structured data objects with complete parameterization (capital, land, water, labor, risk, seasonal availability, evidence provenance).

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_income_catalog.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add backend/app/services/income_knowledge_catalog.py backend/tests/test_income_catalog.py
git commit -m "feat(income): implement comprehensive 5-category opportunity knowledge catalogue"
```

---

### Task 3: Feasibility Engine & Multi-Factor Suitability Scoring

**Files:**
- Create: `backend/app/services/opportunity_feasibility_engine.py`
- Create: `backend/tests/test_opportunity_feasibility.py`

**Interfaces:**
- Consumes: `FarmerResourceProfile`, `OpportunityCatalogItem`
- Produces: `FeasibilityResult` with hard gate evaluation (`FEASIBLE_WITH_CURRENT_RESOURCES`, `NOT_CURRENTLY_AFFORDABLE`, `REQUIRES_MORE_INFORMATION`, etc.), transparent weighted score (0-100), and detailed factor-by-factor reasoning.

- [ ] **Step 1: Write failing tests for feasibility gates and scoring**
Test:
1. Farmer with ₹15,000 budget rejects ₹75,000 enterprise as `NOT_CURRENTLY_AFFORDABLE` with exact capital gap calculation.
2. Farmer with ₹0 budget receives `FEASIBLE_WITH_CURRENT_RESOURCES` for Category A zero-cash options.
3. Missing critical water/space returns `REQUIRES_MORE_INFORMATION` instead of fabricated match.
4. Suitability score dynamically reflects weights: Capital (20), Space (15), Water (15), Labour (10), Market (15), Byproduct (10), Location/Season (10), Interest (5). No static 98% caps.

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_opportunity_feasibility.py -v`
Expected: FAIL (engine not implemented)

- [ ] **Step 3: Implement `OpportunityFeasibilityEngine`**
Build rigorous rule checks with exact capital gap detection, seasonal water verification, labour schedule conflict checks, and transparent rule-based score calculation.

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_opportunity_feasibility.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add backend/app/services/opportunity_feasibility_engine.py backend/tests/test_opportunity_feasibility.py
git commit -m "feat(income): implement multi-gate feasibility and weighted suitability scoring engine"
```

---

### Task 4: Single-Source Authoritative Financial Calculation Service

**Files:**
- Create: `backend/app/services/income_financial_service.py`
- Modify: `backend/app/services/income_engine.py`
- Create: `backend/tests/test_income_financial_reconciliation.py`

**Interfaces:**
- Consumes: `opportunity_id`, `custom_budget_inr`, `FarmerResourceProfile`
- Produces: `EnterpriseFinancialAnalysis` with 12-month production-cycle cashflows, true cumulative payback, explicit cost/revenue breakdown, and identical output across cards, details, and comparisons.

- [ ] **Step 1: Write failing reconciliation and calculation tests**
Test:
1. Enterprise calculations distinguish Cash Operating Surplus, Economic Profit (imputing family labour), and Money Saved.
2. Production calendars differ realistically: Goats show revenue starting month 7-8 after kidding; Mushrooms show recurring batch cycles; Vermicompost shows 60-day cycles.
3. Payback period is derived from cumulative monthly cash flow recovering total initial outlay (not linear capex/profit division).
4. Reconciliation test: The financial outputs of an opportunity retrieved for card view, detail view, and side-by-side comparison are 100% mathematically identical.

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_income_financial_reconciliation.py -v`
Expected: FAIL

- [ ] **Step 3: Implement `IncomeFinancialService`**
Build deterministic, enterprise-specific cashflow generators and link `IncomeEngine.calculate_enterprise_financials` and `compare_opportunities` to this single service.

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_income_financial_reconciliation.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add backend/app/services/income_financial_service.py backend/app/services/income_engine.py backend/tests/test_income_financial_reconciliation.py
git commit -m "feat(income): implement authoritative single-source financial simulation and reconciliation engine"
```

---

### Task 5: Opportunity Discovery Endpoints & Plan Persistence

**Files:**
- Modify: `backend/app/api/v1/endpoints/income.py`
- Modify: `backend/tests/test_income.py`

**Interfaces:**
- Consumes: FastAPI routers, `get_db` session
- Produces:
  - `GET /v1/farms/{farm_id}/income/profile`: Retrieve prefilled resource profile.
  - `PUT /v1/farms/{farm_id}/income/profile`: Update and persist resource profile.
  - `POST /v1/farms/{farm_id}/income/discover`: Discover prioritized opportunities starting with ₹0 cash and cost-saving options.
  - `POST /v1/farms/{farm_id}/income/scenarios`: Compute transparent 3-scenario financial simulation.
  - `POST /v1/farms/{farm_id}/income/compare`: Compare up to 3 feasible candidates using the unified financial service.
  - `POST /v1/farms/{farm_id}/income/plans`: Save an opportunity plan.
  - `GET /v1/farms/{farm_id}/income/plans`: List saved farmer plans.

- [ ] **Step 1: Write failing API route tests**
Test all routes with diverse farmer profiles:
1. Zero budget farmer.
2. Low-budget farmer (₹5,000).
3. Medium budget farmer (₹50,000).
4. Save, retrieve, and update plan workflows.

- [ ] **Step 2: Run test to verify it fails**
Run: `python -m pytest backend/tests/test_income.py -v`
Expected: FAIL (endpoints missing)

- [ ] **Step 3: Implement router updates**
Wire endpoints in `backend/app/api/v1/endpoints/income.py` with thorough validation, clean Pydantic responses, and error handling.

- [ ] **Step 4: Run test to verify it passes**
Run: `python -m pytest backend/tests/test_income.py -v`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add backend/app/api/v1/endpoints/income.py backend/tests/test_income.py
git commit -m "feat(income): add discovery, profile management, comparison, and saved plan API routes"
```

---

### Task 6: Frontend API Service & Farm Models Rebuild

**Files:**
- Modify: `flutter_client/lib/models/farm_models.dart`
- Modify: `flutter_client/lib/services/api_service.dart`
- Create: `flutter_client/test/income_models_test.dart`

**Interfaces:**
- Consumes: Backend income REST API
- Produces: Clean immutable Dart models (`FarmerResourceProfile`, `DiscoveredOpportunity`, `OpportunityFinancialAnalysis`, `SavedIncomePlan`) and typed `ApiService` client methods.

- [ ] **Step 1: Write failing Dart unit tests for income models**
Test deserialization of 5-category opportunities, zero-budget profiles, 12-month cash flows, and saved plans.

- [ ] **Step 2: Run test to verify it fails**
Run: `cd flutter_client; & "C:\Users\verni\flutter\bin\flutter.bat" test test/income_models_test.dart`
Expected: FAIL

- [ ] **Step 3: Implement Dart models and ApiService methods**
Update `flutter_client/lib/models/farm_models.dart` and `flutter_client/lib/services/api_service.dart` with robust parsing, defensive defaults, and typed signatures.

- [ ] **Step 4: Run test to verify it passes**
Run: `cd flutter_client; & "C:\Users\verni\flutter\bin\flutter.bat" test test/income_models_test.dart`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add flutter_client/lib/models/farm_models.dart flutter_client/lib/services/api_service.dart flutter_client/test/income_models_test.dart
git commit -m "feat(flutter): update income domain models and ApiService integration"
```

---

### Task 7: Farmer-First UI Screen Redesign (7 Guided Screens)

**Files:**
- Modify: `flutter_client/lib/screens/extra_income_screen.dart`
- Modify: `flutter_client/test/widget_test.dart`

**Interfaces:**
- Consumes: `ApiService`, `AppState`
- Produces: 7-part simplified farmer experience:
  1. Start Overview ("Find ways to earn more from your farm").
  2. Your Resources Sheet (prefilled, editable, ₹0-friendly chips & inputs).
  3. Discovery Feed grouped by Zero-Cash/Savings, Low Investment, Scaled Enterprises, Alternative Crops.
  4. Transparent Opportunity Cards with reasons and verified status.
  5. Interactive Opportunity Details with cash-flow bar chart, assumptions expander, and risk alerts.
  6. Side-by-side comparison matrix with synchronized metrics.
  7. Save / Reopen Plan dialog and persistence.

- [ ] **Step 1: Write failing widget test for redesigned Extra Income UI**
Test:
1. Extra income screen renders ₹0 starting option and zero-cash opportunity chips.
2. No `98% Fit` badge anywhere in widget tree.
3. Budget of ₹15,000 does NOT show Osmanabadi goat as affordable.
4. Opportunity card profit matches comparison table profit for mushroom.

- [ ] **Step 2: Run test to verify it fails**
Run: `cd flutter_client; & "C:\Users\verni\flutter\bin\flutter.bat" test`
Expected: FAIL

- [ ] **Step 3: Implement redesigned `ExtraIncomeScreen`**
Build clean, accessible widgets following `flutter-build-responsive-layout` with centered constraints, clear touch targets, and progressive disclosure.

- [ ] **Step 4: Run test to verify it passes**
Run: `cd flutter_client; & "C:\Users\verni\flutter\bin\flutter.bat" test`
Expected: PASS

- [ ] **Step 5: Commit**
```bash
git add flutter_client/lib/screens/extra_income_screen.dart flutter_client/test/widget_test.dart
git commit -m "feat(ui): complete farmer-first rebuild of extra income screen with progressive discovery"
```

---

### Task 8: End-to-End Verification, Documentation & Playwright Audit

**Files:**
- Create: `scripts/verify_income_engine.py`
- Modify: `docs/PPT_REQUIREMENTS_TRACEABILITY.md`
- Create: `docs/EXTRA_INCOME_ENGINE_METHODOLOGY.md`

**Interfaces:**
- Consumes: Running FastAPI server and Flutter Web app
- Produces: Full verification report, Playwright visual screenshots of ₹0, ₹5k, and ₹50k workflows, and comprehensive technical documentation.

- [ ] **Step 1: Write and run verification script**
Execute Playwright test covering:
- Farmer opens Extra Income with ₹0 budget -> sees zero-cash composting and byproduct options.
- Farmer adjusts budget to ₹15,000 -> sees micro-vermicomposting and nursery options; goat rearing flagged as requiring additional capital.
- Farmer views detail view and comparison table -> confirms figures match exactly.

- [ ] **Step 2: Run full quality gates**
1. `python -m pytest backend/tests/ -v` (all tests passing)
2. `cd flutter_client; & "C:\Users\verni\flutter\bin\flutter.bat" analyze --no-fatal-warnings --no-fatal-infos` (0 errors)
3. `cd flutter_client; & "C:\Users\verni\flutter\bin\flutter.bat" test` (all passing)
4. `cd flutter_client; & "C:\Users\verni\flutter\bin\flutter.bat" build web --release` (successful compilation)
5. `python scripts/scan_secrets.py` (0 secrets detected)

- [ ] **Step 3: Document methodology and update traceability matrix**
Create `docs/EXTRA_INCOME_ENGINE_METHODOLOGY.md` detailing the 5-category framework, feasibility math, cashflow formulas, and NABARD/Agmarknet provenance.

- [ ] **Step 4: Commit and finalize**
```bash
git add scripts/verify_income_engine.py docs/EXTRA_INCOME_ENGINE_METHODOLOGY.md docs/PPT_REQUIREMENTS_TRACEABILITY.md
git commit -m "docs(income): add complete extra income methodology and traceability documentation"
```
