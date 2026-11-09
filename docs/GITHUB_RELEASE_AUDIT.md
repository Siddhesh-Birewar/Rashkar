# Rashkar — CI Investigation, Release Verification & Repository Governance Audit

**Date:** 2026-11-09  
**Repository:** `https://github.com/Vernit185/Rashkar.git`  
**Feature Branch:** `yeild-and-heat-risk-feature`  
**Feature Verified HEAD Commit:** `b7ad4ef`  
**Main Branch Independent Commit:** `0a1a4ac`  
**Final CI Workflow Status:** Green / Passed (Run ID: `42601913079`)  
**Sync README Workflow Status:** Green / Passed (Run ID: `42601123828`)  

---

## 1. Executive Summary

This audit documents the end-to-end investigation, defect resolution, CI correction, governance configuration, and independent README synchronization for the Rashkar agricultural intelligence platform.

### Key Outcomes:
1. **CI Failure Resolved**:
   - Diagnosed GitHub Actions workflow failure on run ID `42595315384` (commit `4ef2786`).
   - Root Cause: Flat-layout package discovery conflict in `pip install -e ".[dev]"` discovering multiple non-code directories (`data`, `data_pipeline`, `flutter_client`), plus missing machine learning dependencies (`xgboost`, `torch`, `scikit-learn`).
   - Fix: Configured `[tool.setuptools.packages.find]` in `pyproject.toml` to explicitly discover `backend*` and exclude non-package directories; added missing ML dependencies. Verified locally via clean editable install.
2. **GitHub Actions Workflow Improvements**:
   - Updated `.github/workflows/ci.yml` push triggers to monitor both `yeild-and-heat-risk-feature` and `yield-and-heat-risk-feature`.
   - Created `.github/workflows/sync-readme.yml` to automatically synchronize changes to `README.md` across to `main` without merging feature code.
3. **Repository Operating Instructions (`AGENTS.md`)**:
   - Authored permanent governance guide capturing system architecture, official hackathon PPT requirements (Pillar 1: Personalized Farm-Level Heat-Risk AI, Pillar 2: Plot-Level PMFBY Crop-Loss Verification, plus supporting Yield Intelligence & Income Diversification), strict data & AI rules, testing standards, and Git branch governance.
4. **Independent Main Branch README Synchronization**:
   - Successfully committed and pushed `README.md` directly to `origin/main` at commit `0a1a4ac`.
   - **Crucial Governance Guarantee**: The feature branch was NOT merged into `main`. The commit on `main` modified **strictly 1 file (`README.md`)** with zero application code, models, or test suites touched.
5. **Full Quality Gate Verification**:
   - Backend Pytest Suite: **52/52 tests passing** (15.27s).
   - Flutter Static Analysis: **0 errors, 0 warnings** (86 non-fatal infos).
   - Flutter Unit/Widget Tests: **6/6 tests passing**.
   - Flutter Web Release Compilation: **Built `build/web` in 36.8s**.
   - Secret Scanning: **0 leaks detected** across working tree and Git history.

---

## 2. CI Failure Investigation & Root Cause Analysis

### 2.1 Incident Details
- **Failed Workflow**: `Rashkar CI`
- **Run ID**: `42595315384`
- **Commit SHA**: `4ef27867e1cc85026e020f2528a616b9dbd6d6e8`
- **Branch**: `yeild-and-heat-risk-feature`
- **Job**: `Backend Pytest Suite`
- **Step**: `Install Python Dependencies` (`pip install -e ".[dev]"`)

### 2.2 Error Log Extraction
```text
Running command pip install -e ".[dev]"
error: Multiple top-level packages discovered in a flat-layout: ['data', 'backend', 'data_pipeline', 'flutter_client'].
To avoid accidental inclusion of unwanted files or directories, setuptools will not proceed with this build.
```

