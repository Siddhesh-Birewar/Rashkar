"""Farm context, ownership enforcement, and crop-cycle lifecycle adapter."""

from typing import Any, Dict, List, Optional, Union
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

try:
    from cropnet.services.api.app.api.v1.endpoints.farms import (
        _get_farm_and_verify_owner,
        compute_farm_representative_point,
    )
    from cropnet.services.api.app.core.security import CurrentUser
except ImportError:
    from app.api.v1.endpoints.farms import (
        _get_farm_and_verify_owner,
        compute_farm_representative_point,
    )
    from app.core.security import CurrentUser

from ..models import (
    RashkarAdvisoryCatalogueModel,
    RashkarAgronomicThresholdModel,
    RashkarCanonicalCropModel,
    RashkarCropCycleModel,
    RashkarCropStageModel,
    RashkarIncomeOpportunityModel,
)
from ..schemas.context import (
    RashkarCropCycleCreate,
    RashkarCropCycleUpdate,
    RashkarFarmContext,
)
from ..seed import seed_rashkar_reference_data
from ..timezone import now_utc_naive


def ensure_rashkar_seeded(db: Session) -> None:
    """Fast idempotent check ensuring RASHKAR reference tables are seeded."""
    needs_seed = (
        db.query(RashkarCanonicalCropModel.crop_code).first() is None
        or db.query(RashkarCropStageModel.id).first() is None
        or db.query(RashkarAgronomicThresholdModel.id).first() is None
        or db.query(RashkarAdvisoryCatalogueModel.advisory_id).first() is None
        or db.query(RashkarIncomeOpportunityModel.opportunity_id).first() is None
    )
    if needs_seed:
        seed_rashkar_reference_data(db)


def _parse_farm_uuid(farm_id: Union[uuid.UUID, str]) -> uuid.UUID:
    """Validate and coerce a farm identifier to UUID."""
    if isinstance(farm_id, uuid.UUID):
        return farm_id
    try:
        return uuid.UUID(str(farm_id))
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid farm_id UUID format: '{farm_id}'",
        ) from exc


def resolve_owned_farm_context(
    farm_id: Union[uuid.UUID, str],
    current_user: CurrentUser,
    db: Session,
) -> Dict[str, Any]:
    """Resolve canonical CropNet farm context and strictly verify caller ownership."""
    farm_uuid = _parse_farm_uuid(farm_id)
    farm = _get_farm_and_verify_owner(farm_uuid, current_user, db)

    lat = farm.get("centroid_latitude")
    lon = farm.get("centroid_longitude")

    if lat is None or lon is None:
        geometry = farm.get("geometry")
        if not geometry:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Farm coordinates are missing and farm geometry is unavailable.",
            )
        try:
            lat, lon = compute_farm_representative_point(geometry)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unable to derive farm coordinates from geometry: {exc}",
            ) from exc

    if lat is None or lon is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Farm coordinates are missing.",
        )

    ctx = RashkarFarmContext(
        farm_id=str(farm["id"]),
        owner_id=str(farm["owner_id"]),
        farm_name=str(farm.get("name") or "Registered Farm"),
        district=farm.get("district"),
        taluka=farm.get("taluka"),
        village=farm.get("village"),
        state=farm.get("state") or "Maharashtra",
        latitude=float(lat),
        longitude=float(lon),
        elevation_m=farm.get("elevation_m"),
        total_area_acres=farm.get("calculated_area_acres"),
        irrigation_type=farm.get("irrigation_type"),
        water_source=farm.get("water_source"),
    )
    return ctx.model_dump()


def get_active_crop_cycle(
    farm_id: str, db: Session
) -> Optional[RashkarCropCycleModel]:
    """Return the latest active crop cycle for the farm, or None (never fabricates a crop)."""
    return (
        db.query(RashkarCropCycleModel)
        .filter(
            RashkarCropCycleModel.farm_id == str(farm_id),
            RashkarCropCycleModel.is_active == True,  # noqa: E712
        )
        .order_by(
            RashkarCropCycleModel.updated_at_utc.desc(),
            RashkarCropCycleModel.created_at_utc.desc(),
        )
        .first()
    )


def list_crop_cycles(farm_id: str, db: Session) -> List[RashkarCropCycleModel]:
    """List all crop cycles registered for a farm, active cycles first."""
    return (
        db.query(RashkarCropCycleModel)
        .filter(RashkarCropCycleModel.farm_id == str(farm_id))
        .order_by(
            RashkarCropCycleModel.is_active.desc(),
            RashkarCropCycleModel.updated_at_utc.desc(),
            RashkarCropCycleModel.created_at_utc.desc(),
        )
        .all()
    )


