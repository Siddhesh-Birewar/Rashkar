"""
Pydantic data models for Soil Test Report OCR and Structured Extraction.
Enforces strict decoupling of extraction confidence and farmer verification.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


class ReportExtractionStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    EXTRACTION_COMPLETED = "EXTRACTION_COMPLETED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


class MeasurementVerificationStatus(str, Enum):
    EXTRACTED_UNVERIFIED = "EXTRACTED_UNVERIFIED"
    FARMER_CORRECTED = "FARMER_CORRECTED"
    FARMER_CONFIRMED = "FARMER_CONFIRMED"


class ParameterExtractionStatus(str, Enum):
    EXTRACTED = "EXTRACTED"
    NOT_REPORTED = "NOT_REPORTED"
    AMBIGUOUS = "AMBIGUOUS"
    FAILED = "FAILED"


# Canonical soil parameter keys as defined in PROJECT.md
CANONICAL_NUTRIENT_KEYS = [
    "soil_ph",
    "electrical_conductivity",
    "organic_carbon",
    "organic_matter",
    "available_nitrogen",
    "total_nitrogen",
    "available_phosphorus",
    "available_potassium",
    "sulphur",
    "zinc",
    "iron",
    "manganese",
    "copper",
    "boron",
]

# Canonical alias mapping
PARAMETER_ALIASES: Dict[str, str] = {
    # pH
    "ph": "soil_ph",
    "soil_ph": "soil_ph",
    "ph_1_2_5": "soil_ph",
    "सामू": "soil_ph",
    # EC
    "ec": "electrical_conductivity",
    "electrical_conductivity": "electrical_conductivity",
    "e_c": "electrical_conductivity",
    "विद्युत_वाहकता": "electrical_conductivity",
    # OC / SOC
    "oc": "organic_carbon",
    "organic_carbon": "organic_carbon",
    "soc": "organic_carbon",
    "सेंद्रिय_कर्ब": "organic_carbon",
    # Organic Matter (SOM) - strictly distinct from OC!
    "som": "organic_matter",
    "organic_matter": "organic_matter",
    "soil_organic_matter": "organic_matter",
    "सेंद्रिय_पदार्थ": "organic_matter",
    # Available Nitrogen
    "available_nitrogen": "available_nitrogen",
    "avail_n": "available_nitrogen",
    "n": "available_nitrogen",
    "उपलब्ध_नत्र": "available_nitrogen",
    # Total Nitrogen - strictly distinct from Available Nitrogen!
    "total_nitrogen": "total_nitrogen",
    "total_n": "total_nitrogen",
    "एकूण_नत्र": "total_nitrogen",
    # Available Phosphorus
    "available_phosphorus": "available_phosphorus",
    "available_p": "available_phosphorus",
    "available_p_p2o5": "available_phosphorus",
    "p2o5": "available_phosphorus",
    "p": "available_phosphorus",
    "उपलब्ध_स्फुरद": "available_phosphorus",
    # Available Potassium
    "available_potassium": "available_potassium",
    "available_k": "available_potassium",
    "available_k_k2o": "available_potassium",
    "k2o": "available_potassium",
    "k": "available_potassium",
    "उपलब्ध_पालाश": "available_potassium",
    # Secondary & Micronutrients
    "sulphur": "sulphur",
    "sulfur": "sulphur",
    "available_sulphur": "sulphur",
    "s": "sulphur",
    "गंधक": "sulphur",
    "zinc": "zinc",
    "available_zinc": "zinc",
    "zn": "zinc",
    "जस्त": "zinc",
    "iron": "iron",
    "available_iron": "iron",
    "fe": "iron",
    "लोह": "iron",
    "manganese": "manganese",
    "available_manganese": "manganese",
    "mn": "manganese",
    "मॅंगनीज": "manganese",
    "copper": "copper",
    "available_copper": "copper",
    "cu": "copper",
    "तांबे": "copper",
    "boron": "boron",
    "available_boron": "boron",
    "b": "boron",
    "बोरॉन": "boron",
}


class ExtractedSoilMeasurement(BaseModel):
    """
    Extracted measurement for an individual soil parameter.
    Preserves raw reported values, exact units, analytical method,
    and safeguards against silent conversions or false inferences.
    """
    parameter_key: str = Field(..., description="Canonical parameter identifier, e.g. 'soil_ph', 'available_nitrogen'")
    original_parameter_name: str = Field(..., description="Raw string as reported on the laboratory document")
    original_value: Optional[float] = Field(None, description="Numeric value reported. None if not measured (Safeguard 1).")
    original_unit: Optional[str] = Field(None, description="Raw unit string reported, e.g. 'kg/ha', 'dS/m', 'ppm'")
    
    # Normalization (only performed if validated 1:1 mathematical identity exists)
    normalized_value: Optional[float] = Field(None, description="Normalized numeric value")
    normalized_unit: Optional[str] = Field(None, description="Canonical unit identifier")
    
    # Laboratory analytical metadata
    analytical_method: Optional[str] = Field(None, description="Method reported, e.g. 'Walkley-Black', 'Olsen', 'DTPA'")
    laboratory_rating: Optional[str] = Field(None, description="Reported category, e.g. 'Low', 'Medium', 'High', 'Deficient'")
    reference_range: Optional[str] = Field(None, description="Laboratory reference or critical limit range")
    sample_depth: Optional[str] = Field(None, description="Sample depth interval, e.g. '0-15 cm'. None if unstated.")
    sample_id: Optional[str] = Field(None, description="Sample identifier or number within report, e.g. '1', '2'")
    sample_designation: Optional[str] = Field(None, description="Sample designation or field name, e.g. 'Lawn', 'Garden'")
    area_type: Optional[str] = Field(None, description="Area type or crop context, e.g. 'Lawn/Established', 'Garden/Vegetable'")
    page_number: int = Field(default=1, description="Source page number in document")
    
    # Optical and quality confidence
    ocr_confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Statistical OCR model confidence score")
    is_ambiguous: bool = Field(default=False, description="True if blurred, handwriting, OCR artifact, or out-of-range")
    ambiguity_reason: Optional[str] = Field(None, description="Explanation for ambiguity flagging")
    extraction_status: str = Field(
        default=ParameterExtractionStatus.EXTRACTED.value,
        description="EXTRACTED, NOT_REPORTED, AMBIGUOUS, or FAILED"
    )
    verification_status: str = Field(
        default=MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value,
        description="Farmer verification status. Strictly decoupled from OCR confidence!"
    )


class SoilReportMetadata(BaseModel):
    """
    Metadata extracted from soil test report header and client details.
    """
    laboratory_name: Optional[str] = Field(None, description="Testing laboratory or institution name")
    sample_id: Optional[str] = Field(None, description="Laboratory sample ID, barcode, or reference code")
    farmer_name: Optional[str] = Field(None, description="Reported farmer or customer name")
    report_date: Optional[str] = Field(None, description="Report issuance date (YYYY-MM-DD or raw)")
    collection_date: Optional[str] = Field(None, description="Sample collection date (YYYY-MM-DD or raw)")
    sample_depth: Optional[str] = Field(None, description="Reported sampling depth interval (Safeguard 6: do not guess)")
    sampling_point: Optional[str] = Field(None, description="Specific field plot, survey number, or sampling point")
    village: Optional[str] = Field(None, description="Village name")
    taluka: Optional[str] = Field(None, description="Taluka / Tehsil")
    district: Optional[str] = Field(None, description="District")
    state: Optional[str] = Field(None, description="State")


class SoilReportExtractionResult(BaseModel):
    """
    Complete output of the document extraction and parsing pipeline.
    """
    document_type: str = Field(..., description="'text_pdf', 'scanned_pdf', 'image_jpeg', 'image_png', 'unsupported'")
    extraction_status: str = Field(
        default=ReportExtractionStatus.EXTRACTION_COMPLETED.value,
        description="Overall report extraction lifecycle status"
    )
    metadata: SoilReportMetadata = Field(default_factory=SoilReportMetadata)
    measurements: List[ExtractedSoilMeasurement] = Field(default_factory=list)
    raw_text: Optional[str] = Field(None, description="Extracted text or OCR markdown stream")
    warnings: List[str] = Field(default_factory=list, description="Warnings generated during validation and safeguards")
    overall_confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall extraction confidence")
    is_ambiguous: bool = Field(default=False, description="Whether any critical parameter or metadata is ambiguous")
    ambiguity_reasons: List[str] = Field(default_factory=list, description="List of ambiguity warnings")
    total_parameters_detected: int = Field(default=0, description="Total parameters successfully identified")
    ambiguous_parameters_count: int = Field(default=0, description="Number of ambiguous parameters")

    def get_measurement(self, key_or_alias: str) -> Optional[ExtractedSoilMeasurement]:
        """Lookup measurement by canonical key or accepted alias."""
        canonical = PARAMETER_ALIASES.get(key_or_alias.lower().strip(), key_or_alias.lower().strip())
        for m in self.measurements:
            if m.parameter_key == canonical:
                return m
            # Also match original key directly if aliased differently
            if m.parameter_key == key_or_alias:
                return m
        return None
