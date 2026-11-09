from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from shapely.geometry import Polygon
from cropnet.services.api.app.schemas.soil import SoilParameterObservation


class ProviderCapability(BaseModel):
    provider_name: str
    dataset_version: str
    spatial_resolution_or_scale: str
    supported_depth_intervals: List[str]
    vintage_year: Optional[int]
    licensing: str
    attribution_statement: str
    is_operational: bool
    status_message: str
    available_properties: List[str]
    provides_uncertainty: bool
    requires_credentials: bool


class SoilDataProvider(ABC):
    """
    Abstract Base Class for all Soil Data Providers in CropNet.
    Guarantees provider-independence across global, national, and local datasets.
    """

    @abstractmethod
    def get_capabilities(self) -> ProviderCapability:
        """
        Report supported properties, resolution, vintage, licensing, and operational status.
        """
        pass

    @abstractmethod
    def check_coverage(self, polygon: Polygon) -> Dict[str, Any]:
        """
        Check whether the given geometry falls within this dataset's spatial coverage.
        """
        pass

    @abstractmethod
    def extract_farm_soil(
        self,
        polygon: Polygon,
        requested_properties: Optional[List[str]] = None
    ) -> Dict[str, SoilParameterObservation]:
        """
        Extract raster/vector soil attributes for the farm polygon.
        Returns a dictionary of parameter_key -> SoilParameterObservation.
        """
        pass
