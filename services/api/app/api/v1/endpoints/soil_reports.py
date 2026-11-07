"""
FastAPI REST Endpoints for Soil Laboratory Report Lifecycle Management.

Prefix: /api/v1/farms/{farm_id}/soil-reports
Enforces:
- Supabase Bearer Authentication & Farm Ownership Verification
- Supported file types: PDF, JPEG, PNG (max 15MB)
- Storage in private Supabase bucket `soil-reports` with HMAC signed URLs
- Full measurement extraction review, farmer correction, and confirmation workflows
- Strict document streaming without public storage URL exposure
"""
import uuid
import hashlib
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import (
    APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query, Response
)
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

try:
    from cropnet.services.api.app.core.database import get_db
    from cropnet.services.api.app.core.security import get_current_user, CurrentUser
    from cropnet.services.api.app.api.v1.endpoints.farms import _get_farm_and_verify_owner
    from cropnet.services.api.app.models.soil_reports import SoilTestReportModel, SoilMeasurementModel
    from cropnet.services.api.app.services.soil_report_storage import soil_report_storage
    from cropnet.services.api.app.services.soil_ocr.extractor import DocumentExtractionPipeline
    from cropnet.services.api.app.services.soil_ocr.models import ReportExtractionStatus
    from cropnet.services.api.app.schemas.soil_reports import (
        ExtractionStatus,
        ReviewStatus,
        MeasurementVerificationStatus,
        CANONICAL_SOIL_PARAMETERS,
        SoilReportSummary,
        SoilReportDetail,
        SoilMeasurementItem,
        SoilMeasurementCorrectionRequest,
        SoilReportConfirmRequest,
        SoilReportConfirmResponse,
        SignedUrlResponse,
    )
except ImportError:
    from ...core.database import get_db
    from ...core.security import get_current_user, CurrentUser
    from .farms import _get_farm_and_verify_owner
    from ...models.soil_reports import SoilTestReportModel, SoilMeasurementModel
    from ...services.soil_report_storage import soil_report_storage
    from ...services.soil_ocr.extractor import DocumentExtractionPipeline
    from ...services.soil_ocr.models import ReportExtractionStatus
    from ...schemas.soil_reports import (
        ExtractionStatus,
        ReviewStatus,
        MeasurementVerificationStatus,
        CANONICAL_SOIL_PARAMETERS,
        SoilReportSummary,
        SoilReportDetail,
        SoilMeasurementItem,
        SoilMeasurementCorrectionRequest,
        SoilReportConfirmRequest,
        SoilReportConfirmResponse,
        SignedUrlResponse,
    )

router = APIRouter(prefix="/farms/{farm_id}/soil-reports", tags=["Soil Reports"])

MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 Megabytes
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def _parse_optional_date(val: Optional[str]) -> Optional[datetime]:
    """Safely parse ISO date strings."""
    if not val:
        return None
    try:
        clean = val.strip()
        if "T" in clean:
            return datetime.fromisoformat(clean)
        return datetime.strptime(clean, "%Y-%m-%d")
    except Exception:
        return None


