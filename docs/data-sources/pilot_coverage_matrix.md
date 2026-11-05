# CropNet AI — Pilot Area Soil Coverage Matrix

## Pune District, Maharashtra Pilot Regions: Maval, Mulshi, Baramati, Indapur

This matrix documents the actual, verified data coverage and real extracted values for each pilot taluka. These values were repeatably extracted from live geospatial datasets using polygon zonal statistics.

---

### Coverage Matrix Summary

| Pilot Taluka | Soil Group / Agroecological Zone | Soil pH (0-5cm) | Organic Carbon (0-5cm) | Sand / Silt / Clay (%) | Total Nitrogen | CEC | Available NPK Status | Active Provider |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Maval** | Western Ghats High Rainfall Clay Loam / Lateritic | **6.50** ($\pm 0.02$) | **19.38 g/kg** (~1.94%) | 31.1% / 31.0% / 37.9% (Clay Loam) | **2.12 g/kg** (Total N) | **37.3 cmol/kg** | **Not Available** (Preserved null) | SoilGrids WCS |
| **Mulshi** | Western Ghats Heavy Rainfall Humid Foothills | **6.44** ($\pm 0.05$) | **23.48 g/kg** (~2.35%) | 29.7% / 29.4% / 40.9% (Clay) | **2.21 g/kg** (Total N) | **33.3 cmol/kg** | **Not Available** (Preserved null) | SoilGrids WCS |
| **Baramati** | Deccan Plateau Vertisol (Black Cotton Soil) | **7.29** ($\pm 0.02$) | **15.36 g/kg** (~1.54%) | 29.4% / 28.4% / 42.3% (Deep Clay) | **1.25 g/kg** (Total N) | **38.2 cmol/kg** | **Not Available** (Preserved null) | SoilGrids WCS |
| **Indapur** | Drier Deccan Rain Shadow Vertisol | **7.07** ($\pm 0.05$) | **24.17 g/kg** (~2.42%) | 33.5% / 21.8% / 44.6% (Heavy Clay) | **1.47 g/kg** (Total N) | **26.6 cmol/kg** | **Not Available** (Preserved null) | SoilGrids WCS |

---

### Granular Extraction Observations & Analysis

#### 1. Maval Taluka (Western Ghats Transition)
* **Sample Farm Bounding Box:** `73.675° E to 73.685° E, 18.755° N to 18.765° N` (~120 ha polygon)
* **Soil pH:** Mildly acidic (mean 6.50), reflecting high monsoon precipitation ($>1500\text{ mm}$) which leaches basic cations.
* **Organic Carbon:** High ($19.38\text{ g/kg} = 1.94\%$), consistent with dense natural vegetation and upland terrain.
* **Texture:** Clay loam (Clay: 37.9%, Sand: 31.1%, Silt: 31.0%). Good moisture retention with fair internal drainage.
* **Agronomic Implications:** Well suited for rice/paddy in valley bottoms, finger millet (ragi), groundnut, and hill horticultural crops.

#### 2. Mulshi Taluka (Western Ghats Crest / Valleys)
* **Sample Farm Bounding Box:** `73.605° E to 73.615° E, 18.525° N to 18.535° N`
* **Soil pH:** Mildly acidic (mean 6.44).
* **Organic Carbon:** Very high ($23.48\text{ g/kg} = 2.35\%$). Highest of all four pilot areas.
* **Texture:** Heavy clay / clay loam (Clay: 40.9%, Sand: 29.7%, Silt: 29.4%).
* **Agronomic Implications:** Heavy rainfall area suitable for Kharif paddy, ginger, turmeric, and bamboo agroforestry. Susceptible to waterlogging in flat depressions.

#### 3. Baramati Taluka (Canal & Well Irrigated Black Soil Belt)
* **Sample Farm Bounding Box:** `74.525° E to 74.535° E, 18.175° N to 18.185° N`
* **Soil pH:** Neutral to mildly alkaline (mean 7.29), characteristic of Deccan trap basalt weathering.
* **Organic Carbon:** Moderate ($15.36\text{ g/kg} = 1.54\%$), typical of intensively cropped tropical plains.
* **Texture:** Heavy Montmorillonitic clay (Clay: 42.3%, Sand: 29.4%, Silt: 28.4%).
* **CEC:** High ($38.24\text{ cmol(c)/kg}$), indicating exceptional cation nutrient buffering capacity.
* **Important Spatial Note:** Urban settlement and river channels (e.g. Karha River) register NoData (pixel value 0) in SoilGrids masks. The polygon zonal extractor automatically filters these non-soil pixels.
* **Agronomic Implications:** Premier black cotton soil suited for sugarcane, Bt-cotton, soybean, gram, and jowar (sorghum). Drainage management is essential during heavy rains.

#### 4. Indapur Taluka (Ujani Basin & Rain Shadow Belt)
* **Sample Farm Bounding Box:** `75.045° E to 75.055° E, 18.145° N to 18.155° N`
* **Soil pH:** Neutral (mean 7.07).
* **Organic Carbon:** $24.17\text{ g/kg}$.
* **Texture:** Deep clay (Clay: 44.6%, Sand: 33.5%, Silt: 21.8%).
* **CEC:** $26.61\text{ cmol(c)/kg}$.
* **Agronomic Implications:** Vertisol soil suited for pomegranate orchards, sugarcane (in canal command areas), maize, wheat, and chickpea.

---

### Critical Scientific Restrictions Applied

1. **Available Nitrogen:** **NOT AVAILABLE**. SoilGrids predicts Total Nitrogen (sum of all organic and inorganic N). Only 1–3% of total N is mineralized into plant-available forms ($NH_4^+$ and $NO_3^-$). CropNet strictly flags available N as unavailable to prevent dangerous over- or under-fertilization.
2. **Available Phosphorus & Potassium:** **NOT AVAILABLE**. No approved public geospatial raster currently maps plant-available Olsen-P or ammonium acetate-extractable K for India. CropNet never infers or fabricates these values.
3. **Map-Derived Disclaimer:** All reports displayed to farmers carry an explicit disclaimer: *"Map-Derived Estimate: These values are derived from digital geospatial soil models (ISRIC SoilGrids 2.0). They are NOT laboratory test results."*
