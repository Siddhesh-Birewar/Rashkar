# RASHKAR — Yield Intelligence Methodology
**Multi-Dimensional Stress Screening & Historical Reference Baseline**  
**Document ID:** RASHKAR-DOC-YIELD-01  
**Target Pilot:** 36 Districts of Maharashtra  
**Version:** 2.0 (Dynamic Integration)

---

## 1. Core Principle & Ethical Scientific Stance

**No unverified ML predictions without verified farm-level harvest labels.**

Commercial agtech platforms frequently produce pseudo-scientific yield predictions (e.g. predicting "1,842.5 kg/ha" on a single farm without knowing seed variety, fertilization schedule, disease incidence, or historical harvest records). Rashkar rejects this approach.

Instead, Rashkar provides:
1. **Auditable District Historical Baselines:** Computed from 24 years (1997–2021) of verified Ministry of Agriculture / DES crop yield statistics (17,916 records across Maharashtra).
2. **Multi-Dimensional Stress Screening:** Rigorous biophysical vulnerability scoring across 5 agronomic dimensions.
3. **Explicit Safety Gating:** When requested for a farm-level numerical prediction, Rashkar returns `prediction_status = "REQUIRES_FARM_HARVEST_LABELS"`, preventing misleading claims and protecting smallholder farmers from unverified risk exposure.

---

## 2. Historical Baseline Formulation (APY Dataset)

### 2.1 Data Ingestion and Cleansing
The historical yield foundation is derived from the Directorate of Economics and Statistics (DES) / Ministry of Agriculture APY dataset (`data/apy_maharashtra_cleaned.csv`), comprising 17,916 verified district-crop-season records spanning 1997 to 2021.

### 2.2 Statistical Distribution Metrics
For a given district $D$, crop $C$, and season $S$, Rashkar computes the distribution over valid harvest years:
- **Historical Mean ($\mu$):**
  $$\mu = \frac{1}{N} \sum_{i=1}^N Y_i$$
- **Standard Deviation ($\sigma$):**
  $$\sigma = \sqrt{\frac{1}{N-1}\sum_{i=1}^N (Y_i - \mu)^2}$$
- **Median ($M$) & Interquartile Range ($\text{IQR} = Q_3 - Q_1$)**: For non-normal yield distributions.
- **10th Percentile ($P_{10}$)**: Historical drought / severe stress lower bound.
- **90th Percentile ($P_{90}$)**: Historical bumper harvest upper bound.

### 2.3 Sparse Sample Safe Fallback Logic
If the filtered sample count $N < 3$ in a specific district-crop pair (e.g. Nashik Onion or Solapur Cotton), estimating district variance would yield mathematically invalid single-sample results. Rashkar automatically activates the calibrated statewide fallback:
$$\text{If } N_{(D, C)} < 3 \implies \text{Baseline} \gets \text{Aggregated Statewide Maharashtra } (C, S)$$
The returned metadata explicitly flags `geographical_unit = "statewide_maharashtra_{crop}"` to maintain 100% transparency.

---

## 3. CropNet Synthetic Soil Profile Adapter

Soil physical and chemical characteristics govern water retention and root stress. Rashkar interfaces with the CropNet Soil Adapter, synthesizing horizon-depth profiles (0–5 cm, 5–15 cm, 15–30 cm, 30–60 cm, 60–100 cm) based on centroid latitude and longitude:
- **Soil Texture Class:** Clay, Sandy Clay, Clay Loam, or Medium Black Vertisol (typical of Maharashtra's Deccan trap).
- **Available Water Capacity (AWC, mm/m):** Derived from sand, silt, and clay fractions.
- **Cation Exchange Capacity (CEC, cmol(+)/kg):** Nutrient holding capacity.
- **Soil pH:** Detection of sodicity ($pH > 8.5$) or acidity ($pH < 6.0$).
- **Soil Organic Carbon (SOC, %):** Organic matter content.

---

## 4. Multi-Dimensional Stress Screening Framework

Rashkar aggregates stress across 5 distinct biophysical dimensions, normalizing each from $0.0$ (no stress) to $1.0$ (critical yield loss risk):

### 4.1 Thermal Heat Stress Score ($S_{\text{heat}}$)
Evaluates ambient $T_{\text{max}}$ and $T_{\text{min}}$ against stage-specific crop thresholds:
$$S_{\text{heat}} = \min\left(1.0, \max\left(0.0, \frac{T_{\text{max}} - T_{\text{opt\_max}}}{T_{\text{crit}} - T_{\text{opt\_max}}}\right) + \text{Penalty}_{\text{warm\_night}}\right)$$

### 4.2 Moisture / Water Deficit Score ($S_{\text{water}}$)
Evaluates cumulative precipitation against historical normal and days since last effective rainfall ($> 5\text{ mm}$):
$$S_{\text{water}} = \begin{cases}
0.1 & \text{if farm uses Drip/Sprinkler Irrigation} \\
f(\text{dry\_spell\_days}, \text{soil\_AWC}) & \text{if Rainfed / Canal}
\end{cases}$$

### 4.3 Edaphic / Soil Stress Score ($S_{\text{soil}}$)
Evaluates soil depth, pH deviation from optimal ($6.5–7.8$), and CEC:
$$S_{\text{soil}} = w_{\text{pH}} \cdot \Delta pH + w_{\text{depth}} \cdot \text{DepthDeficit} + w_{\text{drainage}} \cdot \text{WaterloggingRisk}$$

### 4.4 Phenological Stage Vulnerability Multiplier ($M_{\text{stage}}$)
Flowering and anthesis stages have high vulnerability multipliers ($1.5\times$), while vegetative and ripening stages have lower multipliers ($0.8\times–1.0\times$):
$$\text{Vulnerability Factor} = \sum (\text{Stress}_i \times M_{\text{stage}})$$

### 4.5 Climate Normal Anomaly ($S_{\text{climate}}$)
Compares seasonal rainfall accumulation against the 30-year IMD climate normal (1991–2020) for the district.

---

## 5. Composite Risk Index & Farmer-Facing Output

The composite yield risk score is computed as:
$$\text{Yield Risk Score} = \sum_{k=1}^5 w_k \, S_k, \quad \sum w_k = 1.0$$
Categorized into actionable levels:
- **LOW (< 0.25):** Favorable conditions; standard package of practices.
- **MODERATE (0.25 – 0.50):** Mild stress; monitor moisture; preventative foliar nutrition.
- **HIGH (0.50 – 0.75):** Severe heat or moisture deficit; urgent protective irrigation and mulching.
- **CRITICAL (> 0.75):** Impending substantial yield reduction; activate PMFBY loss documentation.

---

## 6. Model Safety Architecture & Verifiability

```json
{
  "prediction_status": "REQUIRES_FARM_HARVEST_LABELS",
  "historical_baseline_available": true,
  "geographical_unit": "Pune (1997-2021)",
  "historical_mean_kg_per_ha": 1285.4,
  "historical_p10_kg_per_ha": 720.0,
  "historical_p90_kg_per_ha": 1850.0,
  "farm_stress_score": 0.42,
  "dominant_risk_dimension": "HEAT_STRESS"
}
```
This architecture provides trustworthy agronomic intelligence without over-promising or fabricating predictions.
