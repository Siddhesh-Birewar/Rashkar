"""
SQLAlchemy models for Irrigation Water Sources, Water Test Reports, and Water Quality Measurements.

Supports:
- Multiple irrigation sources per farm (borewell, open well, canal, river, etc.)
- Farmer-reported availability, reliability, capacity vs measured capacity
- Water quality laboratory report document tracking and review lifecycle
- Discrete chemical/physical water measurements (pH, EC, TDS, Na, Ca, Mg, Cl, HCO3, CO3, SO4, B, NO3)
- Strictly isolated from soil measurements table
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


class WaterSourceModel(Base):
    """
    Irrigation water source attached to a specific farm.
    Tracks water availability, seasonal characteristics, farmer-reported reliability,
    and measured or reported capacity without ungrounded estimations.
    """
    __tablename__ = "water_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    farm_id = Column(String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    # Classification & Identity
    # Types: borewell, open_well, canal, river, reservoir, farm_pond, rainwater_harvesting, other
    source_type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    location_description = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Availability & Reliability
    # Seasonal: perennial, seasonal_monsoon, seasonal_winter, summer_dry, kharif_only, rabi_only
    seasonal_availability = Column(String(50), nullable=False, default="perennial")
    # Reliability: reliable, moderate, intermittent, unreliable
    reliability = Column(String(50), nullable=False, default="reliable")
    daily_available_hours = Column(Float, nullable=True)  # e.g., 6.0 hours/day power/water supply

    # Application & Capacity
    # Method: drip, sprinkler, furrow, flood, basin, other
    irrigation_method = Column(String(50), nullable=False, default="drip")
    measured_capacity_lph = Column(Float, nullable=True)  # Flow rate in Liters per Hour
    capacity_provenance = Column(String(50), nullable=False, default="FARMER_REPORTED")  # MEASURED, FARMER_REPORTED, UNSPECIFIED

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    farm = relationship("FarmModel")
    reports = relationship(
        "WaterTestReportModel",
        back_populates="water_source",
        cascade="all, delete-orphan",
        order_by="WaterTestReportModel.created_at.desc()"
    )
    measurements = relationship(
        "WaterMeasurementModel",
        back_populates="water_source",
        cascade="all, delete-orphan",
        order_by="WaterMeasurementModel.created_at.desc()"
    )


class WaterTestReportModel(Base):
    """
    Metadata for an uploaded water testing laboratory report document.
    Preserves document storage path, upload timestamp, laboratory metadata,
    sampling context, extraction status lifecycle, and review status.
    """
    __tablename__ = "water_test_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    farm_id = Column(String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)
    water_source_id = Column(String(36), ForeignKey("water_sources.id", ondelete="SET NULL"), nullable=True, index=True)

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
    sampling_location = Column(String(150), nullable=True)

    # Extraction & Review Lifecycle Statuses
    # Extraction: UPLOADED, PROCESSING, EXTRACTION_COMPLETED, NEEDS_REVIEW, CONFIRMED, FAILED
    extraction_status = Column(String(50), nullable=False, default="UPLOADED", index=True)
    extraction_error = Column(Text, nullable=True)

    # Review: NEEDS_REVIEW, CONFIRMED
    review_status = Column(String(50), nullable=False, default="NEEDS_REVIEW", index=True)
    reviewed_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)

    # Raw extracted payload preservation (audit trail)
    raw_extracted_payload = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    farm = relationship("FarmModel")
    water_source = relationship("WaterSourceModel", back_populates="reports")
    measurements = relationship(
        "WaterMeasurementModel",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="WaterMeasurementModel.created_at"
    )


class WaterMeasurementModel(Base):
    """
    Individual water laboratory measurement.
    Strictly stored in `water_measurements`, never mixed into `soil_measurements`.
    Tracks reported values, standardized ionic units (meq/L), analytical methodology,
    and farmer review verification status.
    """
    __tablename__ = "water_measurements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("water_test_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    farm_id = Column(String(36), ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)
    water_source_id = Column(String(36), ForeignKey("water_sources.id", ondelete="SET NULL"), nullable=True, index=True)

    # Parameter identification
    # Canonical keys: ph, electrical_conductivity, tds, sodium, calcium, magnesium,
    # chloride, bicarbonate, carbonate, sulphate, boron, nitrate, sar, rsc
    parameter_key = Column(String(50), nullable=False, index=True)
    original_parameter_name = Column(String(150), nullable=False)

    # Original reported measurement
    original_value = Column(Float, nullable=True)
    original_value_text = Column(String(100), nullable=True)
    original_unit = Column(String(50), nullable=False)

    # Normalized value in standard agricultural water unit (meq/L for ions, dS/m for EC, mg/L for TDS, unitless for pH/SAR)
    normalized_value = Column(Float, nullable=True)
    normalized_unit = Column(String(50), nullable=True)

    # Analytical Context
    analytical_method = Column(String(150), nullable=True)
    detection_limit = Column(Float, nullable=True)

    # Provenance & Verification
    # Provenance: LAB_REPORT, CALCULATED, FARMER_CORRECTED, FARMER_PROVIDED
    provenance = Column(String(50), nullable=False, default="LAB_REPORT")
    # Verification: EXTRACTED_UNVERIFIED, FARMER_CORRECTED, FARMER_CONFIRMED
    verification_status = Column(String(50), nullable=False, default="EXTRACTED_UNVERIFIED", index=True)
    farmer_corrected_value = Column(Float, nullable=True)
    farmer_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    report = relationship("WaterTestReportModel", back_populates="measurements")
    water_source = relationship("WaterSourceModel", back_populates="measurements")
