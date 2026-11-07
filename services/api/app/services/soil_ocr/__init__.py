"""
Soil OCR and Structured Report Extraction Service Package.
"""

from .models import (
    SoilReportExtractionResult,
    SoilReportMetadata,
    ExtractedSoilMeasurement,
    ReportExtractionStatus,
    MeasurementVerificationStatus,
    ParameterExtractionStatus,
    CANONICAL_NUTRIENT_KEYS,
    PARAMETER_ALIASES,
)
from .parser import SoilReportParser
from .safeguards import ExtractionSafeguards
from .ollama_client import OllamaOCRClient, register_mock_transcription
from .extractor import SoilOCRExtractor

__all__ = [
    "SoilOCRExtractor",
    "SoilReportParser",
    "ExtractionSafeguards",
    "OllamaOCRClient",
    "register_mock_transcription",
    "SoilReportExtractionResult",
    "SoilReportMetadata",
    "ExtractedSoilMeasurement",
    "ReportExtractionStatus",
    "MeasurementVerificationStatus",
    "ParameterExtractionStatus",
    "CANONICAL_NUTRIENT_KEYS",
    "PARAMETER_ALIASES",
]
