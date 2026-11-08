"""
CropNet AI — Phase 5.9A Farm Health Snapshot Endpoint.

Strictly conforms to: docs/architecture/farm_health_snapshot_contract.md
Mounts: GET /api/v1/farms/{farm_id}/health-snapshot
Enforces:
- Farm ownership authorization via _get_farm_and_verify_owner (401/403/404)
- Fast cached responses via 5-minute TTL cache (<= 250ms)
- Cache invalidation via force_refresh=true
- Domain fault isolation & zero universal health score
"""
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from cropnet.services.api.app.core.security import get_current_user, CurrentUser
from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.api.v1.endpoints.farms import _get_farm_and_verify_owner
from cropnet.services.api.app.schemas.farm_health import FarmHealthSnapshotResponse
from cropnet.services.api.app.services.farm_health.aggregator import FarmHealthAggregator
from cropnet.services.api.app.services.farm_health.cache import invalidate_snapshot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/farms", tags=["Farm Health"])
aggregator = FarmHealthAggregator()


@router.get(
    "/{farm_id}/health-snapshot",
    response_model=FarmHealthSnapshotResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve unified multi-domain farm health snapshot",
    description=(
        "Assembles a unified farm health snapshot combining Soil, Water, Satellite Sentinel-2, "
        "Weather, and Crop context intelligence with explicit data availability states, freshness, "
        "and provenance. Strictly enforces farm ownership. Computes zero universal health score."
    ),
)
async def get_farm_health_snapshot(
    farm_id: uuid.UUID,
    force_refresh: bool = Query(
        default=False,
        description="When true, bypasses the 5-minute cache and re-collects fresh observations across all domains."
    ),
    target_season: Optional[str] = Query(
        default=None,
        description="Agricultural season filter for crop evaluation context (e.g. 'Rabi 2026-27')."
    ),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FarmHealthSnapshotResponse:
    """
    Unified Farm Health Snapshot endpoint conforming to Phase 5.9A Contract Specification.
    """
    farm = _get_farm_and_verify_owner(farm_id, current_user, db)

    snapshot = aggregator.get_snapshot(
        farm=farm,
        db=db,
        force_refresh=force_refresh,
        target_season=target_season,
    )
    return snapshot


@router.post(
    "/{farm_id}/health-snapshot/invalidate",
    status_code=status.HTTP_200_OK,
    summary="Invalidate cached farm health snapshot",
    description="Manually evicts cached snapshot entry for the farm parcel.",
)
async def invalidate_farm_health_snapshot(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Invalidates snapshot cache for a farm parcel.
    """
    _get_farm_and_verify_owner(farm_id, current_user, db)
    evicted = invalidate_snapshot(str(farm_id))
    return {
        "success": True,
        "farm_id": str(farm_id),
        "cache_evicted": evicted,
        "message": "Farm health snapshot cache invalidated successfully."
    }
