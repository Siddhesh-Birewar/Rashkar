from datetime import datetime
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.db.models.registry import DatasetRegistryModel
from backend.app.schemas.registry import DatasetRegisterRequest, ProvenanceEnvelope
from backend.app.core.timezone import now_utc

class RegistryService:
    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """Compute SHA-256 hash of a file for cryptographic provenance."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def register_dataset(
        db: Session,
        request: DatasetRegisterRequest,
        file_path: Optional[Path] = None
    ) -> DatasetRegistryModel:
        """Register or update an external dataset in the catalog."""
        checksum = None
        if file_path and file_path.exists():
            checksum = RegistryService.calculate_sha256(file_path)
            if not request.storage_path:
                request.storage_path = str(file_path)

        existing = db.query(DatasetRegistryModel).filter(
            DatasetRegistryModel.dataset_id == request.dataset_id
        ).first()

        if existing:
            existing.dataset_name = request.dataset_name
            existing.publisher = request.publisher
            existing.source_url = request.source_url
            existing.classification = request.classification
            existing.format = request.format
            existing.temporal_coverage = request.temporal_coverage
            existing.spatial_coverage = request.spatial_coverage
            existing.spatial_resolution = request.spatial_resolution
            existing.licence = request.licence
            existing.commercial_use_status = request.commercial_use_status
            existing.storage_path = request.storage_path
            existing.row_count = request.row_count
            if checksum:
                existing.sha256_checksum = checksum
            existing.provenance_metadata = request.provenance_metadata
            existing.updated_at = now_utc()
            db.commit()
            db.refresh(existing)
            return existing

        record = DatasetRegistryModel(
            dataset_id=request.dataset_id,
            dataset_name=request.dataset_name,
            publisher=request.publisher,
            source_url=request.source_url,
            classification=request.classification,
            format=request.format,
            temporal_coverage=request.temporal_coverage,
            spatial_coverage=request.spatial_coverage,
            spatial_resolution=request.spatial_resolution,
            licence=request.licence,
            commercial_use_status=request.commercial_use_status,
            storage_path=request.storage_path,
            row_count=request.row_count,
            sha256_checksum=checksum,
            quality_status="verified" if checksum else "pending_validation",
            provenance_metadata=request.provenance_metadata,
            retrieved_at_utc=now_utc()
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_dataset(db: Session, dataset_id: str) -> Optional[DatasetRegistryModel]:
        return db.query(DatasetRegistryModel).filter(DatasetRegistryModel.dataset_id == dataset_id).first()

    @staticmethod
    def list_datasets(db: Session) -> List[DatasetRegistryModel]:
        return db.query(DatasetRegistryModel).order_by(DatasetRegistryModel.dataset_id).all()

    @staticmethod
    def create_provenance_envelope(
        source_id: str,
        source_name: str,
        unit: str,
        observed_at_utc: Optional[datetime] = None,
        valid_at_utc: Optional[datetime] = None,
        spatial_resolution_m: Optional[int] = None,
        depth_interval: Optional[str] = None,
        quality_flag: str = "PASSED_RANGE_CHECK"
    ) -> ProvenanceEnvelope:
        return ProvenanceEnvelope(
            source_id=source_id,
            source_name=source_name,
            retrieved_at_utc=now_utc(),
            observed_at_utc=observed_at_utc,
            valid_at_utc=valid_at_utc,
            spatial_resolution_m=spatial_resolution_m,
            depth_interval=depth_interval,
            unit=unit,
            quality_flag=quality_flag
        )
