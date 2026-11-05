from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

from cropnet.services.api.app.core.config import settings
from cropnet.services.api.app.services.soil_providers.soilgrids import SoilGridsProvider
from cropnet.services.api.app.services.soil_providers.openlandmap import OpenLandMapProvider
from cropnet.services.api.app.services.soil_providers.natmo import NATMOProvider
from cropnet.services.api.app.services.soil_providers.bhoomi import BhoomiProvider

router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: str
    app_name: str
    environment: str
    timestamp: datetime
    active_pilot_regions: list[str]
    soil_data_providers: Dict[str, Any]


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    sg = SoilGridsProvider()
    olm = OpenLandMapProvider()
    natmo = NATMOProvider()
    bhoomi = BhoomiProvider()

    return HealthCheckResponse(
        status="healthy",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.utcnow(),
        active_pilot_regions=["Maval", "Mulshi", "Baramati", "Indapur"],
        soil_data_providers={
            "isric_soilgrids": {
                "operational": True,
                "version": "2.0.0",
                "access_method": "OGC WCS 2.0.1",
                "resolution": "250m"
            },
            "openlandmap": {
                "operational": True,
                "version": "v20250204",
                "access_method": "Cloud-Optimized GeoTIFFs (Wasabi S3)",
                "resolution": "30m"
            },
            "icar_nbsslup_bhoomi": {
                "operational": False,
                "status": "Pending institutional access / credentials (HTTP 403)"
            },
            "natmo_geoportal": {
                "operational": False,
                "status": "Service unavailable (HTTP 500) & cartographic WMS display tiles only"
            }
        }
    )
