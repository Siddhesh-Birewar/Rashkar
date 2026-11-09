from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, Date, Text, Float, Integer, ForeignKey, JSON, Boolean
from backend.app.db.session import Base
from backend.app.core.timezone import now_utc

class CropLossCaseModel(Base):
    """
    PMFBY crop-loss evidence packet and human-reviewer workflow.
    Prepares verifiable evidence dossiers; strictly does NOT fabricate
    official insurance approval or unapproved claim submission.
    """
    __tablename__ = "crop_loss_cases"

    case_id = Column(String(50), primary_key=True, index=True)
    farmer_id = Column(String(50), nullable=False, index=True)
    farm_id = Column(String(50), nullable=False, index=True)
    plot_id = Column(String(50), nullable=True)
    crop_code = Column(String(50), nullable=False)
    season = Column(String(20), nullable=False)
    event_date = Column(Date, nullable=False)
    peril_type = Column(String(50), nullable=False)  # unseasonal_rainfall, hailstorm, drought, pest_attack, flood
    damage_estimate_pct = Column(Float, nullable=False)  # Farmer estimated 0-100%
    affected_area_acres = Column(Float, nullable=False)
    photo_urls = Column(JSON, default=list)  # List of stored photo paths/URLs
    gps_latitude = Column(Float, nullable=True)
    gps_longitude = Column(Float, nullable=True)
    weather_evidence_summary = Column(JSON, default=dict)  # Associated IMD/ERA5 weather anomalies
    satellite_evidence_summary = Column(JSON, default=dict)  # Vegetation index change (Sentinel-2 NDVI, NDWI, EVI)
    vision_evidence_summary = Column(JSON, default=dict)  # YOLOv8, U-Net, ViT damage analysis
    multimodal_fusion_summary = Column(JSON, default=dict)  # Fused % loss, confidence score, and routing recommendation
    dossier_status = Column(String(50), default="draft_saved")  # draft_saved, evidence_submitted, under_review, review_completed
    is_demo_synthetic = Column(Boolean, default=True)  # Clearly labels demo vs actual legal records
    
    # Human reviewer audit fields
    reviewer_id = Column(String(50), nullable=True)
    reviewed_at_utc = Column(DateTime, nullable=True)
    reviewer_decision = Column(String(50), nullable=True)  # verified_loss, partially_verified, rejected, information_required
    reviewer_rationale = Column(Text, nullable=True)
    recommended_compensation_basis = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)
