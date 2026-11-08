There are three related but different concepts that we should not mix up.

|Capability|Question it answers|
|---|---|
|Yield Risk Assessment|What could go wrong with this farmer's crop?|
|Yield Prediction|How much produce might this farmer harvest?|
|Yield Improvement|What can the farmer do to improve production?|

# Yield Risk Assessment

### The actual objective

Consider a farmer who has planted two acres of cotton.

Rashkar knows the farmer's approximate location, crop, sowing date, soil information and irrigation availability. It also gathers historical and current weather information.

The engine should identify possible threats such as:

- A prolonged dry spell.
    
- Excessive rainfall or waterlogging.
    
- High-temperature stress.
    
- Pest infestation.
    
- Crop diseases.
    
- Soil-related constraints.
    
- Unfavourable crop-stage conditions.

It should then answer:

**"Which risks are relevant to this particular crop, how serious could they become, and what should the farmer do now?"

### Types of risks

1. Weather and climate risk

Drought, dry spells, excessive rainfall, flooding, heat stress, cold stress, and unusual seasonal weather.

2. Pest risk

Crop-specific insect threats, infestation conditions and pest-development stages.

3. Disease risk

Fungal, bacterial and viral disease threats, including conditions that favour their development.

4. Soil and water risk

Nutrient deficiencies, unsuitable soil pH, salinity, poor drainage and insufficient water availability.

5. Crop-stage risk

Risks that become especially important during germination, vegetative growth, flowering, fruiting and maturity.


### Information we need

| Field             | How to obtain it                         | Example                 |
| ----------------- | ---------------------------------------- | ----------------------- |
| Crop              | Farmer selection                         | Cotton                  |
| Crop variety      | Farmer selection                         | Farmer-selected variety |
| Sowing date       | Farmer selection                         | 15 June                 |
| Irrigation        | Farmer selection                         | Rain-fed                |
| Irrigation source | Farmer selection                         | Borewell / canal / pond |
| Previous harvest  | Optional farmer record                   | 8 quintals/acre         |
| Location          | GPS or village selection                 | Nagpur, Maharashtra     |
| Farm boundary     | Optional map drawing                     | 2-acre plot             |
| Crop stage        | Date-based estimate, farmer confirmation | Flowering               |
| Soil type         | Farmer selection or verified soil data   | Black soil              |
| Soil pH           | Soil Health Card, if available           | 7.5                     |
| Soil nutrients    | Soil Health Card, if available           | N, P, K, organic carbon |
You may eventually collect more information, but we should not ask for everything at registration.

### Datasets

#### Dataset A: Historical crop production and yield

