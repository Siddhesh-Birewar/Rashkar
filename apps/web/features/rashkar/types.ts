/**
 * RASHKAR Feature Module — Authoritative TypeScript contracts mirroring
 * `cropnet/services/api/app/rashkar/schemas/*` and `endpoints/*`.
 */

// ── Shared Context & Crop Cycle Types ─────────────────────────────────────────

export interface RashkarFarmContext {
  farm_id: string;
  owner_id: string;
  farm_name: string;
  district?: string | null;
  taluka?: string | null;
  village?: string | null;
  state?: string | null;
  latitude: number;
  longitude: number;
  elevation_m?: number | null;
  total_area_acres?: number | null;
  irrigation_type?: string | null;
  water_source?: string | null;
}

export interface RashkarSoilContext {
  soil_texture?: string | null;
  soil_ph?: number | null;
  organic_carbon_pct?: number | null;
  cation_exchange_capacity?: number | null;
  available_water_capacity_mm_m?: number | null;
  effective_rooting_depth_cm?: number | null;
  clay_pct?: number | null;
  sand_pct?: number | null;
  silt_pct?: number | null;
  bulk_density_g_cm3?: number | null;
  climate_normal_rainfall_mm?: number | null;
  data_provenance?: string | null;
  is_lab_measured: boolean;
  is_synthetic: boolean;
}

export interface RashkarCropStageItem {
  stage_code: string;
  stage_name_en: string;
  stage_name_mr?: string | null;
  sequence_order?: number;
  typical_das_start?: number;
  typical_das_end?: number;
  description?: string | null;
}

export interface RashkarCanonicalCropItem {
  crop_code: string;
  common_name_en: string;
  common_name_mr: string;
  botanical_name: string;
  crop_category: string;
  standard_season: string;
  is_pioneer_pilot_crop: boolean;
  support_level: string;
  apy_alias_list: string[];
  stages?: RashkarCropStageItem[];
}

export interface RashkarCropCycle {
  id: string;
  farm_id: string;
  owner_id: string;
  crop_code: string;
  variety_name?: string | null;
  sowing_date?: string | null;
  season?: string | null;
  planted_area_acres?: number | null;
  irrigation_type?: string | null;
  current_stage_code?: string | null;
  stage_source: string;
  stage_confidence?: number | null;
  is_active: boolean;
  created_at_utc: string;
  updated_at_utc: string;
}

export interface RashkarCropCycleCreate {
  crop_code: string;
  variety_name?: string | null;
  sowing_date?: string | null;
  season?: string | null;
  planted_area_acres?: number | null;
  irrigation_type?: string | null;
  current_stage_code?: string | null;
  stage_source?: string;
  stage_confidence?: number | null;
  is_active?: boolean;
}

export interface RashkarCropCycleUpdate {
  variety_name?: string | null;
  sowing_date?: string | null;
  season?: string | null;
  planted_area_acres?: number | null;
  irrigation_type?: string | null;
  current_stage_code?: string | null;
  stage_source?: string | null;
  stage_confidence?: number | null;
  is_active?: boolean | null;
}

export interface RashkarOverviewWeatherPreview {
  status: "OK" | "WEATHER_UNAVAILABLE" | string;
  provider?: string | null;
  elevation_m?: number | null;
  current_air_temp_c?: number | null;
  current_relative_humidity_pct?: number | null;
  current_wind_speed_ms?: number | null;
  current_solar_irradiance_wm2?: number | null;
  timestamp_ist?: string | null;
  error?: string | null;
}

