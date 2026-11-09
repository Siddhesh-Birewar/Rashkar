# CropNet AI — Data Models

These are the real request/response shapes exposed by FastAPI. TypeScript
interfaces below are hand-written from the Pydantic schemas; `openapi.json`
remains the authoritative machine-readable contract.

## Farm

```ts
type GeoJSONPolygon = {
  type: "Polygon";
  coordinates: number[][][]; // [[ [lon, lat], ... ]] closed ring
};

interface FarmCreate {
  name: string;
  village?: string | null;
  taluka: string;
  district?: string;       // default "Pune"
  state?: string;          // default "Maharashtra"
  irrigation_type?: string; // rainfed | irrigated | mixed | unknown
  water_source?: string;    // rainfall | canal | borewell | well | other | unknown
  geometry: GeoJSONPolygon;
}

interface FarmResponse extends FarmCreate {
  id: string;              // uuid
  owner_id: string;        // uuid
  calculated_area_hectares: number;
  calculated_area_acres: number;
  centroid_latitude: number;
  centroid_longitude: number;
  latitude: number;
  longitude: number;
  created_at: string;      // ISO datetime
  updated_at: string;
}
```

Relationship: one **farm** → many soil profiles, weather snapshots, soil
reports, water sources/reports, satellite observations, health snapshots.

## Soil profile

```ts
interface SoilObservation {
  parameter_key: string;
  display_name: string;
  value: number | null;        // null = not available / unverified
  unit: string;
  source: string;
  dataset_version: string;
  depth_interval: string;
  spatial_resolution: string;
  vintage_year?: number | null;
  uncertainty?: number | null;
  verification_status: string; // map_derived_estimate | laboratory_verified | not_available
  availability_status: string;
  farm_coverage_percent: number;
  scientific_note?: string | null;
}

interface UnifiedSoilProfile {
  profile_id: string;
  farm_id: string;
  created_at: string;
  version: number;
  taluka?: string | null;
  district: string;
  state: string;
  is_map_derived: boolean;
  disclaimer: string;
  source_dataset: string;
  dataset_version: string;
  spatial_resolution: string;
  depth_interval: string;
  spatial_representativeness_warning?: string | null;
  soil_texture_class?: string | null;
  ph?: SoilObservation | null;
  organic_carbon?: SoilObservation | null;
  sand_percent?: SoilObservation | null;
  silt_percent?: SoilObservation | null;
  clay_percent?: SoilObservation | null;
  total_nitrogen?: SoilObservation | null;
  cation_exchange_capacity?: SoilObservation | null;
  available_nitrogen?: SoilObservation | null;      // null unless lab-confirmed
  available_phosphorus?: SoilObservation | null;    // null unless lab-confirmed
  available_potassium?: SoilObservation | null;     // null unless lab-confirmed
  additional_parameters: Record<string, SoilObservation>;
  total_requested_parameters: number;
  available_parameters_count: number;
  data_completeness_ratio: number;
}
```

## Soil laboratory report

```ts
interface SoilMeasurement {
  id: string;
  parameter_key: string;
  parameter_name: string;
  original_value: number | null;
  original_value_text?: string | null;
  original_unit: string;
  normalized_value?: number | null;
  normalized_unit?: string | null;
  effective_value?: number | null;   // farmer correction > normalized > original
  effective_unit?: string;
  analytical_method?: string | null;
  lab_rating?: string | null;
  is_ambiguous: boolean;
  verification_status:
    | "EXTRACTED_UNVERIFIED"
    | "FARMER_CORRECTED"
    | "FARMER_CONFIRMED";
}

interface SoilReportDetail {
  id: string;
  farm_id: string;
  original_filename: string;
  status: "UPLOADED" | "PROCESSING" | "EXTRACTION_COMPLETED"
        | "NEEDS_REVIEW" | "CONFIRMED" | "FAILED";
  review_status: "NEEDS_REVIEW" | "CONFIRMED" | "REJECTED";
  laboratory_name?: string | null;
  report_date?: string | null;
  sample_collection_date?: string | null;
  sample_depth?: string | null;
  depth_provenance?: string | null;
  sampling_point_name?: string | null;
  measurements: SoilMeasurement[];
}
```

## Weather

```ts
interface DailyForecast {
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

interface FarmWeatherForecast {
  farm_id: string;
  source: string;            // e.g. "OpenWeather"
  data_type: "forecast";
  retrieval_time: string;
  forecast_period: string;   // "5 days (3-hour resolution)"
  daily_summaries: DailyForecast[];
  hourly_points: unknown[];
  is_cached: boolean;
}
```

## Crop knowledge base

```ts
interface CropFullProfile {
  id: string;
  common_name: string;
  scientific_name: string;
  marathi_name?: string | null;
  category: string;
  crop_type: string;
  soil: unknown;
  climate: unknown;
  seasons: unknown[];
  water: unknown;
  regional_suitability: unknown[];
  sources: { id: string; organization: string; publication_title: string }[];
}
```

## Deterministic evaluation

