/**
 * CropNet AI — Authoritative TypeScript types mirroring FastAPI backend schemas.
 * No fabricated values; optional and null fields are preserved.
 */

// ── Common & Geospatial ───────────────────────────────────────────────────────

export interface GeoJSONPolygon {
  type: "Polygon";
  coordinates: [number, number][][];
}

// ── Farms ────────────────────────────────────────────────────────────────────

export interface Farm {
  id: string;
  name: string;
  taluka: string;
  district?: string;
  state?: string;
  village?: string | null;
  geometry?: GeoJSONPolygon;
  irrigation_type?: string;
  water_source?: string;
  calculated_area_hectares?: number;
  calculated_area_acres?: number;
  centroid_latitude?: number;
  centroid_longitude?: number;
  latitude?: number;
  longitude?: number;
  owner_id?: string;
  created_at?: string;
  updated_at?: string;
}

export interface FarmCreate {
  name: string;
  taluka: string;
  village?: string | null;
  district?: string;
  state?: string;
  geometry: GeoJSONPolygon;
  irrigation_type?: string;
  water_source?: string;
}

export interface FarmUpdate {
  name?: string;
  village?: string | null;
  taluka?: string;
  district?: string;
  state?: string;
  irrigation_type?: string;
  water_source?: string;
  geometry?: GeoJSONPolygon;
}

// ── Weather & Climate ────────────────────────────────────────────────────────

export interface CurrentWeather {
  farm_id?: string;
  source: string;
  data_type?: string;
  observation_time: string;
  retrieval_time?: string;
  temperature_c: number;
  feels_like_c?: number;
  temperature_min_c?: number;
  temperature_max_c?: number;
  humidity_percent: number;
  wind_speed_ms?: number;
  wind_direction_deg?: number;
  precipitation_mm?: number;
  weather_condition: string;
  weather_description: string;
  weather_icon?: string;
  is_cached?: boolean;
}

export interface DailyForecastSummary {
  date: string;
  day_name: string;
  temp_min_c: number;
  temp_max_c: number;
  humidity_percent: number;
  weather_condition: string;
  weather_description: string;
  weather_icon: string;
  total_rain_mm: number;
  max_pop_pct: number;
}

export interface WeatherForecastPoint {
  forecast_time: string;
  timestamp?: string;
  temperature_c: number;
  temp_min_c?: number;
  temp_max_c?: number;
  humidity_percent: number;
  wind_speed_ms?: number;
  precipitation_probability_pct?: number;
  precipitation_mm: number;
  weather_condition: string;
  weather_description: string;
  weather_icon?: string;
}

export interface WeatherForecast {
  farm_id: string;
  source: string;
  data_type?: string;
  retrieval_time?: string;
  forecast_period?: string;
  daily_summaries?: DailyForecastSummary[];
  hourly_points?: WeatherForecastPoint[];
  forecasts?: WeatherForecastPoint[]; // legacy compatibility
  forecast_days_count?: number;
  is_cached?: boolean;
}

export interface ClimateSummary {
  farm_id: string;
  source: string;
  annual_rainfall_mm?: number;
  monsoon_rainfall_mm?: number;
  mean_temperature_c?: number;
  potential_water_stress_indicator?: string;
  notes?: string[];
}

// ── Soil Intelligence ────────────────────────────────────────────────────────

export interface SoilParameterObservation {
  parameter_key?: string;
  display_name?: string;
  value: number | null;
  unit?: string;
  source?: string;
  dataset_version?: string;
  depth_interval?: string;
  spatial_resolution?: string;
  vintage_year?: number | null;
  uncertainty?: number | null;
  verification_status?: string;
  availability_status?: string;
  farm_coverage_percent?: number;
  scientific_note?: string | null;
}

export interface SoilParameter {
  parameter_name: string;
  value: number | null;
  unit: string;
  depth?: string;
  source: string;
  verification_status: "VERIFIED" | "SPATIAL_ESTIMATE" | "NOT_VERIFIED";
}