def _model_to_measurement_item(m: SoilMeasurementModel) -> SoilMeasurementItem:
    return SoilMeasurementItem(
        id=uuid.UUID(m.id),
        report_id=uuid.UUID(m.report_id),
        farm_id=uuid.UUID(m.farm_id),
        parameter_key=m.parameter_key,
        parameter_category=m.parameter_category,
        original_parameter_name=m.original_parameter_name,
        original_value=m.original_value,
        original_value_text=m.original_value_text,
        original_unit=m.original_unit,
        normalized_value=m.normalized_value,
        normalized_unit=m.normalized_unit,
        analytical_method=m.analytical_method,
        lab_reference_range=m.lab_reference_range,
        lab_rating=m.lab_rating,
        detection_limit=m.detection_limit,
        page_number=m.page_number,
        bounding_box=m.bounding_box,
        extraction_confidence=m.extraction_confidence,
        is_ambiguous=m.is_ambiguous,
        verification_status=MeasurementVerificationStatus(m.verification_status),
        farmer_corrected_value=m.farmer_corrected_value,
        farmer_notes=m.farmer_notes,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _model_to_report_summary(r: SoilTestReportModel) -> SoilReportSummary:
    measurements = r.measurements or []
    total = len(measurements)
    confirmed = sum(1 for m in measurements if m.verification_status == MeasurementVerificationStatus.FARMER_CONFIRMED.value)

    return SoilReportSummary(
        id=uuid.UUID(r.id),
        farm_id=uuid.UUID(r.farm_id),
        user_id=uuid.UUID(r.user_id),
        original_filename=r.original_filename,
        upload_timestamp=r.upload_timestamp,
        laboratory_name=r.laboratory_name,
        report_date=r.report_date,
        sample_collection_date=r.sample_collection_date,
        sample_depth_interval=r.sample_depth_interval,
        sampling_point_name=r.sampling_point_name,
        extraction_status=ExtractionStatus(r.extraction_status),
        review_status=ReviewStatus(r.review_status),
        total_measurements=total,
        confirmed_measurements=confirmed,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def _model_to_report_detail(r: SoilTestReportModel, signed_url: Optional[str] = None) -> SoilReportDetail:
    summary = _model_to_report_summary(r)
    measurements = [_model_to_measurement_item(m) for m in (r.measurements or [])]

    return SoilReportDetail(
        **summary.model_dump(),
        storage_path=r.storage_path,
        file_size_bytes=r.file_size_bytes,
        mime_type=r.mime_type,
        file_hash_sha256=r.file_hash_sha256,
        sample_depth_min_cm=r.sample_depth_min_cm,
        sample_depth_max_cm=r.sample_depth_max_cm,
        sampling_point_latitude=r.sampling_point_latitude,
        sampling_point_longitude=r.sampling_point_longitude,
        extraction_error=r.extraction_error,
        reviewed_at=r.reviewed_at,
        confirmed_at=r.confirmed_at,
        signed_document_url=signed_url,
        measurements=measurements,
    )


def _execute_report_extraction(
    report: SoilTestReportModel,
    content: bytes,
    filename: str,
    content_type: Optional[str],
    db: Session
) -> None:
    """
    Execute OCR and structured measurement extraction on an uploaded report document.
    Updates report extraction_status to NEEDS_REVIEW (or FAILED if unparseable),
    persists raw extraction payload for audit trail, and inserts individual
    SoilMeasurementModel records with EXTRACTED_UNVERIFIED verification status.
    """
    try:
        pipeline = DocumentExtractionPipeline()
        result = pipeline.extract(
            file_bytes=content,
            filename=filename,
            mime_type=content_type
        )
        report.raw_extracted_payload = result.model_dump()

        if result.extraction_status == ReportExtractionStatus.FAILED.value:
            report.extraction_status = ExtractionStatus.FAILED.value
            report.extraction_error = "; ".join(result.warnings) if result.warnings else "Document extraction failed."
        else:
            # Propagate extracted metadata if not manually supplied
            if result.metadata.laboratory_name and not report.laboratory_name:
                report.laboratory_name = result.metadata.laboratory_name
            if result.metadata.report_date and not report.report_date:
                report.report_date = _parse_optional_date(result.metadata.report_date)
            if result.metadata.collection_date and not report.sample_collection_date:
                report.sample_collection_date = _parse_optional_date(result.metadata.collection_date)
            if result.metadata.sample_depth and not report.sample_depth_interval:
                report.sample_depth_interval = result.metadata.sample_depth
            if result.metadata.sampling_point and not report.sampling_point_name:
                report.sampling_point_name = result.metadata.sampling_point

            # Insert extracted measurements
            for m in result.measurements:
                param_meta = CANONICAL_SOIL_PARAMETERS.get(m.parameter_key, {})
                cat = param_meta.get("category", "macronutrient")
                meas = SoilMeasurementModel(
                    id=str(uuid.uuid4()),
                    report_id=report.id,
                    farm_id=report.farm_id,
                    parameter_key=m.parameter_key,
                    parameter_category=cat,
                    original_parameter_name=m.original_parameter_name,
                    original_value=m.original_value,
                    original_value_text=str(m.original_value) if m.original_value is not None else None,
                    original_unit=m.original_unit or "",
                    normalized_value=m.normalized_value,
                    normalized_unit=m.normalized_unit,
                    analytical_method=m.analytical_method,
                    lab_reference_range={"range": m.reference_range} if m.reference_range else None,
                    lab_rating=m.laboratory_rating,
                    detection_limit=None,
                    page_number=m.page_number or 1,
                    bounding_box=None,
                    extraction_confidence=m.ocr_confidence,
                    is_ambiguous=m.is_ambiguous,
                    verification_status=MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value,
                    farmer_notes=m.ambiguity_reason if m.is_ambiguous else None,
                )
                db.add(meas)

            report.extraction_status = ExtractionStatus.NEEDS_REVIEW.value
            report.review_status = ReviewStatus.NEEDS_REVIEW.value
            report.extraction_error = None
    except Exception as exc:
        logger.exception("Error executing OCR pipeline for report %s: %s", report.id, exc)
        report.extraction_status = ExtractionStatus.FAILED.value
        report.extraction_error = str(exc)


@router.post("", response_model=SoilReportDetail, status_code=status.HTTP_201_CREATED)
@router.post("/upload", response_model=SoilReportDetail, status_code=status.HTTP_201_CREATED)
async def upload_soil_report(
    farm_id: uuid.UUID,
    file: UploadFile = File(..., description="Soil report document (PDF, JPEG, PNG, max 15MB)"),
    laboratory_name: Optional[str] = Form(None),
    lab_name: Optional[str] = Form(None),
    report_date: Optional[str] = Form(None),
    sample_collection_date: Optional[str] = Form(None),
    sample_depth_interval: Optional[str] = Form(None),
    sampling_point_name: Optional[str] = Form(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a laboratory soil test report for an authenticated user's farm.
    Validates ownership, file format, and size limit before storing in private storage,
    then executes OCR structured extraction and inserts unverified measurements.
    """
    # 1. Enforce farm ownership
    _get_farm_and_verify_owner(farm_id, current_user, db)

    effective_lab_name = laboratory_name or lab_name

    # 2. Validate file format
    filename = file.filename or "unknown.pdf"
    dot_idx = filename.rfind(".")
    ext = filename[dot_idx:].lower() if dot_idx != -1 else ""

    content_type = file.content_type or ""
    # Normalize empty or generic octet-stream MIME types from web browsers based on extension
    if not content_type or content_type == "application/octet-stream":
        if ext == ".pdf":
            content_type = "application/pdf"
        elif ext in {".jpg", ".jpeg"}:
            content_type = "image/jpeg"
        elif ext == ".png":
            content_type = "image/png"

    if ext not in ALLOWED_EXTENSIONS or (content_type and content_type not in ALLOWED_MIME_TYPES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{filename}'. Only PDF, JPEG, and PNG documents are allowed."
        )

    # 3. Read content and validate size limit (max 15MB)
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed limit of 15MB (received {len(content)} bytes)."
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # Validate file magic bytes / signature to prevent extension spoofing
    if ext == ".pdf" and not (content.startswith(b"%PDF") or b"%PDF" in content[:1024]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF document: file content does not match PDF signature."
        )
    elif ext in {".jpg", ".jpeg"} and not content.startswith(b"\xFF\xD8\xFF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JPEG image: file content does not match JPEG signature."
        )
    elif ext == ".png" and not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PNG image: file content does not match PNG signature."
        )

    # 4. Generate report ID & SHA256
    report_id = str(uuid.uuid4())
    file_hash = hashlib.sha256(content).hexdigest()

    # 5. Upload to private storage
    storage_path = soil_report_storage.upload_file(
        farm_id=str(farm_id),
        report_id=report_id,
        filename=filename,
        content=content,
        content_type=content_type or "application/pdf"
    )

    # 6. Persist initial record to database
    report = SoilTestReportModel(
        id=report_id,
        user_id=str(current_user.user_id),
        farm_id=str(farm_id),
        original_filename=filename,
        storage_path=storage_path,
        file_size_bytes=len(content),
        mime_type=content_type or "application/pdf",
        file_hash_sha256=file_hash,
        upload_timestamp=datetime.utcnow(),
        laboratory_name=effective_lab_name,
        report_date=_parse_optional_date(report_date),
        sample_collection_date=_parse_optional_date(sample_collection_date),
        sample_depth_interval=sample_depth_interval,
        sampling_point_name=sampling_point_name,
        extraction_status=ExtractionStatus.UPLOADED.value,
        review_status=ReviewStatus.NEEDS_REVIEW.value,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    # 7. Bridge to DocumentExtractionPipeline for OCR & Structured Extraction
    _execute_report_extraction(
        report=report,
        content=content,
        filename=filename,
        content_type=content_type,
        db=db
    )
    db.commit()
    db.refresh(report)

    # 8. Generate time-limited signed URL
    signed_url = soil_report_storage.generate_signed_url(
        storage_path=storage_path,
        farm_id=str(farm_id),
        report_id=report_id
    )

    return _model_to_report_detail(report, signed_url)


@router.get("", response_model=List[SoilReportSummary])
async def list_soil_reports(
    farm_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    extraction_status: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all uploaded laboratory soil reports for the authenticated user's farm.
    """
    _get_farm_and_verify_owner(farm_id, current_user, db)

    query = db.query(SoilTestReportModel).filter(SoilTestReportModel.farm_id == str(farm_id))
    if extraction_status:
        query = query.filter(SoilTestReportModel.extraction_status == extraction_status)

    reports = query.order_by(SoilTestReportModel.upload_timestamp.desc()).offset(skip).limit(limit).all()
    return [_model_to_report_summary(r) for r in reports]


@router.get("/{report_id}", response_model=SoilReportDetail)
async def get_soil_report_detail(
    farm_id: uuid.UUID,
    report_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve metadata, extracted measurements, and signed document URL for a specific report.
    """
    _get_farm_and_verify_owner(farm_id, current_user, db)

    report = db.query(SoilTestReportModel).filter(
        SoilTestReportModel.id == str(report_id),
        SoilTestReportModel.farm_id == str(farm_id)
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soil report {report_id} not found for farm {farm_id}"
        )

    signed_url = soil_report_storage.generate_signed_url(
        storage_path=report.storage_path,
        farm_id=str(farm_id),
        report_id=str(report_id)
    )

    return _model_to_report_detail(report, signed_url)


@router.get("/{report_id}/measurements", response_model=List[SoilMeasurementItem])
async def get_soil_report_measurements(
    farm_id: uuid.UUID,
    report_id: uuid.UUID,
    verification_status: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all individual parameter measurements extracted from a report.
    """
    _get_farm_and_verify_owner(farm_id, current_user, db)

    report = db.query(SoilTestReportModel).filter(
        SoilTestReportModel.id == str(report_id),
        SoilTestReportModel.farm_id == str(farm_id)
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soil report {report_id} not found"
        )

    query = db.query(SoilMeasurementModel).filter(
        SoilMeasurementModel.report_id == str(report_id),
        SoilMeasurementModel.farm_id == str(farm_id)
    )
    if verification_status:
        query = query.filter(SoilMeasurementModel.verification_status == verification_status)

    measurements = query.order_by(SoilMeasurementModel.created_at).all()
    return [_model_to_measurement_item(m) for m in measurements]


@router.patch("/{report_id}/measurements/{measurement_id}", response_model=SoilMeasurementItem)
@router.put("/{report_id}/measurements/{measurement_id}", response_model=SoilMeasurementItem)
async def correct_measurement(
    farm_id: uuid.UUID,
    report_id: uuid.UUID,
    measurement_id: uuid.UUID,
    correction: SoilMeasurementCorrectionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit a farmer correction for an individual extracted measurement.
    Preserves original extraction history while updating farmer-reviewed value.
    """
    _get_farm_and_verify_owner(farm_id, current_user, db)

    measurement = db.query(SoilMeasurementModel).filter(
        SoilMeasurementModel.id == str(measurement_id),
        SoilMeasurementModel.report_id == str(report_id),
        SoilMeasurementModel.farm_id == str(farm_id)
    ).first()

    if not measurement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Measurement {measurement_id} not found in report {report_id}"
        )

    # Apply farmer correction
    measurement.farmer_corrected_value = correction.corrected_value
    if correction.corrected_unit:
        measurement.normalized_unit = correction.corrected_unit
    if correction.farmer_notes:
        measurement.farmer_notes = correction.farmer_notes

    measurement.verification_status = MeasurementVerificationStatus.FARMER_CORRECTED.value
    measurement.updated_at = datetime.utcnow()

    # Mark report as partially reviewed if previously needs review
    report = db.query(SoilTestReportModel).filter(SoilTestReportModel.id == str(report_id)).first()
    if report and report.review_status == ReviewStatus.NEEDS_REVIEW.value:
        report.review_status = ReviewStatus.PARTIALLY_REVIEWED.value
        report.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(measurement)

    return _model_to_measurement_item(measurement)


@router.post("/{report_id}/confirm", response_model=SoilReportConfirmResponse)
async def confirm_soil_report(
    farm_id: uuid.UUID,
    report_id: uuid.UUID,
    payload: Optional[SoilReportConfirmRequest] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Farmer confirmation action. Confirms transcribed measurements and transitions
    the report review status to CONFIRMED.
    """
    _get_farm_and_verify_owner(farm_id, current_user, db)

    report = db.query(SoilTestReportModel).filter(
        SoilTestReportModel.id == str(report_id),
        SoilTestReportModel.farm_id == str(farm_id)
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soil report {report_id} not found"
        )

    # Filter measurements to confirm
    query = db.query(SoilMeasurementModel).filter(
        SoilMeasurementModel.report_id == str(report_id),
        SoilMeasurementModel.farm_id == str(farm_id)
    )

    if payload and payload.measurement_ids:
        id_strs = [str(mid) for mid in payload.measurement_ids]
        query = query.filter(SoilMeasurementModel.id.in_(id_strs))

    measurements = query.all()
    now = datetime.utcnow()

    for m in measurements:
        m.verification_status = MeasurementVerificationStatus.FARMER_CONFIRMED.value
        m.updated_at = now

    report.review_status = ReviewStatus.CONFIRMED.value
    report.extraction_status = ExtractionStatus.CONFIRMED.value
    report.confirmed_at = now
    report.reviewed_at = now

    db.commit()

    return SoilReportConfirmResponse(
        report_id=report_id,
        status="confirmed",
        review_status=ReviewStatus.CONFIRMED,
        confirmed_measurement_count=len(measurements),
        confirmed_at=now
    )


@router.post("/{report_id}/reprocess", response_model=SoilReportDetail)
async def reprocess_soil_report(
    farm_id: uuid.UUID,
    report_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger document re-extraction for a report.
    Resets extraction status to PROCESSING and clears unconfirmed measurements.
    """
    _get_farm_and_verify_owner(farm_id, current_user, db)

    report = db.query(SoilTestReportModel).filter(
        SoilTestReportModel.id == str(report_id),
        SoilTestReportModel.farm_id == str(farm_id)
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soil report {report_id} not found"
        )

    # Reset unconfirmed measurements
    db.query(SoilMeasurementModel).filter(
        SoilMeasurementModel.report_id == str(report_id),
        SoilMeasurementModel.verification_status == MeasurementVerificationStatus.EXTRACTED_UNVERIFIED.value
    ).delete(synchronize_session=False)

    report.extraction_error = None
    report.review_status = ReviewStatus.NEEDS_REVIEW.value
    report.updated_at = datetime.utcnow()

    # Re-run extraction pipeline using stored document
    try:
        doc_bytes, mime = soil_report_storage.get_file_bytes(report.storage_path)
        _execute_report_extraction(
            report=report,
            content=doc_bytes,
            filename=report.original_filename,
            content_type=mime or report.mime_type,
            db=db
        )
    except FileNotFoundError:
        # If document file is not present in storage (e.g. test mock), set to PROCESSING
        report.extraction_status = ExtractionStatus.PROCESSING.value

    db.commit()
    db.refresh(report)

    signed_url = soil_report_storage.generate_signed_url(
        storage_path=report.storage_path,
        farm_id=str(farm_id),
        report_id=str(report_id)
    )

    return _model_to_report_detail(report, signed_url)


@router.get("/{report_id}/document")
@router.get("/{report_id}/file")
async def stream_soil_report_document(
    farm_id: uuid.UUID,
    report_id: uuid.UUID,
    redirect: bool = Query(False, description="Redirect to signed cloud storage URL if available"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stream the private soil report document or redirect to a time-limited signed URL.
    Validates farm ownership prior to granting document access.
    """
    _get_farm_and_verify_owner(farm_id, current_user, db)

    report = db.query(SoilTestReportModel).filter(
        SoilTestReportModel.id == str(report_id),
        SoilTestReportModel.farm_id == str(farm_id)
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soil report {report_id} not found"
        )

    if redirect:
        signed_url = soil_report_storage.generate_signed_url(
            storage_path=report.storage_path,
            farm_id=str(farm_id),
            report_id=str(report_id)
        )
        if signed_url.startswith("http"):
            return RedirectResponse(url=signed_url)

    # Stream file bytes directly from private storage / local fallback
    try:
        content, mime_type = soil_report_storage.get_file_bytes(report.storage_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document content not found in private storage"
        )

    return Response(
        content=content,
        media_type=mime_type or report.mime_type or "application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{report.original_filename}"',
            "Cache-Control": "private, max-age=3600"
        }
    )


@router.get("/{report_id}/document-url", response_model=SignedUrlResponse)
async def get_document_signed_url(
    farm_id: uuid.UUID,
    report_id: uuid.UUID,
    expires_in_seconds: int = Query(3600, ge=60, le=86400),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a fresh time-limited signed URL for private document download.
    """
    _get_farm_and_verify_owner(farm_id, current_user, db)

    report = db.query(SoilTestReportModel).filter(
        SoilTestReportModel.id == str(report_id),
        SoilTestReportModel.farm_id == str(farm_id)
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soil report {report_id} not found"
        )

    signed_url = soil_report_storage.generate_signed_url(
        storage_path=report.storage_path,
        farm_id=str(farm_id),
        report_id=str(report_id),
        expires_in_seconds=expires_in_seconds
    )

    return SignedUrlResponse(
        signed_url=signed_url,
        expires_in_seconds=expires_in_seconds
    )
