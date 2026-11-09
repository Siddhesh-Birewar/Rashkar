# CropNet AI — Agricultural Intelligence Benchmark Dataset (Phase 5.0)

**Dataset ID:** `CROPNET-AGRI-BENCH-V1`  
**Total Cases:** 30 Test Cases  
**Domains Covered:** Soil Intelligence, Crop Suitability, Decision Reasoning, Irrigation Intelligence, Weather & Climate, Knowledge Retrieval, Multilingual Communication  
**Target Languages:** English (`en`), Marathi (`mr`)  
**Status:** Canonical Evaluation Standard  

---

## 1. Benchmark Composition & Distribution

| Domain Code | Agricultural Domain | Test Case Count | Test Case IDs | Adversarial Cases Included |
|:---:|---|:---:|---|---|
| **A** | **Soil Intelligence** | 5 | `AGRI-BENCH-001` to `005` | Total vs Available N, pH sole factor fallacy, Missing EC |
| **B** | **Crop Suitability** | 5 | `AGRI-BENCH-006` to `010` | Taluka screening vs farm verification |
| **C** | **Agricultural Decision Reasoning** | 6 | `AGRI-BENCH-011` to `016` | Suitability vs profitability, Contradictions, Abstention, Hallucinated thresholds |
| **D** | **Irrigation Intelligence** | 4 | `AGRI-BENCH-017` to `020` | Conflicting schedules, Weather-aware suspension, Water quality |
| **E** | **Weather & Climate Intelligence** | 3 | `AGRI-BENCH-021` to `023` | Climatology vs forecast, Thermal stress thresholds |
| **F** | **Agricultural Knowledge Retrieval** | 3 | `AGRI-BENCH-024` to `026` | Inapplicable keyword matches, Multi-source attribution, Unregistered crop abstention |
| **G** | **Multilingual Communication** | 4 | `AGRI-BENCH-027` to `030` | Marathi vernacular, Reproductive stress in Marathi, Bilingual parity, Bahar planning |
| **Total** | | **30** | `AGRI-BENCH-001` to `030` | **9 Adversarial Archetypes Verified** |

---

## 2. Test Case Catalog Summary

### Domain A: Soil Intelligence
1. **`AGRI-BENCH-001` — Total Nitrogen vs. Available Nitrogen Distinction**  
   - *Query:* Farmer with 0.06% Total N and 185 kg/ha Available N asks if nitrogen fertilizer can be skipped for Rabi Sorghum.  
   - *Expected Outcome:* System explains Total N is organically bound/unavailable; 185 kg/ha is Low; external nitrogen is required. Refuses the premise.
2. **`AGRI-BENCH-002` — Soil pH as Sole Factor Fallacy**  
   - *Query:* Farmer has ideal pH 6.8 for pomegranate, but shallow (20 cm) waterlogged clay soil.  
   - *Expected Outcome:* Unsuitable. Disqualifies pomegranate due to shallow depth and waterlogging despite optimal pH.
3. **`AGRI-BENCH-003` — Soil Organic Carbon (SOC) Interpretation**  
   - *Query:* Baramati soil test shows SOC of 0.38%. How to interpret for dryland farming?  
   - *Expected Outcome:* Classifies as Low (< 0.50%); explains impact on moisture holding and biological activity; advises organic matter incorporation.
4. **`AGRI-BENCH-004` — Canal Zone Chickpea & Missing Salinity (EC)**  
   - *Query:* Indapur canal zone farmer with pH 7.6 asks if chickpea is suitable.  
   - *Expected Outcome:* Conditional suitability; asks for EC and drainage status due to high salinity sensitivity in canal seepage zones.
5. **`AGRI-BENCH-005` — Pomegranate Soil Texture Bounds**  
   - *Query:* Official ICAR-NRCP texture and pH bounds for pomegranate.  
   - *Expected Outcome:* Light soil; pH 6.5–7.0 most suitable; up to 8.5 under well-managed conditions; lower tolerable pH is NULL.

### Domain B: Crop Suitability
6. **`AGRI-BENCH-006` — Maval vs. Baramati Regional Suitability for Chickpea**  
   - *Query:* Cultivating Rabi chickpea in Maval taluka.  
   - *Expected Outcome:* Classified as `requires_regional_validation`; high humidity and lateritic/acidic soils cause disease and vegetative overgrowth.
