# Rashkar — Dataset Register and Usage Guide

## Yield Intelligence + Heat-Risk Intelligence

**Document status:** Working data acquisition and engineering register  
**Prepared:** 7 November 2026  
**Geography:** Maharashtra, India  
**Soil provider:** CropNet `UnifiedSoilProfile` (teammate-owned feature)  
**Priority features:** Yield Intelligence and Heat-Risk Intelligence  

> **Important:** A portal page is not necessarily a bulk dataset. This document distinguishes direct downloads, API/time-series services, interactive query tools, institutional access requests and data that must be collected during the pilot. Before production use, verify each source's latest version, access terms, licence, attribution, and actual returned files. Do not assume a dataset is free for commercial use simply because its landing page is publicly viewable.

---

## 1. How to read this register

### Availability labels

- **Downloadable:** files can be downloaded from the source page or its supported file service.
- **API / query service:** structured data can be retrieved, but authentication, rate limits, request geometry or API terms may apply.
- **Interactive portal:** useful for inspection/report generation; bulk machine access is not yet confirmed.
- **Access request:** the information may exist operationally, but Rashkar must request access and a data dictionary.
- **Pilot collection:** the data must be measured or recorded with a research/agriculture partner.
- **Reference only:** useful to design methods or build a knowledge base, but not a substitute for Maharashtra labels or measurements.

### Priority labels

- **P0 — Build foundation:** needed for first data pipeline or first risk-engine release.
- **P1 — Important:** needed for stronger spatial/crop coverage, monitoring or validation.
- **P2 — Optional / later:** useful for an additional model or research experiment, but not a blocker.

### Required dataset manifest fields

For every downloaded/API dataset, create a record containing:

`dataset_id, dataset_name, publisher, original_source, source_url, retrieval_method, access_date, version, vintage, temporal_coverage, spatial_coverage, spatial_resolution, temporal_resolution, variables, units, file_format, CRS, licence, attribution, commercial_use_status, redistribution_status, data_dictionary_url, checksum, transformations, quality_flags, known_limitations, owner, storage_path, refresh_frequency, approval_status`.

Never store credentials or tokens in the manifest.

---

## 2. Shared datasets — both Yield Intelligence and Heat-Risk Intelligence

These should be ingested once into the common Rashkar data platform and reused by both features.

### S-01. AgERA5 v2 — daily agrometeorological indicators

