"""
CropNet AI — Phase 5.1 Agricultural Intelligence Schemas.

Pydantic input and output models for deterministic agricultural reasoning,
evidence-gated decision states, and targeted follow-up question selection.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DecisionState(str, Enum):
    """
    Standardized machine-readable agronomic outcomes.
    Absence of evidence is not evidence of suitability.
    """
    VERIFIED_SUITABLE = "VERIFIED_SUITABLE"
    REGIONAL_SCREENING_ONLY = "REGIONAL_SCREENING_ONLY"
    CONDITIONALLY_SUITABLE_PENDING_DATA = "CONDITIONALLY_SUITABLE_PENDING_DATA"
    REQUIRES_REGIONAL_VALIDATION = "REQUIRES_REGIONAL_VALIDATION"
    UNSUITABLE_VERIFIED_CONSTRAINT = "UNSUITABLE_VERIFIED_CONSTRAINT"
    ABSTAIN_INSUFFICIENT_EVIDENCE = "ABSTAIN_INSUFFICIENT_EVIDENCE"


class EvidenceTier(str, Enum):
    """
    Canonical 4-tier evidence gating classifications.
    """
    VERIFIED = "VERIFIED"
    CONDITIONALLY_SUPPORTED = "CONDITIONALLY_SUPPORTED"
    UNVERIFIED_BIBLIOGRAPHIC = "UNVERIFIED_BIBLIOGRAPHIC"
    UNSUPPORTED = "UNSUPPORTED"


class EnforcementLevel(str, Enum):
    """
    Standardized rule enforcement levels for agricultural reasoning.
    Only VERIFIED_HARD_CONSTRAINT can trigger categorical disqualification.
    """
    VERIFIED_HARD_CONSTRAINT = "VERIFIED_HARD_CONSTRAINT"
    CONDITIONAL_CONSTRAINT = "CONDITIONAL_CONSTRAINT"
    ADVISORY_ONLY = "ADVISORY_ONLY"
    UNVERIFIED = "UNVERIFIED"
    UNSUPPORTED = "UNSUPPORTED"


class SoilDataProvenance(str, Enum):
    """
    Provenance distinction for soil input data.
    """
    LABORATORY_MEASURED = "laboratory_measured"
    SPATIALLY_ESTIMATED_ISRIC = "spatially_estimated_isric"
    USER_REPORTED = "user_reported"
    UNKNOWN = "unknown"


class FarmContextInput(BaseModel):
    """
    Structured farm context input for deterministic agricultural reasoning.
    All parameters support explicit NULLs. Missing parameters are never fabricated.
    """
    farm_id: Optional[str] = Field(None, description="Registered farm UUID if known")
    user_id: Optional[str] = Field(None, description="Registered user UUID if known")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    taluka: Optional[str] = Field(None, description="Taluka name (e.g. Baramati, Indapur, Maval, Mulshi)")
    district: Optional[str] = Field(default="Pune", description="District name")

    # Soil chemical and physical parameters
    soil_ph: Optional[float] = Field(None, ge=3.0, le=11.0, description="Soil pH (1:2.5 soil:water)")
    soil_organic_carbon_pct: Optional[float] = Field(None, ge=0.0, le=10.0, description="Soil Organic Carbon percentage (SOC %)")
    soil_texture: Optional[str] = Field(None, description="Soil texture class (e.g. Light soil, Coarse sand, Clay Loam, Vertisol)")
    soil_depth_cm: Optional[float] = Field(None, ge=0.0, le=300.0, description="Effective soil depth in centimeters")
    drainage: Optional[str] = Field(None, description="Drainage condition (e.g. Well-drained, Moderate, Poor / Waterlogged)")
    water_table_depth: Optional[str] = Field(None, description="Water table depth category ('deep', 'moderate', 'high', 'shallow')")
    water_table_depth_m: Optional[float] = Field(None, ge=0.0, le=100.0, description="Measured water table depth in meters")
    standing_water_days: Optional[int] = Field(None, ge=0, le=60, description="Days standing water persists after rainfall")
    electrical_conductivity_ds_m: Optional[float] = Field(None, ge=0.0, le=30.0, description="Soil EC in dS/m (1:2 extract)")
    
    # Nutrient availability (Strict separation of Total vs Available N)
    available_nitrogen_kg_ha: Optional[float] = Field(None, ge=0.0, le=1000.0, description="Available Nitrogen (alkaline permanganate extractable)")
    total_nitrogen_pct: Optional[float] = Field(None, ge=0.0, le=5.0, description="Total Nitrogen % (Kjeldahl - organically bound)")
    available_phosphorus_kg_ha: Optional[float] = Field(None, ge=0.0, le=200.0, description="Olsen Available P in kg/ha")
    available_potassium_kg_ha: Optional[float] = Field(None, ge=0.0, le=1500.0, description="Available K in kg/ha")
    
    # Soil provenance
    soil_data_provenance: SoilDataProvenance = Field(
        default=SoilDataProvenance.UNKNOWN,
        description="Whether soil parameters are laboratory tested or coarse spatial estimates"
    )
    soil_measurement_date: Optional[str] = Field(None, description="ISO measurement date for lab soil test")

    # Hydrology & Irrigation
    irrigation_available: Optional[bool] = Field(None, description="Whether irrigation water is accessible")
    irrigation_source: Optional[str] = Field(None, description="Irrigation source (canal, well, borewell, dryland/rainfed)")
    irrigation_capacity: Optional[str] = Field(None, description="Hydrological capacity (perennial, seasonal_dry_by_february, critical_only)")
    alternative_summer_irrigation: Optional[str] = Field(None, description="Alternative summer irrigation availability (farm_pond, canal, tanker, none)")
    irrigation_water_salinity_tested: Optional[bool] = Field(None, description="Whether irrigation water has been tested for EC/SAR")
    irrigation_water_ec_ds_m: Optional[float] = Field(None, ge=0.0, le=25.0, description="Irrigation water EC in dS/m")

    # Orchard & Bahar Specifics (Pomegranate)
    tree_age_years: Optional[int] = Field(None, ge=1, le=30, description="Orchard tree age in years")
    target_bahar: Optional[str] = Field(None, description="Regulated Bahar (mrig_bahar, hasta_bahar, ambia_bahar)")
    water_scarcity_period: Optional[str] = Field(None, description="Critical water deficit window (e.g. post_february_summer)")

    # Cropping context & Season
    previous_crop: Optional[str] = Field(None, description="Previous crop harvested from parcel")
    target_season: Optional[str] = Field(None, description="Cropping season (kharif, rabi, summer, annual)")
    target_year: Optional[int] = Field(None, description="Target cultivation year (e.g. 2026)")
    proposed_sowing_date: Optional[str] = Field(None, description="Planned sowing date (YYYY-MM-DD)")
    actual_recorded_rain_mm: Optional[float] = Field(None, ge=0.0, le=1000.0, description="Actual recorded soaking rainfall before sowing (mm)")
    monsoon_arrived: Optional[bool] = Field(None, description="Whether South-West Monsoon has officially arrived")

    # Real-time weather & forecast
    forecast_max_temp_c: Optional[float] = Field(None, description="Forecasted maximum daily temperature in Celsius")
    forecast_min_temp_c: Optional[float] = Field(None, description="Forecasted minimum daily temperature in Celsius")
    reproductive_temp_max_c: Optional[float] = Field(None, description="Maximum daily temperature during reproductive stage in Celsius")
    reproductive_temp_mean_c: Optional[float] = Field(None, description="Mean daily temperature during reproductive stage in Celsius")
    sowing_window_rain_mm: Optional[float] = Field(None, ge=0.0, le=1000.0, description="Actual recorded soaking rainfall before sowing (mm)")
    forecast_rain_mm_48h: Optional[float] = Field(None, ge=0.0, description="Forecasted precipitation over next 48 hours in mm")
    growth_stage: Optional[str] = Field(None, description="Current growth stage (vegetative, reproductive/flowering, pod_filling, mature)")
    days_after_sowing: Optional[int] = Field(None, ge=0, le=365, description="Days after sowing (DAS)")

    # Targeted query parameters
    target_crops: Optional[List[str]] = Field(None, description="Specific crops to evaluate (None evaluates all 10 priority crops)")
    user_query: Optional[str] = Field(None, description="User's natural language query in English or Marathi")
    language: str = Field(default="en", description="Preferred output language: 'en' or 'mr'")


class CitationMetadata(BaseModel):
    """
    Granular citation metadata for transparency and provenance.
    """
    source_id: str
    organization: str
    publication_title: str
    publication_year: Optional[int] = None
    section_or_pages: Optional[str] = None
    evidence_tier: EvidenceTier


class AppliedRuleRecord(BaseModel):
    """
    Record of a specific deterministic rule evaluated for a crop.
    """
    rule_id: str
    domain: str
    parameter_checked: str
    rule_statement: str
    condition_met: bool
    evidence_tier: EvidenceTier
    citation: Optional[CitationMetadata] = None

    # Phase 5.1.2 Granular Evidence Enforcement Architecture
    claim_verification_status: str = "VERIFIED"
    source_id: Optional[str] = None
    document_title: Optional[str] = None
    section_or_pages: Optional[str] = None
    supporting_statement: Optional[str] = None
    applicability_conditions: Optional[str] = None
    enforcement_level: EnforcementLevel = EnforcementLevel.ADVISORY_ONLY
    can_trigger_disqualification: bool = False


class CropEvaluationOutcome(BaseModel):
    """
    Detailed deterministic evaluation outcome for a single candidate crop.
    """
    crop_id: str
    common_name: str
    scientific_name: str
    marathi_name: Optional[str] = None
    decision_state: DecisionState
    is_disqualified: bool = False
    
    # Transparent reasoning breakdowns
    limiting_factors: List[str] = Field(default_factory=list)
    reproductive_risk_warnings: List[str] = Field(default_factory=list)
    irrigation_guidance: Optional[Dict[str, Any]] = None
    pomegranate_daily_water: Optional[Dict[str, Any]] = None
    missing_information: List[str] = Field(default_factory=list)
    uncertainty_notes: List[str] = Field(default_factory=list)
    
    # Provenance
    applied_rules: List[AppliedRuleRecord] = Field(default_factory=list)
    citations: List[CitationMetadata] = Field(default_factory=list)
    explanation: str


class FollowUpQuestion(BaseModel):
    """
    Diagnostic follow-up question selected to resolve decision uncertainty.
    """
    question_id: str
    target_parameter: str
    priority: int = Field(..., description="1 = Critical blocker, 2 = Diagnostic, 3 = Optimization")
    question_text_en: str
    question_text_mr: str
    question_type: str = Field(..., description="choice | numeric | boolean")
    options: Optional[List[str]] = None
    agronomic_rationale: str


class FarmEvaluationResponse(BaseModel):
    """
    Complete response payload for farm agricultural evaluation.
    """
    decision_id: str
    evaluated_at: datetime
    input_validation_status: str
    contradictions_detected: List[str] = Field(default_factory=list)
    missing_parameters_flagged: List[str] = Field(default_factory=list)
    taluka_resolved: Optional[str] = None
    target_season: Optional[str] = None
    language: str = "en"
    farm_context: Optional[FarmContextInput] = None
    
    # Evaluated outcomes across crops
    crop_outcomes: List[CropEvaluationOutcome] = Field(default_factory=list)
    
    # Global follow-up questions
    follow_up_questions: List[FollowUpQuestion] = Field(default_factory=list)
    
    # Governance & Decoupling Disclaimer
    governance_notice: str = (
        "CropNet AI evaluates biological and environmental feasibility. "
        "Agronomic suitability does not equate to commercial profitability or guaranteed net returns. "
        "Absence of evidence is never treated as evidence of suitability."
    )


class FollowUpAnswerRequest(BaseModel):
    """
    Payload for submitting follow-up answers to re-evaluate a farm.
    """
    decision_id: str
    answers: Dict[str, Any] = Field(..., description="Key-value mapping of target_parameter to farmer response")


class ExplainDecisionRequest(BaseModel):
    """
    Request payload to generate a natural farmer-friendly explanation of a validated decision.
    """
    decision_id: str = Field(..., description="UUID of the validated decision")
    language: Optional[str] = Field(default="en", description="Target explanation language: 'en' or 'mr'")
    focus_crop: Optional[str] = Field(None, description="Optional specific crop_id to focus the explanation on")
    query: Optional[str] = Field(None, description="Optional specific farmer question or query to evaluate")
    response_mode: Optional[str] = Field(default=None, description="Response length mode: 'QUICK' (default), 'STANDARD', or 'DETAILED'")


class ConversationMessage(BaseModel):
    """
    Individual message in a bounded conversational dialogue.
    """
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")
    timestamp: Optional[datetime] = Field(default=None, description="Message timestamp")


class ConversationRequest(BaseModel):
    """
    Request payload for natural farmer follow-up dialogue grounded in a validated decision.
    """
    decision_id: str = Field(..., description="UUID of the existing validated decision")
    message: str = Field(..., description="Farmer's query or diagnostic response")
    language: Optional[str] = Field(default="en", description="Language preference: 'en' or 'mr'")
    history: Optional[List[ConversationMessage]] = Field(default_factory=list, description="Bounded prior conversation turns")
    submitted_answers: Optional[Dict[str, Any]] = Field(None, description="Optional diagnostic parameter updates to trigger deterministic re-evaluation")
    response_mode: Optional[str] = Field(default=None, description="Response length mode: 'QUICK' (default), 'STANDARD', or 'DETAILED'")


class AdvisoryObservationItem(BaseModel):
    """
    Individual verified agronomic observation with source provenance.
    """
    parameter: str = Field(..., description="Observed parameter name (e.g. Soil pH, Nitrogen, Satellite NDVI)")
    value: str = Field(..., description="Observed value or 'Untested / Pending'")
    source: str = Field(..., description="Source institution or sensor (e.g. SoilGrids, Lab Report, Sentinel-2)")
    status: str = Field(default="available", description="'available', 'missing', or 'untested'")


class StructuredAdvisoryCard(BaseModel):
    """
    Structured farmer-facing advisory card matching the standard UI sections.
    """
    title: str = Field(..., description="Advisory card title")
    direct_answer: str = Field(..., description="Short, direct answer to the farmer's question")
    what_this_means: str = Field(..., description="Understandable 2-3 sentence explanation of the finding")
    crop_status_label: Optional[str] = Field(None, description="Farmer-friendly decision status label")
    crop_status_code: Optional[str] = Field(None, description="Underlying machine-readable DecisionState code")
    observations: List[AdvisoryObservationItem] = Field(default_factory=list, description="Verified actual observations and sensor data")
    what_needs_attention: List[str] = Field(default_factory=list, description="Key limiting factors, missing info, or constraints")
    next_steps: List[str] = Field(default_factory=list, description="Numbered recommended actions")
    evidence_references: List[str] = Field(default_factory=list, description="Authoritative institutional source references")
    key_reasons: Optional[List[str]] = Field(default_factory=list, description="Concise bullet points explaining reasons if needed")
    recommended_action: Optional[str] = Field(default=None, description="Single practical next action for the farmer")
    limitations: Optional[List[str]] = Field(default_factory=list, description="Verified agronomic constraints and risks")
    response_mode: Optional[str] = Field(default="QUICK", description="Mode used for this advisory card ('QUICK', 'STANDARD', 'DETAILED')")


class AgriculturalExplanationResponse(BaseModel):
    """
    Validated natural language explanation response with strictly bound factual metadata.
    """
    decision_id: str
    language: str
    explanation_text: str
    response_mode: str = Field(default="QUICK", description="Response brevity mode applied: 'QUICK', 'STANDARD', or 'DETAILED'")
    direct_answer: Optional[str] = Field(default=None, description="Direct answer isolated from explanation")
    recommended_action: Optional[str] = Field(default=None, description="Single practical action recommended")
    key_reasons: List[str] = Field(default_factory=list, description="Concise bullet points explaining reasons")
    limitations: List[str] = Field(default_factory=list, description="Verified agronomic constraints")
    generation_source: str = Field(..., description="'llm_qwen3_8b' or 'deterministic_fallback'")
    validation_passed: bool = Field(..., description="Whether output passed numerical and constraint guardrails")
    validation_warnings: List[str] = Field(default_factory=list, description="Guardrail warnings or failure notes")
    decision_state_summary: Dict[str, str] = Field(default_factory=dict, description="Crop ID to machine-readable decision state mapping")
    authoritative_citations: List[CitationMetadata] = Field(default_factory=list, description="Institutional citations attached directly from deterministic engine")
    follow_up_questions: List[FollowUpQuestion] = Field(default_factory=list, description="Targeted follow-up questions from deterministic engine")
    structured_card: Optional[StructuredAdvisoryCard] = Field(default=None, description="Optional structured advisory card for rich native UI rendering")
    governance_notice: str = (
        "CropNet AI explanations are strictly derived from validated deterministic agronomic decisions. "
        "The language model is a communication layer and does not establish agronomic suitability or thresholds."
    )