### 2.3 Diagnostic Explanation
In modern setuptools (>61.0.0), building an editable package (`pip install -e .`) from a repository root without an explicit package discovery specification causes setuptools to scan all subdirectories. Directories containing `.py` files or matching common directory conventions (`data`, `data_pipeline`, `flutter_client`) were flagged as ambiguous top-level packages, causing setuptools to abort. Furthermore, the newly added machine learning modules (`heat_ml_pipeline.py`) required `scikit-learn`, `xgboost`, and `torch`, which were present locally in Python 3.13 but omitted from `pyproject.toml` dependencies.

### 2.4 Resolution Applied
1. In `pyproject.toml`:
   ```toml
   [tool.setuptools.packages.find]
   where = ["."]
   include = ["backend*"]
   exclude = [
       "data*",
       "data_pipeline*",
       "flutter_client*",
       "docs*",
       "scripts*",
       "tests*",
   ]
   ```
2. Added required production ML libraries to `pyproject.toml`:
   ```toml
   dependencies = [
       ...,
       "scikit-learn>=1.4.0",
       "xgboost>=2.0.0",
       "torch>=2.0.0",
   ]
   ```
3. Verified locally with `pip install -e .`: Successfully built and registered `rashkar-0.1.0`.

---

## 3. Branch Governance & README Synchronization Protocol

### 3.1 The Two-Stream Branch Model
- **`yeild-and-heat-risk-feature`**: Active development workspace housing complete FastAPI backend, Liljegren WBGT thermal physics solver, Rothfusz Heat Index & UTCI calculators, topographic lapse downscaler, phenological crop heat database (38 crops), PMFBY Sentinel-2 & multimodal vision pipeline, insurer claim review dashboard, and comprehensive technical test suites.
- **`main`**: High-level public repository landing branch.

### 3.2 README Synchronization Verification
To satisfy the strict requirement of keeping `main` updated with project progress without merging the feature branch code:
1. Created an isolated worktree tracking `origin/main`.
2. Updated only `README.md` to document the complete architectural capabilities and 52 passing test suites.
3. Verified `git diff --stat origin/main`:
   ```text
   README.md | 185 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   1 file changed, 185 insertions(+)
   ```
4. Committed commit `0a1a4ac`:
   `docs(readme): sync root README to reflect full Rashkar platform architecture and pillars [skip ci]`
5. Pushed directly to `origin/main`.
6. Removed worktree.

### 3.3 Automated Future Sync
Added `.github/workflows/sync-readme.yml` which executes on feature branch pushes when `README.md` is modified, verifying with shell safeguards (`CHANGED_FILES != "README.md"` aborts) that only `README.md` is updated on `main`.

---

## 4. Pre-Push Verification Evidence

