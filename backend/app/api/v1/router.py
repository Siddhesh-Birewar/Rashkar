from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    registry,
    farms,
    yield_risk,
    worker_heat,
    crop_heat
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(registry.router, prefix="/registry", tags=["Dataset Registry"])
api_router.include_router(farms.router, prefix="/farms", tags=["Farms & Plots"])
api_router.include_router(yield_risk.router, prefix="/yield-intelligence", tags=["Yield Intelligence"])
api_router.include_router(worker_heat.router, prefix="/heat-risk", tags=["Worker Heat Risk"])
api_router.include_router(crop_heat.router, prefix="/heat-risk", tags=["Crop Heat Risk"])
