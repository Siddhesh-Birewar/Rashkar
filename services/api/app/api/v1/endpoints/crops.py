from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session

from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.schemas.crop import (
    CropCatalogSummaryResponse,
    CropFullProfileResponse,
    CropSoilRequirementsResponse,
    CropClimateRequirementsResponse,
    CropWaterRequirementsResponse,
    CropSeasonRequirementResponse,
    AgriculturalKnowledgeSourceResponse
)
from cropnet.services.api.app.services.crop_knowledge.crop_service import CropKnowledgeService

router = APIRouter()
crop_service = CropKnowledgeService()


@router.get("", response_model=List[CropCatalogSummaryResponse])
async def list_crops(
    response: Response,
    category: Optional[str] = Query(None, description="Filter by crop category (e.g. 'Cereal', 'Cash Crop', 'Pulse', 'Oilseed', 'Fiber', 'Horticulture')"),
    season: Optional[str] = Query(None, description="Filter by season (e.g. 'Kharif', 'Rabi', 'Zaid', 'Summer', 'Adsali')"),
    db: Session = Depends(get_db)
):
    """
    List all crops in the Agricultural Knowledge Base.
    Supports filtering by crop category and agricultural cropping season.
    """
    crops = crop_service.get_all_crops(db=db, category=category, season=season)
    is_degraded = any(c.degraded_mode for c in crops) if crops else False
    response.headers["X-CropNet-Degraded-Mode"] = "true" if is_degraded else "false"
    response.headers["X-CropNet-Data-Source"] = "cache_degraded" if is_degraded else "database"
    return crops


@router.get("/{crop_id}", response_model=CropFullProfileResponse)
async def get_crop_profile(
    crop_id: str,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Retrieve comprehensive agricultural profile for a crop including soil, climate,
    season, water requirements, regional suitability, and scientific sources.
    """
    profile = crop_service.get_crop_profile(crop_id, db=db)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop '{crop_id}' not found in Agricultural Knowledge Base"
        )
    response.headers["X-CropNet-Degraded-Mode"] = "true" if profile.degraded_mode else "false"
    response.headers["X-CropNet-Data-Source"] = profile.data_source_mode
    if profile.degraded_warning:
        response.headers["X-CropNet-Degraded-Warning"] = profile.degraded_warning
    return profile


@router.get("/{crop_id}/requirements")
async def get_crop_requirements(
    crop_id: str,
    response: Response,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Retrieve modular requirement packages (soil, climate, seasons, water) for a crop.
    """
    profile = crop_service.get_crop_profile(crop_id, db=db)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop '{crop_id}' not found"
        )
    response.headers["X-CropNet-Degraded-Mode"] = "true" if profile.degraded_mode else "false"
    response.headers["X-CropNet-Data-Source"] = profile.data_source_mode
    return {
        "crop_id": profile.id,
        "common_name": profile.common_name,
        "scientific_name": profile.scientific_name,
        "degraded_mode": profile.degraded_mode,
        "data_source_mode": profile.data_source_mode,
        "degraded_warning": profile.degraded_warning,
        "soil": profile.soil,
        "climate": profile.climate,
        "seasons": profile.seasons,
        "water": profile.water,
        "regional_suitability": profile.regional_suitability
    }


@router.get("/{crop_id}/sources", response_model=List[AgriculturalKnowledgeSourceResponse])
async def get_crop_sources(
    crop_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve all authoritative institutional and university scientific publications
    cited for this crop's requirements.
    """
    profile = crop_service.get_crop_profile(crop_id, db=db)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crop '{crop_id}' not found"
        )
    return profile.sources


@router.post("/seed", status_code=status.HTTP_200_OK)
async def seed_agricultural_knowledge_base(
    db: Session = Depends(get_db)
):
    """
    Seed or refresh the 10 initial crop profiles and MPKV/ICAR source citations.
    """
    count = crop_service.seed_knowledge_base(db)
    return {
        "status": "success",
        "message": f"Successfully seeded {count} crops into Agricultural Knowledge Base"
    }
