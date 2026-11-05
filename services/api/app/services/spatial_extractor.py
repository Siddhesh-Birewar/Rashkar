import uuid
import logging
from typing import Dict, Any, Optional
from shapely.geometry import Polygon
from pyproj import Geod

from cropnet.services.api.app.schemas.soil import (
    UnifiedSoilProfile,
    SoilParameterObservation,
    VerificationStatus,
    ParameterAvailability
)
from cropnet.services.api.app.services.soil_providers.soilgrids import SoilGridsProvider
from cropnet.services.api.app.services.soil_providers.openlandmap import OpenLandMapProvider
from cropnet.services.api.app.services.soil_providers.natmo import NATMOProvider
from cropnet.services.api.app.services.soil_providers.bhoomi import BhoomiProvider
from cropnet.services.api.app.services.soil_providers.local_raster import LocalRasterProvider

logger = logging.getLogger(__name__)

# WGS84 Geodesic for precise metric area calculation
geod = Geod(ellps="WGS84")


def calculate_polygon_area(polygon: Polygon) -> Dict[str, float]:
    """
    Calculate geodesic area of polygon in square meters, hectares, and acres.
    Never calculates area directly from latitude/longitude degrees.
    """
    poly_area, _ = geod.geometry_area_perimeter(polygon)
    area_sq_m = abs(poly_area)
    hectares = area_sq_m / 10000.0
    acres = hectares * 2.47105
    return {
        "square_meters": round(area_sq_m, 2),
        "hectares": round(hectares, 3),
        "acres": round(acres, 3)
    }


class SpatialSoilService:
    """
    Orchestration service for farm-level spatial extraction and Unified Soil Profile creation.
    """

    def __init__(self):
        self.soilgrids_provider = SoilGridsProvider()
        self.openlandmap_provider = OpenLandMapProvider()
        self.bhoomi_provider = BhoomiProvider()
        self.natmo_provider = NATMOProvider()
        self.local_provider = LocalRasterProvider()

    def generate_farm_soil_profile(
        self,
        farm_id: str,
        polygon: Polygon,
        taluka: Optional[str] = None
    ) -> UnifiedSoilProfile:
        """
        Extract soil properties from approved providers and generate UnifiedSoilProfile.
        """
        profile_id = str(uuid.uuid4())
        logger.info("Generating soil profile %s for farm %s", profile_id, farm_id)

        # 1. Primary Extraction via SoilGrids WCS
        sg_extracted = self.soilgrids_provider.extract_farm_soil(polygon)

        # 2. Strict Scientific Parameter Mapping
        ph_obs = sg_extracted.get("ph")
        soc_obs = sg_extracted.get("soc")
        sand_obs = sg_extracted.get("sand_percent")
        silt_obs = sg_extracted.get("silt_percent")
        clay_obs = sg_extracted.get("clay_percent")
        total_n_obs = sg_extracted.get("total_nitrogen")
        cec_obs = sg_extracted.get("cation_exchange_capacity")

        # 3. Available NPK MUST NOT be fabricated. Mark strictly as NOT_AVAILABLE.
        avail_n_obs = SoilParameterObservation(
            parameter_key="available_nitrogen",
            display_name="Available Mineral Nitrogen (N)",
            value=None,
            unit="kg/ha",
            source="None (Unverified)",
            dataset_version="N/A",
            depth_interval="0-15cm",
            spatial_resolution="N/A",
            verification_status=VerificationStatus.NOT_AVAILABLE,
            availability_status=ParameterAvailability.NOT_AVAILABLE,
            farm_coverage_percent=0.0,
            scientific_note="Available nitrogen cannot be derived from global satellite rasters without physical laboratory testing. Total Nitrogen is NOT available nitrogen."
        )

        avail_p_obs = SoilParameterObservation(
            parameter_key="available_phosphorus",
            display_name="Available Phosphorus (P2O5)",
            value=None,
            unit="kg/ha",
            source="None (Unverified)",
            dataset_version="N/A",
            depth_interval="0-15cm",
            spatial_resolution="N/A",
            verification_status=VerificationStatus.NOT_AVAILABLE,
            availability_status=ParameterAvailability.NOT_AVAILABLE,
            farm_coverage_percent=0.0,
            scientific_note="Available phosphorus is not provided by approved public rasters and must not be inferred."
        )

        avail_k_obs = SoilParameterObservation(
            parameter_key="available_potassium",
            display_name="Available Potassium (K2O)",
            value=None,
            unit="kg/ha",
            source="None (Unverified)",
            dataset_version="N/A",
            depth_interval="0-15cm",
            spatial_resolution="N/A",
            verification_status=VerificationStatus.NOT_AVAILABLE,
            availability_status=ParameterAvailability.NOT_AVAILABLE,
            farm_coverage_percent=0.0,
            scientific_note="Available potassium is not provided by approved public rasters and must not be inferred."
        )

        # Count completeness across primary physical & chemical parameters
        primary_params = [ph_obs, soc_obs, sand_obs, silt_obs, clay_obs, total_n_obs, cec_obs]
        total_count = len(primary_params) + 3 # including N, P, K
        available_count = sum(1 for p in primary_params if p and p.value is not None)
        completeness_ratio = round(available_count / total_count, 2)

        return UnifiedSoilProfile(
            profile_id=profile_id,
            farm_id=farm_id,
            taluka=taluka,
            district="Pune",
            state="Maharashtra",
            is_map_derived=True,
            disclaimer=(
                "This soil profile is an estimate derived from geospatial soil models (ISRIC SoilGrids 2.0). "
                "It is NOT a physical laboratory soil test. Map-derived estimates provide regional and spatial guidance "
                "and must not be treated as exact chemical lab measurements."
            ),
            ph=ph_obs,
            organic_carbon=soc_obs,
            sand_percent=sand_obs,
            silt_percent=silt_obs,
            clay_percent=clay_obs,
            total_nitrogen=total_n_obs,
            cation_exchange_capacity=cec_obs,
            available_nitrogen=avail_n_obs,
            available_phosphorus=avail_p_obs,
            available_potassium=avail_k_obs,
            total_requested_parameters=total_count,
            available_parameters_count=available_count,
            data_completeness_ratio=completeness_ratio
        )
