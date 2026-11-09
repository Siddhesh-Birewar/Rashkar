"""
Pydantic schemas for Irrigation Water Sources, Quality Measurements,
Validated Calculations (SAR, RSC), and Institutional Water Evaluation (BIS IS 11624 & ICAR-CSSRI).
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class WaterSourceType(str, Enum):
    BOREWELL = "borewell"
    OPEN_WELL = "open_well"
    CANAL = "canal"
    RIVER = "river"
    RESERVOIR = "reservoir"
    FARM_POND = "farm_pond"
    RAINWATER_HARVESTING = "rainwater_harvesting"
    OTHER = "other"


class SeasonalAvailability(str, Enum):
    PERENNIAL = "perennial"
    SEASONAL_MONSOON = "seasonal_monsoon"
    SEASONAL_WINTER = "seasonal_winter"
    SUMMER_DRY = "summer_dry"
    KHARIF_ONLY = "kharif_only"
    RABI_ONLY = "rabi_only"


class ReliabilityRating(str, Enum):
    RELIABLE = "reliable"
    MODERATE = "moderate"
    INTERMITTENT = "intermittent"
    UNRELIABLE = "unreliable"


class IrrigationMethod(str, Enum):
    DRIP = "drip"
    SPRINKLER = "sprinkler"
    FURROW = "furrow"
    FLOOD = "flood"
    BASIN = "basin"
    OTHER = "other"


class CapacityProvenance(str, Enum):
    MEASURED = "MEASURED"
    FARMER_REPORTED = "FARMER_REPORTED"
    UNSPECIFIED = "UNSPECIFIED"


class WaterReportExtractionStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    EXTRACTION_COMPLETED = "EXTRACTION_COMPLETED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class WaterReportReviewStatus(str, Enum):
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFIRMED = "CONFIRMED"


class WaterMeasurementVerificationStatus(str, Enum):
    EXTRACTED_UNVERIFIED = "EXTRACTED_UNVERIFIED"
    FARMER_CORRECTED = "FARMER_CORRECTED"
    FARMER_CONFIRMED = "FARMER_CONFIRMED"


class WaterQualityHazardLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    SAFE = "SAFE"
    MARGINAL = "MARGINAL"
    RESTRICTED = "RESTRICTED"
    HAZARDOUS = "HAZARDOUS"
    UNVERIFIED = "UNVERIFIED"


CANONICAL_WATER_PARAMETERS = {
    "ph": {
        "display_name": "pH",
        "standard_unit": "pH",
        "category": "physical",
        "equivalent_weight": None,
    },
    "electrical_conductivity": {
        "display_name": "Electrical Conductivity (EC)",
        "standard_unit": "dS/m",
        "category": "salinity",
        "equivalent_weight": None,
    },
    "tds": {
        "display_name": "Total Dissolved Solids (TDS)",
        "standard_unit": "mg/L",
        "category": "salinity",
        "equivalent_weight": None,
    },
    "sodium": {
        "display_name": "Sodium (Na+)",
        "standard_unit": "meq/L",
        "category": "cation",
        "equivalent_weight": 22.99,  # mg per meq
    },
    "calcium": {
        "display_name": "Calcium (Ca2+)",
        "standard_unit": "meq/L",
        "category": "cation",
        "equivalent_weight": 20.04,  # mg per meq
    },
    "magnesium": {
        "display_name": "Magnesium (Mg2+)",
        "standard_unit": "meq/L",
        "category": "cation",
        "equivalent_weight": 12.15,  # mg per meq
    },
    "chloride": {
        "display_name": "Chloride (Cl-)",
        "standard_unit": "meq/L",
        "category": "anion",
        "equivalent_weight": 35.45,  # mg per meq
    },
    "bicarbonate": {
        "display_name": "Bicarbonate (HCO3-)",
        "standard_unit": "meq/L",
        "category": "anion",
        "equivalent_weight": 61.02,  # mg per meq
    },
    "carbonate": {
        "display_name": "Carbonate (CO3 2-)",
        "standard_unit": "meq/L",
        "category": "anion",
        "equivalent_weight": 30.00,  # mg per meq
    },
    "sulphate": {
        "display_name": "Sulphate (SO4 2-)",
        "standard_unit": "meq/L",
        "category": "anion",
        "equivalent_weight": 48.03,  # mg per meq
    },
    "boron": {
        "display_name": "Boron (B)",
        "standard_unit": "mg/L",
        "category": "trace_element",
        "equivalent_weight": None,
    },
    "nitrate": {
        "display_name": "Nitrate (NO3-)",
        "standard_unit": "mg/L",
        "category": "anion",
        "equivalent_weight": 62.00,
    },
    "fluoride": {
        "display_name": "Fluoride (F-)",
        "standard_unit": "mg/L",
        "category": "trace_element",
        "equivalent_weight": 19.00,
    },
    "iron": {
        "display_name": "Iron (Fe)",
        "standard_unit": "mg/L",
        "category": "trace_element",
        "equivalent_weight": 27.92,
    },
    "zinc": {
        "display_name": "Zinc (Zn)",
        "standard_unit": "mg/L",
        "category": "trace_element",
        "equivalent_weight": 32.69,
    },
    "copper": {
        "display_name": "Copper (Cu)",
        "standard_unit": "mg/L",
        "category": "trace_element",
        "equivalent_weight": 31.77,
    },
    "manganese": {
        "display_name": "Manganese (Mn)",
        "standard_unit": "mg/L",
        "category": "trace_element",
        "equivalent_weight": 27.47,
    },
    "arsenic": {
        "display_name": "Arsenic (As)",
        "standard_unit": "mg/L",
        "category": "trace_element",
        "equivalent_weight": 24.97,
    },
    "lead": {
        "display_name": "Lead (Pb)",
        "standard_unit": "mg/L",
        "category": "trace_element",
        "equivalent_weight": 103.60,
    },
    "cadmium": {
        "display_name": "Cadmium (Cd)",
        "standard_unit": "mg/L",
        "category": "trace_element",
        "equivalent_weight": 56.20,
    },
    "chromium": {
        "display_name": "Chromium (Cr)",
        "standard_unit": "mg/L",
        "category": "trace_element",
        "equivalent_weight": 17.33,
    },
    "nickel": {
        "display_name": "Nickel (Ni)",
        "standard_unit": "mg/L",
        "category": "trace_element",
        "equivalent_weight": 29.35,
    },
    "sar": {
        "display_name": "Sodium Adsorption Ratio (SAR)",
        "standard_unit": "ratio",
        "category": "calculated_index",
        "equivalent_weight": None,
    },
    "rsc": {
        "display_name": "Residual Sodium Carbonate (RSC)",
        "standard_unit": "meq/L",
        "category": "calculated_index",
        "equivalent_weight": None,
    },
}


# --- Water Sources Schemas ---

class WaterSourceBase(BaseModel):
    source_type: WaterSourceType = Field(..., description="Classification of water source")
    name: str = Field(..., min_length=1, max_length=100, description="Name or identifier of source")
    location_description: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    seasonal_availability: SeasonalAvailability = Field(default=SeasonalAvailability.PERENNIAL)
    reliability: ReliabilityRating = Field(default=ReliabilityRating.RELIABLE)
    daily_available_hours: Optional[float] = Field(None, ge=0.0, le=24.0, description="Hours per day water is available")
    irrigation_method: IrrigationMethod = Field(default=IrrigationMethod.DRIP)
    measured_capacity_lph: Optional[float] = Field(None, ge=0.0, description="Flow rate / capacity in Liters per Hour")
    capacity_provenance: CapacityProvenance = Field(default=CapacityProvenance.FARMER_REPORTED)


class WaterSourceCreate(WaterSourceBase):
    pass


class WaterSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    source_type: Optional[WaterSourceType] = None
    location_description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    seasonal_availability: Optional[SeasonalAvailability] = None
    reliability: Optional[ReliabilityRating] = None
    daily_available_hours: Optional[float] = Field(None, ge=0.0, le=24.0)
    irrigation_method: Optional[IrrigationMethod] = None
    measured_capacity_lph: Optional[float] = Field(None, ge=0.0)
    capacity_provenance: Optional[CapacityProvenance] = None
    is_active: Optional[bool] = None


class WaterSourceResponse(WaterSourceBase):
    id: str
    farm_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Water Measurement Schemas ---

class WaterMeasurementItem(BaseModel):
    id: str
    parameter_key: str
    original_parameter_name: str
    original_value: Optional[float]
    original_value_text: Optional[str]
    original_unit: str
    normalized_value: Optional[float]
    normalized_unit: Optional[str]
    analytical_method: Optional[str] = None
    verification_status: str
    farmer_corrected_value: Optional[float] = None
    farmer_notes: Optional[str] = None
    provenance: str = "LAB_REPORT"

    model_config = ConfigDict(from_attributes=True)


class WaterMeasurementCorrectionRequest(BaseModel):
    measurement_id: str
    farmer_corrected_value: float
    farmer_notes: Optional[str] = None


# --- Calculated Indicators (SAR, RSC) ---

class WaterCalculatedIndicators(BaseModel):
    sar: Optional[float] = Field(None, description="Sodium Adsorption Ratio = Na / sqrt((Ca + Mg)/2) using meq/L")
    sar_status: str = Field("UNAVAILABLE", description="AVAILABLE, INCOMPLETE_INPUTS, ZERO_DIVISOR, or REPORTED")
    rsc: Optional[float] = Field(None, description="Residual Sodium Carbonate = (CO3 + HCO3) - (Ca + Mg) in meq/L")
    rsc_status: str = Field("UNAVAILABLE", description="AVAILABLE, INCOMPLETE_INPUTS, or REPORTED")
    inputs_used: Dict[str, Any] = Field(default_factory=dict, description="Normalized meq/L values and provenance used in formulas")
    calculation_notes: List[str] = Field(default_factory=list)


# --- Water Test Reports ---

class WaterReportSummary(BaseModel):
    id: str
    farm_id: str
    water_source_id: Optional[str]
    original_filename: str
    file_size_bytes: Optional[int]
    laboratory_name: Optional[str]
    report_date: Optional[datetime]
    sample_collection_date: Optional[datetime]
    extraction_status: str
    review_status: str
    measurement_count: int
    upload_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class WaterReportDetail(BaseModel):
    id: str
    farm_id: str
    water_source_id: Optional[str]
    original_filename: str
    file_size_bytes: Optional[int]
    laboratory_name: Optional[str]
    lab_number: Optional[str]
    report_date: Optional[datetime]
    sample_collection_date: Optional[datetime]
    sampling_location: Optional[str]
    extraction_status: str
    review_status: str
    reviewed_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    measurements: List[WaterMeasurementItem]
    calculated_indices: WaterCalculatedIndicators
    upload_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class WaterReportConfirmRequest(BaseModel):
    corrections: List[WaterMeasurementCorrectionRequest] = Field(default_factory=list)
    laboratory_name: Optional[str] = None
    report_date: Optional[datetime] = None
    sample_collection_date: Optional[datetime] = None
    sampling_location: Optional[str] = None
    water_source_id: Optional[str] = None


class WaterReportConfirmResponse(BaseModel):
    success: bool
    report_id: str
    farm_id: str
    confirmed_measurements_count: int
    review_status: str
    calculated_indices: WaterCalculatedIndicators
    message: str


# --- Institutional Water Evaluation ---

class WaterRuleEvaluationItem(BaseModel):
    parameter_key: str
    parameter_name: str
    observed_value: Optional[float] = None
    observed_unit: Optional[str] = None
    hazard_level: WaterQualityHazardLevel
    hazard_title: str
    rule_id: str
    source_citation: str
    applicable_standard: str  # e.g., "BIS IS 11624:2019", "ICAR-CSSRI Karnal Guidelines"
    management_guidance: str
    scope_and_limitations: str


class WaterQualityEvaluationResponse(BaseModel):
    farm_id: str
    water_source_id: Optional[str]
    evaluation_timestamp: datetime
    evaluations: List[WaterRuleEvaluationItem]
    calculated_indices: WaterCalculatedIndicators
    soil_drainage_caution: str
    crop_sensitivity_overview: Dict[str, str]
    regional_cgwb_context: Optional[Dict[str, Any]] = None
    disclaimer: str
