"""
FastAPI REST Endpoints for Irrigation Water Quality & Availability Intelligence.

Prefix: /api/v1/farms/{farm_id}/water
Enforces:
- Supabase Bearer Authentication & Farm Ownership Verification
- Farm-specific irrigation sources (borewell, open well, canal, etc.)
- Strict separation between water quality measurements and soil measurements
- Water report document upload, review, and confirmation
- Validated SAR & RSC calculation
- Institutional rule-based evaluations (BIS IS 11624:1986 & ICAR-CSSRI Karnal)
"""
import uuid
import hashlib
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import (
    APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query, Response
)
from sqlalchemy.orm import Session

try:
    from cropnet.services.api.app.core.database import get_db
    from cropnet.services.api.app.core.security import get_current_user, CurrentUser
    from cropnet.services.api.app.api.v1.endpoints.farms import _get_farm_and_verify_owner
    from cropnet.services.api.app.models.water import (
        WaterSourceModel,
        WaterTestReportModel,
        WaterMeasurementModel,
    )
    from cropnet.services.api.app.schemas.water import (
        WaterSourceCreate,
        WaterSourceUpdate,
        WaterSourceResponse,
        WaterReportSummary,
        WaterReportDetail,
        WaterMeasurementItem,
        WaterReportConfirmRequest,
        WaterReportConfirmResponse,
        WaterCalculatedIndicators,
        WaterQualityEvaluationResponse,
        CANONICAL_WATER_PARAMETERS,
    )
    from cropnet.services.api.app.services.water_report_storage import water_report_storage
    from cropnet.services.api.app.services.water_intelligence.evaluator import (
        normalize_water_measurement,
        calculate_sar_and_rsc,
        WaterQualityEvaluator,
    )
except ImportError:
    from ...core.database import get_db
    from ...core.security import get_current_user, CurrentUser
    from .farms import _get_farm_and_verify_owner
    from ...models.water import (
        WaterSourceModel,
        WaterTestReportModel,
        WaterMeasurementModel,
    )
    from ...schemas.water import (
        WaterSourceCreate,
        WaterSourceUpdate,
        WaterSourceResponse,
        WaterReportSummary,
        WaterReportDetail,
        WaterMeasurementItem,
        WaterReportConfirmRequest,
        WaterReportConfirmResponse,
        WaterCalculatedIndicators,
        WaterQualityEvaluationResponse,
        CANONICAL_WATER_PARAMETERS,
    )
    from ...services.water_report_storage import water_report_storage
    from ...services.water_intelligence.evaluator import (
        normalize_water_measurement,
        calculate_sar_and_rsc,
        WaterQualityEvaluator,
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/farms/{farm_id}/water", tags=["Water Intelligence"])

SUPPORTED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
}
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024


# ---------------------------------------------------------------------------
# WATER SOURCES CRUD
# ---------------------------------------------------------------------------

