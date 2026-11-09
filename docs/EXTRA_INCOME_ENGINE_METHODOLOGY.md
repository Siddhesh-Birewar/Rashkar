# Extra Income & Farm Diversification Engine — Scientific Methodology & Architecture

## 1. Executive Summary & Design Rationale

The **Extra Income & Farm Diversification Engine** in Rashkar was completely rebuilt to move away from predetermined commercial catalogues towards **farmer-personalized opportunity discovery**. Rather than asking *"What commercial agriculture enterprise can I sell to this farmer?"*, the engine answers:

> *"Given the exact resources, byproducts, spare land, water window, family labour, and capital I already have on my farm, what additional income can I realistically earn or what input expenses can I eliminate without taking destructive financial risks?"*

---

## 2. The 5 Opportunity Discovery Categories

Opportunities are classified and prioritized across five progressive tiers:

### Category A: Zero-Additional-Cash-Cost Opportunities (Evaluated First)
*   **On-Farm Crop Residue Composting (`OPP_COMPOST_COST_SAVING_01`)**: Converts harvested crop biomass (soybean straw, cotton stalks, jowar stover) and cow dung into high-grade organic manure. Replaces 8–12 bags of commercial DAP/Urea, eliminating ₹14,000/year in input expenses at ₹0 upfront capital.
*   **Collective Grain Aggregation & APMC Grading (`OPP_DIRECT_APMC_FPO_01`)**: Simple manual sieving, moisture checking, and collective aggregation with the local FPO capture a ₹250–₹350/quintal quality premium over distressed local trader gates.
*   **Local Farm Equipment Sharing & Custom Hiring Pool (`OPP_EQUIPMENT_SHARING_01`)**: Custom hiring of farm tractor implements or sprayers during idle weekday windows.

### Category B: Very Low-Cost Opportunities (< ₹15,000 Outlay)
*   **Field Boundary Drumstick / Moringa Plantation (`OPP_MORINGA_BUND_01`)**: Cultivating 40–50 PKM-1 hybrid drumstick saplings on uncultivated field bunds using surplus runoff. Capital: ₹3,500; Annual Profit: ₹28,000.
*   **Smallholder Backyard Poultry (`OPP_DESI_POULTRY_LOW_COST_01`)**: 20-bird indigenous Aseel/Kadaknath scavenged backyard flock. Capital: ₹4,500; Annual Profit: ₹18,000.
*   **Azolla Bed Livestock Feed Supplement (`OPP_AZOLLA_FEED_SAVING_01`)**: 12x4 ft silpaulin pit growing protein-rich aquatic fern. Saves 25% of commercial cattle feed purchases (₹11,000/year saved on a ₹2,200 setup).

### Category C: Low-to-Moderate Enterprise Units
*   **Starter Indigenous Osmanabadi Goat Unit (2 Does + 1 Buck - `OPP_SMALL_GOAT_2_PLUS_1`)**: Scaled specifically for ₹15,000–₹25,000 budgets. Requires 1.0 hr/day family labour and pulse crop husks.
*   **Commercial Osmanabadi Goat Unit (10 Does + 1 Buck - `OPP_OSMANABADI_GOAT_10_PLUS_1`)**: Sized for ₹75,000+ budgets. Explicitly marked as infeasible with exact capital shortfall displayed for farmers with lower budgets.
*   **Oyster Mushroom Cultivation (`OPP_OYSTER_MUSHROOM_01`)**: 100-bag seasonal batch indoor crop grown on pasteurized soybean straw. Capital: ₹20,000; Annual Profit: ₹65,000 (reconciled across card, modal, and comparison views).
*   **Scientific Apiculture & Honey Production (`OPP_BEEKEEPING_01`)**: 5 bee colonies providing ₹38,000 net profit plus 15–20% cross-pollination yield boost for oilseeds.

### Category D: Alternative & Secondary Crop Diversification
*   **Short-Duration Summer Moong (`OPP_SUMMER_MOONG_CROP_01`)**: 65-day catch crop utilizing residual moisture, adding ₹32,000 profit and fixing 35 kg atmospheric Nitrogen/ha.

### Category E: Group-Based / FPO External Services
*   **FPO Collective Input Bulk Procurement (`OPP_FPO_COLLECTIVE_INPUT_01`)**: Pooling seed and agro-chemical orders to access wholesale distributor pricing, saving 12–16% (₹12,000/year) on inputs.

---

## 3. Multi-Gate Feasibility Engine

Every opportunity is audited through five distinct feasibility gates before scoring:

1.  **Capital Outlay Gate**: `available_investment_inr >= min_investment_inr`. If false, `capital_gap_inr = min_investment - available_investment`.
2.  **Land & Space Gate**: Verifies whether required space (field, bund, covered room, animal shed, yard) exists on the farm.
3.  **Water Reliability Gate**: Compares seasonal requirement against water source (e.g. rainfed, seasonal canal, perennial borewell).
4.  **Labour Gate**: Ensures required daily hours do not exceed family availability without hired labour capacity.
5.  **Byproduct Match Gate**: Confirms crop residues (straw, stover, dung) are available for composting, mushroom substrates, or livestock feed.

### Suitability Scoring (0–95 Scale)
- Scores are continuously variable (never fake identical 98% badges).
- Infeasible or capital-deficient options are strictly capped at $\le 55$ with status `NOT_CURRENTLY_AFFORDABLE` and explicit capital gap reporting.

---

## 4. Single-Source Authoritative Financial Service

To eliminate discrepancies between cards, detail screens, and comparison tables:
*   `IncomeFinancialService` calculates authoritative figures based on unit capacity.
*   **Reconciled Metrics**: Card profit, comparison matrix net profit, and scenario base-case net profit are derived from the exact same calculation function.
*   **12-Month Production Cash Flows**:
    - Month 1: Initial capital outlay ($-\text{CAPEX}$).
    - Months 2–7: Recurring operational outlays ($-\text{OPEX}$ e.g. feed/vaccination) without immediate returns.
    - Months 8–12: Revenue realization after biological gestation/harvest (e.g. goat kid sales or mushroom harvests).

---

## 5. Verified Data Provenance & Citations

All assumptions and unit costs are grounded in official agricultural institutions:
*   **NABARD Maharashtra State Focus Paper FY 2026-27**: Unit cost norms for small ruminants, sericulture, and micro-enterprises.
*   **Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri**: University package of practices for vermicomposting, pulse residues, and Osmanabadi goat breeding.
*   **ICAR-National Institute of Abiotic Stress Management (NIASM), Baramati**: Agro-allied integration and climate-resilient farming systems.
*   **Khadi and Village Industries Commission (KVIC)**: Beekeeping and honey processing unit economics.
*   **Agmarknet (DMI, Ministry of Agriculture)**: Prevailing modal market prices across Maharashtra APMC mandis.
