# RASHKAR — Heat Risk Intelligence Methodology
**Dual-Path Occupational & Agronomic Thermal Assessment**  
**Document ID:** RASHKAR-DOC-HEAT-01  
**Target Pilot:** Maharashtra Agro-Ecological Zones  
**Version:** 2.0 (Dynamic Integration)

---

## 1. Overview and Core Philosophy

In tropical agricultural systems such as Maharashtra's Deccan Plateau and Vidarbha, extreme heat exerts twin pressures simultaneously:
1. **Human Occupational Stress:** Agricultural laborers face severe risks of heat exhaustion, heat syncope, and lethal heat stroke under intense solar irradiance and humidity.
2. **Crop Phenological Stress:** Crop physiology undergoes pollen sterility, flower abscission, canopy senescence, and excessive nighttime respiration losses.

Rashkar dissociates these two phenomena into distinct, rigorous physical and biological engines while calculating their metrics simultaneously from the same high-resolution micro-meteorological feed.

---

## 2. Worker Occupational Heat Risk Methodology

### 2.1 The Wet Bulb Globe Temperature (WBGT) Standard
Ambient air temperature ($T_a$) and heat index are fundamentally inadequate for outdoor physical laborers because they omit radiant heat load ($S_t$) and convective wind cooling ($u_{10}$). Rashkar implements the **Liljegren et al. (2008)** numerical WBGT model, widely recognized by the World Health Organization (WHO) and ISO 7243 as the physical benchmark.

For outdoor work under direct sunlight:
$$\text{WBGT}_{\text{sun}} = 0.7\,T_{\text{nw}} + 0.2\,T_{\text{g}} + 0.1\,T_{\text{a}}$$

For work in shaded environments:
$$\text{WBGT}_{\text{shade}} = 0.7\,T_{\text{nw}} + 0.3\,T_{\text{g\_shade}} + 0.0\,T_{\text{a}}$$

Where:
- $T_{\text{nw}}$: Natural wet bulb temperature (accounting for evaporative cooling under ambient wind and radiation).
- $T_{\text{g}}$: Black globe temperature (equilibrium between convective cooling and solar radiation absorption).
- $T_{\text{a}}$: Ambient dry bulb temperature (°C).

### 2.2 Thermodynamic Boundary Iteration (Liljegren Formulation)
The natural wet bulb temperature $T_{\text{nw}}$ is obtained by solving the energy balance equation:
$$h_c\,(T_a - T_{\text{nw}}) + \epsilon_{\text{wick}}\,\sigma\,(T_{\text{rad}}^4 - T_{\text{nw}}^4) + S_{\text{absorbed}} = h_m\,L_v\,(q_{\text{sat}}(T_{\text{nw}}) - q_a)$$

The 5 cm black globe temperature $T_g$ is solved from the balance:
$$h_{cg}\,(T_a - T_g) + \alpha_g\,S_t + \epsilon_g\,\sigma\,(T_{\text{rad}}^4 - T_g^4) = 0$$

### 2.3 ACGIH / ISO 7243 Occupational Thresholds and Work-Rest Cycles
Rashkar calculates effective WBGT by adding the Clothing Adjustment Value ($\text{CAV}$):
$$\text{WBGT}_{\text{eff}} = \text{WBGT} + \text{CAV}$$
Typical CAV values calibrated for Maharashtra field conditions:
- Standard single-layer cotton shirt and trousers / dhoti: $\text{CAV} = 0.0^\circ\text{C}$
- Double-layer cotton / protective coverall: $\text{CAV} = +1.5^\circ\text{C}$
- Non-breathable pesticide spraying PPE suit: $\text{CAV} = +3.0^\circ\text{C}$

Threshold Action Limits ($\text{TLV}$) by metabolic workload (Watts):
- **Light Work (180 W, e.g. weeding, manual monitoring):**
  - Acclimatised Limit: $31.0^\circ\text{C}$ | Unacclimatised Limit: $28.0^\circ\text{C}$
- **Moderate Work (300 W, e.g. hoeing, sowing, mechanical weeding):**
  - Acclimatised Limit: $28.0^\circ\text{C}$ | Unacclimatised Limit: $25.0^\circ\text{C}$
- **Heavy Work (415 W, e.g. manual harvesting, spading, digging):**
  - Acclimatised Limit: $26.0^\circ\text{C}$ | Unacclimatised Limit: $23.0^\circ\text{C}$
- **Very Heavy Work (> 500 W):**
  - Acclimatised Limit: $25.0^\circ\text{C}$ | Unacclimatised Limit: $22.0^\circ\text{C}$

### 2.4 Work-to-Rest Recommendations
- $\text{WBGT}_{\text{eff}} < \text{TLV}$: Normal work pace (continuous work).
- $\text{TLV} \le \text{WBGT}_{\text{eff}} < \text{TLV} + 1.5^\circ\text{C}$: 75% work / 25% rest (45 min work, 15 min shade rest per hour).
- $\text{TLV} + 1.5^\circ\text{C} \le \text{WBGT}_{\text{eff}} < \text{TLV} + 3.0^\circ\text{C}$: 50% work / 50% rest (30 min work, 30 min shade rest per hour).
- $\text{WBGT}_{\text{eff}} \ge \text{TLV} + 3.0^\circ\text{C}$: 25% work / 75% rest or complete cessation of heavy outdoor labor.

