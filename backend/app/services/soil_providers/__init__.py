"""
Soil Data Providers Module for Rashkar CropNet Integration.
Guarantees provider-independence across global, national, and local datasets.
"""
from backend.app.services.soil_providers.base import SoilDataProvider, ProviderCapability
from backend.app.services.soil_providers.soilgrids import SoilGridsProvider
from backend.app.services.soil_providers.openlandmap import OpenLandMapProvider
from backend.app.services.soil_providers.local_raster import LocalRasterProvider

__all__ = [
    "SoilDataProvider",
    "ProviderCapability",
    "SoilGridsProvider",
    "OpenLandMapProvider",
    "LocalRasterProvider"
]