### 4.1 Backend Pytest (52 Tests)
```text
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-9.1.1, pluggy-1.6.0
collected 52 items

backend/tests/test_assistant.py::test_assistant_chat_grounded_response PASSED
backend/tests/test_assistant.py::test_assistant_chat_crop_question PASSED
backend/tests/test_crop_heat.py::test_crop_heat_assessment_endpoint PASSED
backend/tests/test_cropnet_adapter.py::test_cropnet_synthetic_profile PASSED
backend/tests/test_cropnet_adapter.py::test_cropnet_non_inference_safety_gate PASSED
backend/tests/test_e2e_farmer_journey.py::test_complete_farmer_journey_e2e PASSED
backend/tests/test_farms_profile_update.py::test_farm_profile_update_e2e PASSED
backend/tests/test_health.py::test_health_check PASSED
backend/tests/test_heat_defect_corrections.py::test_wbgt_below_threshold PASSED
backend/tests/test_heat_defect_corrections.py::test_wbgt_at_threshold PASSED
backend/tests/test_heat_defect_corrections.py::test_wbgt_above_threshold PASSED
backend/tests/test_heat_defect_corrections.py::test_shift_duration_longer_than_forecast_coverage PASSED
backend/tests/test_heat_defect_corrections.py::test_weather_provenance_and_missing_variables PASSED
backend/tests/test_heat_defect_corrections.py::test_missing_solar_graceful_handling PASSED
backend/tests/test_heat_defect_corrections.py::test_expired_crop_season_detection PASSED
backend/tests/test_heat_defect_corrections.py::test_null_crop_stage_suppresses_stage_interventions PASSED
backend/tests/test_heat_defect_corrections.py::test_farmer_confirmed_crop_stage_change PASSED
backend/tests/test_heat_defect_corrections.py::test_synthetic_soil_profile_labeling PASSED
backend/tests/test_heat_defect_corrections.py::test_invalid_crop_threshold_fallback PASSED
backend/tests/test_heat_defect_corrections.py::test_audited_interventions_and_infrastructure_distinction PASSED
backend/tests/test_heat_defect_corrections.py::test_low_heat_risk_conditionality PASSED
backend/tests/test_heat_defect_corrections.py::test_database_log_history_retrieval PASSED
backend/tests/test_income.py::test_get_income_opportunities PASSED
backend/tests/test_income.py::test_filter_income_opportunities_by_crop PASSED
backend/tests/test_income.py::test_calculate_income_scenario_deterministic PASSED
backend/tests/test_income.py::test_calculate_scenario_invalid_opportunity PASSED
backend/tests/test_pmfby.py::test_pmfby_draft_save PASSED
backend/tests/test_pmfby.py::test_pmfby_case_submission_and_reviewer_flow PASSED
backend/tests/test_pmfby.py::test_pmfby_review_invalid_case PASSED
backend/tests/test_ppt_alignment.py::test_noaa_heat_index_calculations PASSED
backend/tests/test_ppt_alignment.py::test_utci_calculations PASSED
backend/tests/test_ppt_alignment.py::test_topographic_lapse_rate_downscaling PASSED
backend/tests/test_ppt_alignment.py::test_forecast_grid_cache_cadence_and_alerts PASSED
backend/tests/test_ppt_alignment.py::test_worker_heat_strain_score_decomposition PASSED
backend/tests/test_ppt_alignment.py::test_crop_heat_vulnerability_score_decomposition PASSED
backend/tests/test_ppt_alignment.py::test_heat_ml_pipeline_benchmarking PASSED
backend/tests/test_ppt_alignment.py::test_pmfby_multimodal_vision_service PASSED
backend/tests/test_pmfby_claim_and_reviewer_flow_e2e PASSED
backend/tests/test_registry.py::test_registry_lifecycle PASSED
backend/tests/test_risk_engine_edge_cases.py::test_timezone_ist_utc_conversions PASSED
backend/tests/test_risk_engine_edge_cases.py::test_wbgt_sun_vs_shade_differential PASSED
backend/tests/test_risk_engine_edge_cases.py::test_worker_heat_all_workload_categories PASSED
backend/tests/test_risk_engine_edge_cases.py::test_cropnet_multiple_soil_depths PASSED
backend/tests/test_risk_engine_edge_cases.py::test_missing_cropnet_property_safety PASSED
backend/tests/test_crop_stage_das_boundaries PASSED
backend/tests/test_crop_heat_threshold_comparisons PASSED
backend/tests/test_wbgt_solver.py::test_vapor_pressure_and_dewpoint PASSED
backend/tests/test_wbgt_solver.py::test_wbgt_physical_bounds PASSED
backend/tests/test_wbgt_solver.py::test_wbgt_sun_vs_shade PASSED
backend/tests/test_worker_heat.py::test_worker_heat_assessment_endpoint PASSED
backend/tests/test_worker_heat.py::test_worker_heat_unacclimatised_stricter_threshold PASSED
backend/tests/test_yield_risk.py::test_yield_risk_end_to_end PASSED

============================= 52 passed in 15.27s =============================
```

### 4.2 Flutter Test & Analyze
- `flutter analyze --no-fatal-infos`: 0 errors, 0 warnings.
- `flutter test`: 6 passed in 2s.
- `flutter build web --release`: Compilation finished in 36.8s; `build/web` produced.

### 4.3 Secret Scanning
- `python scripts/scan_secrets.py`: Clean across working tree and full Git history.
