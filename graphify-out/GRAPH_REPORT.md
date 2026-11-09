# Graph Report - Rashkar  (2026-11-09)

## Corpus Check
- 132 files · ~338,000 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: (none) 10, .example 1, .csv 1)

## Summary
- 1784 nodes · 3164 edges · 78 communities (69 shown, 9 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 240 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `89b0cd02`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Rashkar — Yield Intelligence & Heat-Risk Intelligence
- Rashkar — Dataset Register and Usage Guide
- 3. Yield Intelligence datasets
- Yield Risk Assessment
- test_risk_engine_edge_cases.py
- farm_models.dart
- 5. Heat-Risk Intelligence datasets
- heat_ml_pipeline.py
- 2. Shared datasets — both Yield Intelligence and Heat-Risk Intelligence
- 8. Quality assurance and acceptance checks
- test_browser_journeys.py
- 7. Canonical feature tables to create
- Rashkar — Architectural Execution Plan & Implementation Blueprint
- conftest.py
- fastapi_testclient
- heat_safety_screen.dart
- ForecastGridCache
- api_service.dart
- farms.py
- endpoints/income.py
- farm_registration_screen.dart
- worker_heat_engine.py
- extra_income_screen.dart
- edit_profile_screen.dart
- home_screen.dart
- now_utc
- app_state.dart
- config.py
- test_heat_defect_corrections.py
- main.dart
- Rashkar — Climate-Smart Agriculture Platform
- test_ppt_alignment.py
- RegistryService
- insurer_dashboard_screen.dart
- my_crop_screen.dart
- yield_risk_engine.py
- crop_loss_screen.dart
- endpoints/pmfby.py
- registry_service.py
- DatasetRegisterRequest
- acquire_agera5_multivar.py
- dashboard_screen.dart
- ask_rashkar_screen.dart
- PmfbyVisionService
- scan_secrets.py
- Model Card 1: XGBoost Fast WBGT Predictor
- 2. CI Failure Investigation & Root Cause Analysis
- State
- assistant_chat
- RASHKAR — Yield Intelligence Methodology
- 2. Worker Occupational Heat Risk Methodology
- acquire_imd_1991_2019.py
- os
- session.py
- get_canonical_crops
- RASHKAR — GitHub Pre-Push & Release Verification Report
- RASHKAR — Income Diversification Methodology
- package:flutter/material.dart
- test_feature_completion_journeys.py
- AGENTS.md — Repository Operating Guide & Engineering Governance
- manifest.json
- Rashkar Historical Dataset Foundation & Acquisition Status
- Official Hackathon Presentation Text (Total Pages: 8)
- main.py
- WeatherService
- RASHKAR — Deployment Guide
- RASHKAR — Feature Audit Before Implementation
- 6. Dataset acquisition order and exact processing workflow
- RASHKAR — Yield Intelligence Scope, Baselines & Scientific Boundaries
- 11. What is sufficient to begin and what blocks validated claims?
- 1. How to read this register
- assess_crop_heat_risk
- Settings
- rashkar_farmer
- app_localizations.dart
- rashkar

## God Nodes (most connected - your core abstractions)
1. `RegistryService` - 43 edges
2. `now_utc()` - 37 edges
3. `DatasetRegisterRequest` - 36 edges
4. `FarmModel` - 29 edges
5. `2. Pre-Implementation Audit Matrix` - 29 edges
6. `CropHeatEngine` - 27 edges
7. `UnifiedSoilProfile` - 22 edges
8. `CropNetService` - 21 edges
9. `3. Yield Intelligence datasets` - 19 edges
10. `FarmPlotModel` - 19 edges

## Surprising Connections (you probably didn't know these)
- `1.1 Non-negotiable principles` --references--> `UnifiedSoilProfile`  [INFERRED]
  01_Rashkar_Feature_Blueprint.md → backend/app/schemas/soil.py
- `11. Decisions required from the repository-specific execution plan` --references--> `UnifiedSoilProfile`  [INFERRED]
  01_Rashkar_Feature_Blueprint.md → backend/app/schemas/soil.py
- `Yield Intelligence + Heat-Risk Intelligence` --references--> `UnifiedSoilProfile`  [INFERRED]
  02_Rashkar_Dataset_Register_and_Usage.md → backend/app/schemas/soil.py
- `SOIL-01. CropNet `UnifiedSoilProfile`` --references--> `UnifiedSoilProfile`  [INFERRED]
  02_Rashkar_Dataset_Register_and_Usage.md → backend/app/schemas/soil.py
- `Data Inputs & Provenance Dependencies` --references--> `UnifiedSoilProfile`  [INFERRED]
  docs/EXECUTION_PLAN.md → backend/app/schemas/soil.py

## Import Cycles
- None detected.

## Communities (78 total, 9 thin omitted)

### Community 0 - "Rashkar — Yield Intelligence & Heat-Risk Intelligence"
Cohesion: 0.05
Nodes (41): 10. Explicitly out of scope for this phase, 11. Decisions required from the repository-specific execution plan, 1.1 Non-negotiable principles, 1.2 Initial geography and coverage policy, 1. Product vision and operating principles, 3.1 Purpose, 3.2 Worker heat-risk pathway, 3.3 Crop heat-risk pathway (+33 more)

### Community 1 - "Rashkar — Dataset Register and Usage Guide"
Cohesion: 0.25
Nodes (7): 10. Recommended data storage layout, 4. Soil dataset dependency — CropNet is the source of record, 9. Access-request checklist and data request template, Rashkar — Dataset Register and Usage Guide, SOIL-01. CropNet `UnifiedSoilProfile`, SOIL-02. SoilGrids 2.0 — optional source validation only, Yield Intelligence + Heat-Risk Intelligence

### Community 2 - "3. Yield Intelligence datasets"
Cohesion: 0.11
Nodes (19): 3. Yield Intelligence datasets, Y-01. Maharashtra district/season/crop APY, Y-02. Official OGD district-wise, season-wise crop production statistics, Y-03. Crop-specific APY collection, Y-04. DES APY report/query interface, Y-05. Maharashtra State Data Bank agricultural raw data, Y-06. Horticulture statistics collection, Y-07. Crop calendar — MIRCA-OS (+11 more)

### Community 3 - "Yield Risk Assessment"
Cohesion: 0.08
Nodes (23): BHOOMI soil and land-resource layers, Dataset 10 — Bhuvan Pest and Disease Surveillance, Dataset 1 — Maharashtra district-wise, crop-wise Area, Production and Yield (APY), Dataset 2 — District-wise, season-wise crop production statistics, Dataset 3 — Crop-specific APY collection, Dataset 4 — Maharashtra State Data Bank: agricultural raw data, Dataset 5 — Horticulture crop statistics, Dataset 6 — Pune district soil macro-nutrient dataset (+15 more)

### Community 4 - "test_risk_engine_edge_cases.py"
Cohesion: 0.07
Nodes (34): 2.1 Purpose, 2.2 Feature scope, 2.3 Farmer inputs and profile, 2.4 Risk components and technical approach, 2.5 Yield Intelligence outputs, 2.6 Farmer-facing screens, 2. Feature One — Yield Intelligence, A. Weather and climate risk (+26 more)

### Community 5 - "farm_models.dart"
Cohesion: 0.01
Nodes (287): ActionableRecommendationItem, activeAlerts, activeCropCode, activeCropName, advice, affectedAreaAcres, agronomistReviewer, airTempC (+279 more)

### Community 6 - "5. Heat-Risk Intelligence datasets"
Cohesion: 0.20
Nodes (10): 5. Heat-Risk Intelligence datasets, H-01. ERA5-HEAT — UTCI and Mean Radiant Temperature, H-02. MODIS daily land-surface temperature — MOD11A1, H-03. NOAA GFS forecast, H-04. IMD current observation, nowcast and forecast, H-05. Historical hourly weather for WBGT estimation, H-06. Occupational heat labour-capacity dataset, H-07. Indian outdoor worker WBGT study — request data, not direct bulk download (+2 more)

### Community 7 - "heat_ml_pipeline.py"
Cohesion: 0.06
Nodes (13): HeatMLPipeline, WBGTLSTMModel, actual_vapor_pressure_kpa(), calculate_wbgt(), dew_point_c(), solve_black_globe_temp(), solve_natural_wet_bulb(), balance() (+5 more)

### Community 8 - "2. Shared datasets — both Yield Intelligence and Heat-Risk Intelligence"
Cohesion: 0.29
Nodes (7): 2. Shared datasets — both Yield Intelligence and Heat-Risk Intelligence, S-01. AgERA5 v2 — daily agrometeorological indicators, S-02. ERA5-Land — hourly land reanalysis, S-03. IMD daily gridded rainfall — 0.25°, S-04. IMD public weather APIs, S-05. Survey of India / administrative boundary layers, S-06. NOAA GFS 0.25° forecast — optional supplementary forecast

### Community 9 - "8. Quality assurance and acceptance checks"
Cohesion: 0.29
Nodes (7): 8. Quality assurance and acceptance checks, APY and crop statistics, Crop calendar and recommendations, Heat, Pest/disease, Soil/CropNet, Weather

### Community 10 - "test_browser_journeys.py"
Cohesion: 0.06
Nodes (39): 1. Audit Objective and Scope, 2. Defect Resolution Audit, 3. End-to-End Verification Across the 7 Acceptance Gates, 4. Test Metric Comparison Summary, 5. Conclusion, Gate A: Profile Editing & Dynamic Recalculation, Gate B: Dynamic Worker Heat Risk (Liljegren WBGT), Gate C: Dynamic Crop Heat Risk (ICAR Stage Thresholds) (+31 more)

### Community 11 - "7. Canonical feature tables to create"
Cohesion: 0.33
Nodes (6): 7.1 `weather_daily_features`, 7.2 `weather_hourly_features`, 7.3 `crop_cycle_features`, 7.4 `pest_disease_events`, 7.5 `worker_heat_validation`, 7. Canonical feature tables to create

### Community 12 - "Rashkar — Architectural Execution Plan & Implementation Blueprint"
Cohesion: 0.04
Nodes (44): A.1 Current Environment and Runtime Status, A.2 Inspected File Inventory, A.3 Existing Services, Models & Technical Debt Analysis, A.4 Graphify Structural Insights, A. Repository Audit & Technical Baseline, B.1 Distinguishing the Four Architectural Tiers, B. Scope Differentiation & Geographical Staging, C.1 Foundational Security, Privacy & Data Minimisation (+36 more)

### Community 13 - "conftest.py"
Cohesion: 0.13
Nodes (23): init_db(), seed_advisories(), seed_agronomic_thresholds(), seed_canonical_crops(), seed_crop_stages(), seed_demo_farmer_and_farm(), seed_income_opportunities(), AssistantMessageModel (+15 more)

### Community 14 - "fastapi_testclient"
Cohesion: 0.06
Nodes (28): test_assistant_chat_crop_question(), test_assistant_chat_grounded_response(), test_complete_farmer_journey_e2e(), test_farm_profile_update_e2e(), test_calculate_income_scenario_deterministic(), test_calculate_scenario_invalid_opportunity(), test_filter_income_opportunities_by_crop(), test_get_income_opportunities() (+20 more)

### Community 15 - "heat_safety_screen.dart"
Cohesion: 0.06
Nodes (33): CropHeatAssessment, WorkerHeatResponse, build, _buildCropVulnerabilityScore, _buildDailyOutlookTile, _buildHourlyTimelinePill, _buildIndexComparisonTile, _buildInterventionCard (+25 more)

### Community 16 - "ForecastGridCache"
Cohesion: 0.08
Nodes (16): ForecastGridCache, test_forecast_grid_cache_cadence_and_alerts(), 1. Executive Summary & PPT Alignment, 2. Multi-Index Thermal Safety Suite, 3. Spatial Resolution & Topographic Downscaling, 4. 30-Minute Cadence Grid Caching & Alert Lifecycle, 5. Explainable 0–100 Personalized Heat Risk Scores, 6. Machine Learning Staged Pipeline Performance (+8 more)

### Community 17 - "api_service.dart"
Cohesion: 0.06
Nodes (25): _apiHost, ApiService, baseUrl, _cachedSummary, calculateIncomeScenario, compareOpportunities, getAllFarms, getCropHeatHazard (+17 more)

### Community 18 - "farms.py"
Cohesion: 0.18
Nodes (21): add_plot(), create_crop_cycle(), create_farm(), create_farmer(), get_farm(), get_farm_summary(), get_farmer(), get_farmer_farms() (+13 more)

### Community 19 - "endpoints/income.py"
Cohesion: 0.15
Nodes (13): calculate_income_scenario(), compare_selected_opportunities(), CompareOpportunitiesRequest, get_opportunities(), match_opportunities_to_farmer(), ScenarioCalculateRequest, EnterpriseFinancialAnalysis, FarmerResourceProfile (+5 more)

### Community 20 - "farm_registration_screen.dart"
Cohesion: 0.06
Nodes (31): build, _buildSummaryRow, createState, _crops, _currentStep, _districts, _farmerNameController, _farmNameController (+23 more)

### Community 21 - "worker_heat_engine.py"
Cohesion: 0.14
Nodes (13): assess_worker_heat_hazard(), HourlyHeatRiskProjection, WorkerHeatAssessmentRequest, WorkerHeatAssessmentResponse, calculate_dew_point(), WorkerHeatEngine, test_missing_solar_graceful_handling(), test_shift_duration_longer_than_forecast_coverage() (+5 more)

### Community 22 - "extra_income_screen.dart"
Cohesion: 0.06
Nodes (30): IncomeScenario, ScoredOpportunityItem, _availableInvestment, _availableLand, build, _buildComparisonCard, _buildFinancialSimulatorCard, _buildMarketBenchmarkCard (+22 more)

### Community 23 - "edit_profile_screen.dart"
Cohesion: 0.06
Nodes (29): build, _buildSectionHeader, createState, _crops, dispose, _districts, farm, _farmerNameController (+21 more)

### Community 24 - "home_screen.dart"
Cohesion: 0.08
Nodes (21): build, _buildHistoryTab, _buildCropHeatTab, build, _buildAlertItem, _buildAskRashkarBanner, _buildCleanStartScreen, _buildFarmGlanceCard (+13 more)

### Community 25 - "now_utc"
Cohesion: 0.14
Nodes (10): health_check(), format_ist_iso(), now_ist(), now_utc(), to_ist(), AgronomicAdvisoryCatalogueModel, CanonicalCropMasterModel, CropStageReferenceModel (+2 more)

### Community 26 - "app_state.dart"
Cohesion: 0.07
Nodes (20): FarmSummary, activeCropCode, activeCropName, _activeFarm, activeFarmerId, activeFarmId, activeLatitude, activeLongitude (+12 more)

### Community 27 - "config.py"
Cohesion: 0.15
Nodes (7): acquire_apy_dataset(), acquire_maharashtra_boundaries(), inspect_html(), acquire_imd_rainfall_year(), acquire_mirca_calendar(), compute_sha256(), download_file()

### Community 28 - "test_heat_defect_corrections.py"
Cohesion: 0.20
Nodes (14): CropHeatAssessmentRequest, CropHeatAssessmentResponse, CropHeatIntervention, DailyCropHeatOutlook, CropHeatEngine, create_isolated_farm(), test_audited_interventions_and_infrastructure_distinction(), test_database_log_history_retrieval() (+6 more)

### Community 29 - "main.dart"
Cohesion: 0.08
Nodes (16): build, createState, _currentIndex, main, RashkarFarmerApp, _screens, actions, build (+8 more)

### Community 30 - "Rashkar — Climate-Smart Agriculture Platform"
Cohesion: 0.08
Nodes (24): 1. Overview, 2. Integrated Dataset Catalog, 3. Storage Hierarchy and Immutability Safeguards, RASHKAR — Data Source Register & Provenance, 1. What Rashkar Does, 2. Architecture Overview, 3. Prerequisites, 4. Quick Start & Setup (+16 more)

### Community 31 - "test_ppt_alignment.py"
Cohesion: 0.12
Nodes (12): apply_topographic_lapse_downscaling(), calculate_noaa_heat_index(), calculate_utci_approx(), compute_crop_heat_vulnerability_score(), compute_personalized_worker_heat_strain_score(), test_crop_heat_vulnerability_score_decomposition(), test_noaa_heat_index_calculations(), test_pmfby_claim_and_reviewer_flow_e2e() (+4 more)

### Community 32 - "RegistryService"
Cohesion: 0.14
Nodes (6): get_dataset(), list_registered_datasets(), register_dataset(), RegistryService, test_registry_lifecycle(), generate_derived_reference_periods()

### Community 33 - "insurer_dashboard_screen.dart"
Cohesion: 0.09
Nodes (22): build, _buildCaseDetail, _buildEmptyState, _buildEvidenceSection, _buildIndexCard, _buildMetricTile, _buildQueueList, _buildSlaBadge (+14 more)

### Community 34 - "my_crop_screen.dart"
Cohesion: 0.09
Nodes (22): _assessment, build, _buildActionCard, _buildHistoricalBaselineCard, _buildMLGateBanner, _buildNarrativeCard, _buildRecommendationsSection, _buildRiskDimensionCard (+14 more)

### Community 35 - "yield_risk_engine.py"
Cohesion: 0.21
Nodes (8): get_yield_risk(), ActionableRecommendation, HistoricalYieldBaseline, RiskItem, SoilSuitabilityAnalysis, YieldRiskResponse, _extract_soil_prop(), YieldRiskEngine

### Community 36 - "crop_loss_screen.dart"
Cohesion: 0.10
Nodes (17): _affectedAcres, _buildFormTab, _cases, createState, _cropCode, _damagePct, dispose, _eventDate (+9 more)

### Community 37 - "endpoints/pmfby.py"
Cohesion: 0.24
Nodes (11): _build_case_response(), create_crop_loss_case(), CropLossCaseResponse, CropLossCreateRequest, get_crop_loss_case(), get_farmer_cases(), get_reviewer_queue(), review_crop_loss_case() (+3 more)

### Community 38 - "registry_service.py"
Cohesion: 0.19
Nodes (4): DatasetRegistryModel, process_era5_land_file(), standardize_and_register_era5(), build_canonical_apy_v2()

### Community 39 - "DatasetRegisterRequest"
Cohesion: 0.18
Nodes (8): DatasetRegisterRequest, DatasetRegistryResponse, ProvenanceEnvelope, acquire_or_register_agera5(), check_cds_credentials(), acquire_and_process_boundaries(), classify_mumbai_tract(), register_pending_institutional_datasets()

### Community 40 - "acquire_agera5_multivar.py"
Cohesion: 0.15
Nodes (6): acquire_all_agera5_variables(), download_agera5_variable(), verify_and_register_agera5(), compute_sha256(), download_agera5_daily(), download_era5_land_heat_season()

### Community 41 - "dashboard_screen.dart"
Cohesion: 0.11
Nodes (13): YieldAssessment, _assessment, build, createState, DashboardScreen, _DashboardScreenState, _getIconForDimension, _getTitleForDimension (+5 more)

### Community 42 - "ask_rashkar_screen.dart"
Cohesion: 0.11
Nodes (15): build, _buildMessageBubble, createState, dispose, initState, _initWelcome, _isSending, _messages (+7 more)

### Community 43 - "PmfbyVisionService"
Cohesion: 0.14
Nodes (7): PmfbyVisionService, 1. Executive Summary, 3. Core Pillar 2 Verification: Plot-Level PMFBY Crop Loss Verification, 4. Test Suite Execution Logs, 5. Playwright Browser Visual Evidence Directory, 6. Conclusion, RASHKAR — Official Hackathon Presentation Alignment Test Report

### Community 44 - "scan_secrets.py"
Cohesion: 0.19
Nodes (8): get_token(), monitor(), dump_job_log(), get_github_token(), NoAuthRedirectHandler, scan_git_history(), scan_text(), scan_working_tree()

### Community 45 - "Model Card 1: XGBoost Fast WBGT Predictor"
Cohesion: 0.11
Nodes (17): Feature Importances, Intended Use, Intended Use, Model Card 1: XGBoost Fast WBGT Predictor, Model Card 2: Random Forest Worker Personalization Classifier, Model Card 3: PyTorch LSTM WBGT Trajectory Predictor, Model Card 4: PMFBY Multimodal Vision AI Pipeline (YOLOv8 + U-Net + ViT), Multimodal Fusion Weights (+9 more)

### Community 46 - "2. CI Failure Investigation & Root Cause Analysis"
Cohesion: 0.12
Nodes (16): 1. Executive Summary, 2.1 Incident Details, 2.2 Error Log Extraction, 2.3 Diagnostic Explanation, 2.4 Resolution Applied, 2. CI Failure Investigation & Root Cause Analysis, 3.1 The Two-Stream Branch Model, 3.2 README Synchronization Verification (+8 more)

### Community 47 - "State"
Cohesion: 0.17
Nodes (14): MainNavigationShell, _MainNavigationShellState, AskRashkarScreen, _AskRashkarScreenState, CropLossScreen, _CropLossScreenState, EditProfileScreen, _EditProfileScreenState (+6 more)

### Community 48 - "assistant_chat"
Cohesion: 0.13
Nodes (5): assistant_chat(), call_local_ollama(), ChatMessageRequest, ChatMessageResponse, generate_grounded_template_answer()

### Community 49 - "RASHKAR — Yield Intelligence Methodology"
Cohesion: 0.12
Nodes (15): 1. Core Principle & Ethical Scientific Stance, 2.1 Data Ingestion and Cleansing, 2.2 Statistical Distribution Metrics, 2.3 Sparse Sample Safe Fallback Logic, 2. Historical Baseline Formulation (APY Dataset), 3. CropNet Synthetic Soil Profile Adapter, 4.1 Thermal Heat Stress Score ($S_{\text{heat}}$), 4.2 Moisture / Water Deficit Score ($S_{\text{water}}$) (+7 more)

### Community 50 - "2. Worker Occupational Heat Risk Methodology"
Cohesion: 0.13
Nodes (14): 1. Overview and Core Philosophy, 2.1 The Wet Bulb Globe Temperature (WBGT) Standard, 2.2 Thermodynamic Boundary Iteration (Liljegren Formulation), 2.3 ACGIH / ISO 7243 Occupational Thresholds and Work-Rest Cycles, 2.4 Work-to-Rest Recommendations, 2.5 Emergency Heat Illness Triage Protocol, 2. Worker Occupational Heat Risk Methodology, 3.1 Agronomic Thermal Thresholds (ICAR & Maharashtra State Agricultural Universities) (+6 more)

### Community 51 - "acquire_imd_1991_2019.py"
Cohesion: 0.26
Nodes (6): compute_sha256(), download_imd_year(), download_range(), verify_and_register_year(), acquire_imd_years(), download_imd_year()

### Community 52 - "os"
Cohesion: 0.19
Nodes (4): NoCacheHTTPRequestHandler, run(), run_browser_verification(), run_browser_verification()

### Community 54 - "get_canonical_crops"
Cohesion: 0.20
Nodes (6): CropItem, DistrictItem, get_canonical_crops(), get_maharashtra_districts(), get_maharashtra_talukas(), TalukaItem

### Community 55 - "RASHKAR — GitHub Pre-Push & Release Verification Report"
Cohesion: 0.17
Nodes (11): 1. Commit and Branch History, 2. Secrets and Security Audit Results, 3. Repository Hygiene & Clutter Remediation, 4. API Integrity & Preservation, 5. Verification & Test Execution Summary, 6. Continuous Integration (GitHub Actions), 7. Status & Readiness, Backend Tests (Pytest) (+3 more)

### Community 56 - "RASHKAR — Income Diversification Methodology"
Cohesion: 0.17
Nodes (11): 1. Objective and Approach, 2.1 NABARD Maharashtra FY26-27 Unit Costs, 2.2 Agmarknet / OGD Daily Wholesale Price Benchmarks, 2. Institutional Data Foundations, 3. Farmer Resource Filtering Architecture, 4.1 Scenario Specifications, 4.2 Key Financial Output Metrics, 4. Three-Scenario Financial Simulation Engine (+3 more)

### Community 58 - "test_feature_completion_journeys.py"
Cohesion: 0.17
Nodes (6): setup_module(), test_crop_heat_risk_dynamic_stage_recalculation(), test_frontend_full_browser_experience(), test_income_diversification_catalog_matching_and_scenarios(), test_worker_heat_risk_dynamic_api(), test_yield_intelligence_apy_and_soil_provenance()

### Community 59 - "AGENTS.md — Repository Operating Guide & Engineering Governance"
Cohesion: 0.18
Nodes (10): 1. Project Mission & Core Architectural Pillars, 2. Strict Data & AI Engineering Rules, 3. Engineering Quality Gates & Testing Standards, 4. Git Branch Governance & Release Protocol, AGENTS.md — Repository Operating Guide & Engineering Governance, Branch Responsibilities, Pillar 1: Personalized Farm-Level Heat-Risk AI, Pillar 2: Plot-Level PMFBY Crop-Loss Verification (+2 more)

### Community 60 - "manifest.json"
Cohesion: 0.18
Nodes (10): background_color, description, display, icons, name, orientation, prefer_related_applications, short_name (+2 more)

### Community 61 - "Rashkar Historical Dataset Foundation & Acquisition Status"
Cohesion: 0.20
Nodes (9): 1. Executive Summary, 2. Dataset Inventory & Provenance Register, 3.1 IMD Pune Climate Normals vs Agricultural Baselines, 3.2 ERA5-Land Reanalysis Standardisation & Liljegren WBGT, 3.3 Unit Harmonisation & Reconciliation for Maharashtra APY, 3. Methodological & Scientific Standards Applied, 4. Operational File Locations & Storage Architecture, Rashkar Historical Dataset Foundation & Acquisition Status (+1 more)

### Community 62 - "Official Hackathon Presentation Text (Total Pages: 8)"
Cohesion: 0.20
Nodes (9): Official Hackathon Presentation Text (Total Pages: 8), === PAGE 1 ===, === PAGE 2 ===, === PAGE 3 ===, === PAGE 4 ===, === PAGE 5 ===, === PAGE 6 ===, === PAGE 7 === (+1 more)

### Community 63 - "main.py"
Cohesion: 0.25
Nodes (3): docs_redirect(), lifespan(), root()

### Community 64 - "WeatherService"
Cohesion: 0.25
Nodes (3): CanonicalWeatherObservation, HourlyForecastPoint, WeatherService

### Community 65 - "RASHKAR — Deployment Guide"
Cohesion: 0.25
Nodes (7): 1. System Architecture, 2. Docker Compose Deployment, 3. Manual Production Deployment, 4. Security Considerations, Backend (Systemd / Uvicorn), Frontend (Nginx / Flutter Web Release), RASHKAR — Deployment Guide

### Community 66 - "RASHKAR — Feature Audit Before Implementation"
Cohesion: 0.33
Nodes (5): 1. Executive Summary & Baseline State, 3. Identified Production Defects to Fix, 4. Architecture and Data Flow, Baseline Test Execution Results (Pre-Change), RASHKAR — Feature Audit Before Implementation

### Community 67 - "6. Dataset acquisition order and exact processing workflow"
Cohesion: 0.40
Nodes (5): 6. Dataset acquisition order and exact processing workflow, Batch A — start immediately, Batch B — crop and soil integration, Batch C — external access requests, Batch D — Heat-Risk validation pilot

### Community 68 - "RASHKAR — Yield Intelligence Scope, Baselines & Scientific Boundaries"
Cohesion: 0.40
Nodes (4): 1. Role Within Rashkar Architecture, 2. Permitted Capabilities (Verified in Prototype), 3. Explicit Prohibitions & Out-of-Scope Elements, RASHKAR — Yield Intelligence Scope, Baselines & Scientific Boundaries

### Community 69 - "11. What is sufficient to begin and what blocks validated claims?"
Cohesion: 0.50
Nodes (4): 11. What is sufficient to begin and what blocks validated claims?, Can start a transparent rule-based first release, Can start the first data pipeline, Still needed for stronger supervised models and validation

### Community 70 - "1. How to read this register"
Cohesion: 0.50
Nodes (4): 1. How to read this register, Availability labels, Priority labels, Required dataset manifest fields

## Knowledge Gaps
- **556 isolated node(s):** `AppStrings`, `_currentIndex`, `_screens`, `main`, `build` (+551 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1137 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `UnifiedSoilProfile` connect `test_risk_engine_edge_cases.py` to `Rashkar — Yield Intelligence & Heat-Risk Intelligence`, `Rashkar — Dataset Register and Usage Guide`, `yield_risk_engine.py`, `Rashkar — Architectural Execution Plan & Implementation Blueprint`?**
  _High betweenness centrality (0.160) - this node is a cross-community bridge._
- **Are the 22 inferred relationships involving `RegistryService` (e.g. with `get_dataset()` and `list_registered_datasets()`) actually correct?**
  _`RegistryService` has 22 INFERRED edges - model-reasoned connections that need verification._
- **What connects `AppStrings`, `_currentIndex`, `_screens` to the rest of the system?**
  _556 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Rashkar — Yield Intelligence & Heat-Risk Intelligence` be split into smaller, more focused modules?**
  _Cohesion score 0.047619047619047616 - nodes in this community are weakly interconnected._
- **Why does `Rashkar — Dataset Register and Usage Guide` connect `Rashkar — Dataset Register and Usage Guide` to `3. Yield Intelligence datasets`, `6. Dataset acquisition order and exact processing workflow`, `11. What is sufficient to begin and what blocks validated claims?`, `1. How to read this register`, `5. Heat-Risk Intelligence datasets`, `2. Shared datasets — both Yield Intelligence and Heat-Risk Intelligence`, `8. Quality assurance and acceptance checks`, `7. Canonical feature tables to create`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `DatasetRegisterRequest` (e.g. with `register_dataset()` and `RegistryService`) actually correct?**
  _`DatasetRegisterRequest` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Should `3. Yield Intelligence datasets` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._