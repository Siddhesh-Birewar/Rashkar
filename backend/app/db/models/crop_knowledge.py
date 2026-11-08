from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, Integer, Boolean, JSON
from backend.app.db.session import Base
from backend.app.core.timezone import now_utc

class CanonicalCropMasterModel(Base):
    __tablename__ = "canonical_crops"

    crop_code = Column(String(50), primary_key=True, index=True)
    common_name_en = Column(String(100), nullable=False)
    common_name_mr = Column(String(100), nullable=False)
    botanical_name = Column(String(150), nullable=False)
    crop_category = Column(String(50), nullable=False)  # oilseed, fibre, cereal, millet, pulse, commercial, vegetable, fruit
    standard_season = Column(String(50), nullable=False)  # kharif, rabi, summer, perennial
    is_pioneer_pilot_crop = Column(Boolean, default=False)  # true for Soybean, Cotton, Jowar, Sugarcane
    apy_alias_list = Column(JSON, default=list)  # aliases found in APY/OGD records
    created_at = Column(DateTime, default=now_utc)

class CropStageReferenceModel(Base):
    __tablename__ = "crop_stage_references"

    stage_id = Column(String(50), primary_key=True, index=True)
    crop_code = Column(String(50), nullable=False, index=True)
    stage_code = Column(String(50), nullable=False)  # e.g., "R1_FLOWERING", "R3_POD_DEVELOPMENT"
    stage_name_en = Column(String(100), nullable=False)
    stage_name_mr = Column(String(100), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    typical_duration_days = Column(Integer, nullable=False)
    das_start_typical = Column(Integer, nullable=False)
    das_end_typical = Column(Integer, nullable=False)
    heat_sensitivity = Column(String(20), default="low")  # low, medium, high, critical
    drought_sensitivity = Column(String(20), default="low")
    excess_water_sensitivity = Column(String(20), default="low")
    source_citation = Column(Text, nullable=False)

class AgronomicThresholdRegistryModel(Base):
    """
    Versioned Agronomic Threshold Registry for evidence-based risk cutoffs.
    Every threshold must cite its research institution and verification status.
    """
    __tablename__ = "agronomic_threshold_registry"

    threshold_id = Column(String(50), primary_key=True, index=True)
    crop_code = Column(String(50), nullable=False, index=True)
    applicable_variety = Column(String(100), default="all")
    agro_ecological_zone = Column(String(100), default="Maharashtra Statewide")
    growth_stage = Column(String(50), nullable=False)
    environmental_variable = Column(String(50), nullable=False)  # e.g., "tmax_c", "tmin_c", "consecutive_dry_days"
    unit = Column(String(20), nullable=False)
    critical_threshold = Column(Float, nullable=False)
    required_exposure_duration_hours = Column(Integer, default=1)
    comparison_operator = Column(String(10), default=">=")  # >=, <=, >
    physiological_impact = Column(Text, nullable=False)
    source_institution = Column(String(150), nullable=False)
    publication_citation = Column(Text, nullable=False)
    publication_year = Column(Integer, nullable=False)
    evidence_grade = Column(String(50), nullable=False)  # peer_reviewed_experimental, extension_publication, expert_consensus, unverified_screening
    verification_status = Column(String(50), default="verified_by_agronomist")  # verified_by_agronomist, pending_review, unverified_screening
    created_at = Column(DateTime, default=now_utc)

class AgronomicAdvisoryCatalogueModel(Base):
    __tablename__ = "agronomic_advisory_catalogue"

    action_id = Column(String(50), primary_key=True, index=True)
    crop_code = Column(String(50), nullable=False, index=True)
    risk_dimension = Column(String(50), nullable=False)  # dry_spell, excess_rain, crop_heat, soil_ph, pest_watch, disease_watch
    title_en = Column(String(200), nullable=False)
    title_mr = Column(String(200), nullable=False)
    description_en = Column(Text, nullable=False)
    description_mr = Column(Text, nullable=False)
    evidence_citation = Column(Text, nullable=False)
    expert_reviewer = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