export interface RashkarOverviewResponse {
  farm_context: RashkarFarmContext;
  has_active_crop: boolean;
  active_crop_cycle: RashkarCropCycle | null;
  soil: RashkarSoilContext | null;
  weather: RashkarOverviewWeatherPreview;
  saved_income_plans_count: number;
  latest_assessments: {
    worker_heat: {
      id: string;
      assessed_at_ist: string;
      calculated_wbgt_c: number;
      risk_tier: string;
    } | null;
    crop_heat: {
      id: string;
      assessed_at_ist: string;
      crop_code: string;
      stage_code?: string | null;
      stress_tier: string;
      overall_stress_score?: number | null;
    } | null;
    yield_intelligence: {
      id: string;
      assessed_at_ist: string;
      crop_code: string;
      composite_risk_tier?: string | null;
      composite_risk_score?: number | null;
      benchmark_tier?: string | null;
    } | null;
  };
}

// ── Worker Heat & WBGT Types ──────────────────────────────────────────────────

export type WorkloadCategory = "light" | "moderate" | "heavy" | "very_heavy";
export type ClothingType =
  | "standard_work_clothes"
  | "woven_double_layer"
  | "coveralls_protective"
  | "impermeable_vapor_barrier";
export type SunExposureType = "direct_sun" | "partial_shade" | "full_shade";

export interface WorkerHeatAssessmentRequest {
  farm_id?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  taluka?: string | null;
  workload_category: WorkloadCategory;
  clothing_type: ClothingType;
  is_acclimatised: boolean;
  sun_exposure: SunExposureType;
  exposure_duration_hours: number;
}

export interface HourlyHeatRiskProjection {
  forecast_hour_offset: number;
  valid_time_ist: string;
  air_temp_c: number;
  relative_humidity_pct: number;
  wind_speed_ms: number;
  solar_irradiance_wm2: number;
  wbgt_estimated_c: number;
  wbgt_effective_c: number;
  heat_index_c?: number | null;
  utci_c?: number | null;
  hazard_level: string;
  exceeds_screening_threshold: boolean;
  threshold_limit_c: number;
  trend: string;
  work_rest_cycle: string;
  missing_data_warnings?: string | null;
}

export interface PersonalizedWorkerHeatStrainScore {
  score_0_100: number;
  severity_level: string;
  indicator_color: string;
  sub_indices?: {
    base_thermal_exceedance_points?: number;
    metabolic_workload_points?: number;
    vulnerability_points?: number;
    duration_hydration_points?: number;
  };
  action_summary?: string;
  iso_threshold_c?: number;
  effective_wbgt_c?: number;
  wbgt_exceedance_c?: number;
}

export interface WorkerHeatAssessmentResponse {
  status: string;
  error_message?: string | null;
  session_id: string;
  generated_at_ist: string;
  time_horizon: string;
  recalculation_cadence_minutes: number;

  farm_location_display: string;
  weather_source_name: string;
  weather_retrieval_time_ist: string;
  forecast_issue_time_ist: string;
  valid_time_ist: string;
  spatial_resolution: string;
  grid_coordinates: string;
  is_observed_or_forecast: string;
  current_air_temp_c?: number | null;
  current_relative_humidity_pct?: number | null;
  current_dew_point_c?: number | null;
  current_wind_speed_ms?: number | null;
  current_wind_speed_kmh?: number | null;
  current_solar_radiation_wm2?: number | null;
  current_wbgt_estimated_c?: number | null;
  current_heat_index_c?: number | null;
  current_utci_c?: number | null;
  personalized_heat_strain_score?: PersonalizedWorkerHeatStrainScore | null;
  topographic_downscaling?: Record<string, any> | null;
  ml_forecast_metadata?: Record<string, any> | null;
  next_assessment_refresh_ist?: string | null;
  data_confidence: string;
  missing_variables: string[];
  missing_variables_warning?: string | null;

  peak_risk_hour_ist?: string | null;
  peak_risk_reason?: string | null;
  hourly_projections: HourlyHeatRiskProjection[];

  workload_category: string;
  clothing_type: string;
  clothing_cav_c: number;
  is_acclimatised: boolean;
  sun_exposure: string;
  exposure_duration_hours: number;
  planned_shift_duration_hours: number;
  forecast_coverage_hours: number;
  shift_exceeds_forecast_coverage: boolean;
  coverage_limitation_warning?: string | null;
  current_hazard_level: string;
  max_hazard_level_in_window: string;
  max_wbgt_effective_c?: number | null;
  screening_threshold_c: number;
  threshold_comparison_message: string;
  threshold_difference_c: number;
  threshold_comparison_state: string;