- **Priority:** P0.
- **Availability:** Download/API; point/small-area time-series extraction is available.
- **Publisher:** Copernicus Climate Change Service / ECMWF.
- **Main links:**
  - [AgERA5 daily indicators](https://cds.climate.copernicus.eu/datasets/sis-agrometeorological-indicators)
  - [AgERA5 time-series extraction](https://cds.climate.copernicus.eu/datasets/sis-agrometeorological-indicators-timeseries)
- **Coverage:** Global; 1979 to present in the dataset catalogue.
- **Resolution:** Daily; 0.1° grid for the gridded product, with local-time aggregation and topographic correction described by the provider.
- **Useful variables:** daily temperature statistics, precipitation, relative humidity, dewpoint, wind speed, solar radiation, vapour pressure deficit and FAO-56 Penman-Monteith reference evapotranspiration (ET0), among others.
- **Use in Yield Intelligence:** rainfall accumulation, dry-spell features, rainfall anomalies, heat thresholds, humidity/VPD, ET0 and crop-stage weather features.
- **Use in Heat-Risk:** daily context, seasonal heat climatology, daily maxima/minima and cross-checks. It does not replace hourly inputs for within-day worker alerts.
- **Recommended method:** use the time-series product to extract only Maharashtra points/small areas initially; use the gridded product for reproducible statewide feature generation as data volume and access allow.
- **Caveats:** It is reanalysis-derived, not direct farm weather measurement. Record the AgERA5 version. Copernicus announced that AgERA5 v1.1 was superseded and v2 continued daily updating in 2026; do not start a new operational pipeline on the retired v1.1 product.
- **Format/access:** CDS download/API; inspect the current product documentation and selected variable units before implementation.
- **Official references:** [dataset overview](https://cds.climate.copernicus.eu/datasets/sis-agrometeorological-indicators?tab=overview), [time-series description](https://cds.climate.copernicus.eu/datasets/sis-agrometeorological-indicators-timeseries?tab=overview).

### S-02. ERA5-Land — hourly land reanalysis

- **Priority:** P0 for Heat-Risk; P1 for Yield Intelligence.
- **Availability:** Download/API through CDS.
- **Publisher:** Copernicus Climate Change Service / ECMWF.
- **Link:** [ERA5-Land hourly](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land).
- **Coverage:** Global; 1950 to present in the current catalogue.
- **Resolution:** Hourly; approximately 9 km native grid.
- **Useful variables:** 2 m temperature/dewpoint (atmospheric forcing variables are also available from relevant ERA5 products), precipitation, surface solar radiation, wind components and land-surface variables including soil temperature and soil-water layers. Confirm each variable is in the chosen catalogue entry before writing the downloader.
- **Use in Yield Intelligence:** hourly-to-daily aggregation, soil-water context, heat duration, night-time temperature and weather features where AgERA5 daily summaries are insufficient.
- **Use in Heat-Risk:** historical hourly meteorological sequences for thermal-hazard calculation, feature building and backtesting.
- **Caveats:** Reanalysis estimates, not direct observations; spatial resolution is not plot-scale. ERA5-Land documentation explains that atmospheric forcing is derived from ERA5 and observations are indirectly represented through that forcing.
- **Format/access:** CDS API and supported download formats; use an account/API key where required. Keep credentials in a secret manager.
- **Official references:** [CDS dataset](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land), [ECMWF description](https://www.ecmwf.int/en/forecasts/datasets/era5-land-hourly-data-1950-present).

### S-03. IMD daily gridded rainfall — 0.25°

- **Priority:** P0.
- **Availability:** Direct yearly NetCDF download selection.
- **Publisher:** India Meteorological Department (IMD), Climate Research and Services, Pune.
- **Link:** [IMD 0.25° daily rainfall NetCDF](https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html).
- **Coverage:** 1901–2024 in the listed product (check for newer release before acquisition).
- **Resolution:** 0.25° grid; daily rainfall in mm.
- **Use in Yield Intelligence:** dry-spell, rainfall anomaly, delayed/deficient/excess monsoon, crop-stage rainfall and heavy-rain indicators.
- **Use in Heat-Risk:** contextual weather history, but not the primary temperature/radiation source.
- **Caveats:** Gridded interpolation is not a farm rain-gauge observation. Preserve the IMD grid and source identity. Do not sum IMD rainfall and AgERA5 rainfall together.
- **Format:** NetCDF.
- **Reference:** [IMD dataset page](https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html).

### S-04. IMD public weather APIs

- **Priority:** P0.
- **Availability:** API; account/token or approved access may be required.
- **Publisher:** India Meteorological Department.
- **Links:** [Official API access portal](https://api.imd.gov.in/public/), [API reference](https://api.imd.gov.in/public/api_reference.html).
- **Available service categories listed by IMD:** 7-day city forecast, lat/long forecast, subdivision/state/district rainfall forecast, current weather, district/station nowcast, AWS/ARG data, district warnings, rainfall information and agromet advisories.
- **Use in Yield Intelligence:** current weather, forecasts, district warnings, agromet bulletins and forecast hazard inputs.
- **Use in Heat-Risk:** current temperature/humidity/wind/rainfall observations, nowcasts, warnings and forecast inputs for the near-term 0–6 h assessment where a suitable field/horizon is available.
- **Caveats:** distinguish observation timestamp, issue time and valid time; forecast availability and granularity vary by endpoint. Do not assume all API responses are farm-resolution. Persist request/response metadata and provider update time.
- **Integration steps:** inspect current API reference; register/request access; create an authenticated adapter; store credentials in a secret manager; implement retries/backoff and rate-limit handling; validate schema changes; record response timestamp and freshness.
- **Reference:** [IMD API reference](https://api.imd.gov.in/public/api_reference.html).

### S-05. Survey of India / administrative boundary layers

- **Priority:** P0.
- **Availability:** Downloadable geospatial layers where offered by portal.
- **Purpose:** district/taluka boundaries, administrative joins and map display.
- **Sources:** [National Water Data Portal — district boundary](https://nwdp.nwic.gov.in/dataset/district-boundary) and [sub-district boundary](https://nwdp.nwic.gov.in/en/dataset/sub-district-boundary).
- **Formats:** check each resource for GeoJSON, KML or shapefile.
- **Use:** district/taluka assignment, weather-grid overlays, crop statistics joins and farm plot context.
- **Caveats:** record administrative vintage and codes. Boundary changes/renames can affect historical joins. Do not join by name alone; use stable codes and an alias table.

### S-06. NOAA GFS 0.25° forecast — optional supplementary forecast

- **Priority:** P2 until locally benchmarked.
- **Availability:** operational data download/API via NOMADS.
- **Publisher:** NOAA/NCEP.
- **Link:** [GFS NOMADS](https://www.nco.ncep.noaa.gov/pmb/products/gfs/nomads/).
- **Use:** supplementary short-range forecast variables and ensemble/source comparison if operationally useful.
- **Caveats:** not an Indian ground observation; validate forecast errors over Maharashtra before use. Do not add it merely to increase source count. Confirm variables, run time, forecast lead and redistribution terms.

---

## 3. Yield Intelligence datasets

### Y-01. Maharashtra district/season/crop APY

- **Priority:** P0.
- **Availability:** CSV/XLSX/JSON downloads on the distributor page.
- **Original source:** Ministry of Agriculture & Farmers Welfare APY statistics; distributed by Dataful.
- **Link:** [Maharashtra district, season and crop APY dataset](https://dataful.in/datasets/5632/).
- **Coverage described:** 1997–98 to 2024–25; Maharashtra district, crop, season and year.
- **Use:** historical area, production and yield baseline by district/crop/season/year; identify trend and variability; compare current season with history.
- **Ingestion:** download one canonical file format; save raw file unchanged; record Dataful version/download date/terms; inspect columns and units; parse crop, season, district and year; standardise names using mapping tables; calculate `yield = production / area` only when area > 0 and check against provided yield field; keep original and derived values; validate against official DES/OGD extracts.
- **Caveats:** third-party redistribution of Ministry-derived data. Verify terms and attribution. Some minor crops have shorter time coverage than the headline range. Do not treat district yield as farm yield.

### Y-02. Official OGD district-wise, season-wise crop production statistics

- **Priority:** P0 as an official cross-check; avoid duplicate training rows.
- **Availability:** resource download; confirm latest file and format at download time.
- **Publisher:** Government of India Open Government Data platform.
- **Link:** [District-wise, season-wise crop production statistics from 1997](https://www.data.gov.in/resource/district-wise-season-wise-crop-production-statistics-1997).
- **Variables:** district, crop, season, year, area and production (verify actual file fields).
- **Use:** validate APY rows and official-source attribution; identify discrepancies and changes in crop labels.
- **Caveats:** catalogue metadata may not reflect the newest year. Do not merge as extra observations when it mirrors APY.

### Y-03. Crop-specific APY collection

- **Priority:** P1, only where one-crop extracts make handling easier.
- **Availability:** CSV/XLSX/Parquet listed.
- **Link:** [Dataful crop-wise APY collection](https://dataful.in/collections/964/).
- **Use:** crop-specific QA or convenient filtered acquisition (rice, maize, moong, urad, sesame, groundnut, mustard, sugarcane, tur, wheat, etc.).
- **Caveat:** underlying records largely overlap the APY source. Do not concatenate these files with Y-01 as independent records. Use the same canonical APY table and record dataset lineage.

### Y-04. DES APY report/query interface

- **Priority:** P0 cross-check and selected export.
- **Availability:** interactive query/export service.
- **Publisher:** Directorate of Economics and Statistics, Department of Agriculture & Farmers Welfare.
- **Links:** [DES APY report](https://data.desagri.gov.in/website/crops-apy-report-web), [APY query report](https://www.data.desagri.gov.in/website/apy-query-report-web).
- **Use:** select state Maharashtra, district, crop, season and year range to cross-check the downloaded APY table and fill a documented gap if exports are supported.
- **Caveat:** report interface, not one static bulk file; automated access/export behaviour must be verified.

### Y-05. Maharashtra State Data Bank agricultural raw data

- **Priority:** P1.
- **Availability:** interactive raw-data selector; export format/coverage must be tested.
- **Publisher:** Government of Maharashtra.
- **Link:** [MahasDB raw data](https://www.mahasdb.maharashtra.gov.in/rawData.do).
- **Potential tables:** district/year, Agriculture & Allied Activities — Production Crops and Irrigation Area.
- **Use:** state-specific production and irrigation context; compare with national APY.
- **Acquisition steps:** test selected district/year; record output format, source and year availability; check whether stable downloads or bulk extraction exist; do not build a brittle scraper without permission/terms review.

### Y-06. Horticulture statistics collection

- **Priority:** P1 for fruit/vegetable/spice crops.
- **Availability:** CSV/XLSX/Parquet files listed in collection.
- **Link:** [Horticulture statistics collection](https://dataful.in/collections/336/).
- **Coverage:** multiple horticulture tables such as fruits, vegetables, flowers, spices, crop-group area/production/productivity; geographic level varies by table.
- **Use:** extend Rashkar beyond field crops; use only datasets whose geographic granularity is suitable for the intended model.
- **Caveat:** some data may be state-level or crop-group-only, not district-level. Verify per-file metadata and terms.
- **Supplementary query interface:** [National Horticulture Board production report](https://nhb.gov.in/onlineclient/rptproduction.aspx) is an interactive query tool, not confirmed bulk API.

### Y-07. Crop calendar — MIRCA-OS

- **Priority:** P0/P1.
- **Availability:** downloadable CSV and NetCDF through HydroShare.
- **Publisher:** MIRCA-OS research dataset.
- **Link:** [MIRCA-OS HydroShare](https://hydroshare.org/resource/e4582ca0042148338bb5e0148b749ed6/).
- **Coverage:** 23 irrigated and 23 rainfed crop categories; snapshots for 2000, 2005, 2010, 2015 and 2020; global.
- **Resolution:** 5 arc-minute growing-area grids (roughly 10 km at equator); CSV crop calendar and NetCDF monthly growing area.
- **Use:** broad planting/maturity months, irrigated/rainfed priors and crop distribution context.
- **Caveats:** not farmer-specific sowing dates; only 23 crop classes; snapshot years, not a continuous daily phenology dataset. Confirm which Maharashtra crops map to classes. Do not use as the definitive current local crop calendar.
- **Reference paper:** [Nature Scientific Data](https://www.nature.com/articles/s41597-024-04313-w).

### Y-08. UPAg national crop calendar

- **Priority:** P1.
- **Availability:** interactive calendar/reference; bulk CSV/API access must be verified.
- **Link:** [UPAg Domestic Crop Calendar](https://upag.gov.in/national-calendar).
- **Use:** state/season/crop crop-calendar reference, then cross-check with Maharashtra SAUs/KVKs.
- **Caveat:** page references ICAR and historical horticulture references. Do not assume it contains validated variety-specific phenology or a bulk downloadable dataset.

### Y-09. Maharashtra university / ICAR crop recommendations

- **Priority:** P0 for approved recommendations; knowledge base rather than raw ML training data.
- **Sources:**
  - [MPKV research recommendations](https://mpkv.ac.in/Research/ResearchTechRecomm)
  - [MPKV extension publications](https://mpkv.ac.in/Extension/ExtensionPublication)
  - [PDKV recommendations](https://www.pdkv.ac.in/?page_id=124)
  - [PDKV extension publications](https://www.pdkv.ac.in/?page_id=2499)
  - [VNMKV recommendations](https://www.vnmkv.ac.in/FC_UniversityRecommendation.php)
  - [DBSKKV](https://www.dbskkv.org/)
  - [ICAR Kharif Agro-Advisories 2025](https://icar.org.in/sites/default/files/Circulars/ICAR%20En-Kharif%20Agro-Advisories%20for%20Farmers%202025.pdf)
  - [ICAR-CRIDA district contingency plans](https://www.icar-crida.res.in/Crop_Contingency_Plan.html)
  - [IMD current agromet advisories](https://mausam.imd.gov.in/responsive/agromet_adv_ser_state_current.php)
- **Use:** structured crop calendar, stages, variety suitability, weather sensitivity, cultivation and approved management actions.
- **Extraction schema:** crop, variety, state/zone/district applicability, season, stage, risk, condition, recommendation, units/rate if authoritative, source title/URL/page, publication year, validity/review date, expert reviewer.
- **Caveat:** many sources are PDFs or HTML recommendations, not numerical model-training datasets. Preserve exact source context and publication date; do not convert generic advice into universal thresholds without expert review.

### Y-10. CCE / DGCES plot-level yield observations

- **Priority:** P0 access request for validated plot-level yield prediction.
- **Availability:** access request; no verified open bulk Maharashtra raw-data download identified in this register.
- **Potential custodian:** Maharashtra Agriculture Department / Directorate of Economics and Statistics / responsible crop-estimation authorities.
- **System context:** Digital General Crop Estimation Survey and crop-cutting experiment processes are being digitised; public existence of the platform does not imply open access to all raw observations.
- **Request fields:** district/taluka/village, crop/variety, season/year, sample plot/location (de-identified as necessary), crop-cut area, harvest weight, moisture correction, yield per hectare, irrigation, sowing date, crop stage, measurement protocol, quality/verification and data-use terms.
- **Use:** field-level supervised yield modelling and independent yield validation.
- **Interim use:** APY supports district-level baselines only. Do not claim plot-level yield prediction from APY alone.

### Y-11. Field-level wheat management/weather/yield dataset (method-development reference)

- **Priority:** P2.
- **Availability:** research download.
- **Link:** [CIMMYT field-level wheat data](https://data.cimmyt.org/dataset.xhtml?persistentId=doi%3A10.71682%2F10549424).
- **Coverage described:** wheat fields in Bihar/eastern Uttar Pradesh, multiple seasons; field management, weather and measured yield.
- **Use:** study data schema, feature engineering and modelling methodology; write a reproducible prototype notebook if useful.
- **Caveat:** not Maharashtra and not a substitute for local validation. Check current access/licence metadata and do not transfer learned coefficients/thresholds without validation.

### Y-12. Pest and disease observation records — CROPSAP / HORTSAP / NPSS

- **Priority:** P0 access request for reliable pest/disease forecasting.
- **Availability:** portals/programmes identified; bulk historical data access not confirmed.
- **Sources:**
  - [ICAR-NCIPM database networking / CROPSAP reference](https://www.nriipm.res.in/databasenetworking.aspx)
  - [National Pest Surveillance System](https://npss.dac.gov.in/)
  - [HORTSAP portal](https://nriipm.res.in/Horticulture/Default.aspx)
- **Use:** verified time- and location-specific pest/disease incidence, severity and surveillance history.
- **Request fields:** date, district, taluka, village/coordinate (with permitted precision), crop, variety, crop stage, pest/disease taxon, incidence, severity scale, survey method, observer type, photo/evidence reference, control action, negative survey flag, verification status, source and licence.
- **Caveat:** an advisory bulletin is not a confirmed field observation. Ask for both positive and negative survey results and a data dictionary. Keep farmer-reported observations separate from expert-verified events.

### Y-13. Bhuvan Pest and Disease Surveillance

- **Priority:** P1.
- **Availability:** interactive portal; bulk export/API must be confirmed.
- **Link:** [Bhuvan Pest and Disease Surveillance](https://bhuvan-app1.nrsc.gov.in/pest/pest.php).
- **Filters described:** state, district, village, crop, pest, severity, source and date.
- **Use:** inspect event coverage and potentially obtain spatial observations under applicable terms.
- **Acquisition step:** test permitted export/API and document whether records can be downloaded at useful resolution. Do not scrape without terms/permission.

### Y-14. Crop pest/disease image dataset — ICAR rice and maize

- **Priority:** P2, optional image-identification module.
- **Availability:** hosted download on IndiaAI Aikosh.
- **Link:** [ICAR Crop Disease and Insect-pest Image Dataset for Rice and Maize](https://aikosh.indiaai.gov.in/home/datasets/details/crop_disease_and_insect_pest_image_dataset_for_rice_and_maize.html).
- **Contents:** annotated real-field images for rice and maize, including listed diseases, insect pests and healthy samples.
- **Licence:** ICAR Data Use License; read the full licence and attribution requirements before use.
- **Use:** image classification/detection prototype and computer-vision benchmarking.
- **Caveats:** static dataset, not a live village surveillance feed; it covers rice and maize rather than all Maharashtra crops. Inspect class balance, split by original field/source and avoid duplicate/near-duplicate leakage.

### Y-15. Multi-crop leaf disease image dataset

- **Priority:** P2.
- **Availability:** ZIP download.
- **Link:** [15 Crop and 45 Disease and Healthy Dataset — Mendeley](https://data.mendeley.com/datasets/8fr7grr73p/1).
- **Contents described:** cashew, cassava, tomato, potato, maize, papaya, sugarcane, rice, chilli, grapes, citrus, groundnut, cotton, wheat and soybean; multiple disease/healthy classes.
- **Licence:** CC BY 4.0 listed on the record; retain attribution and confirm any third-party component constraints.
- **Use:** image-model experiments and crop label taxonomy review.
- **Caveats:** large archive (listed around 4.15 GB), assembled from multiple image datasets and field captures; inspect duplicate images, capture conditions, class imbalance and geographic bias. Lab/clean leaf images may not generalise to field photos.

### Y-16. Sentinel-2 satellite imagery

- **Priority:** P1.
- **Availability:** download/API.
- **Publisher:** Copernicus.
- **Link:** [Copernicus Sentinel-2 Data Space](https://dataspace.copernicus.eu/data-collections/copernicus-sentinel-missions/sentinel-2).
- **Resolution:** selected visible/NIR bands at 10 m, other bands at 20 m or 60 m.
- **Use:** field-level vegetation time series, NDVI/EVI/NDMI, crop development anomalies and spatial comparison.
- **Processing:** retrieve Level-2A surface reflectance where suitable; apply cloud/shadow/quality masks; use plot polygon; calculate indices using documented bands; store acquisition time and pixel coverage; aggregate with valid-pixel fraction.
- **Caveats:** cloud cover and revisit gaps; field boundary accuracy matters; indices do not identify the cause of crop stress on their own.

### Y-17. MODIS vegetation indices

- **Priority:** P2.
- **Availability:** downloadable via NASA LP DAAC/LAADS.
- **Product:** MOD13Q1.
- **Link:** [MOD13Q1 documentation/download](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD13Q1).
- **Resolution/periodicity:** 250 m, 16-day composite.
- **Use:** longer regional vegetation-condition history and comparison with Sentinel-2.
- **Caveat:** too coarse for many small plots; do not treat as plot-specific ground truth.

### Y-18. Maharashtra irrigation statistics

- **Priority:** P1.
- **Availability:** downloadable third-party compilation and official interactive query tools; verify each file.
- **Potential sources:** [DES crop-irrigated-area report](https://data.desagri.gov.in/weblus/lus-crop-irrigated-area-report-web) and [Maharashtra State Data Bank](https://www.mahasdb.maharashtra.gov.in/rawData.do).
- **Availability caveat:** these are query/report interfaces until a specific export is tested. Do not treat the APY crop-wise collection as an irrigation dataset.
- **Use:** regional rainfed/irrigated context and crop vulnerability stratification.
- **Caveat:** district averages do not reveal the water reliability of an individual farm. Collect farmer-reported irrigation type/source/reliability progressively.

---

## 4. Soil dataset dependency — CropNet is the source of record

### SOIL-01. CropNet `UnifiedSoilProfile`

- **Priority:** P0 integration dependency.
- **Availability:** teammate-owned service/API; actual endpoint, authentication and schema must be confirmed with the CropNet team.
- **Expected parameters described by the team:** pH, organic carbon, sand/silt/clay fractions, USDA texture class, CEC and total nitrogen, with depth intervals (currently described as 0–5 cm and 5–15 cm), source/vintage/resolution/verification metadata, coverage and mapped soil zones.
- **Potential sources named in CropNet provenance:** SoilGrids 2.0, OpenLandMap, NATMO and laboratory-verified Soil Health Card values.
- **Use in Yield Intelligence:** soil pH/texture/organic-carbon/CEC/total-N context, depth-specific interpretation, mapped-zone boundaries and data quality.
- **Must preserve:** `map_derived_estimate`, `laboratory_verified`, `regional_estimate` and `not_available` distinctions; per-parameter units and depths; coverage; uncertainty if supplied.
- **Explicit non-inferences:**
  - Do not treat total N as available mineral N.
  - Do not fabricate available P or K from rasters.
  - Do not infer EC/salinity from pH.
  - Do not infer soil depth/bedrock from texture.
  - Do not infer plant-available water capacity from clay percentage alone.
  - Do not equate USDA texture class with soil taxonomic order such as Vertisol.
- **Fields to ask CropNet to clarify/expose, if available:** EC; available N/P/K only from verified lab tests; soil depth/depth to restrictive layer; coarse fragments; drainage class; hydraulic properties/available water capacity; deeper profile intervals; source uncertainty intervals.
- **Use policy:** Rashkar must not duplicate CropNet's soil raster extraction/OCR. Soil Health Card is optional and should enter through CropNet's supported upload/verification path.

### SOIL-02. SoilGrids 2.0 — optional source validation only

- **Priority:** P2; do not ingest as a duplicate production source unless needed for QA.
- **Link:** [ISRIC SoilGrids](https://www.isric.org/explore/soilgrids).
- **Use:** check CropNet's stated provenance, global soil property coverage and resolution/uncertainty methodology; only use independent comparison when compatible with variables, depths and version.
- **Caveat:** if CropNet already derives and serves SoilGrids, another Rashkar SoilGrids pipeline duplicates logic and risks inconsistent values. Coordinate with the CropNet owner first.

---

## 5. Heat-Risk Intelligence datasets

### H-01. ERA5-HEAT — UTCI and Mean Radiant Temperature

- **Priority:** P1 historical benchmark/context.
- **Availability:** downloadable/API through CDS.
- **Publisher:** Copernicus Climate Change Service / ECMWF.
- **Link:** [Thermal comfort indices derived from ERA5](https://cds.climate.copernicus.eu/datasets/derived-utci-historical).
- **Variables:** Mean Radiant Temperature (MRT) and Universal Thermal Climate Index (UTCI).
- **Use:** historical outdoor thermal-stress context, regional analysis, benchmarking and comparison with Rashkar's meteorological hazard calculations.
- **Caveat:** UTCI is not WBGT. Do not rename, convert or use UTCI values as WBGT thresholds. It is a reanalysis-derived estimate and not a direct worker exposure measurement.

### H-02. MODIS daily land-surface temperature — MOD11A1

- **Priority:** P1 supplementary spatial heat context.
- **Availability:** daily product download via NASA LAADS DAAC.
- **Publisher:** NASA MODIS Terra.
- **Link:** [MOD11A1 Collection 6.1](https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD11A1).
- **Resolution:** 1 km; daily; daytime and nighttime land-surface temperature plus quality/observation metadata.
- **Use:** identify regional surface-heating patterns and compare land-cover/land-surface context.
- **Caveat:** land-surface temperature is not near-surface air temperature, worker body temperature or WBGT. Respect cloud/quality flags and missing observations.

### H-03. NOAA GFS forecast

- **Priority:** P1 only after Maharashtra forecast validation.
- **Availability:** operational download/API.
- **Link:** [NOAA NOMADS GFS](https://www.nco.ncep.noaa.gov/pmb/products/gfs/nomads/).
- **Use:** supplementary short-range forecast input where required; compare against IMD and local observations.
- **Caveat:** retain model run, forecast lead and valid time. Do not merge runs without selecting a consistent forecast policy.

### H-04. IMD current observation, nowcast and forecast

- **Priority:** P0 operational source.
- **Availability:** API.
- **Link:** [IMD public APIs](https://api.imd.gov.in/public/api_reference.html).
- **Fields useful to worker heat-risk:** current temperature, humidity, wind speed/direction, observation time, rainfall; AWS/ARG data where available; district/station nowcasts and district warnings; forecast feeds where their variables and horizons are sufficient.
- **Use:** operational weather features and time-stamped refreshes.
- **Caveat:** do not claim a field-level 30-minute fresh sensor update if the latest provider observation is older. Display `observed_at`, `issued_at`, `valid_at` and `data_age`.

### H-05. Historical hourly weather for WBGT estimation

- **Priority:** P0.
- **Availability:** ERA5-Land download/API; IMD station/AWS observations where accessible.
- **Sources:** S-02 and S-04 above.
- **Use:** calculate/reconstruct the required meteorological inputs to an approved outdoor thermal-hazard method; backtest by time-of-day, season and land-cover/exposure context.
- **Critical requirement:** the selected WBGT estimation method must specify which inputs are required (air temperature, humidity/dewpoint, wind, radiation/globe-temperature approximation, pressure/altitude as appropriate) and how missing inputs are handled. Temperature and humidity alone are not enough for a defensible outdoor radiant-heat estimate.

### H-06. Occupational heat labour-capacity dataset

- **Priority:** P2 research reference.
- **Availability:** research download.
- **Link:** [Global gridded occupational heat-stress labour capacity dataset](https://zenodo.org/records/21636524).
- **Use:** regional climate/labour-capacity context and method comparison.
- **Caveat:** not individual worker exposure or Maharashtra hourly WBGT labels; scenarios and assumptions must be understood before use.

### H-07. Indian outdoor worker WBGT study — request data, not direct bulk download

- **Priority:** P1 access request / reference.
- **Reference:** [Scientific Reports paper on heat stress and outdoor labour productivity in Southern India](https://www.nature.com/articles/s41598-026-41807-6).
- **Study context reported:** outdoor workers in multiple Tamil Nadu districts, including agricultural workers, with WBGT and worker/workload observations.
- **Availability:** publication is accessible; raw data availability is subject to the authors' data-sharing terms and request process. Do not claim the raw dataset is a direct open download.
- **Use:** design validation variables, survey questions and data collection methodology; request de-identified data and data dictionary if useful.
- **Caveat:** Tamil Nadu workers/conditions are not automatically representative of Maharashtra. Use as a methodological reference, not local ground truth.

### H-08. Maharashtra worker heat validation dataset

- **Priority:** P0 pilot collection for validating worker risk.
- **Availability:** must be collected with a research partner; measurement devices are for research reference only, not a farmer product requirement.
- **Proposed observations:**
  - pseudonymous study ID and consent record;
  - date/time and worksite coordinates at an approved precision;
  - reference-measured WBGT and instrument/calibration details;
  - temperature, humidity, wind and radiation inputs where independently available;
  - sun/shade, task/workload category, work duration and break/rest opportunity;
  - clothing category and acclimatisation category if approved by study protocol;
  - optional symptom/perceived exertion/productivity outcome questionnaire subject to ethics review;
  - environmental and worker-data missingness/quality flags.
- **Use:** compare WBGT proxy to measured WBGT; assess timing and category error; build a local validation set.
- **Governance:** informed consent, ethics/IRB or institutional review as applicable, privacy minimisation, de-identification, controlled access and retention policy.

### H-09. Crop heat threshold knowledge base

- **Priority:** P0 for crop heat-risk pathway.
- **Availability:** build from verified publications/recommendations; not one universal ready-made CSV dataset identified.
- **Sources:** MPKV, PDKV, VNMKV, DBSKKV, ICAR commodity institutes and relevant peer-reviewed crop physiology research.
- **Required record:** crop, variety (if relevant), phenological stage, temperature/radiation/water variable, threshold, required duration, expected impact, region, source title/URL/page, publication date, evidence grade, expert reviewer and review date.
- **Use:** crop-specific heat exposure assessment; never apply one generic temperature cutoff to all crops/stages.
- **Caveat:** scientific thresholds may depend on cultivar, humidity, exposure duration, night temperature, water status and stage. Store conditions and source notes, not just a single number.

---

## 6. Dataset acquisition order and exact processing workflow

### Batch A — start immediately

1. Download one Maharashtra APY master dataset from Y-01.
2. Download the matching official OGD resource Y-02 for cross-checking.
3. Obtain AgERA5 v2 for Maharashtra, initially a limited pilot period and selected points/grid cells.
4. Obtain IMD rainfall NetCDF for the same period and geography.
5. Obtain ERA5-Land hourly sample for the pilot areas and a representative warm season.
6. Register an IMD API account/access if required and test the relevant APIs.
7. Obtain boundary layers for Maharashtra districts and talukas.
8. Obtain MIRCA-OS calendar files and inspect crop-code coverage.
9. Obtain CropNet service documentation and test one synthetic/de-identified farm profile.

### Batch B — crop and soil integration

1. Build a canonical crop-code dictionary and APY alias map.
2. Build crop-season mapping and region-specific calendar reference table.
3. Extract crop-stage/recommendation records from MPKV, PDKV, VNMKV, DBSKKV, ICAR and IMD sources.
4. Integrate CropNet output exactly as received, with provenance and missingness preserved.
5. Establish CropNet fields that are absent (EC, available NPK, soil depth, water capacity, etc.) and display those absences.
6. Build initial weather and soil feature tables by plot/crop cycle.

### Batch C — external access requests

Send requests to the relevant Maharashtra authorities and institutions for:
- CCE/DGCES crop-cutting records, crop-cut area, weight and yield calculations.
- CROPSAP/HORTSAP/NPSS historical pest and disease observations, including negative survey results.
- Relevant IMD station/AWS observations or permissible archived data for validation.
- Crop heat threshold references and technical review from SAUs/ICAR institutes.
- De-identified WBGT/worker data from relevant Indian research groups where sharing is allowed.

### Batch D — Heat-Risk validation pilot

1. Select participating research/academic partner and pilot agricultural work settings.
2. Agree measurement protocol, reference instrument, calibration and sampling time.
3. Get ethics/consent approval as required.
4. Record reference WBGT and context variables for multiple days and conditions.
5. Compare against the selected WBGT proxy calculation.
6. Analyse bias, MAE/RMSE, risk category agreement and error by sun/shade/workload/time of day.
7. Refine model only after the proxy is demonstrably suitable for the intended alert use.

---

## 7. Canonical feature tables to create

### 7.1 `weather_daily_features`

Suggested fields:
- `location_id`, `grid_id`, `date_local`, `source_id`, `source_version`.
- `precipitation_mm`, `tmax_c`, `tmin_c`, `tmean_c`, `rh_mean_pct`, `rh_max_pct`, `rh_min_pct`.
- `wind_speed_ms`, `solar_radiation_mj_m2`, `vpd_kpa`, `et0_mm`.
- `rain_3d_mm`, `rain_7d_mm`, `rain_14d_mm`, `rain_30d_mm`.
- `consecutive_dry_days`, `heavy_rain_days_7d`, `hot_days_7d`, `warm_nights_7d`.
- quality flags, data age and feature-generation version.

Only populate variables actually provided or calculated by documented transformations. Keep source-specific data and calculated features separately auditable.

### 7.2 `weather_hourly_features`

Suggested fields:
- `location_id`, `grid_id`, `valid_time_utc`, `valid_time_local`.
- `source_id`, `run_id`, `issued_at`, `lead_hours`.
- `air_temperature_c`, `dewpoint_c`, `relative_humidity_pct`, `wind_speed_ms`, `shortwave_radiation_w_m2`, `pressure_hpa`, `cloud_cover_pct`.
- derived thermal inputs, quality flags and missing-input flags.

### 7.3 `crop_cycle_features`

Suggested fields:
- `farm_id`, `plot_id`, `crop_cycle_id`, `crop_code`, `variety_code`, `season`, `sowing_date`, `stage_code`, `stage_source`.
- weather windows and threshold exceedance counters.
- soil profile snapshot reference and per-parameter confidence.
- irrigation status/source and farmer-confirmed management fields.
- APY regional baseline features with geographic-level label.

### 7.4 `pest_disease_events`

Suggested fields:
- event ID, observed date/time, location, crop, variety, stage.
- pest/disease code, incidence percentage, severity scale/value.
- survey method, observer class, evidence/photo reference.
- verified status, verification time and source.
- explicit `survey_negative` flag; no event row must not automatically mean no pest.

### 7.5 `worker_heat_validation`

Suggested fields:
- pseudonymous study ID, consent version, date/time and location precision.
- measured WBGT, instrument ID, calibration date and measurement protocol.
- air temperature, humidity, wind and radiation where recorded.
- workload, sun/shade, work/rest intervals and optional approved context variables.
- optional outcome/symptom fields only if approved.
- missingness and quality flags.

---

## 8. Quality assurance and acceptance checks

### Weather
- Confirm units: precipitation mm, temperature °C, wind m/s or km/h (normalise and retain original), radiation units, RH percentage, ET0 mm/day.
- Check time zone and local-day aggregation policy.
- Check missing grid cells, duplicate timestamps and forecast run consistency.
- Compare AgERA5 rainfall with IMD gridded rainfall without adding them.
- Validate station matchups where IMD observations are available.
- Record source data age and forecast lead.

### APY and crop statistics
- Area > 0 before calculating yield.
- Production/area unit consistency.
- Detect duplicates across mirrored files.
- Normalise crop/district/season spellings while retaining original text.
- Check district boundary changes and missing years.
- Flag implausible values for manual review, never silently delete.

### Crop calendar and recommendations
- Preserve source publication year and geography.
- Confirm crop/variety/season applicability.
- Distinguish a calendar estimate from farmer sowing date.
- Review stage-specific thresholds with a qualified agronomist.

### Soil/CropNet
- Preserve null/NOT_AVAILABLE, units and depth intervals.
- Check polygon coverage and raster resolution against farm size.
- Store per-parameter verification and source metadata.
- Do not present map estimates as lab tests.

### Pest/disease
- Separate observed, farmer-reported, expert-verified and advisory-only records.
- Standardise taxonomy and severity scales.
- Retain survey-negative events.
- Check observation date and source precision.
- Split train/test by geography and time; group images by original source/plant/field to avoid leakage.

### Heat
- Never equate UTCI, land-surface temperature or air temperature with WBGT.
- Preserve reference instrument, calibration and measurement method.
- Validate estimated WBGT with measured WBGT across sun/shade and workloads.
- Keep worker-health outcomes separate from environmental exposure estimates.
- Do not deploy unsupported medical or clinical claims.

---

## 9. Access-request checklist and data request template

When requesting CCE, pest/disease or worker heat data, ask the provider to confirm:

1. Does the requested dataset exist for Maharashtra? Which years and districts/talukas?
2. Can the data be shared for research/product development? Under what agreement?
3. Is bulk download/API access available? What are the formats and update cadence?
4. What is the complete data dictionary, units and codes?
5. What are the geographic and temporal precision levels?
6. How are observations verified, and are negative survey results retained?
7. Are there missing years, revised records or known biases?
8. What licence, attribution, redistribution and commercial-use conditions apply?
9. Can a small anonymised sample be shared first for schema review?
10. Who is the technical/data steward for follow-up?

**Suggested request wording:**

> We are developing Rashkar, a cloud-based agricultural climate-risk decision-support platform. We are requesting access to an anonymised, structured sample and, if permitted, historical records for Maharashtra for research, model development and validation. Please share the data dictionary, coverage by year/district/crop, spatial and temporal precision, verification methodology, file format/API documentation, licence and restrictions on commercial use or redistribution. We will not publish personal or restricted records and can work under the institution's data-sharing agreement.

---

## 10. Recommended data storage layout

```text
RASHKAR_DATA/
  00_REGISTRY/
    dataset_register.csv
    crop_code_dictionary.csv
    district_taluka_code_map.csv
    source_licences_and_terms/
  01_RAW_IMMUTABLE/
    WEATHER/
      AGERA5_V2/
      ERA5_LAND/
      IMD_RAINFALL/
      IMD_API_SNAPSHOTS/
      NOAA_GFS_OPTIONAL/
    CROP_STATISTICS/
      APY/
      OGD_CROSSCHECK/
      MAHASDB/
      HORTICULTURE/
    CROP_CALENDARS/
      MIRCA_OS/
      UPAG/
      SAU_ICAR_REFERENCE_DOCS/
    PEST_DISEASE/
      CROPSAP_REQUESTED/
      HORTSAP_REQUESTED/
      NPSS_REQUESTED/
      BHUVAN/
      IMAGE_DATASETS/
    HEAT/
      ERA5_HEAT/
      MODIS_LST/
      WORKER_STUDIES/
      WBGT_PILOT/
    GEO/
      DISTRICT_TALUKA_BOUNDARIES/
      SENTINEL2/
      MODIS_VI/
  02_PROCESSED/
    WEATHER_DAILY/
    WEATHER_HOURLY/
    APY_CANONICAL/
    CROP_CALENDARS_CANONICAL/
    CROP_KNOWLEDGE_CANONICAL/
    SATELLITE_INDICES/
    SOIL_PROFILE_SNAPSHOTS/
    PEST_DISEASE_EVENTS/
    HEAT_VALIDATION/
  03_FEATURES/
    YIELD_INTELLIGENCE/
    WORKER_HEAT_RISK/
    CROP_HEAT_RISK/
  04_LABELS/
    PLOT_YIELD_CCE/
    PEST_DISEASE_VERIFIED/
    WBGT_WORKER_VALIDATION/
  05_MODELS/
    EXPERIMENTS/
    MODEL_ARTIFACTS/
  06_DOCUMENTATION/
    DATA_DICTIONARIES/
    QUALITY_REPORTS/
    LICENCE_AUDIT/
```

Use cloud object storage for actual production data. This directory is a logical layout; do not commit large or restricted data files into Git.

---

## 11. What is sufficient to begin and what blocks validated claims?

### Can start the first data pipeline
- APY district/crop/season/year data.
- AgERA5 v2 daily weather.
- IMD rainfall history.
- ERA5-Land hourly weather.
- IMD API access for current conditions and forecasts.
- CropNet soil profile integration.
- Crop calendars and verified crop knowledge references.
- Maharashtra administrative boundaries.

### Can start a transparent rule-based first release
- Weather-related dry-spell, excess rainfall and heat exposure signals.
- Soil pH/texture/SOC/CEC contextual constraints, preserving the map/lab distinction.
- Crop-stage estimates with confidence.
- Crop-specific crop heat exposure where sourced thresholds exist.
- Worker heat hazard estimate only after the thermal method is reviewed and inputs are adequate; initially mark it as an estimate and validate it.

### Still needed for stronger supervised models and validation
- Maharashtra plot-level CCE/DGCES yield records or equivalent verified farm harvest data.
- Structured CROPSAP/HORTSAP/NPSS pest/disease observations.
- Maharashtra reference WBGT/work-context observations collected with a research partner.
- Local crop/variety/stage heat-sensitivity evidence.
- Wider, representative crop and district coverage.

**Do not block all engineering while waiting for restricted datasets.** Build the ingest/feature/rule foundations with accessible data, but do not claim supervised farm-level predictive performance before the labels and validation exist.
