import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from cropnet.services.api.app.schemas.income import OpportunityCatalogItem

logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent / "data" / "income_opportunities.json"

_CACHED_OPPORTUNITIES: Optional[List[Dict[str, Any]]] = None
_CACHED_CATEGORIES: Optional[List[Dict[str, Any]]] = None


def load_raw_income_data() -> Dict[str, Any]:
    global _CACHED_OPPORTUNITIES, _CACHED_CATEGORIES
    if not DATA_PATH.exists():
        logger.warning("income_opportunities.json not found at %s", DATA_PATH)
        return {"categories": [], "opportunities": []}

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            _CACHED_OPPORTUNITIES = data.get("opportunities", [])
            _CACHED_CATEGORIES = data.get("categories", [])
            return data
    except Exception as e:
        logger.error("Failed to load income_opportunities.json: %s", e)
        return {"categories": [], "opportunities": []}


def get_all_categories() -> List[Dict[str, Any]]:
    global _CACHED_CATEGORIES
    if _CACHED_CATEGORIES is None:
        load_raw_income_data()
    return _CACHED_CATEGORIES or []


def get_all_raw_opportunities() -> List[Dict[str, Any]]:
    global _CACHED_OPPORTUNITIES
    if _CACHED_OPPORTUNITIES is None:
        load_raw_income_data()
    return _CACHED_OPPORTUNITIES or []


def get_raw_opportunity_by_id(opportunity_id: str) -> Optional[Dict[str, Any]]:
    opps = get_all_raw_opportunities()
    for opp in opps:
        if opp.get("opportunity_id") == opportunity_id:
            return opp
    return None


def convert_raw_to_catalog_item(raw: Dict[str, Any]) -> OpportunityCatalogItem:
    setup_range = raw.get("setup_investment_range", {})
    min_inv = float(setup_range.get("min_inr", 0.0))
    max_inv = float(setup_range.get("max_inr", min_inv))
    
    opex_range = raw.get("recurring_operating_cost_range", {})
    working_cap = float(opex_range.get("typical_inr", opex_range.get("min_inr", 0.0)))
    
    surplus = raw.get("estimated_operating_surplus", {})
    profit = float(surplus.get("base_inr", surplus.get("low_inr", 0.0)))
    
    labour = raw.get("labour_requirements", {})
    daily_hrs = float(labour.get("daily_hours", 1.0))

    category_slug = raw.get("category", "CROP_DIVERSIFICATION").lower()
    is_zero = min_inv <= 0.0

    return OpportunityCatalogItem(
        opportunity_id=raw["opportunity_id"],
        title=raw.get("name", raw.get("title", "Opportunity")),
        category="zero_cash" if is_zero else category_slug,
        is_cost_saving=raw.get("is_cost_saving", False) or "saving" in raw.get("name", "").lower(),
        tagline=raw.get("farmer_friendly_description", "")[:120],
        min_investment_inr=min_inv,
        max_investment_inr=max_inv,
        working_capital_required_inr=working_cap,
        required_land_acres=float(raw.get("suitable_land_acres", 0.0)),
        required_space_type="field" if float(raw.get("suitable_land_acres", 0.0)) > 0 else "yard",
        water_requirement=raw.get("water_requirement", "low"),
        daily_labor_hours=daily_hrs,
        risk_level="low" if min_inv < 20000 else ("high" if min_inv > 200000 else "moderate"),
        payback_period_months=max(1, int(raw.get("time_to_first_income_months", 3))),
        potential_annual_profit_inr=profit,
        potential_annual_savings_inr=profit if "cost_saving" in raw.get("opportunity_id", "").lower() else 0.0,
        summary=raw.get("business_model", raw.get("farmer_friendly_description", "")),
        market_commodity=raw.get("unit_of_operation", ""),
        market_benchmark_price=f"Typical surplus: ₹{profit:,.0f}/yr",
        market_source=raw.get("source_references", ["NABARD / MPKV"])[0],
        market_verified=True,
        target_crops=["all"],
        key_assumptions=[
            f"Unit scale: {raw.get('unit_of_operation', '1 unit')}",
            f"Time to income: {raw.get('time_to_first_income_months', 3)} months",
            f"Production cycle: {raw.get('production_cycle_days', 90)} days",
        ],
        key_risks=raw.get("major_risks", [])[:3],
        source_attribution="; ".join(raw.get("source_references", [])[:2]),
        minimum_viable_unit_description=raw.get("unit_of_operation", ""),
        production_cycle_days=int(raw.get("production_cycle_days", 90)),
        revenue_delay_months=max(1, int(raw.get("time_to_first_income_months", 2))),
    )
