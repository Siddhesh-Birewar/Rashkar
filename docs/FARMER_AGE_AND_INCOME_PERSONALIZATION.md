# Farmer Age, Preferences & Personal Circumstances in Rashkar Income Intelligence

## 1. Guiding Principles & Ethical Standards

In Indian smallholder agriculture, farmers span diverse generations, experience levels, and physical preferences. Many senior farmers (aged 55+) retain unmatched agronomic wisdom and deep local institutional ties, while younger family members provide physical agility and digital connectivity.

The Rashkar Income Intelligence engine follows four fundamental rules:

1. **Age is Never Treated as a Disqualification or Disability**:
   - An age range of `above_65` or `56_to_65` never reduces the eligibility score or blocks any agricultural enterprise.
   - Senior farmers can and do successfully manage commercial dairy, apiaries, goat units, and secondary crops.
2. **Preference Over Assumption**:
   - Physical capability is determined by the farmer's self-selected `work_preference`, not inferred mechanically from their age.
   - If a senior farmer selects `active_physical`, the system respects their preference without friction.
3. **Transparent Advisory Support**:
   - When a farmer selects `manage_supervise` or `light_physical` and evaluates an intensive manual operation (e.g., commercial goat penning or manual compost turning requiring 2+ hours daily), the engine does not reject the enterprise. Instead, it provides an advisory recommending family or hired labor assistance.
4. **Time Horizon Respect**:
   - When a farmer indicates a `few_weeks` or `3_to_6_months` desired cash flow horizon, enterprises requiring long biological gestation (e.g. 14 months for kid rearing) explicitly surface a timeline warning so the farmer can make an informed choice.

---

## 2. Supported Personalization Dimensions

### A. Age Ranges (`age_range`)
- `under_25`: Early career farmer; often open to innovative diversification (sericulture, solar dehydration, beekeeping).
- `25_to_35`: Active prime producer; balancing investment capital accumulation with high labor capacity.
- `36_to_45`: Experienced producer; established farm assets, managing school/family cash commitments.
- `46_to_55`: Senior manager; established credit history, potential FPO leadership linkage.
- `56_to_65`: Senior grower; rich agronomic experience, evaluating retirement transitions or high-margin low-stress enterprises.
- `above_65`: Village elder / master farmer; high community respect, supervision, seed saving.
- `prefer_not_to_say`: Safe default; assumes standard working norms with zero bias.

### B. Work Preferences (`work_preference`)
- `active_physical`: Full manual participation in fieldwork, tillage, harvesting, spraying, and livestock feeding.
- `light_physical`: Prefers lighter operations (apiculture inspection, seed sorting, azolla bed maintenance, nursery grafting).
- `manage_supervise`: Management, record keeping, input procurement, market negotiation, and worker supervision.

### C. Payback Horizon (`payback_horizon`)
- `few_weeks`: Emergency liquidity or immediate operational cash requirements.
- `3_to_6_months`: Seasonal crop cycle alignment (e.g. 65-day summer moong or 90-day broiler poultry).
- `within_1_year`: Standard annual agricultural calendar.
- `long_term`: Multi-year capital investment (e.g. horticulture orchard, breeding stock).

### D. Family Management Role (`family_management_role`)
- `personal_direct`: Solo farmer execution.
- `family_collective`: Joint family effort sharing physical and managerial duties.
- `youth_empowered`: Younger generation executing daily field tasks while senior provides oversight.

---

## 3. Test Verification & Agronomic Parity

The implementation is verified by `backend/tests/test_farmer_age_and_preferences.py`:
- `test_age_is_not_treated_as_physical_ability_or_disqualification`: Proves senior farmers retain full eligibility across zero-cash and commercial enterprises.
- `test_supervisory_work_preference_flags_heavy_manual_tasks`: Proves supervisory preferences trigger constructive labor-sharing advisories.
- `test_payback_horizon_influences_timing_advisories`: Proves timeline mismatches are surfaced transparently.
