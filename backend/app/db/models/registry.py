from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, Boolean, JSON
from backend.app.db.session import Base
from backend.app.core.timezone import now_utc

class DatasetRegistryModel(Base):
    """
    Registry of all external and ingested datasets in Rashkar.
    Maintains provenance, SHA-256 checksums, licensing, spatial/temporal coverage.
    """
    __tablename__ = "dataset_registry"

    dataset_id = Column(String(50), primary_key=True, index=True)
    dataset_name = Column(String(200), nullable=False)
    publisher = Column(String(200), nullable=False)
    source_url = Column(Text, nullable=True)
    classification = Column(String(50), nullable=False)  # direct_download, api, interactive_portal, institutional_request, pilot_collection, reference_only
    format = Column(String(50), nullable=False)  # netcdf, csv, json, parquet, geotiff
    temporal_coverage = Column(String(100), nullable=True)  # e.g., "2010-2024"
    spatial_coverage = Column(String(100), nullable=True)  # e.g., "Maharashtra Statewide", "Pune District"
    spatial_resolution = Column(String(100), nullable=True)  # e.g., "0.25 deg", "10 m"
    licence = Column(String(200), nullable=False)
    commercial_use_status = Column(String(100), nullable=True)
    retrieved_at_utc = Column(DateTime, default=now_utc, nullable=False)
    sha256_checksum = Column(String(64), nullable=True)
    storage_path = Column(Text, nullable=True)
    row_count = Column(Integer, nullable=True)
    quality_status = Column(String(50), default="unverified")  # verified, pending_validation, corrupted
    provenance_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc, onupdate=now_utc)
