# Extra Income & Farm Diversification Engine — Scientific Methodology & Architecture

## 1. Executive Summary & Design Rationale

The **Extra Income & Farm Diversification Engine** in Rashkar was completely rebuilt to move away from predetermined commercial catalogues towards **farmer-personalized opportunity discovery**. Rather than asking *"What commercial agriculture enterprise can I sell to this farmer?"*, the engine answers:

> *"Given the exact resources, byproducts, spare land, water window, family labour, age and working preferences, and capital I already have on my farm, what additional income can I realistically earn or what input expenses can I eliminate without taking destructive financial risks?"*

---

## 2. The 5 Clean Feasibility Categories

Rather than relying on confusing numerical percentage scores, every enterprise is classified into five unmistakable categories based on multi-gate feasibility and capital gap audits:

1. **`CAN_TRY_WITH_WHAT_YOU_HAVE`**: Zero additional investment required or completely affordable within current budget and working capital, with zero physical or biological constraints violated.
2. **`CAN_TRY_WITH_SMALL_ADDITIONAL_AMOUNT`**: Highly suited to current farm assets and skills, with a small capital gap ($\le ₹10,000$) that can be covered by micro-credit or seasonal savings.
3. **`NEEDS_MORE_MONEY`**: Requires substantial capital beyond available funds ($> ₹10,000$ gap). Explicitly states exact setup + operational cash shortfall.
4. **`NEEDS_MORE_INFORMATION`**: Biological feasibility depends on unresolved field variables (e.g., standing crop rotation window, soil drainage, unverified market linkage).
5. **`NOT_SUITABLE_CURRENTLY`**: Hard physical, agronomic, or resource constraints violated (e.g. required machinery not owned, water insufficient for high-water crop, standing crop conflict).

---

## 3. Farmer Age, Working Preferences & Personal Circumstances

The engine treats farmer age with dignity and practical nuance, adhering to strict ethical guidelines:
- **No Disqualification Based on Age**: Age is **NEVER** treated as an automatic disqualifier or equated with physical disability. A farmer over 65 is eligible for all enterprises.
- **Work Preferences**:
  - `active_physical`: Routine manual agricultural operations.
  - `light_physical`: Lower physical impact operations (e.g., apiculture inspection, seed grading, azolla skimming).
  - `manage_supervise`: Farm management, procurement, and supervision. If a labor-intensive activity is evaluated, an alert highlights family or hired labor support without blocking the recommendation.
- **Payback Horizon**:
  - `few_weeks`: Quick-cash activities (e.g., grain aggregation, custom hiring, composting).
  - `3_to_6_months`: Seasonal crop and poultry cycles.
  - `within_1_year`: Annual farm diversification.
  - `long_term`: Multi-year gestation (e.g. goat breeding, horticulture). Alerts are triggered if an activity has gestation exceeding the farmer's stated horizon.
- **Family Role**:
  - Distinguishes between direct personal execution and shared family collective operations.

---

## 4. Rigorous Agronomic & Resource Gates

1. **Standing Crop & Sunflower Validation**:
   - Hybrid sunflower (`OPP_SUNFLOWER_INTERCROP_01`) cannot be intercropped with standing onion during bulb development due to canopy shading, root zone moisture competition, and bulb rotting.
   - It is approved only when dedicated fallow acreage is available or as a sequential post-harvest rotation.
2. **Composting Zero-Cost Audit**:
   - Zero-cash composting requires verified cattle dung or livestock on farm.
   - For farms without livestock, a bio-decomposer starter culture (~₹1,200) is required and audited against available operating cash.
   - Biomass audits strictly reserve 50% of residues for livestock feed and surface mulching.
3. **Custom Hiring / Equipment Sharing Gate**:
   - Strictly verifies owned machinery (tractor, sprayer, pump, rotavator) in `existing_assets` before recommending custom hiring pool income.

---

## 5. The 6 Plain-Language Farmer Questions & Answers

Every opportunity provides standardized, plain-language answers:
1. **What is it?**: Simple, non-technical explanation.
2. **Why does it suit my farm?**: Explicitly lists matching resources from the farmer's profile.
3. **What will I need to start?**: Transparent capital, space, and labor breakdown.
4. **How will I earn or save money?**: Economic value split into direct cash income, avoided input expenses, and loss prevention.
5. **When will I receive money?**: Realistic gestation and APMC market payment cadence.
6. **What should I be careful about?**: Honest operational warnings, disease vulnerabilities, and market risks.
