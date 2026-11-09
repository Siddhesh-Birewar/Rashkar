import os
import logging
from typing import List, Dict, Optional, Any
import numpy as np
import rasterio
from rasterio.mask import mask
from shapely.geometry import Polygon, mapping

from cropnet.services.api.app.services.soil_providers.base import SoilDataProvider, ProviderCapability
from cropnet.services.api.app.schemas.soil import (
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
        """
        Extract from local GeoTIFF files matching property names in self.raster_dir.
        """
        extracted: Dict[str, SoilParameterObservation] = {}
        if not os.path.exists(self.raster_dir):
            return extracted

        bounds = polygon.bounds
        for fname in os.listdir(self.raster_dir):
            if not fname.endswith(('.tif', '.tiff')):
                continue
            prop_key = os.path.splitext(fname)[0]
            if requested_properties and prop_key not in requested_properties:
                continue

            file_path = os.path.join(self.raster_dir, fname)
            try:
                with rasterio.open(file_path) as src:
                    out_image, _ = mask(src, [mapping(polygon)], crop=True, nodata=-9999)
                    valid_pixels = out_image[(out_image > 0) & (out_image < 30000)]
                    if len(valid_pixels) > 0:
                        mean_val = float(np.mean(valid_pixels))
                        extracted[prop_key] = SoilParameterObservation(
                            parameter_key=prop_key,
                            display_name=prop_key.replace("_", " ").title(),
                            value=round(mean_val, 2),
                            unit="value",
                            source="Local Raster Cache",
                            dataset_version="v1.0",
                            depth_interval="0-5cm",
                            spatial_resolution=f"{round(src.res[0], 5)} deg",
                            vintage_year=2026,
                            verification_status=VerificationStatus.MAP_DERIVED_ESTIMATE,
                            availability_status=ParameterAvailability.AVAILABLE,
                            farm_coverage_percent=100.0,
                            scientific_note="Extracted from locally cached regional raster."
                        )
            except Exception as e:
                logger.error("Error reading local raster %s: %s", fname, e)

        return extracted
