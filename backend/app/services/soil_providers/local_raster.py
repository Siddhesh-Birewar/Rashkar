import os
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

class LocalRasterProvider(SoilDataProvider):
    """
    Provider for locally cached, pre-downloaded, or offline GeoTIFF rasters.
    Useful for field pilots in low-bandwidth regions and offline development.
    """

    def __init__(self, raster_dir: str = "./data_cache/rasters"):
        self.raster_dir = raster_dir

    def get_capabilities(self) -> ProviderCapability:
        files = []
        if os.path.exists(self.raster_dir):
            files = [f for f in os.listdir(self.raster_dir) if f.endswith(('.tif', '.tiff'))]
        return ProviderCapability(
            provider_name="CropNet Local Raster Cache",
            dataset_version="local_cache_v1",
            spatial_resolution_or_scale="Variable (Source Resolution)",
            supported_depth_intervals=["0-5cm", "0-30cm"],
            vintage_year=2026,
            licensing="Internal Cached Derivatives for CropNet AI Pilot",
            attribution_statement="Cached geospatial soil rasters for offline operation",
            is_operational=len(files) > 0,
            status_message=f"Local raster cache contains {len(files)} raster files." if files else "Local cache empty.",
            available_properties=[os.path.splitext(f)[0] for f in files],
            provides_uncertainty=False,
            requires_credentials=False
        )

    def check_coverage(self, polygon: Polygon) -> Dict[str, Any]:
        if not os.path.exists(self.raster_dir):
            return {"has_coverage": False, "files_count": 0}
        files = [f for f in os.listdir(self.raster_dir) if f.endswith(('.tif', '.tiff'))]
        return {"has_coverage": len(files) > 0, "files_count": len(files)}

    def extract_farm_soil(
        self,
        polygon: Polygon,
        requested_properties: Optional[List[str]] = None
    ) -> Dict[str, SoilParameterObservation]:
        return {}