export interface SoilProfile {
  profile_id?: string;
  farm_id: string;
  source?: string;
  source_dataset?: string;
  dataset_version?: string;
  spatial_resolution?: string;
  depth?: string;
  depth_interval?: string;
  taluka?: string | null;
  district?: string;
  state?: string;
  is_map_derived?: boolean;
  disclaimer?: string;
  soil_texture_class?: string | null;
  texture_class?: string | null;

  ph?: SoilParameterObservation | number | null;
  organic_carbon?: SoilParameterObservation | number | null;
  organic_carbon_percentage?: SoilParameterObservation | number | null;
  sand_percent?: SoilParameterObservation | number | null;
  sand_percentage?: SoilParameterObservation | number | null;
  silt_percent?: SoilParameterObservation | number | null;
  silt_percentage?: SoilParameterObservation | number | null;
  clay_percent?: SoilParameterObservation | number | null;
  clay_percentage?: SoilParameterObservation | number | null;
  total_nitrogen?: SoilParameterObservation | number | null;
  cation_exchange_capacity?: SoilParameterObservation | number | null;
  electrical_conductivity?: SoilParameterObservation | number | null;
  available_nitrogen?: SoilParameterObservation | number | null;
  available_phosphorus?: SoilParameterObservation | number | null;
  available_potassium?: SoilParameterObservation | number | null;
  nitrogen_available_kg_ha?: SoilParameterObservation | number | null;
  phosphorus_available_kg_ha?: SoilParameterObservation | number | null;
  potassium_available_kg_ha?: SoilParameterObservation | number | null;

  mapped_soil_zones?: any[];
  additional_parameters?: Record<string, SoilParameterObservation>;
  parameters?: Record<string, SoilParameter>;
  available_parameters_count?: number;
  total_requested_parameters?: number;
  data_completeness_ratio?: number;
  last_analyzed?: string;
  created_at?: string;
}