  category_selection_reason: string;
  main_contributing_factors: string[];
  workload_interaction_explanation: string;
  methodology_reference: string;
  methodology_standards_version: string;
  threshold_meaning_explanation: string;
  safety_guarantee_disclaimer: string;
  technical_details: Record<string, any>;

  disclaimer: string;
  safety_cautions: string[];
  hydration_guidance: {
    rule_summary?: string;
    max_hourly_rate?: string;
    electrolyte_advice?: string;
    beverage_restrictions?: string;
  };
  before_work_guidance: string[];
  during_work_guidance: string[];
  high_risk_actions: string[];
  emergency_triage: {
    heat_exhaustion?: { warning_signs?: string[]; immediate_response?: string[] };
    heat_stroke?: { warning_signs?: string[]; immediate_response?: string[] };
  };
  local_emergency_contacts: Record<string, string>;

  provenance?: Record<string, any> | null;
  audit_logged: boolean;
}

export interface WorkerHeatHistoryItem {
  id: string;
  farm_id: string;
  owner_id: string;
  request_timestamp_ist: string;
  forecast_target_timestamp_ist?: string | null;
  weather_provider: string;
  air_temp_c: number;
  relative_humidity_pct: number;
  wind_speed_kmh: number;
  solar_radiation_wm2: number;
  calculated_wbgt_c: number;
  calculated_heat_index_c?: number | null;
  risk_tier: string;
  workload_class: string;
  acclimatization_status: boolean;
  applied_threshold_wbgt_c: number;
  provenance_summary?: Record<string, any> | null;
}

// ── Crop Heat Stress Types ────────────────────────────────────────────────────

export interface CropHeatAssessmentRequest {
  farm_id: string;
  plot_id?: string | null;
  crop_code?: string | null;
  farmer_confirmed_stage?: string | null;
  forecast_tmax_c?: number | null;
  forecast_tmin_c?: number | null;
  forecast_sun_hours?: number | null;
}

export interface CropHeatIntervention {
  intervention_id: string;
  title_en: string;
  title_mr: string;
  description_en: string;
  description_mr: string;
  why_appropriate: string;
  evidence_citation: string;
  source_page_or_table?: string | null;
  agronomist_reviewer?: string | null;
  application_method?: string | null;
  application_dose?: string | null;
  infrastructure_requirements?: string | null;
  trigger_condition?: string | null;
  evidence_status: string;
  category: string;
}

export interface DailyCropHeatOutlook {
  date: string;
  day_label: string;
  tmax_c: number;
  tmin_c: number;
  hours_above_critical: number;
  risk_category: string;
  explanation: string;
}

export interface SupportedStageOption {
  stage_code: string;
  stage_name?: string;
  stage_name_en?: string;
  stage_name_mr?: string;
  das_range?: string;
  crit_tmax?: number;
}

export interface CropHeatAssessmentResponse {
  status: string;
  has_active_crop: boolean;
  needs_crop_registration: boolean;
  message?: string | null;

  assessment_id: string;
  farm_id: string;
  farm_name: string;
  plot_name: string;
  crop_code?: string | null;
  crop_common_name?: string | null;
  crop_variety?: string | null;
  sowing_date?: string | null;
  days_after_sowing?: number | null;
  crop_area_acres?: number | null;
  irrigation_status?: string | null;
  soil_texture?: string | null;
  soil_provenance_label: string;
  is_soil_synthetic: boolean;

  is_season_expired: boolean;
  season_status: string;
  requires_season_update: boolean;
  season_expiry_message?: string | null;

