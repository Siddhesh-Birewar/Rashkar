import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from shapely.geometry import Polygon
from pydantic import BaseModel

from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.models.soil_and_farm import FarmModel

from cropnet.services.api.app.schemas.soil import UnifiedSoilProfile, SoilLayerInfo
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


@router.get("/layers", response_model=List[SoilLayerInfo])
async def list_soil_layers():
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
            scientific_note="Soil pH measured in H2O solution. Calibrated using digital soil mapping ensembles."
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
            parameter_key="sand_percent",
            display_name="Sand Fraction",
            unit="%",
            source="ISRIC SoilGrids 2.0",
            dataset_version="2.0.0",
            spatial_resolution="250m",
            supported_depth_intervals=["0-5cm", "5-15cm"],
            is_derived=False,
            scientific_note="Particle size 50 - 2000 um."
        ),
        SoilLayerInfo(
            parameter_key="silt_percent",
            display_name="Silt Fraction",
            unit="%",
            source="ISRIC SoilGrids 2.0",
            dataset_version="2.0.0",
            spatial_resolution="250m",
            supported_depth_intervals=["0-5cm", "5-15cm"],
            is_derived=False,
            scientific_note="Particle size 2 - 50 um."
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
            scientific_note="Particle size < 2 um."
        ),
        SoilLayerInfo(
            parameter_key="soil_texture_class",
            display_name="USDA Soil Texture Class",
            unit="class",
            source="Derived via USDA Triangle",
            dataset_version="2.0.0",
            spatial_resolution="250m",
            supported_depth_intervals=["0-5cm", "5-15cm"],
            is_derived=True,
            scientific_note="Derived deterministically from Sand, Silt, and Clay fractions."
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
            scientific_note="IMPORTANT: Total Nitrogen is NOT available mineral nitrogen (NH4+/NO3-)."
        ),
        SoilLayerInfo(
            parameter_key="cation_exchange_capacity",
            display_name="Cation Exchange Capacity (CEC)",
            unit="cmol(c)/kg",
            source="ISRIC SoilGrids 2.0",
            dataset_version="2.0.0",
            spatial_resolution="250m",
            supported_depth_intervals=["0-5cm", "5-15cm"],
            is_derived=False,
            scientific_note="CEC of fine earth fraction at pH 7."
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
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate unified soil profile snapshot for a registered farm.
    Validates farm ownership before extracting geospatial data.
    """
    farm = _FARM_STORAGE.get(farm_id)
    if not farm:
        db_farm = db.query(FarmModel).filter(FarmModel.id == str(farm_id)).first()
        if db_farm:
            farm = {
                "owner_id": uuid.UUID(db_farm.owner_id),
                "geometry": db_farm.geometry_geojson,
                "taluka": db_farm.taluka
            }
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
        taluka=farm.get("taluka"),
        depth="0-5cm",
        farm_area_hectares=farm.get("calculated_area_hectares")
    )
    spatial_service.save_profile(db, profile)
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


class SoilReportStatusResponse(BaseModel):
    job_id: str
    report_id: str
    farm_id: Optional[str] = None
    status: str
    review_status: Optional[str] = None
    extraction_error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@router.get("/report-status/{job_id}", response_model=SoilReportStatusResponse)
def get_soil_report_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[CurrentUser] = Depends(get_current_user)
):
    """
    Poll the background OCR extraction status of an uploaded soil report.
    Returns status: PROCESSING, NEEDS_REVIEW, CONFIRMED, or FAILED.
    """
    from cropnet.services.api.app.models.soil_reports import SoilTestReportModel

    report = db.query(SoilTestReportModel).filter(SoilTestReportModel.id == job_id).first()
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Soil report job '{job_id}' not found."
        )

    if current_user and report.user_id and str(report.user_id) != str(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this report status."
        )

    return SoilReportStatusResponse(
        job_id=report.id,
        report_id=report.id,
        farm_id=report.farm_id,
        status=report.extraction_status,
        review_status=report.review_status,
        extraction_error=report.extraction_error,
        created_at=report.upload_timestamp.isoformat() if report.upload_timestamp else None,
        updated_at=report.updated_at.isoformat() if getattr(report, "updated_at", None) else None,
    )