7. **`AGRI-BENCH-007` — Sugarcane Hydrological Constraints in Indapur**  
   - *Query:* Growing sugarcane in Vertisols with seasonal borewell dry by February.  
   - *Expected Outcome:* Unsuitable due to water deficit during peak summer tillering; suggests short-duration Rabi crops (chickpea/sorghum).
8. **`AGRI-BENCH-008` — Regional Screening vs. Farm-Level Verification**  
   - *Query:* Does `regional_screening` for cotton in Baramati mean guaranteed success on every farm?  
   - *Expected Outcome:* Explains screening is a macro agroecological filter, not a farm guarantee; local depth, salinity, and drainage must be tested.
9. **`AGRI-BENCH-009` — Kharif Pearl Millet (Bajra) Sowing Window**  
   - *Query:* Optimum sowing window for Kharif Bajra in Baramati.  
   - *Expected Outcome:* June 15 to July 15 with monsoon onset; delays cause downy mildew and terminal drought.
10. **`AGRI-BENCH-010` — Soybean in Mulshi Western Ghats**  
    - *Query:* Growing Kharif soybean in Mulshi.  
    - *Expected Outcome:* Classified as `requires_regional_validation`; heavy rains (>2000 mm) cause flower abortion and fungal collar rot.

### Domain C: Agricultural Decision Reasoning
11. **`AGRI-BENCH-011` — Agronomic Suitability vs. Financial Profitability**  
    - *Query:* Does 100% agronomic suitability of Bajra guarantee high profits?  
    - *Expected Outcome:* Strictly decouples suitability from market prices and commercial profitability; no financial guarantees.
12. **`AGRI-BENCH-012` — Contradictory Farm Inputs (Sandy Soil + 14-day Waterlogging)**  
    - *Query:* Coarse sandy soil with water standing for 14 days after rain.  
    - *Expected Outcome:* Detects physical impossibility; asks clarifying questions regarding impermeable hardpans or low-lying runoff.
13. **`AGRI-BENCH-013` — Alkaline pH Misconception (Applying Lime to pH 8.3)**  
    - *Query:* Farmer thinks pH 8.3 is acidic and wants to apply lime.  
    - *Expected Outcome:* Corrects that pH 8.3 is alkaline; strictly warns AGAINST lime application to prevent micronutrient lockout.
14. **`AGRI-BENCH-014` — Complete Context Absence Abstention**  
    - *Query:* "Tell me the best crop to grow on my farm."  
    - *Expected Outcome:* Abstains from recommending crops; asks structured questions (location, season, soil type, water).
15. **`AGRI-BENCH-015` — Hallucinated Scientific Thresholds (Pomegranate pH 6.0)**  
    - *Query:* Is 6.0 the verified lower tolerable pH for pomegranate?  
    - *Expected Outcome:* Denies unsupported 6.0 limit; confirms 6.5–7.0 optimum and 8.5 upper tolerance; preserves lower limit as unverified NULL.
16. **`AGRI-BENCH-016` — Pomegranate Annual Water Requirement in Millimeters**  
    - *Query:* Is annual water requirement for pomegranate 600 mm?  
    - *Expected Outcome:* Explains requirements are defined in liters/tree/day by Bahar and tree age, not aggregate annual mm. Preserves mm as NULL.

### Domain D: Irrigation Intelligence
17. **`AGRI-BENCH-017` — Pomegranate Mrig Bahar October Tree Water Schedule**  
    - *Query:* Daily water requirement for 4-year-old pomegranate tree in October (Mrig Bahar).  
    - *Expected Outcome:* Cites ICAR-NRCP Table 1 schedule (28.3 to 34.2 L/tree/day, averaging ~31 L/tree/day).
18. **`AGRI-BENCH-018` — Decoupled Chickpea Irrigation Schedules (ICRISAT vs. MPKV)**  
    - *Query:* Should chickpea be irrigated at 25 DAS or branching stage?  
    - *Expected Outcome:* Explains physiological stage approach (ICRISAT: branching & pod filling) vs calendar approach (MPKV: 20–25 & 60–65 DAS). Does not blend into 4 irrigations.
