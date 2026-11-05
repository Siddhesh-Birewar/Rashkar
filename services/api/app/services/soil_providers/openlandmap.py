import logging
import os
from typing import List, Dict, Optional, Any
import numpy as np
from shapely.geometry import Polygon
import rasterio
from rasterio.windows import from_bounds

from cropnet.services.api.app.services.soil_providers.base import SoilDataProvider, ProviderCapability
from cropnet.services.api.app.schemas.soil import (
    SoilParameterObservation,
    VerificationStatus,
    ParameterAvailability
)

logger = logging.getLogger(__name__)


class OpenLandMapProvider(SoilDataProvider):
    """
    Provider for OpenLandMap global high-resolution (30m) digital soil mapping.
    Data is hosted as Cloud-Optimized GeoTIFFs (COGs) via OpenGeoHub S3 / Wasabi.
    """

    DEFAULT_BASE_URL = "http://s3.opengeohub.org/global-soil/global_soil_props_v20250204_mosaics"

    LAYER_CATALOGUE = {
        "soc": {
            "file_template": "oc_iso.10694.1995.mg.cm3_m_30m_{depth}_20150101_20201231_g_epsg.4326_v20250204.tif",
            "p16_template": "oc_iso.10694.1995.mg.cm3_p16_120m_{depth}_20150101_20201231_g_epsg.4326_v20250204.tif",
            "p84_template": "oc_iso.10694.1995.mg.cm3_p84_120m_{depth}_20150101_20201231_g_epsg.4326_v20250204.tif",
            "display_name": "Soil Organic Carbon Density (30m)",
            "unit": "mg/cm3",
            "scale_factor": 1.0,
            "note": "OpenLandMap Soil Organic Carbon Density at 30m resolution predicted using Quantile Regression Random Forests."
        },
        "ph": {
            "file_template": "ph.h2o_usda.a483_m_30m_{depth}_20150101_20201231_g_epsg.4326_v20250204.tif",
            "display_name": "Soil pH in H2O (30m)",
            "unit": "pH",
            "scale_factor": 1.0,
            "note": "OpenLandMap soil pH in H2O at 30m resolution."
        },
        "clay_percent": {
            "file_template": "clay.wrb_usda.c1_m_30m_{depth}_20150101_20201231_g_epsg.4326_v20250204.tif",
            "display_name": "Clay Fraction (30m)",
            "unit": "%",
            "scale_factor": 1.0,
            "note": "OpenLandMap clay fraction percent (<2 um)."
        },
        "sand_percent": {
            "file_template": "sand.wrb_usda.c1_m_30m_{depth}_20150101_20201231_g_epsg.4326_v20250204.tif",
            "display_name": "Sand Fraction (30m)",
            "unit": "%",
            "scale_factor": 1.0,
            "note": "OpenLandMap sand fraction percent (50-2000 um)."
        }
    }

    DEPTH_MAPPING = {
        "0-5cm": "b0cm..30cm",
        "0-30cm": "b0cm..30cm",
        "30-60cm": "b30cm..60cm",
        "60-100cm": "b60cm..100cm"
    }

    def __init__(self, base_url: str = DEFAULT_BASE_URL, local_cache_dir: Optional[str] = None):
        self.base_url = base_url
        self.local_cache_dir = local_cache_dir

    def get_capabilities(self) -> ProviderCapability:
        return ProviderCapability(
            provider_name="OpenLandMap",
            dataset_version="v20250204",
            spatial_resolution_or_scale="30m",
            supported_depth_intervals=["0-30cm", "30-60cm", "60-100cm"],
            vintage_year=2022,
            licensing="Creative Commons Attribution 4.0 International (CC BY 4.0)",
            attribution_statement="Soil data derived from OpenLandMap (OpenGeoHub Foundation, Zenodo DOI: 10.5281/zenodo.15470431)",
            is_operational=True,
            status_message="Cloud-Optimized GeoTIFFs hosted on OpenGeoHub Wasabi S3; remote HTTP range access supported with local regional caching recommended for production latency.",
            available_properties=list(self.LAYER_CATALOGUE.keys()),
            provides_uncertainty=True,
            requires_credentials=False
        )

    def check_coverage(self, polygon: Polygon) -> Dict[str, Any]:
        bounds = polygon.bounds
        is_covered = (-180.0 <= bounds[0] <= 180.0) and (-60.0 <= bounds[1] <= 84.0)
        return {
            "has_coverage": is_covered,
            "coverage_type": "global_30m_spatiotemporal_model",
            "spatial_resolution": "30m"
        }

    def extract_farm_soil(
        self,
        polygon: Polygon,
        requested_properties: Optional[List[str]] = None,
        depth: str = "0-30cm"
    ) -> Dict[str, SoilParameterObservation]:
        """
        Extract 30m soil properties from OpenLandMap COG or local regional mirror.
        """
        properties_to_query = requested_properties or list(self.LAYER_CATALOGUE.keys())
        extracted_observations: Dict[str, SoilParameterObservation] = {}
        depth_tag = self.DEPTH_MAPPING.get(depth, "b0cm..30cm")

        # Configure GDAL environment for remote COG streaming
        os.environ["GDAL_DISABLE_READDIR_ON_OPEN"] = "EMPTY_DIR"
        os.environ["CPL_VSIL_CURL_ALLOWED_EXTENSIONS"] = ".tif"

        for prop_key in properties_to_query:
            if prop_key not in self.LAYER_CATALOGUE:
                continue
            meta = self.LAYER_CATALOGUE[prop_key]
            filename = meta["file_template"].format(depth=depth_tag)
            remote_url = f"/vsicurl/{self.base_url}/{filename}"

            # Check if cached locally first
            local_path = os.path.join(self.local_cache_dir, filename) if self.local_cache_dir else None
            target_path = local_path if (local_path and os.path.exists(local_path)) else remote_url

            try:
                # Open with small timeout window
                with rasterio.open(target_path) as src:
                    bounds = polygon.bounds
                    window = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], src.transform)
                    data = src.read(1, window=window)
                    valid_data = data[data > 0]

                    if len(valid_data) > 0:
                        mean_val = float(np.mean(valid_data)) * meta["scale_factor"]
                        extracted_observations[prop_key] = SoilParameterObservation(
                            parameter_key=prop_key,
                            display_name=meta["display_name"],
                            value=round(mean_val, 2),
                            unit=meta["unit"],
                            source="OpenLandMap",
                            dataset_version="v20250204",
                            depth_interval=depth,
                            spatial_resolution="30m",
                            vintage_year=2022,
                            verification_status=VerificationStatus.MAP_DERIVED_ESTIMATE,
                            availability_status=ParameterAvailability.AVAILABLE,
                            farm_coverage_percent=100.0,
                            scientific_note=meta["note"]
                        )
                    else:
                        extracted_observations[prop_key] = SoilParameterObservation(
                            parameter_key=prop_key,
                            display_name=meta["display_name"],
                            value=None,
                            unit=meta["unit"],
                            source="OpenLandMap",
                            dataset_version="v20250204",
                            depth_interval=depth,
                            spatial_resolution="30m",
                            vintage_year=2022,
                            verification_status=VerificationStatus.MAP_DERIVED_ESTIMATE,
                            availability_status=ParameterAvailability.NOT_AVAILABLE,
                            farm_coverage_percent=0.0,
                            scientific_note="No valid 30m pixels returned for polygon window."
                        )
            except Exception as e:
                logger.warning("OpenLandMap extraction failed or timed out for %s: %s", prop_key, e)
                extracted_observations[prop_key] = SoilParameterObservation(
                    parameter_key=prop_key,
                    display_name=meta["display_name"],
                    value=None,
                    unit=meta["unit"],
                    source="OpenLandMap",
                    dataset_version="v20250204",
                    depth_interval=depth,
                    spatial_resolution="30m",
                    vintage_year=2022,
                    verification_status=VerificationStatus.MAP_DERIVED_ESTIMATE,
                    availability_status=ParameterAvailability.SOURCE_UNAVAILABLE,
                    farm_coverage_percent=0.0,
                    scientific_note=f"Remote COG range request unavailable or timed out: {str(e)}"
                )

        return extracted_observations