export interface SoilReportMeasurement {
  id: string;
  report_id?: string;
  farm_id?: string;
  parameter_key?: string;
  parameter_category?: string;
  original_parameter_name?: string;
  display_name?: string;
  parameter_name?: string;
  parameter_code?: string;
  original_value?: number | null;
  original_value_text?: string | null;
  original_unit?: string;
  normalized_value?: number | null;
  normalized_unit?: string | null;
  numeric_value?: number | null;
  unit?: string;
  analytical_method?: string | null;
  lab_reference_range?: Record<string, any> | null;
  lab_rating?: string | null;
  page_number?: number;
  sample_id?: string | null;
  sample_designation?: string | null;
  area_type?: string | null;
  extraction_confidence?: number;
  confidence_score?: number;
  is_ambiguous?: boolean;
  verification_status?: string;
  verified?: boolean;
  farmer_corrected_value?: number | null;
  farmer_notes?: string | null;
  interpretation?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SoilTestReport {
  id: string;
  farm_id: string;
  user_id?: string;
  original_filename?: string;
  file_name?: string;
  upload_timestamp: string;
  laboratory_name?: string | null;
  lab_number?: string | null;
  report_date?: string | null;
  sample_collection_date?: string | null;
  sample_date?: string | null;
  date_received?: string | null;
  date_processed?: string | null;
  sample_depth_interval?: string | null;
  depth_provenance?: string;
  sampling_point_name?: string | null;
  extraction_status?: "UPLOADED" | "PROCESSING" | "NEEDS_REVIEW" | "CONFIRMED" | "FAILED" | string;
  review_status?: "NEEDS_REVIEW" | "PARTIALLY_REVIEWED" | "CONFIRMED" | "REJECTED" | string;
  status?: "PROCESSING" | "NEEDS_REVIEW" | "CONFIRMED" | "REJECTED" | "FAILED" | string;
  total_measurements?: number;
  confirmed_measurements?: number;
  storage_path?: string;
  file_size_bytes?: number;
  mime_type?: string;
  extraction_error?: string | null;
  reviewed_at?: string | null;
  confirmed_at?: string | null;
  signed_document_url?: string | null;
  measurements?: SoilReportMeasurement[];
  created_at?: string;
  updated_at?: string;
}

// ── Farm Health Snapshot ─────────────────────────────────────────────────────

export interface HealthDomainState {
  availability_state: "AVAILABLE" | "PARTIALLY_AVAILABLE" | "NOT_AVAILABLE" | "STALE" | "INSUFFICIENT_EVIDENCE";
  last_updated?: string | null;
  data_age_days?: number | null;
  provenance?: string | null;
  [key: string]: any;
}

export interface FarmHealthSnapshot {
  contract_version: string;
  farm_id: string;
  farm_name: string;
  owner_id?: string;
  taluka: string;
  district?: string;
  state?: string;
  calculated_area_hectares?: number;
  calculated_area_acres?: number;
  snapshot_timestamp: string;
  overall_evidence_overview: {
    domains_available: number;
    domains_partially_available: number;
    domains_stale: number;
    domains_not_available: number;
    domains_insufficient_evidence: number;
    total_domains: number;
    actionable_summary: string;
  };
  soil: HealthDomainState;
  water: HealthDomainState;
  satellite: HealthDomainState;
  weather: HealthDomainState;
  crop_context: HealthDomainState;
  governance_notice: string;
}

// ── Water Intelligence ───────────────────────────────────────────────────────

export interface WaterSource {
  id: string;
  farm_id: string;
  name: string;
  source_type: "well" | "borewell" | "canal" | "river" | "farm_pond" | "tanker" | "other";
  capacity_status?: string;
  is_perennial?: boolean;
  notes?: string;
}

export interface WaterEvaluation {
  evaluation_id: string;
  farm_id: string;
  suitability: string;
  bis_standard_compliance: boolean;
  cssri_category?: string;
  actionable_recommendations: string[];
  disclaimer: string;
}

// ── Satellite Intelligence ───────────────────────────────────────────────────

export interface SatelliteObservation {
  id?: string;
  farm_id: string;
  observation_date: string;
  canopy_ndvi: number | null;
  canopy_ndmi: number | null;
  vegetation_coverage_percent?: number | null;
  cloud_masked_percent?: number | null;
  sensor?: string;
  raster_maps?: {
    ndvi_map_url?: string | null;
    ndmi_map_url?: string | null;
    scl_map_url?: string | null;
  };
  agronomic_interpretation?: string;
  scientific_disclaimer?: string;
}

// ── Crop Doctor ──────────────────────────────────────────────────────────────

export interface ChemicalTreatment {
  product: string;
  dosage_per_liter: string;
  dosage_per_acre: string;
  application_type?: string;
  spray_interval?: string;
  pre_harvest_interval_days?: number;
  notes?: string;
}

export interface BiologicalControl {
  agent: string;
  dosage: string;
  application_method: string;
  benefits?: string;
}

export interface CropDoctorDiseaseItem {
  key: string;
  crop: string;
  common_name: string;
  pathogen_type: string;
  causal_agent: string;
  severity_level: string;
  severity_score: number;
}

export interface CropDoctorStatus {
  loaded: boolean;
  model_id: string;
  error?: string | null;
}

export interface CropDoctorPrediction {
  crop: string;
  diagnosis: string;
  confidence_percent: number;
  is_healthy: boolean;
  raw_label?: string;
  pathogen_type?: string;
  causal_agent?: string;
  severity_level?: string;
  severity_score?: number;
  yield_loss_risk?: string;
  damage_symptoms?: string;
  favorable_conditions?: string;
  chemical_control?: ChemicalTreatment[];
  organic_control?: BiologicalControl[];
  cultural_ipm?: string[];
  actionable_advice?: string | string[];
  differential_diagnosis?: string;
  disclaimer: string;
}

// ── Heat Risk ────────────────────────────────────────────────────────────────

export interface HeatRiskCrop {
  crop_code: string;
  common_name: string;
  night_crit_c: number;
  stages: string[];
}

export interface HeatRiskCropsResponse {
  crops: HeatRiskCrop[];
}

export interface CropHeatRequest {
  crop_code: string;
  forecast_tmax_c: number;
  forecast_tmin_c: number;
  growth_stage?: string;
  days_after_sowing?: number;
  forecast_sun_hours?: number;
}

export interface CropHeatResponse {
  crop_code: string;
  growth_stage_code: string;
  growth_stage_name: string;
  critical_tmax_c: number;
  critical_tmin_c: number;
  forecast_tmax_c: number;
  forecast_tmin_c: number;
  hours_above_critical: number;
  warm_night_hazard: boolean;
  warm_night_penalty: number;
  cumulative_gdd: number;
  risk_category: "LOW" | "MODERATE" | "HIGH" | "SEVERE";
  risk_label: string;
  explanation: string;
  evidence_citation: string;
  methodology_note: string;
}

export interface WorkerHeatRequest {
  air_temp_c: number;
  relative_humidity_pct: number;
  wind_speed_ms?: number;
  solar_irradiance_wm2?: number;
  workload_category?: string;
  clothing_type?: string;
  is_acclimatised?: boolean;
  sun_exposure?: string;
}

export interface WorkerHeatResponse {
  wbgt_c: number;
  wbgt_effective_c: number;
  threshold_c: number;
  hazard_level: string;
  exceeds_threshold: boolean;
  work_rest_cycle: string;
  heat_index_c?: number | null;
  utci_c?: number | null;
  recommendation: string;
  methodology_note: string;
}

export interface HeatRiskDailyOutlook {
  date: string;
  day_name?: string;
  tmax_c: number;
  tmin_c: number;
  hours_above_critical: number;
  warm_night_hazard: boolean;
  risk_category: string;
}

export interface HeatRiskIntervention {
  title: string;
  description: string;
  rationale: string;
  evidence: string;
  category: string;
}

export interface FarmHeatRiskRequest {
  crop_code: string;
  sowing_date?: string | null;
  days_after_sowing?: number | null;
  growth_stage?: string | null;
  include_worker_heat?: boolean;
  workload_category?: string;
  is_acclimatised?: boolean;
  sun_exposure?: string;
}

export interface FarmHeatRiskResponse {
  farm_id: string;
  farm_name: string;
  crop_code: string;
  crop_common_name: string;
  growth_stage_code: string;
  growth_stage_name: string;
  forecast_tmax_c: number;
  forecast_tmin_c: number;
  critical_tmax_c: number;
  risk_category: string;
  risk_label: string;
  hours_above_critical: number;
  warm_night_hazard: boolean;
  cumulative_gdd: number;
  daily_outlook: HeatRiskDailyOutlook[];
  interventions: HeatRiskIntervention[];
  worker_heat?: WorkerHeatResponse;
  weather_source: string;
  provenance: string;
  limitations: string[];
  generated_at: string;
}

// ── Crops Catalogue ──────────────────────────────────────────────────────────

export interface Crop {
  id: string;
  crop_name: string;
  botanical_name?: string;
  category: string;
  season?: string;
  water_requirement_mm?: number;
  soil_preference?: string;
  ph_min?: number;
  ph_max?: number;
  description?: string;
}

export interface CropRequirement {
  crop_id: string;
  ph_min?: number;
  ph_max?: number;
  preferred_texture?: string[];
  annual_water_requirement_mm?: number;
  temperature_min_c?: number;
  temperature_max_c?: number;
  critical_stages?: string[];
}

// ── Government Schemes ───────────────────────────────────────────────────────

export interface GovernmentScheme {
  id: string;
  scheme_name: string;
  category: string;
  government_level: "Central" | "State";
  state?: string | null;
  description?: string | null;
  benefits?: string[] | null;
  eligibility?: string[] | null;
  required_documents?: string[] | null;
  application_steps?: string[] | null;
  department?: string | null;
  application_url?: string | null;
  source_url?: string | null;
  status: "ACTIVE" | "INACTIVE" | "DRAFT";
  verification_status: "VERIFIED" | "NOT_VERIFIED" | "PENDING_REVIEW";
  last_verified_date?: string | null;
}

export interface SchemeFilters {
  categories: string[];
  government_levels: string[];
  states: string[];
}

export interface SchemeAdminStatus {
  is_admin: boolean;
  user_id?: string;
  email?: string;
}

// ── Income Diversification ───────────────────────────────────────────────────

export interface IncomeOpportunity {
  opportunity_id: string;
  title: string;
  category: string;
  is_cost_saving?: boolean;
  tagline: string;
  estimated_investment_inr?: number;
  expected_payback_period?: string;
  water_requirement_level?: string;
  suitable_crops?: string[];
  actionable_guidelines?: string[];
  eligibility_notes?: string;
}

// ── Agricultural Intelligence & Advisory ─────────────────────────────────────

export interface AppliedRuleRecord {
  rule_id: string;
  domain: string;
  parameter_checked: string;
  rule_statement: string;
  condition_met: boolean;
  evidence_tier?: string;
  supporting_statement?: string;
}

export interface CitationMetadata {
  source_id: string;
  organization: string;
  publication_title: string;
  publication_year?: number;
  section_or_pages?: string;
  evidence_tier?: string;
}

export interface FollowUpQuestion {
  question_id: string;
  target_parameter: string;
  priority: number;
  question_text_en: string;
  question_text_mr: string;
  question_type: "choice" | "numeric" | "boolean";
  options?: string[];
  agronomic_rationale?: string;
}

export interface CropEvaluationOutcome {
  crop_id: string;
  common_name: string;
  scientific_name: string;
  marathi_name?: string | null;
  decision_state: string; // RECOMMENDED | CONDITIONALLY_SUITABLE | REGIONAL_SCREENING_ONLY | NOT_RECOMMENDED | DISQUALIFIED | ABSTAIN_INSUFFICIENT_DATA
  is_disqualified: boolean;
  limiting_factors: string[];
  reproductive_risk_warnings: string[];
  missing_information: string[];
  uncertainty_notes: string[];
  applied_rules?: AppliedRuleRecord[];
  citations?: CitationMetadata[];
  explanation: string;
}

export interface StructuredAdvisoryCard {
  title: string;
  direct_answer: string;
  what_this_means?: string;
  crop_status_label?: string;
  crop_status_code?: string;
  observations?: Array<{ parameter: string; value: string; source: string; status: string }>;
  what_needs_attention?: string[];
  next_steps?: string[];
  evidence_references?: string[];
}

export interface FarmEvaluationResponse {
  decision_id: string;
  evaluated_at: string;
  input_validation_status: string;
  contradictions_detected?: string[];
  missing_parameters_flagged?: string[];
  taluka_resolved?: string;
  target_season?: string;
  language?: string;
  crop_outcomes: CropEvaluationOutcome[];
  follow_up_questions: FollowUpQuestion[];
  governance_notice?: string;
}

export interface AgriculturalExplanationResponse {
  decision_id: string;
  language: string;
  explanation_text: string;
  generation_source?: string;
  validation_passed?: boolean;
  validation_warnings?: string[];
  decision_state_summary?: Record<string, string>;
  structured_card?: StructuredAdvisoryCard;
  citations?: CitationMetadata[];
  authoritative_citations?: CitationMetadata[];
  follow_up_questions?: FollowUpQuestion[];
  governance_notice?: string;
}

export interface AgriculturalConversationResponse {
  decision_id?: string;
  language?: string;
  explanation_text?: string;
  answer?: string;
  generation_source?: string;
  validation_passed?: boolean;
  structured_card?: StructuredAdvisoryCard;
  citations?: CitationMetadata[];
  authoritative_citations?: CitationMetadata[];
  follow_up_questions?: FollowUpQuestion[];
  governance_notice?: string;
}

export interface CropSuitabilityOutcome {
  crop_code: string;
  crop_name: string;
  decision_state: string;
  confidence_tier?: string;
  limiting_factors?: string[];
  agronomic_recommendation?: string;
}

export interface CropDecisionResponse {
  decision_id: string;
  evaluated_at: string;
  farm_id?: string;
  taluka_resolved: string;
  suitable_crops: CropSuitabilityOutcome[];
  conditionally_suitable_crops: CropSuitabilityOutcome[];
  disqualified_crops: CropSuitabilityOutcome[];
  abstain_crops: CropSuitabilityOutcome[];
  top_limiting_factors: string[];
  pending_followup_questions_count: number;
}
