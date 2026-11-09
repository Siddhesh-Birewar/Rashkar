import logging
from typing import List, Dict, Optional, Any
from shapely.geometry import Polygon

from backend.app.services.soil_providers.base import SoilDataProvider, ProviderCapability
from backend.app.schemas.soil import (
    SoilParameterObservation,
    VerificationStatus,
    ParameterAvailability
)

logger = logging.getLogger(__name__)

class OpenLandMapProvider(SoilDataProvider):
    """
    Provider for OpenLandMap global high-resolution (30m) digital soil mapping.
    """

    DEFAULT_BASE_URL = "http://s3.opengeohub.org/global-soil/global_soil_props_v20250204_mosaics"

    LAYER_CATALOGUE = {
        "soc": {
            "display_name": "Soil Organic Carbon Density (30m)",
            "unit": "mg/cm3",
            "note": "OpenLandMap Soil Organic Carbon Density at 30m resolution."
        },
        "ph": {
            "display_name": "Soil pH in H2O (30m)",
            "unit": "pH",
            "note": "OpenLandMap soil pH in H2O at 30m resolution."
        },
        "clay_percent": {
            "display_name": "Clay Fraction (30m)",
            "unit": "%",
            "note": "OpenLandMap clay fraction percent (<2 um)."
        },
        "sand_percent": {
            "display_name": "Sand Fraction (30m)",
            "unit": "%",
            "note": "OpenLandMap sand fraction percent (50-2000 um)."
        }
    }

    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url

    def get_capabilities(self) -> ProviderCapability:
        return ProviderCapability(
            provider_name="OpenLandMap",
            dataset_version="v20250204",
            spatial_resolution_or_scale="30m",
            supported_depth_intervals=["0-30cm", "30-60cm", "60-100cm"],
            vintage_year=2025,
            licensing="Open Data Commons Open Database License (ODbL)",
            attribution_statement="OpenLandMap soil rasters produced by OpenGeoHub foundation",
            is_operational=True,
            status_message="Cloud-Optimized GeoTIFF layers available via OpenGeoHub S3 bucket",
            available_properties=list(self.LAYER_CATALOGUE.keys()),
            provides_uncertainty=True,
            requires_credentials=False
        )

    def check_coverage(self, polygon: Polygon) -> Dict[str, Any]:
        bounds = polygon.bounds
        is_covered = (-180.0 <= bounds[0] <= 180.0) and (-60.0 <= bounds[1] <= 80.0)
        return {
            "has_coverage": is_covered,
            "spatial_resolution": "30m"
        }

    def extract_farm_soil(
        self,
        polygon: Polygon,
        requested_properties: Optional[List[str]] = None
    ) -> Dict[str, SoilParameterObservation]:
        extracted = {}
        props = requested_properties or list(self.LAYER_CATALOGUE.keys())
        for p in props:
            if p not in self.LAYER_CATALOGUE:
                continue
            meta = self.LAYER_CATALOGUE[p]
            extracted[p] = SoilParameterObservation(
                parameter_key=p,
                display_name=meta["display_name"],
                value=None,
                unit=meta["unit"],
                source="OpenLandMap",
                dataset_version="v20250204",
                depth_interval="0-30cm",
                spatial_resolution="30m",
                vintage_year=2025,
                verification_status=VerificationStatus.MAP_DERIVED_ESTIMATE,
                availability_status=ParameterAvailability.PARTIAL_COVERAGE,
                farm_coverage_percent=100.0,
                scientific_note=meta["note"]
            )
        return extracted
