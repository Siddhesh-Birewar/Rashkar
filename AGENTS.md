# AGENTS.md — Repository Operating Guide & Engineering Governance

> **Target Audience:** Autonomous AI coding agents (Antigravity, Cursor, Copilot) and human maintainers working on **Rashkar**.  
> **Repository:** `https://github.com/Vernit185/Rashkar`  
> **Primary Feature Branch:** `yeild-and-heat-risk-feature` (also tracked as `yield-and-heat-risk-feature`)  
> **Production/Release Baseline:** `main`

---

## 1. Project Mission & Core Architectural Pillars

Rashkar is an integrated agricultural intelligence and micro-climate risk platform designed for smallholders in Maharashtra, India. All engineering contributions must align with the official hackathon proposal and presentation:

### Pillar 1: Personalized Farm-Level Heat-Risk AI
- **Worker Heat Risk**: High-resolution 0–6 hour wet-bulb globe temperature (WBGT) occupational safety screening using the Liljegren et al. (2008) physics engine calibrated to ACGIH 2023 TLVs and ISO 7243:2017 screening action limits. Supports Rothfusz Heat Index, Steadman Apparent Temperature, UTCI polynomial approximations, signed threshold exceedance logic, workload screening (light, moderate, heavy, very heavy), sun vs. shade micro-climate modeling, shift duration limitation warnings, and clinically reviewed emergency triage.
- **Topographic Downscaling**: Elevation lapse-rate corrections (-6.5°C / 1000m) for accurate parcel-level thermal adjustments.
- **Crop Heat Risk**: Phenological heat hazard assessment across 38 canonical Maharashtra crops. Tracks Days After Sowing (DAS), identifies biological stage vulnerabilities (e.g. flowering/anthesis sterility vs vegetative stress), alerts on expired crop cycles, and provides agronomist-reviewed, citation-backed interventions (distinguishing drip lateral pulse irrigation from micro-sprinkler canopy misting).
- **Predictive Machine Learning**: Validated multi-model pipeline:
  - Extreme Heat Event Classifier: Random Forest (96.35% test accuracy).
  - Effective Temperature Regressor: XGBoost ($R^2 = 0.9981$).
  - Sequence Forecasting: PyTorch LSTM ($\text{MAE} = 0.308^\circ\text{C}$).

### Pillar 2: Plot-Level PMFBY Crop-Loss Verification
- **Satellite & Spectral Index Verification**: Sentinel-2 10-meter optical band analysis for baseline vs post-event NDVI and NDWI deficit tracking.
- **Multimodal Vision Pipeline**: Ground-truth field image validation leveraging YOLOv8 defect detection, U-Net damage segmentation, and Vision Transformer (ViT) loss severity assessment.
- **Insurer Workflow & SLA Triage**: Dedicated insurer dashboard (`/insurer-dashboard`) featuring 48-hour mandatory claim SLA timers, evidence verification audit trails, confidence scoring, and structured approval/rejection actions.

### Supporting Capabilities
- **Yield Intelligence & Yield Risk**: Multi-scenario yield benchmarking combining historical APY crop records with agro-climatic normal distributions (1991–2020 IMD normal baseline and 2010–2024 AgERA5 reanalysis).
- **Income Diversification**: Pragmatic enterprise addition (dairy, indigenous goat rearing, desi poultry, sericulture, apiary, shade net polyhouse) with realistic CAPEX, recurring OPEX, net margins, and water requirements calibrated to NABARD FY 2026-27 unit cost norms.
- **Local AI Agricultural Assistant**: Grounded conversational assistant powered by local Ollama models (`qwen3:8b`) with transparent fallback to deterministic rule engines when AI runtimes are offline.

---

## 2. Strict Data & AI Engineering Rules

1. **Zero Fake Data as Real Information**:
   - Synthetic or test data must never be presented to users or insurers as live farmer measurements.
   - All external feeds, forecasts, and soil profiles must disclose data source, retrieval timestamp, grid coordinates, and resolution.
2. **Deterministic Primacy for Science**:
   - Core agronomic, occupational, and financial calculations are executed by deterministic mathematical models and validated ML pipelines.
   - LLMs (e.g. Ollama `qwen3:8b`) are strictly restricted to synthesizing explanations and providing grounded assistance. LLMs must NEVER invent, hallucinate, or recalculate physical constants, risk categories, or claim decisions.
3. **Traceability & Provenance**:
   - Every risk score (0–100) and recommendation must include traceable reasoning, citing specific thresholds, environmental factors, and scientific references.
4. **Privacy & Security**:
   - Zero Personally Identifiable Information (PII) or proprietary coordinates are stored in source control.
   - All sample datasets must use synthetic or anonymized coordinates.

---

## 3. Engineering Quality Gates & Testing Standards

Every pull request or commit must satisfy the following gates before merging or pushing:

1. **Backend Tests**:
   - Run `python -m pytest backend/tests/ -v`.
   - All tests (currently 52 unit, engine, and integration tests) must pass with zero failures.
   - Never delete or suppress tests to make a build pass.
2. **Frontend Quality & Build**:
   - `cd flutter_client && flutter analyze --no-fatal-infos`: Must produce 0 errors.
   - `cd flutter_client && flutter test`: All widget and unit tests must pass.
   - `cd flutter_client && flutter build web --release`: Web compilation must succeed.
3. **Secret Security Audit**:
   - Run `python scripts/scan_secrets.py`.
   - Zero sensitive keys, tokens, credentials, or private certificates may be committed.
4. **Package Discovery & Layout**:
   - Backend uses `pyproject.toml` with `[tool.setuptools.packages.find]` configured with `include = ["backend*"]` and explicit exclusions to prevent flat-layout discovery collisions.

---

## 4. Git Branch Governance & Release Protocol

> [!IMPORTANT]
> **Independent Branch Lifecycle Policy:**  
> The development feature branch and the `main` branch have distinct responsibilities and must NOT be cross-contaminated.

### Branch Responsibilities
- **`yeild-and-heat-risk-feature` (and `yield-and-heat-risk-feature`)**:
  - The active development branch containing all complete application source code, Flutter UI, FastAPI services, scientific models, database schemas, and comprehensive documentation (`docs/`).
- **`main`**:
  - The clean repository landing branch.
  - Represents stable, high-level project status and general overview.

### Rules of Engagement
1. **NO Fast-Forward or Blanket Merges of Feature Branch into Main**:
   - Never merge `yeild-and-heat-risk-feature` into `main` simply to update `README.md` or high-level docs.
   - Merging feature code into `main` is reserved for formal production releases after user authorization.
2. **Independent README Synchronization**:
   - The root `README.md` on `main` may be synchronized with the latest project progress via `.github/workflows/sync-readme.yml` or via isolated worktree commits.
   - Any commit pushed to `main` during documentation synchronization MUST touch **ONLY `README.md`**. No application code, backend packages, or test files may be staged or pushed to `main` during a sync operation.
3. **Branch Name Compatibility**:
   - GitHub Actions CI triggers must monitor both `yeild-and-heat-risk-feature` and `yield-and-heat-risk-feature` to prevent broken builds due to legacy spelling differences.
