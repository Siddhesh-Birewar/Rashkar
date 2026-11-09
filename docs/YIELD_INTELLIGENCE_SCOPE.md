# RASHKAR — Yield Intelligence Scope, Baselines & Scientific Boundaries

**Document Purpose:** Defines the explicit boundary between Rashkar's core hackathon pillars and the supporting Yield Intelligence module, preventing false or unverified claims regarding harvest prediction without farm-level ground truth.  
**Reference Proposal:** PCCOE International Grand Challenge 2026  

---

## 1. Role Within Rashkar Architecture

The hackathon presentation defines two primary pillars:
1. **Personalized Farm-Level Heat Risk AI** (Preventive health & agronomic guidance).
2. **Plot-Level PMFBY Crop Loss Verification** (Accelerated 24–48h insurance evidence).

Yield Intelligence serves as a **supporting agronomic context capability**, not an autonomous speculative harvest betting tool. It contextualizes whether a farmer's plot is on track relative to historical agro-ecological baselines or experiencing acute abiotic stress.

---

## 2. Permitted Capabilities (Verified in Prototype)

1. **Historical APY Benchmark:** Compares the active crop with district/sub-district Area, Production, and Yield (APY) statistical baselines published by the Ministry of Agriculture & Farmers Welfare (MoA&FW) and DES Maharashtra.
2. **Environmental Stress Quantification:**
   - Accumulated Growing Degree Days (GDD) tracking relative to phenological stage requirements.
   - High daytime heat accumulation (hours exceeding critical $T_{\max}$ threshold).
   - High nighttime respiration penalty (warm night respiration stress $T_{\min} > 22^\circ\text{C}$).
3. **Soil Context Integration:** Reads physical soil texture and water-holding capacity (sand/silt/clay fractions, bulk density, available water capacity).
4. **Soil Provenance Disclosure:** Explicitly labels whether soil parameters stem from laboratory-tested soil health cards or regional spatial interpolation models (CropNet unsampled coordinate proxy).

---

## 3. Explicit Prohibitions & Out-of-Scope Elements

- **NO Speculative Farm-Level Harvest Tonnage Prediction:** The platform does NOT claim to predict exact yield in quintals per acre for an individual smallholder without verified multi-year farm-level harvest labels. Doing so would be scientifically fraudulent.
- **NO Autonomous Financial Settlement:** Yield risk indicators inform farmer decision-support; they are strictly never used as automated justification for financial loans or insurance payouts without formal assessment.
