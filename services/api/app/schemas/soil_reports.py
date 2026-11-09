"""
Pydantic Schemas for Soil Laboratory Reports and Extracted Measurements.

Strictly adheres to PROJECT.md § Shared Data Contract:
- Report Lifecycle States: UPLOADED, PROCESSING, EXTRACTION_COMPLETED, NEEDS_REVIEW, CONFIRMED, FAILED
- Measurement Verification Statuses: EXTRACTED_UNVERIFIED, FARMER_CORRECTED, FARMER_CONFIRMED
- Canonical parameter keys, units, and conversion safeguards.
"""
import uuid
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ExtractionStatus(str, Enum):
    """Lifecycle states of the document extraction pipeline."""
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    EXTRACTION_COMPLETED = "EXTRACTION_COMPLETED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class ReviewStatus(str, Enum):
    """Farmer review and confirmation state."""
    NEEDS_REVIEW = "NEEDS_REVIEW"
    PARTIALLY_REVIEWED = "PARTIALLY_REVIEWED"
    CONFIRMED = "CONFIRMED"


class MeasurementVerificationStatus(str, Enum):
    """Verification status for an individual chemical or physical measurement."""
    EXTRACTED_UNVERIFIED = "EXTRACTED_UNVERIFIED"
    FARMER_CORRECTED = "FARMER_CORRECTED"
    FARMER_CONFIRMED = "FARMER_CONFIRMED"


# Canonical soil parameter keys mapping
CANONICAL_SOIL_PARAMETERS: Dict[str, Dict[str, Any]] = {
    "soil_ph": {
        "display_name": "pH",
        "standard_unit": "pH",
        "category": "chemical",
        "normal_range": (3.5, 10.5),
    },
    "electrical_conductivity": {
        "display_name": "Electrical Conductivity",
        "standard_unit": "dS/m",
        "category": "chemical",
        "normal_range": (0.0, 30.0),
    },
    "organic_carbon": {
        "display_name": "Soil Organic Carbon (SOC)",
        "standard_unit": "%",
        "category": "chemical",
        "normal_range": (0.0, 10.0),
    },
    "organic_matter": {
        "display_name": "Organic Matter",
        "standard_unit": "%",
        "category": "chemical",
        "normal_range": (0.0, 20.0),
    },
    "available_nitrogen": {
        "display_name": "Available Nitrogen",
        "standard_unit": "kg/ha",
        "category": "macronutrient",
        "normal_range": (0.0, 1000.0),
    },
    "total_nitrogen": {
        "display_name": "Total Nitrogen",
        "standard_unit": "g/kg",
        "category": "macronutrient",
        "normal_range": (0.0, 50.0),
    },
    "phosphorus": {
        "display_name": "Phosphorus (P)",
        "standard_unit": "ppm",
        "category": "macronutrient",
        "normal_range": (0.0, 500.0),
    },
    "available_phosphorus": {
        "display_name": "Available Phosphorus (P2O5)",
        "standard_unit": "kg/ha",
        "category": "macronutrient",
        "normal_range": (0.0, 300.0),
    },
    "potassium": {
        "display_name": "Potassium (K)",
        "standard_unit": "ppm",
        "category": "macronutrient",
        "normal_range": (0.0, 2000.0),
    },
    "available_potassium": {
        "display_name": "Available Potassium (K2O)",
        "standard_unit": "kg/ha",
        "category": "macronutrient",
        "normal_range": (0.0, 1500.0),
    },
    "sulphur": {
        "display_name": "Available Sulphur (S)",
        "standard_unit": "mg/kg",
        "category": "secondary_nutrient",
        "normal_range": (0.0, 100.0),
    },
    "zinc": {
        "display_name": "Available Zinc (Zn)",
        "standard_unit": "mg/kg",
        "category": "micronutrient",
        "normal_range": (0.0, 50.0),
    },
    "iron": {
        "display_name": "Available Iron (Fe)",
        "standard_unit": "mg/kg",
        "category": "micronutrient",
        "normal_range": (0.0, 200.0),
    },
    "manganese": {
        "display_name": "Available Manganese (Mn)",
        "standard_unit": "mg/kg",
        "category": "micronutrient",
        "normal_range": (0.0, 150.0),
    },
    "copper": {
        "display_name": "Available Copper (Cu)",
        "standard_unit": "mg/kg",
        "category": "micronutrient",
        "normal_range": (0.0, 50.0),
    },
    "boron": {
        "display_name": "Available Boron (B)",
        "standard_unit": "mg/kg",
        "category": "micronutrient",
        "normal_range": (0.0, 20.0),
    },
}


