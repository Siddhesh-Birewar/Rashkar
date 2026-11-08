# Graph Report - Rashkar  (2026-11-07)

## Corpus Check
- Corpus is ~12,813 words - fits in a single context window. You may not need a graph.

## Summary
- 149 nodes · 146 edges · 12 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Subsystem 0
- Subsystem 1
- Subsystem 2
- Subsystem 3
- Subsystem 4
- Subsystem 5
- Subsystem 6
- Subsystem 7
- Subsystem 8
- Subsystem 9
- Subsystem 10
- Subsystem 11

## God Nodes (most connected - your core abstractions)
1. `3. Yield Intelligence datasets` - 19 edges
2. `Yield Risk Assessment` - 15 edges
3. `Rashkar — Yield Intelligence & Heat-Risk Intelligence` - 13 edges
4. `Rashkar — Dataset Register and Usage Guide` - 13 edges
5. `7. Exact implementation sequence` - 10 edges
6. `5. Heat-Risk Intelligence datasets` - 10 edges
7. `2. Feature One — Yield Intelligence` - 7 edges
8. `2.4 Risk components and technical approach` - 7 edges
9. `2. Shared datasets — both Yield Intelligence and Heat-Risk Intelligence` - 7 edges
10. `8. Quality assurance and acceptance checks` - 7 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Communities (12 total, 0 thin omitted)

### Community 0 - "Subsystem 0"
Cohesion: 0.09
Nodes (22): 10. Explicitly out of scope for this phase, 11. Decisions required from the repository-specific execution plan, 1.1 Non-negotiable principles, 1.2 Initial geography and coverage policy, 1. Product vision and operating principles, 4.1 Recommended default, 4.2 Cloud architecture, 4.3 Architecture diagram (+14 more)

### Community 1 - "Subsystem 1"
Cohesion: 0.10
Nodes (20): 10. Recommended data storage layout, 11. What is sufficient to begin and what blocks validated claims?, 1. How to read this register, 4. Soil dataset dependency — CropNet is the source of record, 6. Dataset acquisition order and exact processing workflow, 9. Access-request checklist and data request template, Availability labels, Batch A — start immediately (+12 more)

### Community 2 - "Subsystem 2"
Cohesion: 0.11
Nodes (19): 3. Yield Intelligence datasets, Y-01. Maharashtra district/season/crop APY, Y-02. Official OGD district-wise, season-wise crop production statistics, Y-03. Crop-specific APY collection, Y-04. DES APY report/query interface, Y-05. Maharashtra State Data Bank agricultural raw data, Y-06. Horticulture statistics collection, Y-07. Crop calendar — MIRCA-OS (+11 more)

### Community 3 - "Subsystem 3"
Cohesion: 0.12
Nodes (16): BHOOMI soil and land-resource layers, Dataset 10 — Bhuvan Pest and Disease Surveillance, Dataset 1 — Maharashtra district-wise, crop-wise Area, Production and Yield (APY), Dataset 2 — District-wise, season-wise crop production statistics, Dataset 3 — Crop-specific APY collection, Dataset 4 — Maharashtra State Data Bank: agricultural raw data, Dataset 5 — Horticulture crop statistics, Dataset 6 — Pune district soil macro-nutrient dataset (+8 more)

### Community 4 - "Subsystem 4"
Cohesion: 0.15
Nodes (13): 2.1 Purpose, 2.2 Feature scope, 2.3 Farmer inputs and profile, 2.4 Risk components and technical approach, 2.5 Yield Intelligence outputs, 2.6 Farmer-facing screens, 2. Feature One — Yield Intelligence, A. Weather and climate risk (+5 more)

### Community 5 - "Subsystem 5"
Cohesion: 0.20
Nodes (10): 7. Exact implementation sequence, Phase 0 — Repository discovery and planning (no implementation changes), Phase 1 — Data contracts and registry, Phase 2 — Shared geospatial and weather pipeline, Phase 3 — Crop catalogue, calendar and crop knowledge, Phase 4 — Yield Intelligence v1 (rules and baselines), Phase 5 — Heat-Risk v1 (hazard calculation and transparent rules), Phase 6 — Label acquisition and ML readiness (+2 more)

### Community 6 - "Subsystem 6"
Cohesion: 0.20
Nodes (10): 5. Heat-Risk Intelligence datasets, H-01. ERA5-HEAT — UTCI and Mean Radiant Temperature, H-02. MODIS daily land-surface temperature — MOD11A1, H-03. NOAA GFS forecast, H-04. IMD current observation, nowcast and forecast, H-05. Historical hourly weather for WBGT estimation, H-06. Occupational heat labour-capacity dataset, H-07. Indian outdoor worker WBGT study — request data, not direct bulk download (+2 more)

### Community 7 - "Subsystem 7"
Cohesion: 0.22
Nodes (9): 3.1 Purpose, 3.2 Worker heat-risk pathway, 3.3 Crop heat-risk pathway, 3.4 Heat-risk outputs, 3.5 Heat-risk farmer-facing flow, 3. Feature Two — Heat-Risk Intelligence, Inputs, WBGT / thermal hazard calculation (+1 more)

### Community 8 - "Subsystem 8"
Cohesion: 0.29
Nodes (7): 2. Shared datasets — both Yield Intelligence and Heat-Risk Intelligence, S-01. AgERA5 v2 — daily agrometeorological indicators, S-02. ERA5-Land — hourly land reanalysis, S-03. IMD daily gridded rainfall — 0.25°, S-04. IMD public weather APIs, S-05. Survey of India / administrative boundary layers, S-06. NOAA GFS 0.25° forecast — optional supplementary forecast

### Community 9 - "Subsystem 9"
Cohesion: 0.29
Nodes (7): 8. Quality assurance and acceptance checks, APY and crop statistics, Crop calendar and recommendations, Heat, Pest/disease, Soil/CropNet, Weather

### Community 10 - "Subsystem 10"
Cohesion: 0.29
Nodes (7): Dataset A: Historical crop production and yield, Dataset B: Historical and current weather, Dataset C: Soil information, Dataset D: Agricultural recommendations and crop knowledge, Dataset E: Pests and diseases, Dataset F: Satellite and geographical data, Datasets

### Community 11 - "Subsystem 11"
Cohesion: 0.33
Nodes (6): 7.1 `weather_daily_features`, 7.2 `weather_hourly_features`, 7.3 `crop_cycle_features`, 7.4 `pest_disease_events`, 7.5 `worker_heat_validation`, 7. Canonical feature tables to create

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Rashkar — Dataset Register and Usage Guide` connect `Subsystem 1` to `Subsystem 2`, `Subsystem 6`, `Subsystem 8`, `Subsystem 9`, `Subsystem 11`?**
  _High betweenness centrality (0.188) - this node is a cross-community bridge._
- **Should `Subsystem 0` be split into smaller, more focused modules?**
  _Cohesion score 0.08695652173913043 - nodes in this community are weakly interconnected._
- **Why does `Rashkar — Yield Intelligence & Heat-Risk Intelligence` connect `Subsystem 0` to `Subsystem 4`, `Subsystem 5`, `Subsystem 7`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Should `Subsystem 1` be split into smaller, more focused modules?**
  _Cohesion score 0.09523809523809523 - nodes in this community are weakly interconnected._
- **Why does `3. Yield Intelligence datasets` connect `Subsystem 2` to `Subsystem 1`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Should `Subsystem 2` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._
- **Should `Subsystem 3` be split into smaller, more focused modules?**
  _Cohesion score 0.11764705882352941 - nodes in this community are weakly interconnected._