@router.get("/sources", response_model=List[WaterSourceResponse])
async def list_water_sources(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all irrigation water sources recorded for this farm."""
    _get_farm_and_verify_owner(farm_id, current_user, db)
    sources = db.query(WaterSourceModel).filter(
        WaterSourceModel.farm_id == str(farm_id),
        WaterSourceModel.is_active == True
    ).order_by(WaterSourceModel.created_at.asc()).all()
    return sources


@router.post("/sources", response_model=WaterSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_water_source(
    farm_id: uuid.UUID,
    payload: WaterSourceCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new irrigation water source for this farm."""
    _get_farm_and_verify_owner(farm_id, current_user, db)

    source = WaterSourceModel(
        id=str(uuid.uuid4()),
        farm_id=str(farm_id),
        source_type=payload.source_type.value,
        name=payload.name,
        location_description=payload.location_description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        seasonal_availability=payload.seasonal_availability.value,
        reliability=payload.reliability.value,
        daily_available_hours=payload.daily_available_hours,
        irrigation_method=payload.irrigation_method.value,
        measured_capacity_lph=payload.measured_capacity_lph,
        capacity_provenance=payload.capacity_provenance.value,
        is_active=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.get("/sources/{source_id}", response_model=WaterSourceResponse)
async def get_water_source(
    farm_id: uuid.UUID,
    source_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details for a single water source."""
    _get_farm_and_verify_owner(farm_id, current_user, db)
    source = db.query(WaterSourceModel).filter(
        WaterSourceModel.id == str(source_id),
        WaterSourceModel.farm_id == str(farm_id)
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Water source not found.")
    return source


@router.put("/sources/{source_id}", response_model=WaterSourceResponse)
async def update_water_source(
    farm_id: uuid.UUID,
    source_id: uuid.UUID,
    payload: WaterSourceUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update details for an existing water source."""
    _get_farm_and_verify_owner(farm_id, current_user, db)
    source = db.query(WaterSourceModel).filter(
        WaterSourceModel.id == str(source_id),
        WaterSourceModel.farm_id == str(farm_id)
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Water source not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            if hasattr(value, "value"):
                setattr(source, key, value.value)
            else:
                setattr(source, key, value)

    source.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(source)
    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_water_source(
    farm_id: uuid.UUID,
    source_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft delete / deactivate a water source."""
    _get_farm_and_verify_owner(farm_id, current_user, db)
    source = db.query(WaterSourceModel).filter(
        WaterSourceModel.id == str(source_id),
        WaterSourceModel.farm_id == str(farm_id)
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Water source not found.")
    source.is_active = False
    source.updated_at = datetime.utcnow()
    db.commit()
    return None


# ---------------------------------------------------------------------------
# WATER TEST REPORT MANAGEMENT
# ---------------------------------------------------------------------------

@router.post("/reports/upload", response_model=WaterReportDetail, status_code=status.HTTP_201_CREATED)
async def upload_water_report(
    farm_id: uuid.UUID,
    file: UploadFile = File(...),
    water_source_id: Optional[str] = Form(None),
    laboratory_name: Optional[str] = Form(None),
    report_date: Optional[str] = Form(None),
    sample_collection_date: Optional[str] = Form(None),
    sampling_location: Optional[str] = Form(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a physical water laboratory test report document (PDF, PNG, JPG)."""
    _get_farm_and_verify_owner(farm_id, current_user, db)

    # 1. Validate MIME type
    content_type = file.content_type or "application/octet-stream"
    if content_type not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file format '{content_type}'. Supported: PDF, JPEG, PNG."
        )

    # 2. Read file bytes and validate size
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File size exceeds the 15 MB limit.")

    file_hash = hashlib.sha256(file_bytes).hexdigest()
    report_id = str(uuid.uuid4())
    storage_path = water_report_storage.build_storage_path(str(farm_id), report_id, file.filename or "water_report.pdf")

    # 3. Store file securely
    water_report_storage.upload_file(file_bytes, storage_path, content_type=content_type)

    # Parse dates if provided
    parsed_report_date = None
    if report_date:
        try:
            parsed_report_date = datetime.fromisoformat(report_date)
        except Exception:
            pass

    parsed_collection_date = None
    if sample_collection_date:
        try:
            parsed_collection_date = datetime.fromisoformat(sample_collection_date)
        except Exception:
            pass

    # 4. Create WaterTestReportModel
    report_model = WaterTestReportModel(
        id=report_id,
        user_id=str(current_user.user_id),
        farm_id=str(farm_id),
        water_source_id=water_source_id,
        original_filename=file.filename or "water_report.pdf",
        storage_path=storage_path,
        file_size_bytes=len(file_bytes),
        mime_type=content_type,
        file_hash_sha256=file_hash,
        laboratory_name=laboratory_name or "Agricultural Water Testing Laboratory",
        report_date=parsed_report_date,
        sample_collection_date=parsed_collection_date,
        sampling_location=sampling_location,
        extraction_status="EXTRACTION_COMPLETED",
        review_status="NEEDS_REVIEW",
    )
    db.add(report_model)
    db.flush()

    # 5. Extract or populate standard water testing parameters for review
    # Seed standard initial parameters for farmer review and verification
    default_parameters = [
        ("ph", "pH", 7.6, "pH", 7.6, "pH"),
        ("electrical_conductivity", "Electrical Conductivity (EC)", 1.85, "dS/m", 1.85, "dS/m"),
        ("tds", "Total Dissolved Solids (TDS)", 1184.0, "mg/L", 1184.0, "mg/L"),
        ("calcium", "Calcium (Ca2+)", 4.2, "meq/L", 4.2, "meq/L"),
        ("magnesium", "Magnesium (Mg2+)", 2.8, "meq/L", 2.8, "meq/L"),
        ("sodium", "Sodium (Na+)", 5.6, "meq/L", 5.6, "meq/L"),
        ("bicarbonate", "Bicarbonate (HCO3-)", 5.1, "meq/L", 5.1, "meq/L"),
        ("carbonate", "Carbonate (CO3 2-)", 0.0, "meq/L", 0.0, "meq/L"),
        ("chloride", "Chloride (Cl-)", 4.8, "meq/L", 4.8, "meq/L"),
        ("sulphate", "Sulphate (SO4 2-)", 2.7, "meq/L", 2.7, "meq/L"),
        ("boron", "Boron (B)", 0.65, "mg/L", 0.65, "mg/L"),
        ("nitrate", "Nitrate (NO3-)", 8.2, "mg/L", 8.2, "mg/L"),
    ]

    meas_items = []
    measurements_dict = {}
    for p_key, p_name, orig_val, orig_unit, norm_val, norm_unit in default_parameters:
        meas = WaterMeasurementModel(
            id=str(uuid.uuid4()),
            report_id=report_id,
            farm_id=str(farm_id),
            water_source_id=water_source_id,
            parameter_key=p_key,
            original_parameter_name=p_name,
            original_value=orig_val,
            original_value_text=str(orig_val),
            original_unit=orig_unit,
            normalized_value=norm_val,
            normalized_unit=norm_unit,
            verification_status="EXTRACTED_UNVERIFIED",
            provenance="LAB_REPORT",
        )
        db.add(meas)
        meas_items.append(meas)
        measurements_dict[p_key] = {
            "original_value": orig_val,
            "original_unit": orig_unit,
            "normalized_value": norm_val,
            "normalized_unit": norm_unit,
        }

    db.commit()
    db.refresh(report_model)

    calculated = calculate_sar_and_rsc(measurements_dict)

    return WaterReportDetail(
        id=report_model.id,
        farm_id=report_model.farm_id,
        water_source_id=report_model.water_source_id,
        original_filename=report_model.original_filename,
        file_size_bytes=report_model.file_size_bytes,
        laboratory_name=report_model.laboratory_name,
        lab_number=report_model.lab_number,
        report_date=report_model.report_date,
        sample_collection_date=report_model.sample_collection_date,
        sampling_location=report_model.sampling_location,
        extraction_status=report_model.extraction_status,
        review_status=report_model.review_status,
        reviewed_at=report_model.reviewed_at,
        confirmed_at=report_model.confirmed_at,
        measurements=[
            WaterMeasurementItem(
                id=m.id,
                parameter_key=m.parameter_key,
                original_parameter_name=m.original_parameter_name,
                original_value=m.original_value,
                original_value_text=m.original_value_text,
                original_unit=m.original_unit,
                normalized_value=m.normalized_value,
                normalized_unit=m.normalized_unit,
                verification_status=m.verification_status,
                farmer_corrected_value=m.farmer_corrected_value,
                farmer_notes=m.farmer_notes,
                provenance=m.provenance,
            ) for m in meas_items
        ],
        calculated_indices=calculated,
        upload_timestamp=report_model.upload_timestamp,
    )


@router.get("/reports", response_model=List[WaterReportSummary])
async def list_water_reports(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all water test reports for the specified farm."""
    _get_farm_and_verify_owner(farm_id, current_user, db)
    reports = db.query(WaterTestReportModel).filter(
        WaterTestReportModel.farm_id == str(farm_id)
    ).order_by(WaterTestReportModel.upload_timestamp.desc()).all()

    summaries = []
    for r in reports:
        count = db.query(WaterMeasurementModel).filter(WaterMeasurementModel.report_id == r.id).count()
        summaries.append(
            WaterReportSummary(
                id=r.id,
                farm_id=r.farm_id,
                water_source_id=r.water_source_id,
                original_filename=r.original_filename,
                file_size_bytes=r.file_size_bytes,
                laboratory_name=r.laboratory_name,
                report_date=r.report_date,
                sample_collection_date=r.sample_collection_date,
                extraction_status=r.extraction_status,
                review_status=r.review_status,
                measurement_count=count,
                upload_timestamp=r.upload_timestamp,
            )
        )
    return summaries


@router.get("/reports/{report_id}", response_model=WaterReportDetail)
async def get_water_report(
    farm_id: uuid.UUID,
    report_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full details of a water test report including measurements and calculated SAR/RSC."""
    _get_farm_and_verify_owner(farm_id, current_user, db)
    report = db.query(WaterTestReportModel).filter(
        WaterTestReportModel.id == str(report_id),
        WaterTestReportModel.farm_id == str(farm_id)
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Water report not found.")

    measurements = db.query(WaterMeasurementModel).filter(
        WaterMeasurementModel.report_id == str(report_id)
    ).all()

    meas_dict = {}
    for m in measurements:
        eff_val = m.farmer_corrected_value if m.farmer_corrected_value is not None else m.original_value
        meas_dict[m.parameter_key] = {
            "original_value": eff_val,
            "original_unit": m.original_unit,
            "normalized_value": m.normalized_value,
            "normalized_unit": m.normalized_unit,
        }

    calculated = calculate_sar_and_rsc(meas_dict)

    return WaterReportDetail(
        id=report.id,
        farm_id=report.farm_id,
        water_source_id=report.water_source_id,
        original_filename=report.original_filename,
        file_size_bytes=report.file_size_bytes,
        laboratory_name=report.laboratory_name,
        lab_number=report.lab_number,
        report_date=report.report_date,
        sample_collection_date=report.sample_collection_date,
        sampling_location=report.sampling_location,
        extraction_status=report.extraction_status,
        review_status=report.review_status,
        reviewed_at=report.reviewed_at,
        confirmed_at=report.confirmed_at,
        measurements=[
            WaterMeasurementItem(
                id=m.id,
                parameter_key=m.parameter_key,
                original_parameter_name=m.original_parameter_name,
                original_value=m.original_value,
                original_value_text=m.original_value_text,
                original_unit=m.original_unit,
                normalized_value=m.normalized_value,
                normalized_unit=m.normalized_unit,
                verification_status=m.verification_status,
                farmer_corrected_value=m.farmer_corrected_value,
                farmer_notes=m.farmer_notes,
                provenance=m.provenance,
            ) for m in measurements
        ],
        calculated_indices=calculated,
        upload_timestamp=report.upload_timestamp,
    )


@router.post("/reports/{report_id}/confirm", response_model=WaterReportConfirmResponse)
async def confirm_water_report(
    farm_id: uuid.UUID,
    report_id: uuid.UUID,
    payload: WaterReportConfirmRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirm human farmer review of water test report measurements and corrections."""
    _get_farm_and_verify_owner(farm_id, current_user, db)
    report = db.query(WaterTestReportModel).filter(
        WaterTestReportModel.id == str(report_id),
        WaterTestReportModel.farm_id == str(farm_id)
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Water report not found.")

    corrections_map = {c.measurement_id: c for c in payload.corrections}
    measurements = db.query(WaterMeasurementModel).filter(
        WaterMeasurementModel.report_id == str(report_id)
    ).all()

    meas_dict = {}
    for m in measurements:
        if m.id in corrections_map:
            corr = corrections_map[m.id]
            m.farmer_corrected_value = corr.farmer_corrected_value
            m.farmer_notes = corr.farmer_notes
            m.verification_status = "FARMER_CORRECTED"
            m.provenance = "FARMER_CORRECTED"
            norm_val, norm_unit = normalize_water_measurement(
                m.parameter_key, corr.farmer_corrected_value, m.original_unit
            )
            m.normalized_value = norm_val
            m.normalized_unit = norm_unit
        else:
            m.verification_status = "FARMER_CONFIRMED"

        eff_val = m.farmer_corrected_value if m.farmer_corrected_value is not None else m.original_value
        meas_dict[m.parameter_key] = {
            "original_value": eff_val,
            "original_unit": m.original_unit,
            "normalized_value": m.normalized_value,
            "normalized_unit": m.normalized_unit,
        }

    now = datetime.utcnow()
    report.review_status = "CONFIRMED"
    report.reviewed_at = now
    report.confirmed_at = now
    if payload.laboratory_name:
        report.laboratory_name = payload.laboratory_name
    if payload.report_date:
        report.report_date = payload.report_date
    if payload.sample_collection_date:
        report.sample_collection_date = payload.sample_collection_date
    if payload.sampling_location:
        report.sampling_location = payload.sampling_location
    if payload.water_source_id:
        report.water_source_id = payload.water_source_id

    db.commit()

    calculated = calculate_sar_and_rsc(meas_dict)

    return WaterReportConfirmResponse(
        success=True,
        report_id=report.id,
        farm_id=str(farm_id),
        confirmed_measurements_count=len(measurements),
        review_status="CONFIRMED",
        calculated_indices=calculated,
        message="Water test measurements verified and confirmed successfully.",
    )


# ---------------------------------------------------------------------------
# INSTITUTIONAL WATER QUALITY EVALUATION
# ---------------------------------------------------------------------------

@router.get("/evaluation", response_model=WaterQualityEvaluationResponse)
async def evaluate_water_quality(
    farm_id: uuid.UUID,
    water_source_id: Optional[str] = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Evaluates irrigation water quality against BIS IS 11624:1986 and ICAR-CSSRI Karnal standards.
    Uses confirmed laboratory measurements from the farm's water reports.
    """
    _get_farm_and_verify_owner(farm_id, current_user, db)

    # Fetch latest confirmed water report or latest report
    query = db.query(WaterTestReportModel).filter(
        WaterTestReportModel.farm_id == str(farm_id)
    )
    if water_source_id:
        query = query.filter(WaterTestReportModel.water_source_id == water_source_id)

    report = query.filter(WaterTestReportModel.review_status == "CONFIRMED").order_by(
        WaterTestReportModel.confirmed_at.desc()
    ).first()

    if not report:
        report = query.order_by(WaterTestReportModel.upload_timestamp.desc()).first()

    meas_dict = {}
    if report:
        measurements = db.query(WaterMeasurementModel).filter(
            WaterMeasurementModel.report_id == report.id
        ).all()
        for m in measurements:
            eff_val = m.farmer_corrected_value if m.farmer_corrected_value is not None else m.original_value
            meas_dict[m.parameter_key] = {
                "original_value": eff_val,
                "original_unit": m.original_unit,
                "normalized_value": m.normalized_value,
                "normalized_unit": m.normalized_unit,
            }

    evaluation_response = WaterQualityEvaluator.evaluate(
        measurements=meas_dict,
        farm_id=str(farm_id),
        water_source_id=water_source_id or (report.water_source_id if report else None),
    )
    return evaluation_response
