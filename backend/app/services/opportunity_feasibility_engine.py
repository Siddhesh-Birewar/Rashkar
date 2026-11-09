from typing import List
from backend.app.schemas.income import (
    FarmerResourceProfile,
    OpportunityCatalogItem,
    DiscoveredOpportunity
)
from backend.app.services.income_knowledge_catalog import EXTENDED_OPPORTUNITY_CATALOG

class OpportunityFeasibilityEngine:
    @staticmethod
    def evaluate_opportunity(
        opp: OpportunityCatalogItem,
        profile: FarmerResourceProfile
    ) -> DiscoveredOpportunity:
        matching_resources: List[str] = []
        missing_requirements: List[str] = []
        
        is_feasible = True
        feasibility_status = "FEASIBLE_WITH_CURRENT_RESOURCES"
        capital_gap = 0.0

        # ---------------------------------------------------------------------
        # 1. CAPITAL GATE
        # ---------------------------------------------------------------------
        if profile.available_investment_inr < opp.min_investment_inr:
            capital_gap = round(opp.min_investment_inr - profile.available_investment_inr, 2)
            is_feasible = False
            feasibility_status = "NOT_CURRENTLY_AFFORDABLE"
            missing_requirements.append(
                f"Capital Gap: Minimum setup cost (₹{opp.min_investment_inr:,.0f}) exceeds available budget (₹{profile.available_investment_inr:,.0f}). Requires ₹{capital_gap:,.0f} additional capital."
            )
        else:
            matching_resources.append(
                f"Capital Match: Setup cost (₹{opp.min_investment_inr:,.0f}) fits within your available budget (₹{profile.available_investment_inr:,.0f})."
            )

        # ---------------------------------------------------------------------
        # 2. LAND / SPACE GATE
        # ---------------------------------------------------------------------
        if opp.required_space_type == "bund":
            if not profile.field_bunds_available:
                is_feasible = False
                feasibility_status = "REQUIRES_MORE_INFORMATION" if is_feasible else feasibility_status
                missing_requirements.append("Space Constraint: Requires perimeter field bunds.")
            else:
                matching_resources.append("Space Match: Utilizes existing outer field perimeter bunds.")
        elif opp.required_space_type == "shed":
            if not profile.has_animal_shed:
                if is_feasible:
                    feasibility_status = "FEASIBLE_WITH_SMALL_ADDITIONAL_INPUT"
                missing_requirements.append("Facility Note: Requires a shaded animal shelter or lean-to shed.")
            else:
                matching_resources.append("Facility Match: Existing farm shed satisfies shelter requirement.")
        elif opp.required_space_type == "room":
            if not profile.has_storage_room:
                if is_feasible:
                    feasibility_status = "FEASIBLE_WITH_SMALL_ADDITIONAL_INPUT"
                missing_requirements.append("Facility Note: Requires a clean, ventilated room (10x12 ft).")
            else:
                matching_resources.append("Facility Match: Existing ventilated room satisfies microclimate need.")
        elif opp.required_space_type == "field":
            avail = max(profile.available_land_acres, profile.unused_land_acres)
            if avail < opp.required_land_acres:
                is_feasible = False
                feasibility_status = "NOT_SUITABLE_FOR_LOCATION_OR_SEASON" if is_feasible else feasibility_status
                missing_requirements.append(
                    f"Land Constraint: Requires {opp.required_land_acres} acres; available unused land is {avail} acres."
                )
            else:
                matching_resources.append(f"Land Match: Requires {opp.required_land_acres} acres, available on farm.")
        else:
            matching_resources.append("Space Match: Fits within standard domestic farm yard.")

        # ---------------------------------------------------------------------
        # 3. WATER GATE
        # ---------------------------------------------------------------------
        if opp.water_requirement == "high":
            if profile.water_availability in ["rainfed_only", "limited", "none"]:
                is_feasible = False
                feasibility_status = "NOT_SUITABLE_FOR_LOCATION_OR_SEASON"
                missing_requirements.append("Water Constraint: Requires reliable perennial water; farm has rainfed/limited supply.")
            elif profile.water_availability == "seasonal_canal":
                if is_feasible:
                    feasibility_status = "FEASIBLE_WITH_SMALL_ADDITIONAL_INPUT"
                missing_requirements.append("Water Alert: High water requirement requires borewell or pond buffer during summer.")
            else:
                matching_resources.append("Water Match: Reliable water supply meets intensive enterprise needs.")
        elif opp.water_requirement in ["low", "very_low", "none"]:
            matching_resources.append(f"Water Efficient: Low water need ({opp.water_requirement.replace('_', ' ')}) is well-suited to your farm.")

        # ---------------------------------------------------------------------
        # 4. LABOR GATE
        # ---------------------------------------------------------------------
        if profile.family_labor_hours_day < opp.daily_labor_hours and not profile.hired_labor_possible:
            missing_requirements.append(
                f"Labor Constraint: Requires {opp.daily_labor_hours} hrs/day; available family labor is {profile.family_labor_hours_day} hrs/day."
            )
        else:
            matching_resources.append(
                f"Labor Match: {profile.family_labor_hours_day} hrs/day family labor readily accommodates the {opp.daily_labor_hours} hrs/day required."
            )

        # ---------------------------------------------------------------------
        # 5. BYPRODUCT & RESOURCE UTILIZATION GATE
        # ---------------------------------------------------------------------
        if opp.category == "zero_cash":
            if opp.is_cost_saving:
                matching_resources.append("Resource Utilization: Direct on-farm recycling saves purchased chemical fertilizers.")
            else:
                matching_resources.append("Resource Utilization: Directly monetizes existing produce or idle farm equipment.")

        # ---------------------------------------------------------------------
        # 6. CALCULATE WEIGHTED SUITABILITY SCORE (0 to 100)
        # ---------------------------------------------------------------------
        score = 0

        # Capital Compatibility (Weight: 20)
        if opp.min_investment_inr == 0.0:
            score += 20
        elif profile.available_investment_inr >= opp.min_investment_inr:
            score += 20
        elif profile.available_investment_inr > 0:
            ratio = profile.available_investment_inr / opp.min_investment_inr
            score += int(ratio * 12)

        # Space Compatibility (Weight: 15)
        if opp.required_space_type in ["none", "yard"]:
            score += 15
        elif opp.required_space_type == "bund" and profile.field_bunds_available:
            score += 15
        elif opp.required_space_type == "shed" and profile.has_animal_shed:
            score += 15
        elif opp.required_space_type == "room" and profile.has_storage_room:
            score += 15
        elif opp.required_space_type == "field" and max(profile.available_land_acres, profile.unused_land_acres) >= opp.required_land_acres:
            score += 15
        else:
            score += 4

        # Water Availability (Weight: 15)
        if opp.water_requirement in ["none", "very_low"]:
            score += 15
        elif opp.water_requirement == "low":
            score += 14 if profile.water_availability != "none" else 5
        elif opp.water_requirement == "moderate":
            score += 12 if profile.water_availability in ["reliable_year_round", "seasonal_canal"] else 6
        elif opp.water_requirement == "high":
            score += 15 if profile.water_availability == "reliable_year_round" else (8 if profile.water_availability == "seasonal_canal" else 2)

        # Labor Compatibility (Weight: 10)
        if profile.family_labor_hours_day >= opp.daily_labor_hours:
            score += 10
        elif profile.family_labor_hours_day > 0:
            score += int((profile.family_labor_hours_day / max(0.5, opp.daily_labor_hours)) * 8)

        # Market Accessibility (Weight: 15)
        if opp.market_verified:
            score += 10
            if profile.has_fpo_access or profile.has_transport:
                score += 5
            elif profile.distance_to_apmc_km and profile.distance_to_apmc_km <= 20:
                score += 3
            else:
                score += 2
        else:
            score += 5

        # Resource / Byproduct Match (Weight: 10)
        if opp.category == "zero_cash":
            score += 10
        elif any(c in opp.target_crops for c in profile.crop_byproducts) or profile.byproduct_surplus_available:
            score += 9
        elif "all" in opp.target_crops:
            score += 7
        else:
            score += 4

        # Location and Season Suitability (Weight: 10)
        score += 9  # Calibrated for Maharashtra semi-arid agro-climatic zones

        # Farmer Interest & Risk Preference (Weight: 5)
        if profile.category_preference in ["all", opp.category]:
            score += 3
        if profile.risk_tolerance == "conservative" and opp.risk_level == "low":
            score += 2
        elif profile.risk_tolerance != "conservative":
            score += 2

        # Clamp between 10 and 95 (no artificial 98% caps)
        score = max(10, min(95, score))

        # If not feasible due to hard constraints (capital gap, missing land/water),
        # penalize overall score so it is clearly distinct from feasible opportunities
        if not is_feasible:
            score = min(55, score)

        # ---------------------------------------------------------------------
        # 7. BENEFIT LABELS & COMPATIBILITY
        # ---------------------------------------------------------------------
        if opp.is_cost_saving and opp.potential_annual_savings_inr > 0:
            benefit_label = f"Saves ~₹{opp.potential_annual_savings_inr:,.0f}/year in farm input expenses"
        elif opp.potential_annual_profit_inr > 0:
            benefit_label = f"Earns ~₹{opp.potential_annual_profit_inr:,.0f}/year additional net profit"
        else:
            benefit_label = "Reduces post-harvest loss and improves quality"

        if not is_feasible and capital_gap > 0:
            benefit_label = f"Requires ₹{capital_gap:,.0f} additional capital to begin"

        # Compatibility verdicts
        verdict = "Highly Recommended" if (is_feasible and score >= 75) else (
            "Suitable with Minor Inputs" if is_feasible else (
                "Capital Constrained" if capital_gap > 0 else "Resource Limited"
            )
        )

        return DiscoveredOpportunity(
            opportunity=opp,
            feasibility_status=feasibility_status,
            suitability_score=score,
            is_feasible=is_feasible,
            capital_gap_inr=capital_gap,
            matching_resources=matching_resources,
            missing_requirements=missing_requirements,
            primary_benefit_label=benefit_label,
            evidence_source=opp.source_attribution,
            suitability_score_pct=score,
            is_suitable=is_feasible,
            suitability_verdict=verdict,
            reasons_why_suitable=matching_resources,
            reasons_why_unsuitable=missing_requirements
        )

    @staticmethod
    def discover_and_rank_opportunities(
        profile: FarmerResourceProfile
    ) -> List[DiscoveredOpportunity]:
        results: List[DiscoveredOpportunity] = []

        for opp in EXTENDED_OPPORTUNITY_CATALOG:
            res = OpportunityFeasibilityEngine.evaluate_opportunity(opp, profile)
            results.append(res)

        # Category priority ranking:
        # 1. Feasible zero-cash (priority 1)
        # 2. Feasible very-low cost (priority 2)
        # 3. Feasible moderate enterprise (priority 3)
        # 4. Feasible crop diversification (priority 4)
        # 5. Feasible group/external (priority 5)
        # 6. Infeasible / Capital constrained options sorted by smallest capital gap
        def sort_key(d: DiscoveredOpportunity):
            if d.is_feasible:
                category_order = {
                    "zero_cash": 1,
                    "very_low_cost": 2,
                    "moderate_enterprise": 3,
                    "crop_diversification": 4,
                    "group_external": 5
                }.get(d.opportunity.category, 6)
                # Primary sort by category priority, secondary by suitability score descending
                return (0, category_order, -d.suitability_score)
            else:
                # Infeasible items sorted by smallest capital gap
                return (1, d.capital_gap_inr, -d.suitability_score)

        results.sort(key=sort_key)
        return results