```ts
type DecisionState =
  | "VERIFIED_SUITABLE"
  | "CONDITIONALLY_SUITABLE_PENDING_DATA"
  | "REQUIRES_REGIONAL_VALIDATION"
  | "REGIONAL_SCREENING_ONLY"
  | "UNSUITABLE_VERIFIED_CONSTRAINT"
  | "ABSTAIN_INSUFFICIENT_EVIDENCE";

interface CropEvaluationOutcome {
  crop_id: string;
  common_name: string;
  scientific_name: string;
  marathi_name?: string | null;
  decision_state: DecisionState;
  is_disqualified: boolean;
  limiting_factors: string[];
  reproductive_risk_warnings: string[];
  irrigation_guidance?: Record<string, unknown> | null;
  pomegranate_daily_water?: Record<string, unknown> | null;
  missing_information: string[];
  uncertainty_notes: string[];
  applied_rules: AppliedRule[];
  citations: Citation[];
  explanation: string;
}

interface FarmEvaluationResponse {
  decision_id: string;            // pass to explain/conversation/follow-up
  evaluated_at: string;
  input_validation_status: string; // VALID | CONTRADICTORY_INPUTS_DETECTED | ABSTAIN_*
  contradictions_detected: string[];
  missing_parameters_flagged: string[];
  taluka_resolved?: string | null;
  target_season?: string | null;
  language: "en" | "mr";
  farm_context: FarmContextInput;
  crop_outcomes: CropEvaluationOutcome[];
  follow_up_questions: FollowUpQuestion[];
}
```

## Farm Health snapshot

```ts
interface FarmHealthSnapshot {
  farm_id: string;
  farm_name: string;
  generated_at: string;
  sections: {
    soil?: unknown;
    weather?: unknown;
    crops?: unknown;
    water?: unknown;
    satellite?: unknown;
    timeline?: unknown;
    evidence?: unknown;
  };
  is_from_cache: boolean;
  cached_at?: string | null;
}
```

## Water intelligence

```ts
interface WaterQualityEvaluation {
  farm_id: string;
  water_source_id?: string | null;
  evaluation_timestamp: string;
  evaluations: {
    parameter_key: string;
    parameter_name: string;
    observed_value: number | null;
    observed_unit: string | null;
    hazard_level: string;
    hazard_title: string;
    rule_id: string;
    source_citation: string;
    management_guidance: string;
    scope_and_limitations: string;
  }[];
  calculated_indices: {
    sar: number | null;
    sar_status: string;
    rsc: number | null;
    rsc_status: string;
    inputs_used: Record<string, unknown>;
    calculation_notes: string[];
  };
  disclaimer: string;
}
```

## Satellite vegetation

```ts
interface SatelliteObservation {
  observation_date: string;
  product_id: string;
  sensor: string;
  mean_ndvi: number | null;
  mean_ndmi: number | null;
  quality_status: string;
  quality_notes?: string | null;
  radiometric_conversion_provenance?: string | null;
  // plus pixel counts, coverage %, bounds, raster URLs
}
```

## Government Schemes

```ts
interface GovernmentScheme {
  id: string;
  scheme_name: string;
  category: string;           // Crop Insurance, Financial Assistance, ...
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
  created_at: string;
  updated_at: string;
}
```

## Heat Risk

```ts
interface CropHeatResponse {
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
  risk_category: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  risk_label: string;
  explanation: string;
  evidence_citation: string;
  methodology_note: string;
}

interface WorkerHeatResponse {
  wbgt_c: number;
  wbgt_effective_c: number;
  threshold_c: number;
  hazard_level: "LOW" | "MODERATE" | "HIGH" | "EXTREME";
  exceeds_threshold: boolean;
  work_rest_cycle: string;
  heat_index_c?: number | null;
  utci_c?: number | null;
  recommendation: string;
  methodology_note: string;
}

interface FarmHeatRiskResponse {
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
  daily_outlook: { date: string; tmax_c: number; tmin_c: number;
                   hours_above_critical: number; warm_night_hazard: boolean;
                   risk_category: string }[];
  interventions: { title: string; description: string; rationale: string;
                   evidence: string; category: string }[];
  worker_heat?: WorkerHeatResponse | null;
  weather_source: string;
  provenance: string;
  limitations: string[];
  generated_at: string;
}
```

## Crop Doctor

```ts
interface CropDoctorPrediction {
  filename: string;
  crop: string;
  diagnosis: string;
  raw_label: string;
  confidence_percent: number;
  is_healthy: boolean;
  actionable_advice: string[];
  disclaimer: string;
}
```

## Income Diversification

```ts
interface OpportunityCatalogItem {
  opportunity_id: string;
  title: string;
  category: "zero_cash" | "very_low_cost" | "moderate_enterprise"
          | "crop_diversification" | "group_external";
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
  target_crops: string[];
}

interface FarmerResourceProfile { /* see openapi.json for full fields */ }
interface DiscoveredOpportunity { /* ranked match + reasons */ }
interface EnterpriseFinancialAnalysis { /* 3 scenarios + monthly cash flows */ }
interface OpportunityComparisonItem { /* side-by-side matrix */ }
```
