import io
import logging
from typing import List, Dict, Optional, Any
import requests
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


class SoilGridsProvider(SoilDataProvider):
    """
    Provider for ISRIC SoilGrids 2.0 global digital soil mapping.
    Queries OGC Web Coverage Service (WCS 2.0.1) endpoints directly.
    """

    DEFAULT_BASE_URL = "https://maps.isric.org/mapserv"

    LAYER_CATALOGUE = {
        "ph": {
            "map_name": "phh2o",
            "layer_template": "phh2o_{depth}_mean",
            "uncertainty_template": "phh2o_{depth}_uncertainty",
            "display_name": "Soil pH (H2O)",
            "unit": "pH",
            "scale_factor": 10.0,
            "note": "Soil pH in H2O. Divide raw pixel value by 10."
        },
        "soc": {
            "map_name": "soc",
            "layer_template": "soc_{depth}_mean",
            "uncertainty_template": "soc_{depth}_uncertainty",
            "display_name": "Soil Organic Carbon Content",
            "unit": "g/kg",
            "scale_factor": 10.0,
            "note": "Soil Organic Carbon content. Divide raw pixel value by 10 to obtain g/kg."
        },
        "sand_percent": {
            "map_name": "sand",
            "layer_template": "sand_{depth}_mean",
            "uncertainty_template": "sand_{depth}_uncertainty",
            "display_name": "Sand Fraction",
            "unit": "%",
            "scale_factor": 10.0,
            "note": "Sand fraction (50-2000 um). Divide raw pixel value by 10 to obtain %."
        },
        "silt_percent": {
            "map_name": "silt",
            "layer_template": "silt_{depth}_mean",
            "uncertainty_template": "silt_{depth}_uncertainty",
            "display_name": "Silt Fraction",
            "unit": "%",
            "scale_factor": 10.0,
            "note": "Silt fraction (2-50 um). Divide raw pixel value by 10 to obtain %."
        },
        "clay_percent": {
            "map_name": "clay",
            "layer_template": "clay_{depth}_mean",
            "uncertainty_template": "clay_{depth}_uncertainty",
            "display_name": "Clay Fraction",
            "unit": "%",
            "scale_factor": 10.0,
            "note": "Clay fraction (<2 um). Divide raw pixel value by 10 to obtain %."
        },
        "total_nitrogen": {
            "map_name": "nitrogen",
            "layer_template": "nitrogen_{depth}_mean",
            "uncertainty_template": "nitrogen_{depth}_uncertainty",
            "display_name": "Total Nitrogen",
            "unit": "g/kg",
            "scale_factor": 100.0,
            "note": "IMPORTANT SCIENTIFIC NOTICE: SoilGrids total nitrogen is the sum of all organic and mineral nitrogen. It is NOT available mineral nitrogen (NH4/NO3) and cannot be directly compared to fertilizer requirements or Soil Health Card thresholds."
        },
        "cation_exchange_capacity": {
            "map_name": "cec",
            "layer_template": "cec_{depth}_mean",
            "uncertainty_template": "cec_{depth}_uncertainty",
            "display_name": "Cation Exchange Capacity (at pH 7)",
            "unit": "cmol(c)/kg",
            "scale_factor": 10.0,
            "note": "Cation exchange capacity of the fine earth fraction at pH 7. Divide by 10 to obtain cmol(c)/kg."
        }
    }

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: int = 25):
        self.base_url = base_url
        self.timeout = timeout

    def get_capabilities(self) -> ProviderCapability:
        return ProviderCapability(
            provider_name="ISRIC SoilGrids",
            dataset_version="2.0.0",
            spatial_resolution_or_scale="250m",
            supported_depth_intervals=["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm", "100-200cm"],
            vintage_year=2020,
            licensing="Creative Commons Attribution 4.0 International (CC BY 4.0)",
            attribution_statement="Soil data derived from SoilGrids 2.0 (ISRIC — World Soil Information, https://soilgrids.org)",
            is_operational=True,
            status_message="Operational via OGC WCS 2.0.1 endpoints on maps.isric.org",
            available_properties=list(self.LAYER_CATALOGUE.keys()),
            provides_uncertainty=True,
            requires_credentials=False
        )

    def check_coverage(self, polygon: Polygon) -> Dict[str, Any]:
        bounds = polygon.bounds
        # SoilGrids has global land coverage (lat -60 to +84)
        is_covered = (-180.0 <= bounds[0] <= 180.0) and (-60.0 <= bounds[1] <= 84.0)
        return {
            "has_coverage": is_covered,
            "coverage_type": "global_land_model",
            "spatial_resolution": "250m"
        }

    def _fetch_wcs_geotiff(self, map_name: str, coverage_id: str, bounds: tuple, padding: float = 0.005) -> Optional[bytes]:
        """
        Request cropped GeoTIFF from SoilGrids WCS 2.0.1.
        """
        minx, miny, maxx, maxy = bounds[0] - padding, bounds[1] - padding, bounds[2] + padding, bounds[3] + padding
        url = (
            f"{self.base_url}?map=/map/{map_name}.map"
            f"&SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage"
            f"&COVERAGEID={coverage_id}"
            f"&SUBSET=Long({minx:.5f},{maxx:.5f})"
            f"&SUBSET=Lat({miny:.5f},{maxy:.5f})"
            f"&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/4326"
            f"&OUTPUTCRS=http://www.opengis.net/def/crs/EPSG/0/4326"
        )
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code == 200 and resp.content:
                return resp.content
            logger.warning("SoilGrids WCS returned status %d for %s", resp.status_code, coverage_id)
            return None
        except Exception as e:
            logger.error("Failed to fetch SoilGrids WCS coverage %s: %s", coverage_id, e)
            return None

    def extract_farm_soil(
        self,
        polygon: Polygon,
        requested_properties: Optional[List[str]] = None,
        depth: str = "0-5cm"
    ) -> Dict[str, SoilParameterObservation]:
        """
        Extract raster soil attributes for the farm polygon using zonal statistics.
        """
        properties_to_query = requested_properties or list(self.LAYER_CATALOGUE.keys())
        extracted_observations: Dict[str, SoilParameterObservation] = {}
        bounds = polygon.bounds

        for prop_key in properties_to_query:
            if prop_key not in self.LAYER_CATALOGUE:
                continue
            meta = self.LAYER_CATALOGUE[prop_key]
            coverage_id = meta["layer_template"].format(depth=depth)
            unc_coverage_id = meta["uncertainty_template"].format(depth=depth)

            # Query mean layer
            mean_bytes = self._fetch_wcs_geotiff(meta["map_name"], coverage_id, bounds)
            if not mean_bytes:
                extracted_observations[prop_key] = SoilParameterObservation(
                    parameter_key=prop_key,
                    display_name=meta["display_name"],
                    value=None,
                    unit=meta["unit"],
                    source="ISRIC SoilGrids",
                    dataset_version="2.0.0",
                    depth_interval=depth,
                    spatial_resolution="250m",
                    vintage_year=2020,
                    verification_status=VerificationStatus.MAP_DERIVED_ESTIMATE,
                    availability_status=ParameterAvailability.SOURCE_UNAVAILABLE,
                    farm_coverage_percent=0.0,
                    scientific_note=meta["note"]
                )
                continue

            try:
                with rasterio.open(io.BytesIO(mean_bytes)) as src:
                    out_image, _ = mask(src, [mapping(polygon)], crop=True, nodata=-9999)
                    # Filter valid positive pixels (excluding 0 mask and nodata)
                    valid_pixels = out_image[(out_image > 0) & (out_image < 30000)]
                    total_polygon_pixels = np.sum(out_image != -9999)

                    if len(valid_pixels) == 0:
                        extracted_observations[prop_key] = SoilParameterObservation(
                            parameter_key=prop_key,
                            display_name=meta["display_name"],
                            value=None,
                            unit=meta["unit"],
                            source="ISRIC SoilGrids",
                            dataset_version="2.0.0",
                            depth_interval=depth,
                            spatial_resolution="250m",
                            vintage_year=2020,
                            verification_status=VerificationStatus.MAP_DERIVED_ESTIMATE,
                            availability_status=ParameterAvailability.NOT_AVAILABLE,
                            farm_coverage_percent=0.0,
                            scientific_note=f"No valid pixels found inside farm polygon (likely water or urban mask). {meta['note']}"
                        )
                        continue

                    mean_val = float(np.mean(valid_pixels)) / meta["scale_factor"]
                    coverage_pct = round(float(len(valid_pixels)) / max(1, total_polygon_pixels) * 100.0, 1)

                    # Query uncertainty layer
                    uncertainty_val = None
                    unc_bytes = self._fetch_wcs_geotiff(meta["map_name"], unc_coverage_id, bounds)
                    if unc_bytes:
                        try:
                            with rasterio.open(io.BytesIO(unc_bytes)) as unc_src:
                                unc_image, _ = mask(unc_src, [mapping(polygon)], crop=True, nodata=-9999)
                                valid_unc = unc_image[(unc_image > 0) & (unc_image < 30000)]
                                if len(valid_unc) > 0:
                                    uncertainty_val = round(float(np.mean(valid_unc)) / meta["scale_factor"], 2)
                        except Exception as e:
                            logger.debug("Could not parse uncertainty layer: %s", e)

                    extracted_observations[prop_key] = SoilParameterObservation(
                        parameter_key=prop_key,
                        display_name=meta["display_name"],
                        value=round(mean_val, 2),
                        unit=meta["unit"],
                        source="ISRIC SoilGrids",
                        dataset_version="2.0.0",
                        depth_interval=depth,
                        spatial_resolution="250m",
                        vintage_year=2020,
                        uncertainty=uncertainty_val,
                        verification_status=VerificationStatus.MAP_DERIVED_ESTIMATE,
                        availability_status=ParameterAvailability.AVAILABLE if coverage_pct >= 50.0 else ParameterAvailability.PARTIAL_COVERAGE,
                        farm_coverage_percent=coverage_pct,
                        scientific_note=meta["note"]
                    )
            except Exception as e:
                logger.error("Error masking SoilGrids raster for %s: %s", prop_key, e)
                extracted_observations[prop_key] = SoilParameterObservation(
                    parameter_key=prop_key,
                    display_name=meta["display_name"],
                    value=None,
                    unit=meta["unit"],
                    source="ISRIC SoilGrids",
                    dataset_version="2.0.0",
                    depth_interval=depth,
                    spatial_resolution="250m",
                    vintage_year=2020,
                    verification_status=VerificationStatus.MAP_DERIVED_ESTIMATE,
                    availability_status=ParameterAvailability.NOT_AVAILABLE,
                    farm_coverage_percent=0.0,
                    scientific_note=str(e)
                )

        return extracted_observations