[DES — Area, Production and Yield reports](https://data.desagri.gov.in/website/crops-apy-report-web?utm_source=chatgpt.com)
	There is also the Open Government Data dataset for district-wise, season-wise crop production statistics. It describes crop area and production by district, crop, season and year.

#### Dataset B: Historical and current weather

	We need weather data across several growing seasons.

Core variables:

| Variable             | Why needed                             |
| -------------------- | -------------------------------------- |
| Daily rainfall       | Drought and excess rainfall assessment |
| Maximum temperature  | Heat stress                            |
| Minimum temperature  | Temperature-related crop stress        |
| Relative humidity    | Disease-conducive conditions           |
| Wind speed           | Evapotranspiration and weather context |
| Solar radiation      | Evaporative demand                     |
| Consecutive dry days | Dry-spell assessment                   |

[IMD official data access portal](https://api.imd.gov.in/public/?utm_source=chatgpt.com) The current IMD API catalogue lists weather forecasts, rainfall, current observations, warnings and agrometeorological advisories.

For historical climate data, we can investigate IMD gridded datasets and ERA5/ERA5-Land. Access arrangements, temporal coverage and spatial resolution need to be checked for each dataset before we build the data pipeline.
We can use ERA5 as a supplementary historical source:
[Copernicus Climate Data Store](https://cds.climate.copernicus.eu/?utm_source=chatgpt.com) 


#### Dataset C: Soil information
	We need:
- pH.
- Electrical conductivity.
- Organic carbon.
- Nitrogen.
- Phosphorus.
- Potassium.
- Soil texture.
- Available soil-water information, where obtainable.

The first version can accept a Soil Health Card upload. Later, we can investigate soil maps and authorized soil-data integrations.

#### Dataset D: Agricultural recommendations and crop knowledge

We need reliable information about cotton growth stages, regional cultivation practices, pests, diseases and management.

A good starting reference is the ICAR Kharif Agro-Advisory for Farmers 2025.

It contains a specific Maharashtra and Vidarbha section, rather than only generic all-India advice. It covers cotton practices, planting periods, soil testing, water management and crop protection.

[ICAR Kharif Agro-Advisories 2025](https://icar.org.in/sites/default/files/Circulars/ICAR%20En-Kharif%20Agro-Advisories%20for%20Farmers%202025.pdf?utm_source=chatgpt.com)

It identifies Vidarbha as including Nagpur, Akola, Amravati, Yavatmal, Wardha, Buldhana, Washim, Bhandara, Chandrapur, Gondia and Gadchiroli. Its cotton advisory provides a region-specific starting point for our prototype.


#### Dataset E: Pests and diseases

We need two types of information:

1. Knowledge data: What pests and diseases affect cotton, what symptoms they cause, and when they are relevant.

2. Observation data: Whether a particular pest or disease was actually observed in a particular location and crop stage.

[Cotton integrated pest management reference](https://agritech.tnau.ac.in/crop_protection/crop_prot_ipm_cotton.html?utm_source=chatgpt.com)

#### Dataset F: Satellite and geographical data

[ISRO Bhuvan](https://bhuvan.nrsc.gov.in/?utm_source=chatgpt.com)


## Dataset 1 — Maharashtra district-wise, crop-wise Area, Production and Yield (APY)

Highest priority

CSV / XLSX / JSON

[Soyabean production estimated to increase by 6 percent despite decreased cultivation area - Farmer News: Government Schemes for Farmers, Successful Farmer Stories](https://images.openai.com/static-rsc-4/hRPX655ajvnJAHCV9J_nstEbLki7DZgnAQdiwy75mgyCHfF-ph-FQGbG-zAgsSpeGX6Jxs4dUje_5XBCgc2c2YNtegTCZzjG-tyNgq4Wx88ZgCpGtziPh-WmqE9NS1QRUcjIGzF5FtnjWb62J1D235hBOBJrFB0WTwCsXQMTNzM?purpose=inline)

Source: Ministry of Agriculture and Farmers Welfare

Time period: 1997–98 to 2024–25

Geographical detail: State, district, crop and season.

Formats: CSV, XLSX and JSON.

Download dataset

[Maharashtra District, Season and Crop-wise APY dataset](https://dataful.in/datasets/5632/?utm_source=chatgpt.com)

The dataset page offers direct CSV, XLSX and JSON downloads. It is a third-party distribution of Ministry data, so retain the original source attribution and check its terms.

## Dataset 2 — District-wise, season-wise crop production statistics

High priority

CSV / ZIP

Source: Official Open Government Data platform, Government of India.

[Download district-wise crop production statistics](https://www.data.gov.in/resource/district-wise-season-wise-crop-production-statistics-1997?utm_source=chatgpt.com)

This contains district-wise, crop-wise, season-wise and year-wise agricultural statistics, including:

- Crop-covered area in hectares.
    
- Production in tonnes.
    
- Historical records starting from 1997.

## Dataset 3 — Crop-specific APY collection

High priority

CSV / XLSX / Parquet

[Open all crop-wise APY datasets](https://dataful.in/collections/964/?utm_source=chatgpt.com)

This collection contains 55 individual crop datasets from the Ministry of Agriculture and Farmers Welfare.

Examples listed include:

- Rice.
    
- Maize.
    
- Moong.
    
- Urad.
    
- Sesamum.
    
- Groundnut.
    
- Rapeseed and mustard.
    
- Sugarcane.
    
- Arhar (Tur).
    
- Wheat.
    

The datasets include state, district, season and year information, with downloads in CSV, XLSX and Parquet formats. You can filter the data for Maharashtra


## Dataset 4 — Maharashtra State Data Bank: agricultural raw data

High priority

[Maharashtra State Data Bank — Raw Data](https://www.mahasdb.maharashtra.gov.in/rawData.do?utm_source=chatgpt.com)

This is an official Maharashtra government data source.

It provides a raw-data selection interface with:

- District.
    
- Year.
    
- Agriculture and Allied Activities — Production Crops.
    
- Agriculture and Allied Activities — Irrigation Area.
    

It is useful for retrieving Maharashtra-specific district statistics. The exact export format and available historical coverage need to be checked for each selection.

MahasDB+1

Use: Supplement the national APY data with Maharashtra government statistics, particularly irrigation and production-related information.


## Dataset 5 — Horticulture crop statistics

High priority for horticulture

[Horticulture crop statistics collection](https://dataful.in/collections/336/?utm_source=chatgpt.com)

This is particularly important because Rashkar should not be restricted to traditional field crops.

The collection contains 12 horticulture statistics datasets covering:

- Fruits.
    
- Vegetables.
    
- Flowers.
    
- Spices.
    
- Horticulture area and production.
    
- Crop-group productivity.


## Dataset 6 — Pune district soil macro-nutrient dataset

Downloadable dataset

[Download Soil Macro Nutrient Dataset for Fertilizer Combinations Advice, Pune](https://data.mendeley.com/datasets/tfvgnm8rxt/1?utm_source=chatgpt.com)

Geographical coverage: Selected Pune district areas.

Years: 2016, 2017 and 2018.

Licence: CC BY 4.0.

Format: Dataset files available through Download All.


## BHOOMI soil and land-resource layers

[Open ICAR-NBSS&LUP BHOOMI Geoportal](https://bhoomigeoportal-nbsslup.in/BHOOMI_StateWise/?utm_source=chatgpt.com)

This portal provides Maharashtra selection and thematic layers for:

- Soil properties.
    
- Soil fertility.
    
- Nutrient status.
    
- Land degradation.
    
- Agro-ecology.
    
- Terrain.
    
- Land-use planning.
    
- Soil Health Card lookup.

## Dataset 8 — National Pest Surveillance System (NPSS)

Accessible platform; bulk-data access to verify

[National Pest Surveillance System](https://npss.dac.gov.in/?utm_source=chatgpt.com)

This is an official pest-surveillance system listed by ICAR-NCIPM.

## Dataset 9 — CROPSAP Maharashtra

Important; request structured records

[ICAR-NCIPM CROPSAP information](https://www.nriipm.res.in/databasenetworking.aspx?utm_source=chatgpt.com)

CROPSAP is particularly valuable because it covers multiple Maharashtra crops.

The 2025–26 programme reports surveillance across eight target crops over 174.04 lakh hectares and more than 2,764 pest-management advisories. Its associated insecticide/fungicide calculation applications cover:

- Rice.
    
- Soybean.
    
- Cotton.
    
- Pigeon pea.
    
- Chickpea.
    
- Maize.
    
- Sugarcane.
    
- Sorghum.

## Dataset 10 — Bhuvan Pest and Disease Surveillance

[Open ISRO Bhuvan Pest and Disease Surveillance](https://bhuvan-app1.nrsc.gov.in/pest/pest.php?utm_source=chatgpt.com)

The portal allows filtering observations by state, district, village, crop, pest, severity, source and date.

It is a useful source for geographical pest and disease observations.



### Step three: turn all that data into ML features.

### Step four: design the actual AI models




