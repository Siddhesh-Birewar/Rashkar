from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.farm import FarmModel
from backend.app.schemas.soil import (
    UnifiedSoilProfile,
    CropNetSoilCardResponse,
    SoilLayerInfo
)
from backend.app.services.soil_providers.base import ProviderCapability
from backend.app.services.soil_providers.soilgrids import SoilGridsProvider
from backend.app.services.soil_providers.openlandmap import OpenLandMapProvider
from backend.app.services.soil_providers.local_raster import LocalRasterProvider
from backend.app.services.cropnet_spatial_service import SpatialSoilService

router = APIRouter()
spatial_service = SpatialSoilService()

@router.get("/providers", response_model=List[ProviderCapability])
def list_providers():
    """
    List supported soil data providers and their independent capabilities.
    """
    providers = [
        SoilGridsProvider(),
        OpenLandMapProvider(),
        LocalRasterProvider()
    ]
    return [p.get_capabilities() for p in providers]

@router.get("/layers", response_model=List[SoilLayerInfo])
def list_soil_layers():
    """
    Metadata catalogue of all operational and derived soil layers.
    Includes resolution, supported depth intervals, units, and scientific restrictions.
    """
    return [
        SoilLayerInfo(
            parameter_key="ph",
            display_name="Soil pH (H2O)",
            unit="pH",
            source="ISRIC SoilGrids 2.0",
            dataset_version="2.0.0",
            spatial_resolution="250m",
            supported_depth_intervals=["0-5cm", "5-15cm"],
            is_derived=False,
            scientific_note="Soil pH measured in H2O solution."
        ),
        SoilLayerInfo(
            parameter_key="soc",
            display_name="Soil Organic Carbon",
            unit="g/kg",
            source="ISRIC SoilGrids 2.0",
            dataset_version="2.0.0",
            spatial_resolution="250m",
            supported_depth_intervals=["0-5cm", "5-15cm"],
            is_derived=False,
            scientific_note="Mass fraction of organic carbon in fine earth."
        ),
        SoilLayerInfo(
            parameter_key="clay_percent",
            display_name="Clay Fraction",
            unit="%",
            source="ISRIC SoilGrids 2.0",
            dataset_version="2.0.0",
            spatial_resolution="250m",
            supported_depth_intervals=["0-5cm", "5-15cm"],
            is_derived=False,
            scientific_note="Particles < 2 um. Essential for moisture retention."
        ),
        SoilLayerInfo(
            parameter_key="total_nitrogen",
            display_name="Total Nitrogen",
            unit="g/kg",
            source="ISRIC SoilGrids 2.0",
            dataset_version="2.0.0",
            spatial_resolution="250m",
            supported_depth_intervals=["0-5cm", "5-15cm"],
            is_derived=False,
            scientific_note="Total Nitrogen is NOT available mineral nitrogen (NH4+/NO3-)."
        ),
        SoilLayerInfo(
            parameter_key="available_nitrogen",
            display_name="Available Mineral Nitrogen (N)",
            unit="kg/ha",
            source="None (Physical Test Required)",
            dataset_version="N/A",
            spatial_resolution="N/A",
            supported_depth_intervals=["0-15cm"],
            is_derived=False,
            scientific_note="NOT AVAILABLE from digital rasters. Requires laboratory soil testing."
        ),
        SoilLayerInfo(
            parameter_key="available_phosphorus",
            display_name="Available Phosphorus (P2O5)",
            unit="kg/ha",
            source="None (Physical Test Required)",
            dataset_version="N/A",
            spatial_resolution="N/A",
            supported_depth_intervals=["0-15cm"],
            is_derived=False,
            scientific_note="NOT AVAILABLE from digital rasters. Requires laboratory soil testing."
        ),
        SoilLayerInfo(
            parameter_key="available_potassium",
            display_name="Available Potassium (K2O)",
            unit="kg/ha",
            source="None (Physical Test Required)",
            dataset_version="N/A",
            spatial_resolution="N/A",
            supported_depth_intervals=["0-15cm"],
            is_derived=False,
            scientific_note="NOT AVAILABLE from digital rasters. Requires laboratory soil testing."
        )
    ]

@router.get("/farms/{farm_id}/profile", response_model=UnifiedSoilProfile)
def get_farm_soil_profile(
    farm_id: str,
    x_farmer_id: Optional[str] = Header(None, alias="X-Farmer-Id"),
    db: Session = Depends(get_db)
):
    """
    Retrieve or generate canonical UnifiedSoilProfile for a registered farm.
    Enforces multi-tenant ownership check: returns 403 Forbidden if requester is not owner.
    """
    farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm '{farm_id}' not found"
        )

    # Multi-tenant owner isolation
    if x_farmer_id and farm.owner_id != x_farmer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this farm"
        )

    return spatial_service.get_or_create_farm_profile(db=db, farm_id=farm_id)

@router.get("/farms/{farm_id}/card", response_model=CropNetSoilCardResponse)
def get_farm_soil_card(
    farm_id: str,
    db: Session = Depends(get_db)
):
    """
    Get lightweight, farmer-friendly soil intelligence card for UI display.
    """
    farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
    farm_name = farm.farm_name if farm else "Demo Farm"
    village = farm.village if farm else None
    taluka = farm.taluka if farm else "Baramati"
    district = farm.district if farm else "Pune"

    profile = spatial_service.get_or_create_farm_profile(db=db, farm_id=farm_id)
    return spatial_service.to_soil_card_response(
        profile=profile,
        farm_name=farm_name,
        village=village,
        taluka=taluka,
        district=district
    )

@router.post("/farms/{farm_id}/refresh", response_model=UnifiedSoilProfile)
def refresh_farm_soil_profile(
    farm_id: str,
    x_farmer_id: Optional[str] = Header(None, alias="X-Farmer-Id"),
    db: Session = Depends(get_db)
):
    """
    Forces fresh spatial extraction from SoilGrids, invalidating the cache.
    """
    farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    if x_farmer_id and farm.owner_id != x_farmer_id:
        raise HTTPException(status_code=403, detail="You do not have permission to access this farm")

    return spatial_service.get_or_create_farm_profile(db=db, farm_id=farm_id, force_refresh=True)
