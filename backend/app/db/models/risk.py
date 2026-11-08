from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Float, Integer, Boolean, JSON
from backend.app.db.session import Base
from backend.app.core.timezone import now_utc

class YieldAssessmentLogModel(Base):
    __tablename__ = "yield_assessment_logs"

    assessment_id = Column(String(50), primary_key=True, index=True)
    farm_id = Column(String(50), nullable=False, index=True)
    crop_cycle_id = Column(String(50), nullable=False, index=True)
    generated_at_utc = Column(DateTime, default=now_utc, nullable=False)
    overall_confidence = Column(String(20), default="medium")
    coverage_status = Column(String(50), nullable=False)
    crop_stage_code = Column(String(50), nullable=False)
    risk_summary = Column(JSON, default=list)
    yield_baseline_json = Column(JSON, default=dict)
    provenance_chain = Column(JSON, default=list)

class WorkerHazardAuditLogModel(Base):
    """
    Session-pseudonymous audit log for worker heat hazard calculations.
    Maintains NO names, NO personal health data, NO phone numbers.
    Subject to automated 30-day retention partition drop.
    """
    __tablename__ = "worker_hazard_audit_log"

    session_id = Column(String(50), primary_key=True, index=True)
    generated_at_utc = Column(DateTime, default=now_utc, nullable=False)
    latitude_rounded = Column(Float, nullable=False)  # Rounded to 3 decimals (~100m)
    longitude_rounded = Column(Float, nullable=False)
    taluka = Column(String(50), nullable=False)
    workload_category = Column(String(50), nullable=False)
    sun_exposure = Column(String(50), nullable=False)
    is_acclimatised = Column(Boolean, default=True)
    max_estimated_wbgt_c = Column(Float, nullable=False)
    hazard_level = Column(String(50), nullable=False)
    weather_provider = Column(String(100), nullable=False)
    weather_observation_time_utc = Column(DateTime, nullable=False)

class CropHeatAssessmentLogModel(Base):
    __tablename__ = "crop_heat_assessment_logs"

    assessment_id = Column(String(50), primary_key=True, index=True)
    farm_id = Column(String(50), nullable=False, index=True)
    crop_code = Column(String(50), nullable=False)
    stage_code = Column(String(50), nullable=False)
    generated_at_utc = Column(DateTime, default=now_utc, nullable=False)
    max_forecast_temp_c = Column(Float, nullable=False)
    critical_threshold_c = Column(Float, nullable=False)
    exceedance_hours = Column(Integer, default=0)
    warm_night_flag = Column(Boolean, default=False)
    risk_level = Column(String(50), nullable=False)
    evidence_citation = Column(Text, nullable=False)
