from fastapi import APIRouter
from cropnet.services.api.app.api.v1.endpoints import health, farms, soil

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(farms.router, prefix="/farms", tags=["Farms"])
api_router.include_router(soil.router, prefix="/soil", tags=["Soil Intelligence"])