class SoilMeasurementItem(BaseModel):
    """Extracted soil measurement record."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    report_id: uuid.UUID
    farm_id: uuid.UUID

    parameter_key: str
    parameter_category: Optional[str] = "macronutrient"
    original_parameter_name: str
    display_name: Optional[str] = None

    original_value: Optional[float] = None
    original_value_text: Optional[str] = None
    original_unit: str

    normalized_value: Optional[float] = None
    normalized_unit: Optional[str] = None

    analytical_method: Optional[str] = None
    lab_reference_range: Optional[Dict[str, Any]] = None
    lab_rating: Optional[str] = None
    detection_limit: Optional[float] = None

    page_number: Optional[int] = 1
    sample_id: Optional[str] = None
    sample_designation: Optional[str] = None
    area_type: Optional[str] = None
    bounding_box: Optional[List[float]] = None
    extraction_confidence: Optional[float] = 1.0
    is_ambiguous: Optional[bool] = False

    verification_status: MeasurementVerificationStatus = MeasurementVerificationStatus.EXTRACTED_UNVERIFIED
    farmer_corrected_value: Optional[float] = None
    farmer_notes: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SoilMeasurementResponse(SoilMeasurementItem):
    """API response alias for SoilMeasurementItem."""
    pass


class SoilMeasurementCorrectionRequest(BaseModel):
    """Farmer correction payload for a single extracted measurement."""
    corrected_value: float = Field(..., description="Farmer-corrected numeric measurement value")
    corrected_unit: Optional[str] = Field(None, description="Corrected unit if OCR extracted incorrect unit")
    farmer_notes: Optional[str] = Field(None, description="Optional explanation or reference note from farmer")


class SoilReportSummary(BaseModel):
    """Summary representation for report listings."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farm_id: uuid.UUID
    user_id: uuid.UUID
    original_filename: str
    upload_timestamp: datetime
    laboratory_name: Optional[str] = None
    lab_number: Optional[str] = None
    report_date: Optional[datetime] = None
    sample_collection_date: Optional[datetime] = None
    date_received: Optional[datetime] = None
    date_processed: Optional[datetime] = None
    sample_depth_interval: Optional[str] = None
    depth_provenance: Optional[str] = "UNKNOWN"
    sampling_point_name: Optional[str] = None
    extraction_status: ExtractionStatus = ExtractionStatus.UPLOADED
    review_status: ReviewStatus = ReviewStatus.NEEDS_REVIEW
    total_measurements: int = 0
    confirmed_measurements: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SoilReportDetail(SoilReportSummary):
    """Full detail of a laboratory report including document URL and extracted measurements."""
    storage_path: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    file_hash_sha256: Optional[str] = None
    sample_depth_min_cm: Optional[float] = None
    sample_depth_max_cm: Optional[float] = None
    sampling_point_latitude: Optional[float] = None
    sampling_point_longitude: Optional[float] = None
    extraction_error: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    signed_document_url: Optional[str] = None
    measurements: List[SoilMeasurementItem] = []


class SoilReportConfirmRequest(BaseModel):
    """Request to confirm report transcription."""
    measurement_ids: Optional[List[uuid.UUID]] = Field(
        None,
        description="Explicit list of measurement IDs to confirm. If omitted or empty, confirms all measurements in the report."
    )
    confirmation_notes: Optional[str] = Field(
        None,
        description="Optional farmer verification comments"
    )


class SoilReportConfirmResponse(BaseModel):
    """Response returned upon successful farmer confirmation."""
    report_id: uuid.UUID
    status: str = "confirmed"
    review_status: ReviewStatus = ReviewStatus.CONFIRMED
    confirmed_measurement_count: int
    confirmed_at: datetime


class SignedUrlResponse(BaseModel):
    """Time-limited signed download URL response."""
    signed_url: str
    expires_in_seconds: int = 3600


class SoilReportUploadMetadata(BaseModel):
    """Form metadata passed alongside file upload."""
    laboratory_name: Optional[str] = None
    report_date: Optional[datetime] = None
    sample_collection_date: Optional[datetime] = None
    sample_depth_interval: Optional[str] = None
    depth_provenance: Optional[str] = "UNKNOWN"
    sampling_point_name: Optional[str] = None
