import uuid
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from shapely.geometry import Polygon

from cropnet.services.api.app.schemas.farm import FarmCreate, FarmUpdate, FarmResponse
from cropnet.services.api.app.core.security import get_current_user, CurrentUser
from cropnet.services.api.app.services.spatial_extractor import calculate_polygon_area

router = APIRouter()

# In-memory store for Phase 0 / Phase 1 verification (keyed by farm_id)
# Demonstrates strict multi-user tenant isolation
_FARM_STORAGE: dict[uuid.UUID, dict] = {}


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    payload: FarmCreate,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Register a new farm with validated GeoJSON polygon boundary.
    Calculates geodesic area in metric hectares and acres.
    Enforces user ownership.
    """
    farm_id = uuid.uuid4()
    now = datetime.utcnow()

    # Calculate geodesic area
    poly = Polygon(payload.geometry.coordinates[0])
    area_dict = calculate_polygon_area(poly)

    farm_data = {
        "id": farm_id,
        "owner_id": current_user.user_id,
        "name": payload.name,
        "village": payload.village,
        "taluka": payload.taluka,
        "district": payload.district,
        "state": payload.state,
        "irrigation_type": payload.irrigation_type,
        "water_source": payload.water_source,
        "geometry": payload.geometry.model_dump(),
        "calculated_area_hectares": area_dict["hectares"],
        "calculated_area_acres": area_dict["acres"],
        "created_at": now,
        "updated_at": now
    }
    _FARM_STORAGE[farm_id] = farm_data
    return FarmResponse(**farm_data)


@router.get("", response_model=List[FarmResponse])
async def list_farms(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    List all farms belonging to the authenticated user.
    Strictly isolated: users cannot see other users' farms.
    """
    user_farms = [
        f for f in _FARM_STORAGE.values()
        if f["owner_id"] == current_user.user_id
    ]
    return [FarmResponse(**f) for f in user_farms]


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get farm by ID. Enforces ownership check.
    """
    farm = _FARM_STORAGE.get(farm_id)
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm {farm_id} not found"
        )
    if farm["owner_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this farm"
        )
    return FarmResponse(**farm)
