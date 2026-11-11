export type FeasibilityStatus =
  | "GOOD_POTENTIAL_FIT"
  | "POTENTIALLY_SUITABLE"
  | "MORE_INFORMATION_REQUIRED"
  | "NOT_SUITABLE";

export interface OpportunityCategory {
  key: string;
  name: string;
  tagline: string;
  count: number;
}

export interface DetailedOpportunity {
  opportunity_id: str;
  name: str;
  category: str;
  category_name: str;
  farmer_friendly_description: str;
  business_model: str;
  suitable_geography: str;
  suitable_land_acres: number;
  unit_of_operation: str;
  minimum_scale: number;
  typical_scale: number;
  water_requirement: "none" | "very_low" | "low" | "moderate" | "high";
  soil_climate_considerations: str;
  initial_setup_requirements: str;
  recurring_requirements: str;
  equipment_and_infrastructure: str;
  setup_investment_range: {
    min_inr: number;
    max_inr: number;
    typical_inr: number;
  };
  recurring_operating_cost_range: {
    min_inr: number;
    max_inr: number;
    typical_inr: number;
  };
  production_yield_assumptions: {
    low?: number;
    base?: number;
    high?: number;
    unit?: string;
  };
  expected_sales_revenue_assumptions: {
    low_price_per_unit?: number;
    base_price_per_unit?: number;
    high_price_per_unit?: number;
  };
  estimated_operating_surplus: {
    low_inr?: number;
    base_inr?: number;
    high_inr?: number;
  };
  time_to_first_income_months: number;
  production_cycle_days: number;
  labour_requirements: {
    daily_hours?: number;
    skill_level?: string;
  };
  electricity_requirements: string;
  market_access_requirements: string;
  major_risks: string[];
  permissions_or_registrations: string[];
  source_references: string[];
  reference_geography: string;
  last_verified_date: string;
  confidence_classification: string;
  feasibility_status: FeasibilityStatus;
  why_recommended: string[];
  supporting_resources: string[];
  missing_requirements: string[];
  what_to_arrange: string[];
  risks_to_consider: string[];
}

type str = string;

export interface FarmResourceProfile {
  farm_id: string;
  farm_name?: string;
  total_farm_acres: number;
  available_diversification_acres: number;
  available_investment_inr: number;
  monthly_operating_budget_inr: number;
  water_source: string;
  family_labor_hours_day: number;
  has_animal_shed: boolean;
  has_storage_room: boolean;
  has_farm_pond: boolean;
  existing_equipment: string[];
  existing_livestock: string[];
  preferred_category?: string;
}

export interface FinancialSimulation {
  opportunity_id: string;
  opportunity_name: string;
  category: string;
  scale_unit: string;
  allocated_scale: number;
  initial_setup_investment_inr: number;
  recurring_operating_expenses_inr: number;
  expected_gross_revenue_inr: number;
  estimated_operating_surplus_inr: number;
  break_even_estimate: string;
  estimated_payback_months?: number | null;
  scenario_mode: "LOW" | "BASE" | "HIGH";
  scenarios: Record<
    string,
    {
      setup_investment_inr: number;
      annual_opex_inr: number;
      production_quantity: number;
      production_unit: string;
      price_per_unit_inr: number;
      gross_revenue_inr: number;
      operating_surplus_inr: number;
      payback_months?: number | null;
    }
  >;
  assumptions_applied: string[];
  key_risks: string[];
  source_attribution: string;
  disclaimer: string;
}

export interface OpportunityComparison {
  opportunity_id: string;
  name: string;
  category: string;
  unit_of_operation: string;
  setup_investment_min_inr: number;
  setup_investment_max_inr: number;
  recurring_opex_typical_inr: number;
  estimated_operating_surplus_base_inr: number;
  time_to_first_income_months: number;
  production_cycle_days: number;
  water_requirement: string;
  labour_daily_hours: number;
  electricity_requirements: string;
  market_access: string;
  major_risk: string;
  is_affordable: boolean;
}

export interface SavedPlan {
  plan_id: string;
  opportunity_id: string;
  opportunity_title: string;
  category: string;
  chosen_budget_inr: number;
  projected_operating_surplus_inr: number;
  payback_months?: number | null;
  break_even_reached: boolean;
  notes?: string;
  created_at_utc: string;
}