  growth_stage_code?: string | null;
  growth_stage_name_en?: string | null;
  growth_stage_name_mr?: string | null;
  stage_source?: string | null;
  supported_stages: SupportedStageOption[];
  farmer_confirmed_stage?: string | null;

  base_temp_c?: number | null;
  optimal_temp_min_c?: number | null;
  optimal_temp_max_c?: number | null;
  critical_tmax_threshold_c?: number | null;
  critical_tmin_threshold_c?: number | null;
  tmax_forecast_c?: number | null;
  tmin_forecast_c?: number | null;
  peak_vpd_kpa?: number | null;
  hours_above_critical?: number | null;
  consecutive_hot_days?: number | null;
  daytime_exposure_hours?: number | null;
  warm_night_respiration_hazard?: boolean | null;
  warm_night_penalty_score?: number | null;
  cumulative_heat_units_gdd?: number | null;
  overall_stress_score?: number | null;
  evidence_citation: string;
  evidence_status: string;
  institution_attribution?: string | null;
  thermal_analysis?: Record<string, any> | null;
  personalized_crop_vulnerability_score?: {
    score_0_100: number;
    vulnerability_level: string;
    indicator_color: string;
    sub_indices?: Record<string, number>;
    action_recommendation?: string;
    max_temp_c?: number;
    optimum_temp_c?: number;
    critical_temp_c?: number;
  } | null;
  topographic_downscaling?: Record<string, any> | null;

  daily_outlook: DailyCropHeatOutlook[];
  four_day_outlook?: DailyCropHeatOutlook[] | null;

  generated_at_ist: string;
  daytime_heat_stress_level?: string | null;
  overall_crop_heat_risk?: string | null;
  physiological_mechanism?: string | null;
  stage_biological_vulnerability?: string | null;

  recommended_interventions: CropHeatIntervention[];
  field_recommendations: CropHeatIntervention[];

  assessment_history: Array<Record<string, any>>;
  provenance?: Record<string, any> | null;
  audit_logged: boolean;
}

export interface CropHeatHistoryItem {
  id: string;
  farm_id: string;
  owner_id: string;
  crop_code: string;
  stage_code?: string | null;
  stage_source?: string | null;
  assessed_at_ist: string;
  peak_tmax_c?: number | null;
  peak_vpd_kpa?: number | null;
  overall_stress_score?: number | null;
  stress_tier: string;
  weather_source?: string | null;
  provenance_summary?: Record<string, any> | null;
}

// ── Yield Intelligence & DES APY Baseline Types ───────────────────────────────

export interface YieldRiskItem {
  risk_dimension: string;
  risk_level: string;
  time_horizon: string;
  impact_severity: string;
  confidence: string;
  drivers: string[];
  evidence_provenance: Array<Record<string, any>>;
  recommended_actions: Array<{ title?: string; description?: string; [key: string]: any }>;
}

export interface HistoricalYieldBaseline {
  status: string;
  geographical_unit: string;
  district: string;
  crop_code: string;
  season: string;
  data_period: string;
  sample_seasons_count: number;
  historical_mean_t_ha?: number | null;
  historical_median_t_ha?: number | null;
  historical_p10_t_ha?: number | null;
  historical_p25_t_ha?: number | null;
  historical_p90_t_ha?: number | null;
  min_recorded_t_ha?: number | null;
  max_recorded_t_ha?: number | null;
  historical_std_dev?: number | null;
  disclaimer: string;
}

export interface SoilSuitabilityAnalysis {
  soil_texture?: string | null;
  soil_ph?: number | null;
  ph_status: string;
  organic_carbon_pct?: number | null;
  cation_exchange_capacity?: number | null;
  available_water_capacity_mm_m?: number | null;
  effective_rooting_depth_cm?: number | null;
  climate_normal_rainfall_mm?: number | null;
  suitability_verdict: string;
  data_provenance: string;
}

export interface YieldActionableRecommendation {
  recommendation_id: string;
  title: string;
  description: string;
  why_recommended: string;
  supporting_data: string;
  evidence_source: string;
  urgency: string;
  limitations: string;
}

