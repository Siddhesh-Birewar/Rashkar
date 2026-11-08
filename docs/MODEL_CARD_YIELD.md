# RASHKAR — Model Card: Yield Risk & Stress Screening Engine
**Document ID:** RASHKAR-MC-YIELD-01  
**Version:** 2.0  
**Status:** Validated / Production-Gated

---

## 1. Model Details

- **Model Name:** Rashkar Multi-Dimensional Yield Risk Screener & Historical Baseline Evaluator
- **Model Type:** Hybrid Biophysical Vulnerability Scoring + Empirical Historical Distribution Engine
- **Developer:** Rashkar Engineering Team
- **Release Date:** November 2026
- **License:** Proprietary (Rashkar Platform)

---

## 2. Intended Use & Target Users

- **Intended Use:** 
  - Providing smallholder farmers in Maharashtra with transparent, auditable historical yield baselines for their specific district, crop, and season.
  - Screening current and near-term agronomic stress (thermal, moisture, soil, phenological) to guide timely preventative interventions.
- **Out of Scope / Prohibited Uses:**
  - Automated PMFBY claim adjudication or denial.
  - Granting or denying agricultural credit/loans based purely on algorithmic yield estimates.
  - Making unverified farm-level harvest tonnage guarantees to farmers.

---

## 3. Explicit Model Gating: `REQUIRES_FARM_HARVEST_LABELS`

### 3.1 The Smallholder Vulnerability Safeguard
Predicting exact farm-level crop yields (e.g. predicting "1,420 kg/ha") without multi-year ground-truth harvest labels from the specific plot introduces unacceptable scientific and financial risk. Uncalibrated machine learning models over-fit to satellite vegetation indices (NDVI) while missing catastrophic localized factors (pest attacks, soil salinity, micro-nutrient deficiencies, spurious cloud contamination).

### 3.2 Gating Mechanism
Rashkar implements an explicit programmatic gate:
```json
{
  "prediction_status": "REQUIRES_FARM_HARVEST_LABELS",
  "historical_baseline_available": true,
  "farm_stress_score": 0.38,
  "dominant_risk_dimension": "HEAT_STRESS"
}
```
Until verified farm-level harvest records are uploaded and validated over multiple seasons, numerical farm predictions are locked, and the platform delivers auditable district historical percentiles ($P_{10}, \mu, P_{90}$) alongside real-time stress screening.

---

## 4. Factors and Stress Dimensions

The model computes vulnerability across 5 biophysical dimensions:
1. **Thermal Stress:** Stage-specific critical temperature thresholds ($T_{\text{max}} > T_{\text{crit}}$) and warm-night minimum respiration penalties ($T_{\text{min}} > T_{\text{night\_crit}}$).
2. **Moisture Deficit:** Precipitation deficit relative to historical IMD normal, consecutive dry spell days, and soil Available Water Capacity (AWC).
3. **Edaphic / Soil Factors:** Rooting depth constraints, pH deviation, cation exchange capacity (CEC), and drainage class from CropNet Soil Adapter.
4. **Phenological Stage Weight:** Anthesis/flowering stages receive highest sensitivity weighting ($1.5\times$).
5. **Climate Normal Deviation:** Seasonal accumulation against 30-year IMD normal (1991–2020).

---

## 5. Evaluation & Verification

- **Historical Foundation:** 17,916 cleaned records from Directorate of Economics and Statistics (DES), Ministry of Agriculture (1997–2021).
- **Automated Verification:** Verified by pytest suites:
  - `backend/tests/test_yield_risk.py::test_yield_risk_end_to_end`: Verifies dynamic baseline calculation, stress dimension aggregation, and gating response.
  - `tests/test_dynamic_district_journey.py::test_solapur_jowar_dynamic_registration_and_yield_intelligence`: Verifies dynamic registration and yield baseline retrieval for Jowar in Solapur district.
  - `backend/tests/test_farms_profile_update.py::test_farm_profile_update_e2e`: Verifies instant yield baseline recalculation upon farm profile update.