### 2.5 Emergency Heat Illness Triage Protocol
Rashkar features an instant emergency heat illness triage panel:
- **Heat Exhaustion:** Profuse sweating, clammy skin, weakness, dizziness, headache, nausea.  
  *Action:* Move to deep shade, loosen clothing, sip cool salted water or ORS, elevate feet.
- **Heat Stroke (Medical Emergency):** High body temperature (> 40°C), hot dry skin or cessation of sweating, confusion, irrational behavior, seizures, loss of consciousness.  
  *Action:* Immediate cooling takes priority over transit: drench with cool water, fan aggressively, place ice packs on armpits, groin, and neck; call 108 immediately.

---

## 3. Crop Heat Risk Methodology

### 3.1 Agronomic Thermal Thresholds (ICAR & Maharashtra State Agricultural Universities)
Crop heat sensitivity varies dramatically across phenological growth stages. Rashkar defines stage-specific thresholds derived from research by ICAR-CRIDA, MPKV Rahuri, and VNMKV Parbhani across 38 canonical crops.

Example: **Soybean (*Glycine max*) Phenological Stages**:
1. **Germination / Emergence (DAS 0–10):**
   - Base Temp: $10.0^\circ\text{C}$ | Optimal: $25–30^\circ\text{C}$ | Critical Max: $38.0^\circ\text{C}$
2. **Vegetative (DAS 11–35):**
   - Base Temp: $10.0^\circ\text{C}$ | Optimal: $25–32^\circ\text{C}$ | Critical Max: $39.0^\circ\text{C}$
3. **Flowering / Anthesis (DAS 36–55) [CRITICAL VULNERABILITY]:**
   - Base Temp: $10.0^\circ\text{C}$ | Optimal: $22–28^\circ\text{C}$ | Critical Max: $35.0^\circ\text{C}$
   - *Impact:* Pollen sterility and reduced pod set when $T_{\text{max}} > 35^\circ\text{C}$.
4. **Pod Development & Seed Filling (DAS 56–85):**
   - Base Temp: $10.0^\circ\text{C}$ | Optimal: $22–29^\circ\text{C}$ | Critical Max: $37.0^\circ\text{C}$
   - *Impact:* Premature senescence, shriveled seed, reduced oil content.
5. **Maturity / Harvest (DAS 86–105):**
   - Base Temp: $10.0^\circ\text{C}$ | Optimal: $20–30^\circ\text{C}$ | Critical Max: $42.0^\circ\text{C}$

### 3.2 Diurnal Exposure Duration and Heat Sum
Exceeding $T_{\text{crit}}$ for 1 hour causes transient leaf wilting; exceeding it for $> 4$ consecutive hours causes irreversible cellular membrane rupture and floral desiccation. Rashkar simulates the diurnal temperature curve $T(t)$ from daily $T_{\text{min}}$, $T_{\text{max}}$, and sunrise/sunset times to calculate:
$$\text{Hours Above } T_{\text{crit}} = \int_{0}^{24} \mathbb{I}[T(t) > T_{\text{crit}}]\,dt$$

### 3.3 Warm-Night Minimum Temperature Penalty
High nighttime minimum temperatures ($T_{\text{min}} > 22.0^\circ\text{C}$ for pulses/cereals; $> 24.0^\circ\text{C}$ for cotton) prevent nighttime thermal dissipation and trigger high dark respiration rates, burning carbohydrate stores accumulated during daytime photosynthesis:
$$\text{Respiration Penalty Factor} = \max\left(0.0, \frac{T_{\text{min}} - T_{\text{night\_crit}}}{5.0}\right)$$

### 3.4 Actionable Agronomic Interventions
When Crop Heat Risk reaches `HIGH` or `CRITICAL`, Rashkar delivers specific, non-destructive advisories:
- Early morning or night light irrigation (protective misting/sprinkling) to lower canopy micro-climate temperature by 2–4°C through evaporative cooling.
- Spraying 2% Potassium Nitrate ($\text{KNO}_3$) or Salicylic acid (100 ppm) to enhance stomatal regulation and antioxidant enzyme activity.
- Trash/straw mulching to suppress soil temperature spikes in root zones.

---

## 4. References & Standards
1. Liljegren, J. C., Carhart, R. A., Lawday, P., Tschopp, S., & Sharp, R. (2008). *Modeling the Wet Bulb Globe Temperature Using Standard Meteorological Measurements*. Journal of Occupational and Environmental Hygiene, 5(10), 645-655.
2. ISO 7243:2017. *Ergonomics of the thermal environment — Assessment of heat stress using the WBGT (wet bulb globe temperature) index*.
3. ACGIH (2023). *Threshold Limit Values and Biological Exposure Indices for Chemical Substances and Physical Agents: Heat Stress and Strain*.
4. ICAR-Central Research Institute for Dryland Agriculture (CRIDA). *Contingency Agriculture Plans for Maharashtra Districts*.
5. Vasantrao Naik Marathwada Krishi Vidyapeeth (VNMKV), Parbhani. *Agrometeorological Advisory Guidelines for Kharif and Rabi Crops*.
