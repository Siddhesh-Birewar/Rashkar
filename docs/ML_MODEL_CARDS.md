# RASHKAR — Machine Learning Model Cards

**Platform:** RASHKAR Climate-Smart Agriculture Platform  
**Purpose:** Official documentation of machine learning models implemented in Rashkar for WBGT forecasting, worker heat strain personalization, and PMFBY computer vision loss assessment.  
**Reference Presentation:** PCCOE International Grand Challenge 2026 (Slide 4: Tech Stack)  

---

## Model Card 1: XGBoost Fast WBGT Predictor

### Overview
- **Model Name:** `rashkar_xgb_wbgt_forecast_v1`
- **Architecture:** Gradient Boosted Decision Trees (`xgboost.XGBRegressor`)
- **Version:** 1.0.0
- **Primary Function:** Ultra-low latency prediction of Liljegren outdoor Wet-Bulb Globe Temperature (°C) from standard numerical weather prediction (NWP) parameters.

### Intended Use
- Serves sub-hourly heat hazard assessments for registered smallholder farms without incurring numerical iterative solver overhead during bulk forecast processing.

### Training & Evaluation Data
- **Sample Count:** 2,000 meteorological observation samples calibrated to Maharashtra agro-climatic zones (Pune, Baramati, Indapur, Haveli, Shirur).
- **Split:** 80% Train, 20% Test.
- **Reference Ground Truth:** Liljegren et al. (2008) numerical natural wet bulb and black globe radiative balance solver.

### Performance Metrics
- **Mean Absolute Error (MAE):** $0.217^\circ\text{C}$
- **Root Mean Squared Error (RMSE):** $0.278^\circ\text{C}$
- **Coefficient of Determination ($R^2$):** $0.9981$

### Feature Importances
| Feature Name | Description | Relative Importance |
|:---|:---|:---|
| `temp_c` | Ambient dry-bulb air temperature (°C) | 78.44% |
| `rh_pct` | Relative humidity (%) | 20.93% |
| `solar_w_m2` | Downward shortwave solar irradiance (W/m²) | 0.32% |
| `wind_mps` | 10-meter horizontal wind speed (m/s) | 0.27% |
| `elevation_m` | Farm surface elevation above sea level (m) | 0.02% |
| `zenith_deg` | Solar zenith angle (degrees) | 0.02% |

---

## Model Card 2: Random Forest Worker Personalization Classifier

### Overview
- **Model Name:** `rashkar_rf_worker_personalization_v1`
- **Architecture:** Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`)
- **Parameters:** `n_estimators=80`, `max_depth=6`, `random_state=42`
- **Classes:** 4 categories (`Low`, `Moderate`, `High`, `Extreme`)

### Intended Use
- Personalizes heat hazard screening levels using individual worker physiological factors (age, acclimatization status) and operational parameters (metabolic workload, continuous shift exposure).

### Performance Metrics
- **Accuracy:** $96.35\%$ on held-out test split.
- **Calibration Anchor:** ACGIH TLVs (2023) and ISO 7243:2017 screening action limits.

---

## Model Card 3: PyTorch LSTM WBGT Trajectory Predictor

### Overview
- **Model Name:** `rashkar_lstm_wbgt_trajectory_v1`
- **Architecture:** Recurrent Neural Network (`torch.nn.LSTM`, hidden dimension = 24, layers = 1, fully connected output = 6)
- **Primary Function:** Predicts continuous 0–6 hour WBGT diurnal trend from a sequence of preceding meteorological vectors.

### Performance Metrics
- **Mean Absolute Error (MAE):** $0.308^\circ\text{C}$ across all 6 future hourly forecast timesteps.

---

## Model Card 4: PMFBY Multimodal Vision AI Pipeline (YOLOv8 + U-Net + ViT)

### Overview
- **Pipeline Architecture:**
  1. **YOLOv8 Object & Pattern Detector:** Detects localized damage signatures in geotagged field photos (`flattened_stalk_lodging`, `broken_stems`, `leaf_shredding`, `standing_water_pool`, `stem_rotting`, `leaf_scorching`).
  2. **U-Net Canopy Segmentation:** Computes damaged vs intact plot polygon area percentage with bounding box mask intersection (mIoU: 0.88).
  3. **Vision Transformer (ViT-B/16):** Generates 768-dimensional visual feature embeddings to evaluate structural similarity index (SSIM) degradation against healthy crop reference libraries.
  4. **Sentinel-2 Multi-Spectral Indices:** MSI L2A Band 4 (Red), Band 8 (NIR), and Band 11 (SWIR) providing NDVI, NDWI, and EVI delta anomaly detection at 10m spatial resolution.

### Multimodal Fusion Weights
$$\text{Verified Loss} = 0.35 \times \Delta\text{NDVI}_{\text{sat}} + 0.40 \times \text{Damage}_{\text{vision}} + 0.15 \times \text{Claim}_{\text{farmer}} + 0.10 \times \text{Hazard}_{\text{weather}}$$

- **Confidence Score Output:** Calibrated $0\text{--}100\%$ scale based on cross-modal sensor agreement factor.
- **SLA Operational Target:** 24–48 hours turnaround for surveyor/insurer review queue (versus 45–60 day manual crop cutting experiment bottleneck).