export interface YieldRiskResponse {
  status: string;
  has_active_crop: boolean;
  needs_crop_registration: boolean;
  message?: string | null;

  farm_id: string;
  farm_name: string;
  plot_id: string;
  crop_code?: string | null;
  crop_name?: string | null;
  sowing_date?: string | null;
  days_after_sowing?: number | null;
  total_area_acres?: number | null;
  irrigation_type?: string | null;
  location_display: string;
  generated_at_utc: string;
  timezone: string;

  yield_baseline?: HistoricalYieldBaseline | null;
  suitability_analysis?: SoilSuitabilityAnalysis | null;
  coverage: Record<string, any>;
  crop_stage: Record<string, any>;
  risks: YieldRiskItem[];
  composite_risk_score?: number | null;
  composite_risk_tier?: string | null;
  ml_prediction_gate: {
    prediction_status?: string;
    historical_baseline_available?: boolean;
    farm_level_supervised_model?: string;
    ethical_safeguard?: string;
    historical_p10_t_ha?: number | null;
    historical_p25_t_ha?: number | null;
    historical_mean_t_ha?: number | null;
    historical_p90_t_ha?: number | null;
    [key: string]: any;
  };
  recommendations: YieldActionableRecommendation[];
  farmer_narrative_explanation: string;
  provenance?: Record<string, any> | null;
  audit_logged: boolean;
}

export interface YieldHistoryItem {
  id: string;
  farm_id: string;
  owner_id: string;
  crop_code: string;
  district?: string | null;
  assessed_at_ist: string;
  benchmark_tier?: string | null;
  apy_mean_t_ha?: number | null;
  apy_median_t_ha?: number | null;
  apy_sample_count: number;
  composite_risk_score?: number | null;
  composite_risk_tier?: string | null;
  prediction_lock_status: string;
  provenance_summary?: Record<string, any> | null;
}

// ── Extra Income ("Earn More") Types ──────────────────────────────────────────

export interface FarmerResourceProfile {
  available_investment_inr: number;
  monthly_operating_budget_inr: number;
  max_risk_capital_inr?: number | null;
  willing_to_borrow: boolean;

  total_farm_acres?: number | null;
  cultivated_acres?: number | null;
  available_land_acres: number;
  unused_land_acres: number;
  field_bunds_available: boolean;

  has_animal_shed: boolean;
  has_storage_room: boolean;
  has_shaded_space: boolean;

  water_availability: string;
  water_months_available: number[];

  family_labor_hours_day: number;
  hired_labor_possible: boolean;

  existing_livestock: string;
  existing_assets: string[];

  crop_byproducts: string[];
  byproduct_surplus_available: boolean;

  interests: string[];
  has_transport: boolean;
  has_fpo_access: boolean;
  distance_to_apmc_km?: number | null;

  risk_tolerance: string;
  category_preference: string;

  age_range?: string | null;
  work_preference?: string | null;
  payback_horizon?: string | null;
  family_management_role?: string | null;
  current_crop_code?: string | null;
  current_crop_stage?: string | null;
}

export interface OpportunityCatalogItem {
  opportunity_id: string;
  title: string;
  category: string;
  is_cost_saving: boolean;
  tagline: string;
  min_investment_inr: number;
  max_investment_inr: number;
  working_capital_required_inr: number;
  required_land_acres: number;
  required_space_type: string;
  water_requirement: string;
  daily_labor_hours: number;
  risk_level: string;
  payback_period_months: number;
  potential_annual_profit_inr: number;
  potential_annual_savings_inr: number;
  summary: string;
  market_commodity: string;
  market_benchmark_price: string;
  market_source: string;
  market_verified?: boolean;
  target_crops: string[];
  key_assumptions: string[];
  key_risks: string[];
  source_attribution: string;
  minimum_viable_unit_description: string;
  production_cycle_days?: number;
  revenue_delay_months?: number;
}

