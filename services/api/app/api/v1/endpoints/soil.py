import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from shapely.geometry import Polygon
from pydantic import BaseModel

from cropnet.services.api.app.schemas.soil import UnifiedSoilProfile
from cropnet.services.api.app.schemas.farm import GeoJSONPolygonGeometry
from cropnet.services.api.app.core.security import get_current_user, CurrentUser
from cropnet.services.api.app.services.spatial_extractor import SpatialSoilService
from cropnet.services.api.app.services.soil_providers.base import ProviderCapability
from cropnet.services.api.app.services.soil_providers.soilgrids import SoilGridsProvider
from cropnet.services.api.app.services.soil_providers.openlandmap import OpenLandMapProvider
from cropnet.services.api.app.services.soil_providers.natmo import NATMOProvider
from cropnet.services.api.app.services.soil_providers.bhoomi import BhoomiProvider
from cropnet.services.api.app.services.soil_providers.local_raster import LocalRasterProvider
from cropnet.services.api.app.api.v1.endpoints.farms import _FARM_STORAGE

router = APIRouter()
spatial_service = SpatialSoilService()


class PolygonSoilExtractRequest(BaseModel):
    geometry: GeoJSONPolygonGeometry
    taluka: str = "Baramati"


@router.get("/providers", response_model=List[ProviderCapability])
async def list_providers():
    """
    List all supported soil data providers and their independent capabilities:
    - Available properties
    - Dataset version
    - Spatial resolution / scale
    - Depth intervals
    - Vintage
    - Licensing & attribution
    - Uncertainty availability
    """
    providers = [
        SoilGridsProvider(),
        OpenLandMapProvider(),
        NATMOProvider(),
        BhoomiProvider(),
        LocalRasterProvider()
    ]
    return [p.get_capabilities() for p in providers]


@router.get("/pilot-coverage")
async def get_pilot_coverage_matrix() -> Dict[str, Any]:
    """
    Verified pilot coverage matrix for Maharashtra pilot regions:
    Maval, Mulshi, Baramati, Indapur.
    """
    return {
        "pilot_regions": [
            {
                "taluka": "Maval",
                "center_coords": {"lat": 18.76, "lon": 73.68},
                "soil_group": "Western Ghats High Rainfall Clay Loam / Red Lateritic Gravelly",
                "soilgrids_coverage": "Full 250m coverage (pH 6.5, SOC 19.4 g/kg, Clay 37.9%, Sand 31.1%)",
                "openlandmap_coverage": "Available at 30m resolution",
                "bhoomi_status": "Blocked (HTTP 403 Forbidden - Institutional Credentials Required)",
                "natmo_status": "Unavailable (HTTP 500 & WMS Display Only)",
                "available_npk_status": "NOT AVAILABLE (Preserved as null in schema)"
            },
            {
                "taluka": "Mulshi",
                "center_coords": {"lat": 18.53, "lon": 73.61},
                "soil_group": "Western Ghats Heavy Rainfall Humid High-Organic Clay",
                "soilgrids_coverage": "Full 250m coverage (pH 6.4, SOC 23.5 g/kg, Clay 40.9%, Sand 29.7%)",
                "openlandmap_coverage": "Available at 30m resolution",
                "bhoomi_status": "Blocked (HTTP 403 Forbidden - Institutional Credentials Required)",
                "natmo_status": "Unavailable (HTTP 500 & WMS Display Only)",
                "available_npk_status": "NOT AVAILABLE (Preserved as null in schema)"
            },
            {
                "taluka": "Baramati",
                "center_coords": {"lat": 18.18, "lon": 74.53},
                "soil_group": "Deccan Plateau Deep Black Vertisol (Smectite / Montmorillonitic)",
                "soilgrids_coverage": "Full 250m coverage in agricultural belt (pH 7.3, SOC 15.4 g/kg, Clay 42.3%, CEC 38.2 cmol/kg)",
                "openlandmap_coverage": "Available at 30m resolution",
                "bhoomi_status": "Blocked (HTTP 403 Forbidden - Institutional Credentials Required)",
                "natmo_status": "Unavailable (HTTP 500 & WMS Display Only)",
                "available_npk_status": "NOT AVAILABLE (Preserved as null in schema)"
            },
            {
                "taluka": "Indapur",
                "center_coords": {"lat": 18.15, "lon": 75.05},
                "soil_group": "Rain Shadow Deccan Medium to Deep Black Vertisol",
                "soilgrids_coverage": "Full 250m coverage (pH 7.1, SOC 24.2 g/kg, Clay 44.6%, CEC 26.6 cmol/kg)",
                "openlandmap_coverage": "Available at 30m resolution",
                "bhoomi_status": "Blocked (HTTP 403 Forbidden - Institutional Credentials Required)",
                "natmo_status": "Unavailable (HTTP 500 & WMS Display Only)",
                "available_npk_status": "NOT AVAILABLE (Preserved as null in schema)"
            }
        ]
    }


@router.post("/farms/{farm_id}/profile", response_model=UnifiedSoilProfile)
async def generate_soil_profile_for_farm(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Generate unified soil profile snapshot for a registered farm.
    Validates farm ownership before extracting geospatial data.
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

    coords = farm["geometry"]["coordinates"][0]
    poly = Polygon(coords)
    profile = spatial_service.generate_farm_soil_profile(
        farm_id=str(farm_id),
        polygon=poly,
        taluka=farm.get("taluka")
    )
    return profile


@router.post("/extract-polygon", response_model=UnifiedSoilProfile)
async def extract_ad_hoc_polygon(
    payload: PolygonSoilExtractRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Directly extract soil intelligence for an ad-hoc polygon.
    """
    coords = payload.geometry.coordinates[0]
    poly = Polygon(coords)
    adhoc_id = f"adhoc-{uuid.uuid4()}"
    profile = spatial_service.generate_farm_soil_profile(
        farm_id=adhoc_id,
        polygon=poly,
        taluka=payload.taluka
    )
    return profile
