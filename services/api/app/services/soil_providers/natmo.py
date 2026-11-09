import logging
from typing import List, Dict, Optional, Any
from shapely.geometry import Polygon

from cropnet.services.api.app.services.soil_providers.base import SoilDataProvider, ProviderCapability
from cropnet.services.api.app.schemas.soil import (
    SoilParameterObservation,
    VerificationStatus,
    ParameterAvailability
)

logger = logging.getLogger(__name__)


class NATMOProvider(SoilDataProvider):
    """
    Provider adapter for National Atlas & Thematic Mapping Organisation (NATMO) Geoportal.
    Investigated: https://www.geoportal.natmo.gov.in/
    """

    def __init__(self, portal_url: str = "https://geoportal.natmo.gov.in"):
        self.portal_url = portal_url

    def get_capabilities(self) -> ProviderCapability:
        return ProviderCapability(
            provider_name="NATMO Geoportal (National Atlas & Thematic Mapping Organisation)",
            dataset_version="National Atlas Thematic Soil Series",
            spatial_resolution_or_scale="1:1,000,000 to 1:2,000,000 (Macro Regional Scale)",
            supported_depth_intervals=["Whole Profile Classification"],
            vintage_year=2004,
            licensing="Government of India / NATMO restricted copyright (Non-commercial / viewer display only)",
            attribution_statement="Source: National Atlas and Thematic Mapping Organisation (NATMO), Department of Science & Technology, Govt. of India",
            is_operational=False,
            status_message="UNAVAILABLE: Geoportal currently returning HTTP 500. Furthermore, NATMO publishes WMS raster map visualization tiles only (no WCS / raw numerical GeoTIFFs or WFS vector attributes for farm-level extraction).",
            available_properties=["soil_order", "soil_reaction_class", "soil_texture_broad_class"],
            provides_uncertainty=False,
            requires_credentials=False
        )

    def check_coverage(self, polygon: Polygon) -> Dict[str, Any]:
        # NATMO covers India national territory (lat 6 to 37, lon 68 to 97)
        bounds = polygon.bounds
        is_in_india = (68.0 <= bounds[0] <= 97.0) and (6.0 <= bounds[1] <= 37.0)
        return {
            "has_coverage": is_in_india,
            "coverage_type": "national_macro_cartographic_atlas",
            "spatial_resolution": "1:1,000,000",
            "numerical_data_available": False,
            "limitation": "Cartographic map viewer only; no numerical raster data."
        }

    def extract_farm_soil(
        self,
        polygon: Polygon,
        requested_properties: Optional[List[str]] = None
    ) -> Dict[str, SoilParameterObservation]:
        """
        NATMO does not provide numerical GIS datasets; it is a cartographic visualization service.
        Returns explicit NOT_AVAILABLE / SOURCE_UNAVAILABLE parameters with clear provenance.
        """
        properties_to_query = requested_properties or ["soil_order", "soil_texture_broad_class"]
        extracted: Dict[str, SoilParameterObservation] = {}

        for prop_key in properties_to_query:
            extracted[prop_key] = SoilParameterObservation(
                parameter_key=prop_key,
                display_name=f"NATMO {prop_key.replace('_', ' ').title()}",
                value=None,
                unit="categorical",
                source="NATMO Geoportal",
                dataset_version="National Atlas Series",
                depth_interval="whole_profile",
                spatial_resolution="1:1,000,000",
                vintage_year=2004,
                verification_status=VerificationStatus.NOT_AVAILABLE,
                availability_status=ParameterAvailability.SOURCE_UNAVAILABLE,
                farm_coverage_percent=0.0,
                scientific_note="NATMO provides cartographic map tiles only. Numerical GIS extraction is not supported by the public geoportal."
            )

        return extracted