def upsert_active_crop_cycle(
    farm_id: str,
    owner_id: str,
    payload: RashkarCropCycleCreate,
    db: Session,
) -> RashkarCropCycleModel:
    """Create a crop cycle for a farm, deactivating any prior active cycle when active."""
    crop_code = payload.crop_code.strip().lower()
    if not crop_code:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="crop_code cannot be blank.",
        )

    now = now_utc_naive()
    if payload.is_active:
        db.query(RashkarCropCycleModel).filter(
            RashkarCropCycleModel.farm_id == str(farm_id),
            RashkarCropCycleModel.is_active == True,  # noqa: E712
        ).update(
            {"is_active": False, "updated_at_utc": now},
            synchronize_session=False,
        )

    stage_source = payload.stage_source or "estimated_from_das"
    stage_confidence = payload.stage_confidence
    if payload.current_stage_code and stage_source == "estimated_from_das" and stage_confidence is None:
        stage_source = "farmer_confirmed"
        stage_confidence = 1.0

    cycle = RashkarCropCycleModel(
        id=str(uuid.uuid4()),
        farm_id=str(farm_id),
        owner_id=str(owner_id),
        crop_code=crop_code,
        variety_name=payload.variety_name,
        sowing_date=payload.sowing_date,
        season=payload.season,
        planted_area_acres=payload.planted_area_acres,
        irrigation_type=payload.irrigation_type,
        current_stage_code=payload.current_stage_code,
        stage_source=stage_source,
        stage_confidence=stage_confidence,
        is_active=payload.is_active,
        created_at_utc=now,
        updated_at_utc=now,
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle


def update_crop_cycle(
    farm_id: str,
    cycle_id: str,
    payload: RashkarCropCycleUpdate,
    db: Session,
) -> RashkarCropCycleModel:
    """Update an existing crop cycle belonging to the specified farm."""
    cycle = (
        db.query(RashkarCropCycleModel)
        .filter(
            RashkarCropCycleModel.id == str(cycle_id),
            RashkarCropCycleModel.farm_id == str(farm_id),
        )
        .first()
    )
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop cycle '{cycle_id}' not found for farm '{farm_id}'.",
        )

    updates = payload.model_dump(exclude_unset=True)
    now = now_utc_naive()

    if updates.get("is_active") is True:
        db.query(RashkarCropCycleModel).filter(
            RashkarCropCycleModel.farm_id == str(farm_id),
            RashkarCropCycleModel.id != str(cycle_id),
            RashkarCropCycleModel.is_active == True,  # noqa: E712
        ).update(
            {"is_active": False, "updated_at_utc": now},
            synchronize_session=False,
        )

    if "current_stage_code" in updates and updates["current_stage_code"] is not None:
        if "stage_source" not in updates:
            updates["stage_source"] = "farmer_confirmed"
        if "stage_confidence" not in updates:
            updates["stage_confidence"] = 1.0

    for field, value in updates.items():
        setattr(cycle, field, value)

    cycle.updated_at_utc = now
    db.commit()
    db.refresh(cycle)
    return cycle


def confirm_crop_stage(
    farm_id: str,
    stage_code: str,
    db: Session,
    cycle_id: Optional[str] = None,
) -> RashkarCropCycleModel:
    """Persist farmer-confirmed growth stage on the active (or specified) crop cycle."""
    clean_stage = (stage_code or "").strip()
    if not clean_stage:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="stage_code cannot be blank.",
        )

    if cycle_id:
        cycle = (
            db.query(RashkarCropCycleModel)
            .filter(
                RashkarCropCycleModel.id == str(cycle_id),
                RashkarCropCycleModel.farm_id == str(farm_id),
            )
            .first()
        )
    else:
        cycle = get_active_crop_cycle(farm_id, db)

    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active crop cycle found for this farm.",
        )

    cycle.current_stage_code = clean_stage
    cycle.stage_source = "farmer_confirmed"
    cycle.stage_confidence = 1.0
    cycle.updated_at_utc = now_utc_naive()
    db.commit()
    db.refresh(cycle)
    return cycle


__all__ = [
    "ensure_rashkar_seeded",
    "resolve_owned_farm_context",
    "get_active_crop_cycle",
    "list_crop_cycles",
    "upsert_active_crop_cycle",
    "update_crop_cycle",
    "confirm_crop_stage",
]
