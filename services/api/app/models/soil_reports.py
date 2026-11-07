"""
SQLAlchemy models for Soil Test Reports and Soil Measurements.

Supports laboratory soil test report metadata preservation,
multi-sample/multi-depth sampling per farm, document provenance,
extraction status lifecycle, and human-in-the-loop farmer review.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship

try:
    from cropnet.services.api.app.models.soil_and_farm import Base, FarmModel
except ImportError:
    from .soil_and_farm import Base, FarmModel


class SoilTestReportModel(Base):
    """
    Metadata for an uploaded laboratory soil test report document.
    Preserves document storage path, upload timestamp, laboratory metadata,
    sampling context, extraction status lifecycle, and review status.
    """
    __tablename__ = "soil_test_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    farm_id = Column(String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Document storage metadata
    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    file_hash_sha256 = Column(String(64), nullable=True, index=True)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Laboratory & Sampling Metadata
    laboratory_name = Column(String(200), nullable=True)
    lab_number = Column(String(100), nullable=True)
    report_date = Column(DateTime, nullable=True)
    sample_collection_date = Column(DateTime, nullable=True)
    date_received = Column(DateTime, nullable=True)
    date_processed = Column(DateTime, nullable=True)
    sample_depth_interval = Column(String(50), nullable=True)  # e.g., "0-15cm", "15-30cm"
    sample_depth_min_cm = Column(Float, nullable=True)
    sample_depth_max_cm = Column(Float, nullable=True)
    depth_provenance = Column(String(50), nullable=True, default="UNKNOWN")  # LAB_REPORT, FARMER_PROVIDED, UNKNOWN
    sampling_point_name = Column(String(150), nullable=True)  # e.g., "North Field Plot 1"
    sampling_point_latitude = Column(Float, nullable=True)
    sampling_point_longitude = Column(Float, nullable=True)

    # Extraction & Review Lifecycle Statuses
    # Extraction statuses: UPLOADED, PROCESSING, EXTRACTION_COMPLETED, NEEDS_REVIEW, CONFIRMED, FAILED
    extraction_status = Column(String(50), nullable=False, default="UPLOADED", index=True)
    extraction_error = Column(Text, nullable=True)

    # Review statuses: NEEDS_REVIEW, CONFIRMED
    review_status = Column(String(50), nullable=False, default="NEEDS_REVIEW", index=True)
    reviewed_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)

    # Raw extracted payload preservation (audit trail)
    raw_extracted_payload = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    farm = relationship("FarmModel")
    measurements = relationship(
        "SoilMeasurementModel",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="SoilMeasurementModel.created_at"
    )


class SoilMeasurementModel(Base):
    """
    Individual soil parameter measurement extracted from a laboratory report.
    Tracks exact reported value, canonical key, normalized units (where deterministic conversions exist),
    analytical methodology, extraction confidence, and farmer verification status.
    """
    __tablename__ = "soil_test_measurements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("soil_test_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    farm_id = Column(String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Parameter identification
    parameter_key = Column(String(50), nullable=False, index=True)
    # Categories: physical, macronutrient, micronutrient, secondary_nutrient, chemical
    parameter_category = Column(String(50), nullable=True, default="macronutrient")
    original_parameter_name = Column(String(150), nullable=False)

    # Original reported measurement (Never modified)
    original_value = Column(Float, nullable=True)
    original_value_text = Column(String(100), nullable=True)
    original_unit = Column(String(50), nullable=False)

    # Normalized measurement (Populated only when validated deterministic conversion exists)
    normalized_value = Column(Float, nullable=True)
    normalized_unit = Column(String(50), nullable=True)

    # Analytical Context & Reference Ranges
    analytical_method = Column(String(150), nullable=True)
    lab_reference_range = Column(JSON, nullable=True)
    lab_rating = Column(String(50), nullable=True)
    detection_limit = Column(Float, nullable=True)

    # Document Provenance & OCR Confidence
    page_number = Column(Integer, nullable=True, default=1)
    bounding_box = Column(JSON, nullable=True)
    extraction_confidence = Column(Float, nullable=True, default=1.0)
    is_ambiguous = Column(Boolean, nullable=True, default=False)

    # Farmer Human-in-the-Loop Review & Verification
    # Statuses: EXTRACTED_UNVERIFIED, FARMER_CORRECTED, FARMER_CONFIRMED
    verification_status = Column(String(50), nullable=False, default="EXTRACTED_UNVERIFIED", index=True)
    farmer_corrected_value = Column(Float, nullable=True)
    farmer_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    report = relationship("SoilTestReportModel", back_populates="measurements")
