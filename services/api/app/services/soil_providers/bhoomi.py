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


class BhoomiProvider(SoilDataProvider):
    """
    Provider adapter for ICAR-NBSS&LUP BHOOMI Geoportal.
    Investigated: https://bhoomigeoportal-nbsslup.in/
    GeoServer Endpoint: https://bhoomigeoportal-nbsslup.in/geoserver/wms
    
    Status: Modular integration for future production rollout.
    Currently blocked for public unauthenticated access (GeoServer returns HTTP 403 Forbidden).
    Requires institutional approval / credentials from ICAR-NBSS&LUP.
    """

    def __init__(self, base_url: str = "https://bhoomigeoportal-nbsslup.in/geoserver", api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key

    def get_capabilities(self) -> ProviderCapability:
        has_creds = bool(self.api_key)
        return ProviderCapability(
            provider_name="ICAR-NBSS&LUP BHOOMI Geoportal",
            dataset_version="BHOOMI Soil Series & Land Degradation Maps",
            spatial_resolution_or_scale="1:50,000 to 1:250,000 (District/National Scales)",
            supported_depth_intervals=["0-15cm (Surface)", "Whole Soil Series Profile"],
            vintage_year=2021,
            licensing="Government of India / ICAR institutional access policy (Proprietary / Permission Required)",
            attribution_statement="Source: ICAR - National Bureau of Soil Survey and Land Use Planning (NBSS&LUP), Nagpur, India",
            is_operational=has_creds,
            status_message="PENDING INSTITUTIONAL ACCESS: Public OGC GeoServer endpoints are protected (HTTP 403 Forbidden). Integration is modular and awaits official institutional API credentials.",
            available_properties=[
                "soil_series", "soil_depth_class", "soil_texture_class",
                "slope_class", "erosion_class", "drainage_class", "ph", "organic_carbon"
            ],
            provides_uncertainty=False,
            requires_credentials=True
        )

    def check_coverage(self, polygon: Polygon) -> Dict[str, Any]:
        bounds = polygon.bounds
        is_in_india = (68.0 <= bounds[0] <= 97.0) and (6.0 <= bounds[1] <= 37.0)
        return {
            "has_coverage": is_in_india,
            "coverage_type": "national_soil_series_cartography",
            "spatial_resolution": "1:50,000 to 1:250,000",
            "access_status": "institutional_credentials_required",
            "http_status_code": 403
        }

    def extract_farm_soil(
        self,
        polygon: Polygon,
        requested_properties: Optional[List[str]] = None
    ) -> Dict[str, SoilParameterObservation]:
        """
        If credentials are not yet configured, returns explicit awaiting_source_access parameters.
        Does not fabricate values.
        """
        properties_to_query = requested_properties or [
            "soil_series", "soil_depth_class", "soil_texture_class"
        ]
        extracted: Dict[str, SoilParameterObservation] = {}

        for prop_key in properties_to_query:
            extracted[prop_key] = SoilParameterObservation(
                parameter_key=prop_key,
                display_name=f"BHOOMI {prop_key.replace('_', ' ').title()}",
                value=None,
                unit="categorical",
                source="ICAR-NBSS&LUP BHOOMI",
                dataset_version="BHOOMI Geoportal",
                depth_interval="soil_series_profile",
                spatial_resolution="1:50,000",
                vintage_year=2021,
                verification_status=VerificationStatus.NOT_AVAILABLE,
                availability_status=ParameterAvailability.SOURCE_UNAVAILABLE,
                farm_coverage_percent=0.0,
                scientific_note="ICAR-NBSS&LUP BHOOMI integration is modular and pending institutional access approval (public endpoints return HTTP 403 Forbidden)."
            )

        return extracted
