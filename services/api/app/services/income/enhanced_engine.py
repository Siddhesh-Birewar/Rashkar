import logging
from typing import Any, Dict, List, Optional

from cropnet.services.api.app.schemas.income import (
    DetailedOpportunityItem,
    FinancialScenarioSimulateRequest,
    FinancialScenarioSimulateResponse,
)
from cropnet.services.api.app.services.income.data_loader import (
    get_all_raw_opportunities,
    get_raw_opportunity_by_id,
)

logger = logging.getLogger(__name__)


class EnhancedIncomeEngine:
    @staticmethod
    def match_opportunities_for_farm(
        farm_context: Dict[str, Any],
        profile_overrides: Optional[Dict[str, Any]] = None,
    ) -> List[DetailedOpportunityItem]:
        """Transparent, deterministic rule-based matching engine for farm income diversification.

        Evaluates available land, investment budget, water security, electricity, labour,
        and existing farm assets without using opaque black-box or LLM scoring.
        """
        raw_opps = get_all_raw_opportunities()
        profile = profile_overrides or {}

        # 1. Extract Farm & Farmer Resources
        total_farm_acres = float(farm_context.get("calculated_area_acres") or farm_context.get("area_acres") or 2.0)
        allocated_acres = float(profile.get("available_diversification_acres") or min(0.5, total_farm_acres))
        available_budget = float(profile.get("available_investment_inr") or 0.0)
        water_source = str(profile.get("water_source") or farm_context.get("water_source") or "seasonal_canal").lower()
        has_electricity = bool(profile.get("has_electricity", True))
        electricity_type = str(profile.get("electricity_type") or "single_phase").lower()
        family_hours = float(profile.get("family_labor_hours_day") or 2.0)
        has_shed = bool(profile.get("has_animal_shed", False))
        has_storage = bool(profile.get("has_storage_room", False))
        has_pond = bool(profile.get("has_farm_pond", False) or "pond" in water_source or "shet_tale" in water_source)
        equipment = [str(e).lower() for e in profile.get("existing_equipment", [])]
        livestock = [str(l).lower() for l in profile.get("existing_livestock", [])]
        taluka = str(farm_context.get("taluka") or "")
        district = str(farm_context.get("district") or "Maharashtra")

        results: List[DetailedOpportunityItem] = []

        for opp in raw_opps:
            opp_id = opp["opportunity_id"]
            cat = opp.get("category", "")
            req_land = float(opp.get("suitable_land_acres", 0.0))
            water_req = str(opp.get("water_requirement", "low")).lower()
            setup_range = opp.get("setup_investment_range", {})
            min_inv = float(setup_range.get("min_inr", 0.0))
            max_inv = float(setup_range.get("max_inr", min_inv))
            labour_info = opp.get("labour_requirements", {})
            daily_hours_needed = float(labour_info.get("daily_hours", 1.0))
            elec_req = str(opp.get("electricity_requirements", "none")).lower()

            why_recommended: List[str] = []
            supporting_resources: List[str] = []
            missing_requirements: List[str] = []
            what_to_arrange: List[str] = []
            risks_to_consider: List[str] = list(opp.get("major_risks", []))

            # Rule 1: Land Feasibility
            land_ok = True
            if req_land > 0:
                if allocated_acres >= req_land:
                    supporting_resources.append(
                        f"Allocated land: {allocated_acres:.2f} acres is sufficient for the {req_land:.2f} acre requirement."
                    )
                elif total_farm_acres >= req_land:
                    land_ok = False
                    missing_requirements.append(
                        f"Allocated land ({allocated_acres:.2f} ac) is below required {req_land:.2f} ac. You have {total_farm_acres:.2f} total acres; consider allocating more space."
                    )
                    what_to_arrange.append(f"Allocate at least {req_land:.2f} acres from existing field area.")
                else:
                    land_ok = False
                    missing_requirements.append(
                        f"Total farm area ({total_farm_acres:.2f} ac) is smaller than required {req_land:.2f} acres."
                    )
            else:
                supporting_resources.append("Zero field land requirement: Can operate in yards, sheds, bunds, or existing ponds.")

            # Rule 2: Water Feasibility
            water_ok = True
            if water_req == "high":
                if has_pond or "borewell" in water_source or "perennial" in water_source or "well" in water_source:
                    supporting_resources.append(f"Water source ({water_source}): Sufficient for high-water aquaculture/horticulture.")
                else:
                    water_ok = False
                    missing_requirements.append("Requires assured high-volume water source (e.g. farm pond or perennial well).")
                    what_to_arrange.append("Construct or deepen farm pond (shet tale) with liner before stocking.")
            elif water_req == "moderate":
                if water_source in ["none", "rainfed_only", "limited"]:
                    water_ok = False
                    missing_requirements.append("Requires moderate seasonal or drip irrigation; rainfed only is insufficient.")
                    what_to_arrange.append("Install drip irrigation or arrange seasonal canal/well allocation.")
                else:
                    supporting_resources.append(f"Water source ({water_source}): Adequate for moderate drip/fertigation demand.")
            else:
                supporting_resources.append(f"Low/no water requirement ({water_req}): Resilient to dry spells.")

            # Rule 3: Budget / Capital Feasibility
            budget_ok = True
            if min_inv == 0.0:
                supporting_resources.append("Zero upfront cash requirement: Can be started immediately with existing farm assets.")
                why_recommended.append("Zero financial entry barrier; leverages your existing assets and farm labor.")
            elif available_budget >= min_inv:
                supporting_resources.append(
                    f"Investment budget (₹{available_budget:,.0f}): Fully covers initial setup requirement of ₹{min_inv:,.0f}."
                )
                why_recommended.append(f"Within your stated investment capacity (₹{min_inv:,.0f} to ₹{max_inv:,.0f}).")
            else:
                gap = min_inv - available_budget
                budget_ok = False
                missing_requirements.append(
                    f"Initial setup requires ₹{min_inv:,.0f} (your budget is ₹{available_budget:,.0f}; shortfall: ₹{gap:,.0f})."
                )
                what_to_arrange.append(f"Mobilize ₹{gap:,.0f} via KCC crop loan, SHG group loan, or phased expansion.")

            # Rule 4: Labour Feasibility
            labour_ok = True
            if family_hours >= daily_hours_needed:
                supporting_resources.append(
                    f"Family labour ({family_hours:.1f} hrs/day): Sufficient for {daily_hours_needed:.1f} hrs/day daily requirement."
                )
            else:
                labour_ok = False
                missing_requirements.append(
                    f"Requires {daily_hours_needed:.1f} hrs/day; stated family labour is {family_hours:.1f} hrs/day."
                )
                what_to_arrange.append("Engage part-time family support or budget for casual hired assistance.")

            # Rule 5: Electricity Feasibility
            elec_ok = True
            if elec_req == "three_phase" and electricity_type != "three_phase":
                elec_ok = False
                missing_requirements.append("Requires 3-phase agricultural power connection.")
                what_to_arrange.append("Apply for 3-phase grid connection or install solar agri-pump.")
            elif elec_req == "single_phase" and not has_electricity:
                elec_ok = False
                missing_requirements.append("Requires continuous single-phase electric supply.")
                what_to_arrange.append("Arrange farm power connection or generator backup.")
            elif elec_req != "none":
                supporting_resources.append(f"Electricity available ({electricity_type}): Meets enterprise power needs.")

            # Rule 6: Infrastructure / Asset Specific Checks
            if cat == "POULTRY" and not has_shed:
                what_to_arrange.append("Construct simple night shelter / chicken coop (approx 150 sq.ft) with wire mesh.")
            if cat == "LIVESTOCK" and not has_shed:
                what_to_arrange.append("Construct elevated slatted floor or shaded goat shed with feeding mangers.")
            if cat == "FISHERY" and not has_pond:
                missing_requirements.append("Requires an excavated farm pond (shet tale) with minimum 2m depth.")
                what_to_arrange.append("Apply for Magel Tyala Shet Tale scheme subsidy to construct lined farm pond.")

            # Category-specific positive reasons
            if cat == "CROP_DIVERSIFICATION":
                why_recommended.append(f"High-value diversification for {district} agro-climatic conditions.")
            elif cat == "FLORICULTURE":
                why_recommended.append("Fast cash turnover with harvest cycles matching regional festival demand.")
            elif cat == "POULTRY":
                why_recommended.append("Low land requirement with steady weekly cash flow from eggs or meat.")
            elif cat == "FISHERY":
                why_recommended.append("Dual-use water utilization from your farm pond without losing irrigation water.")
            elif cat == "LIVESTOCK":
                why_recommended.append("High feed conversion of crop byproducts and resilient semi-arid breed performance.")
            elif cat == "SMALL_SPACE":
                why_recommended.append("Generates substantial surplus on zero or minimal land under shaded farm areas.")
            elif cat == "RESOURCE_MONETIZATION":
                why_recommended.append("Turns idle machinery and equipment into immediate rental income.")
            elif cat == "VALUE_ADDITION":
                why_recommended.append("Captures 10%–20% higher market price by eliminating middleman grading deductions.")

            # Determine Final Status
            critical_missing = [m for m in missing_requirements if "Shortfall" in m or "smaller than" in m or "water source" in m]
            if land_ok and water_ok and budget_ok and labour_ok and elec_ok:
                feasibility_status = "GOOD_POTENTIAL_FIT"
            elif land_ok and water_ok and (not budget_ok or not labour_ok):
                feasibility_status = "POTENTIALLY_SUITABLE"
            elif not water_ok or not land_ok:
                feasibility_status = "NOT_SUITABLE"
            else:
                feasibility_status = "MORE_INFORMATION_REQUIRED"

            item = DetailedOpportunityItem(
                opportunity_id=opp_id,
                name=opp.get("name", "Opportunity"),
                category=cat,
                category_name=cat.replace("_", " ").title(),
                farmer_friendly_description=opp.get("farmer_friendly_description", ""),
                business_model=opp.get("business_model", ""),
                suitable_geography=opp.get("suitable_geography", "Maharashtra"),
                suitable_land_acres=req_land,
                unit_of_operation=opp.get("unit_of_operation", "1 unit"),
                minimum_scale=float(opp.get("minimum_scale", 1.0)),
                typical_scale=float(opp.get("typical_scale", 1.0)),
                water_requirement=water_req,
                soil_climate_considerations=opp.get("soil_climate_considerations", ""),
                initial_setup_requirements=opp.get("initial_setup_requirements", ""),
                recurring_requirements=opp.get("recurring_requirements", ""),
                equipment_and_infrastructure=opp.get("equipment_and_infrastructure", ""),
                setup_investment_range={
                    "min_inr": min_inv,
                    "max_inr": max_inv,
                    "typical_inr": float(setup_range.get("typical_inr", min_inv)),
                },
                recurring_operating_cost_range={
                    "min_inr": float(opp.get("recurring_operating_cost_range", {}).get("min_inr", 0.0)),
                    "max_inr": float(opp.get("recurring_operating_cost_range", {}).get("max_inr", 0.0)),
                    "typical_inr": float(opp.get("recurring_operating_cost_range", {}).get("typical_inr", 0.0)),
                },
                production_yield_assumptions=opp.get("production_yield_assumptions", {}),
                expected_sales_revenue_assumptions=opp.get("expected_sales_revenue_assumptions", {}),
                estimated_operating_surplus=opp.get("estimated_operating_surplus", {}),
                time_to_first_income_months=float(opp.get("time_to_first_income_months", 1.0)),
                production_cycle_days=int(opp.get("production_cycle_days", 30)),
                labour_requirements=labour_info,
                electricity_requirements=elec_req,
                market_access_requirements=opp.get("market_access_requirements", "local_village"),
                major_risks=risks_to_consider,
                permissions_or_registrations=opp.get("permissions_or_registrations", []),
                source_references=opp.get("source_references", []),
                reference_geography=opp.get("reference_geography", "Maharashtra"),
                last_verified_date=opp.get("last_verified_date", "2026-11-01"),
                confidence_classification=opp.get("confidence_classification", "NABARD_MODEL_PROJECT"),
                feasibility_status=feasibility_status,
                why_recommended=why_recommended,
                supporting_resources=supporting_resources,
                missing_requirements=missing_requirements,
                what_to_arrange=what_to_arrange,
                risks_to_consider=risks_to_consider,
            )
            results.append(item)

        # Sort: GOOD_POTENTIAL_FIT first, then POTENTIALLY_SUITABLE, then MORE_INFO, then NOT_SUITABLE
        priority = {
            "GOOD_POTENTIAL_FIT": 1,
            "POTENTIALLY_SUITABLE": 2,
            "MORE_INFORMATION_REQUIRED": 3,
            "NOT_SUITABLE": 4,
        }
        results.sort(key=lambda x: (priority.get(x.feasibility_status, 5), x.setup_investment_range.get("min_inr", 0)))
        return results

    @staticmethod
    def simulate_financial_scenario(
        req: FinancialScenarioSimulateRequest,
    ) -> FinancialScenarioSimulateResponse:
        """Calculates opportunity-specific initial investment, annual operating expenses,

        gross revenue, and estimated operating surplus across LOW, BASE, and HIGH scenarios.
        """
        raw = get_raw_opportunity_by_id(req.opportunity_id)
        if not raw:
            # Fallback placeholder if not found in JSON
            return FinancialScenarioSimulateResponse(
                opportunity_id=req.opportunity_id,
                opportunity_name="Unknown Enterprise",
                category="CROP_DIVERSIFICATION",
                scale_unit="acre",
                allocated_scale=req.allocated_scale,
                initial_setup_investment_inr=0.0,
                recurring_operating_expenses_inr=0.0,
                expected_gross_revenue_inr=0.0,
                estimated_operating_surplus_inr=0.0,
                break_even_estimate="N/A",
                scenario_mode=req.scenario_mode,
                disclaimer="Opportunity not found in canonical catalogue.",
            )

        name = raw.get("name", "Agricultural Enterprise")
        cat = raw.get("category", "CROP_DIVERSIFICATION")
        unit_desc = raw.get("unit_of_operation", "unit")
        typical_scale = float(raw.get("typical_scale") or 1.0)
        scale_ratio = req.allocated_scale / typical_scale if typical_scale > 0 else 1.0

        setup_range = raw.get("setup_investment_range", {})
        opex_range = raw.get("recurring_operating_cost_range", {})
        yield_data = raw.get("production_yield_assumptions", {})
        price_data = raw.get("expected_sales_revenue_assumptions", {})

        # Compute LOW, BASE, HIGH values scaled by requested capacity
        def calc_mode_metrics(mode: str) -> Dict[str, Any]:
            m = mode.lower()
            # 1. Setup Investment (Capex)
            if m == "low":
                capex = float(setup_range.get("min_inr", 0.0))
            elif m == "high":
                capex = float(setup_range.get("max_inr", 0.0))
            else:
                capex = float(setup_range.get("typical_inr", setup_range.get("min_inr", 0.0)))
            # Scale capex if variable
            scaled_capex = round(capex * scale_ratio, 2)

            # 2. Recurring Operating Expenses (Opex)
            if m == "low":
                opex = float(opex_range.get("min_inr", 0.0))
            elif m == "high":
                opex = float(opex_range.get("max_inr", 0.0))
            else:
                opex = float(opex_range.get("typical_inr", opex_range.get("min_inr", 0.0)))
            scaled_opex = round(opex * scale_ratio, 2)

            # 3. Yield & Price
            production_val = float(yield_data.get(m, yield_data.get("base", 1.0))) * scale_ratio
            if m == "low":
                unit_price = float(price_data.get("low_price_per_unit", price_data.get("base_price_per_unit", 1.0)))
            elif m == "high":
                unit_price = float(price_data.get("high_price_per_unit", price_data.get("base_price_per_unit", 1.0)))
            else:
                unit_price = float(price_data.get("base_price_per_unit", 1.0))

            # 4. Gross Revenue & Operating Surplus
            gross_revenue = round(production_val * unit_price, 2)
            operating_surplus = round(gross_revenue - scaled_opex, 2)

            # 5. Payback period in months
            if operating_surplus > 0 and scaled_capex > 0:
                payback_months = round((scaled_capex / operating_surplus) * 12.0, 1)
            elif scaled_capex == 0:
                payback_months = 1.0
            else:
                payback_months = None

            return {
                "setup_investment_inr": scaled_capex,
                "annual_opex_inr": scaled_opex,
                "production_quantity": round(production_val, 1),
                "production_unit": yield_data.get("unit", "units"),
                "price_per_unit_inr": unit_price,
                "gross_revenue_inr": gross_revenue,
                "operating_surplus_inr": operating_surplus,
                "payback_months": payback_months,
            }

        scenarios = {
            "LOW": calc_mode_metrics("low"),
            "BASE": calc_mode_metrics("base"),
            "HIGH": calc_mode_metrics("high"),
        }

        # Apply farmer custom overrides if specified
        active_mode = req.scenario_mode.upper() if req.scenario_mode.upper() in ["LOW", "BASE", "HIGH"] else "BASE"
        active = dict(scenarios[active_mode])

        if req.custom_setup_investment_inr is not None:
            active["setup_investment_inr"] = float(req.custom_setup_investment_inr)
        if req.custom_annual_opex_inr is not None:
            active["annual_opex_inr"] = float(req.custom_annual_opex_inr)
        if req.custom_yield is not None:
            active["production_quantity"] = float(req.custom_yield)
        if req.custom_sale_price is not None:
            active["price_per_unit_inr"] = float(req.custom_sale_price)

        # Recalculate gross revenue and surplus with active overrides
        final_gross = round(active["production_quantity"] * active["price_per_unit_inr"], 2)
        final_surplus = round(final_gross - active["annual_opex_inr"], 2)
        final_capex = active["setup_investment_inr"]

        if final_surplus > 0 and final_capex > 0:
            final_payback = round((final_capex / final_surplus) * 12.0, 1)
            be_str = f"Estimated break-even in ~{final_payback} months ({final_payback / 12:.1f} years)"
        elif final_capex == 0:
            final_payback = 1.0
            be_str = "Immediate (Zero initial capex required)"
        else:
            final_payback = None
            be_str = "Operating surplus negative at current input prices; break-even not reached."

        assumptions_applied = [
            f"Allocated scale: {req.allocated_scale} {unit_desc}",
            f"Annual production: {active['production_quantity']:,.1f} {active['production_unit']}",
            f"Average realization rate: ₹{active['price_per_unit_inr']:,.2f} per {active['production_unit'].split(' ')[0]}",
            f"Recurring annual operating outlays: ₹{active['annual_opex_inr']:,.0f}",
            "Operating surplus = Gross revenue minus recurring operating outlays (excludes family labor and finance interest)",
        ]

        return FinancialScenarioSimulateResponse(
            opportunity_id=req.opportunity_id,
            opportunity_name=name,
            category=cat,
            scale_unit=unit_desc,
            allocated_scale=req.allocated_scale,
            initial_setup_investment_inr=final_capex,
            recurring_operating_expenses_inr=active["annual_opex_inr"],
            expected_gross_revenue_inr=final_gross,
            estimated_operating_surplus_inr=final_surplus,
            break_even_estimate=be_str,
            estimated_payback_months=final_payback,
            scenario_mode=active_mode,
            scenarios=scenarios,
            assumptions_applied=assumptions_applied,
            key_risks=list(raw.get("major_risks", []))[:3],
            source_attribution="; ".join(raw.get("source_references", [])[:2]),
            disclaimer="Indicative planning estimate based on published institutional benchmarks. Not guaranteed returns. Local market mandi rates, climatic factors and operational management will vary actual returns.",
        )

    @staticmethod
    def compare_selected_opportunities(
        opp_ids: List[str],
        allocated_scale: float = 1.0,
        budget_inr: float = 50000.0,
    ) -> List[Dict[str, Any]]:
        """Produces a structured multi-dimensional comparison of 2 or 3 opportunities."""
        results: List[Dict[str, Any]] = []
        for oid in opp_ids[:3]:
            raw = get_raw_opportunity_by_id(oid)
            if not raw:
                continue
            setup = raw.get("setup_investment_range", {})
            opex = raw.get("recurring_operating_cost_range", {})
            surplus = raw.get("estimated_operating_surplus", {})
            results.append({
                "opportunity_id": oid,
                "name": raw.get("name", "Enterprise"),
                "category": raw.get("category", ""),
                "unit_of_operation": raw.get("unit_of_operation", ""),
                "setup_investment_min_inr": float(setup.get("min_inr", 0.0)),
                "setup_investment_max_inr": float(setup.get("max_inr", 0.0)),
                "recurring_opex_typical_inr": float(opex.get("typical_inr", opex.get("min_inr", 0.0))),
                "estimated_operating_surplus_base_inr": float(surplus.get("base_inr", 0.0)),
                "time_to_first_income_months": float(raw.get("time_to_first_income_months", 1.0)),
                "production_cycle_days": int(raw.get("production_cycle_days", 30)),
                "water_requirement": raw.get("water_requirement", "low"),
                "labour_daily_hours": float(raw.get("labour_requirements", {}).get("daily_hours", 1.0)),
                "electricity_requirements": raw.get("electricity_requirements", "none"),
                "market_access": raw.get("market_access_requirements", "local_village"),
                "major_risk": raw.get("major_risks", ["Market volatility"])[0] if raw.get("major_risks") else "Market volatility",
                "is_affordable": budget_inr >= float(setup.get("min_inr", 0.0)),
            })
        return results