export interface FarmerSummaryQA {
  what_is_it?: string;
  why_suits_my_farm?: string;
  what_will_i_need?: string;
  how_will_i_earn_or_save?: string;
  when_will_i_receive_money?: string;
  what_to_be_careful_about?: string;
}

export interface DiscoveredOpportunity {
  opportunity: OpportunityCatalogItem;
  feasibility_status: string;
  suitability_score: number;
  is_feasible: boolean;
  capital_gap_inr: number;
  matching_resources: string[];
  missing_requirements: string[];
  primary_benefit_label: string;
  evidence_source: string;
  estimated_annual_profit_inr: number;
  estimated_annual_savings_inr: number;
  payback_months: number;
  market_benchmark_summary: string;
  tripartite_return?: {
    additional_cash_income_inr: number;
    cost_savings_inr: number;
    loss_avoidance_inr: number;
  } | null;
  feasibility_category: string;
  farmer_summary_qa?: FarmerSummaryQA | null;
  suitability_score_pct?: number | null;
  is_suitable?: boolean | null;
  suitability_verdict?: string | null;
  reasons_why_suitable: string[];
  reasons_why_unsuitable: string[];
}

export interface FinancialScenarioItem {
  name: string;
  price_assumption: string;
  cost_assumption: string;
  gross_annual_revenue_inr: number;
  annual_money_saved_inr: number;
  annual_opex_inr: number;
  cash_operating_surplus_inr: number;
  imputed_family_labor_cost_inr: number;
  economic_profit_inr: number;
  net_annual_profit_inr: number;
  break_even_months?: number | null;
  break_even_reached: boolean;
  monthly_net_cash_flow_inr: number[];
}

export interface EnterpriseFinancialAnalysis {
  scenario_id: string;
  opportunity_id: string;
  opportunity_title: string;
  category: string;
  is_cost_saving: boolean;
  custom_budget_inr: number;
  calculated_capex_inr: number;
  working_capital_inr: number;
  total_initial_outlay_inr: number;
  calculated_gross_revenue_inr: number;
  calculated_annual_savings_inr: number;
  calculated_opex_annual_inr: number;
  cash_operating_surplus_inr: number;
  imputed_family_labor_cost_inr: number;
  economic_profit_inr: number;
  calculated_net_profit_annual_inr: number;
  calculated_break_even_months?: number | null;
  break_even_reached: boolean;
  monthly_cash_flows: number[];
  assumptions_applied: string[];
  risks_to_monitor: string[];
  source_attribution: string;
  scenarios: Record<string, FinancialScenarioItem>;
  local_mandi_benchmark: Record<string, any>;
  sensitivity_analysis: Record<string, any>;
  nabard_source_citation: string;
  disclaimer: string;
}

export interface ScenarioCalculateRequest {
  opportunity_id: string;
  custom_budget_inr?: number | null;
  water_availability?: string | null;
  available_labour_hours_day?: number | null;
  available_land_acres?: number | null;
  custom_assumptions?: Record<string, any> | null;
  farm_id?: string | null;
}

export interface OpportunityComparisonItem {
  opportunity_id: string;
  title: string;
  category: string;
  is_cost_saving: boolean;
  initial_investment_inr: number;
  net_annual_profit_inr: number;
  annual_money_saved_inr: number;
  payback_months?: number | null;
  break_even_reached: boolean;
  land_required_acres: number;
  water_needs: string;
  daily_labor_hours: number;
  risk_level: string;
  suitability_verdict: string;
}

export interface SavedIncomePlan {
  plan_id: string;
  farmer_id: string;
  farm_id: string;
  opportunity_id: string;
  opportunity_title: string;
  category: string;
  chosen_budget_inr: number;
  projected_annual_profit_inr: number;
  projected_annual_savings_inr: number;
  payback_months?: number | null;
  break_even_reached: boolean;
  notes?: string | null;
  created_at_utc: string;
}