19. **`AGRI-BENCH-019` — Weather-Aware Irrigation Suspension**  
    - *Query:* Scheduled irrigation at 22 DAS for chickpea, but 50 mm heavy rain forecast in 48 hours.  
    - *Expected Outcome:* Suspends irrigation immediately to prevent waterlogging and fungal collar rot; advises opening drainage channels.
20. **`AGRI-BENCH-020` — Irrigation Water Quality Risk in Semi-Arid Vertisols**  
    - *Query:* Using uninspected well water for wheat in Baramati.  
    - *Expected Outcome:* Warns of salinity (EC > 1.5 dS/m) and sodicity (SAR) in Baramati aquifers; advises water testing before irrigation.

### Domain E: Weather & Climate Intelligence
21. **`AGRI-BENCH-021` — Climatology Mistaken for Weather Forecast**  
    - *Query:* Sowing groundnut on June 5 based on 30-year average 115 mm rainfall, despite delayed monsoon.  
    - *Expected Outcome:* Distinguishes historical normal from real-time forecast; strictly forbids dry sowing without actual 75–100 mm rainfall.
22. **`AGRI-BENCH-022` — Chickpea Reproductive High-Temperature Stress**  
    - *Query:* Max temperature forecast of 37°C during chickpea flowering.  
    - *Expected Outcome:* Cites ICRISAT 2010 (>35°C during reproductive stage causes flower drop and reduced pod set); qualifies as reproductive threshold.
23. **`AGRI-BENCH-023` — Chickpea Reproductive Low-Temperature Stress**  
    - *Query:* Daily max 20°C and min 8°C (mean 14°C) during chickpea flowering.  
    - *Expected Outcome:* Cites ICRISAT 2010 (mean of max and min <15°C causes flower abortion and delayed pod set).

### Domain F: Agricultural Knowledge Retrieval
24. **`AGRI-BENCH-024` — Inapplicable Keyword Match in Divergent Agroecological Zone**  
    - *Query:* Applying MPKV 2023 Vertisol gram recommendation to shallow gravelly soil in Maval.  
    - *Expected Outcome:* Rejects recommendation as contextually inapplicable due to soil type and agroecological zone mismatch.
25. **`AGRI-BENCH-025` — Multi-Source Citation Verification**  
    - *Query:* Institutional sources for chickpea pH and irrigation in CropNet.  
    - *Expected Outcome:* Cites ICRISAT 2010 (pH 6.0–8.0, branching/pod stages) and MPKV 2023 (Vertisol calendar stages).
26. **`AGRI-BENCH-026` — Out-of-Catalogue Crop Abstention**  
    - *Query:* NPK schedule and water requirement for Dragon Fruit in Indapur.  
    - *Expected Outcome:* Abstains; explains CropNet covers 10 priority crops; refuses to synthesize unverified parameters.

### Domain G: Multilingual Communication
27. **`AGRI-BENCH-027` — Marathi Advisory: Pomegranate Bacterial Blight & Drainage**  
    - *Query:* Oily black spots and waterlogged soil in pomegranate.  
    - *Expected Outcome:* Uses Marathi terms 'तेलकट डाग / जिवाणूजन्य करपा' (*Xanthomonas*), 'पाण्याचा निचरा', and 'हलकी जमीन'.
28. **`AGRI-BENCH-028` — Marathi Advisory: Chickpea Heat Stress**  
    - *Query:* Chickpea flower drop under rising heat.  
    - *Expected Outcome:* Uses 'पुनरुत्पादन अवस्था', 'कमाल तापमान ३५°C', 'फूल गळ', and 'घाटे धारणा'.
29. **`AGRI-BENCH-029` — Bilingual Semantic Parity Verification**  
    - *Query:* Soil pH 7.8 chickpea suitability in Baramati (English & Marathi).  
    - *Expected Outcome:* 100% numerical and conceptual parity between English and Marathi outputs.
30. **`AGRI-BENCH-030` — Vernacular Bahar Management under Water Scarcity**  
    - *Query:* Ambia Bahar vs. Hasta Bahar when water runs out post-February.  
    - *Expected Outcome:* Advises Hasta Bahar ('हस्त बहार') to avoid summer water exhaustion; explains Ambia Bahar's peak summer water demand.
Path: file:///Users/siddheshbirewar/Downloads/Cropnet Feature/cropnet/benchmarks/agricultural_intelligence/benchmark_dataset.md
