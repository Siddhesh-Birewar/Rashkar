from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    health,
    registry,
    farms,
    yield_risk,
    worker_heat,
    crop_heat,
    income,
    pmfby,
    assistant,
    geo
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(geo.router, prefix="/geo", tags=["Geography & Crops"])
api_router.include_router(registry.router, prefix="/registry", tags=["Dataset Registry"])
api_router.include_router(farms.router, prefix="/farms", tags=["Farms & Plots"])
api_router.include_router(yield_risk.router, prefix="/yield-intelligence", tags=["Yield Intelligence"])
api_router.include_router(worker_heat.router, prefix="/heat-risk", tags=["Worker Heat Risk"])
api_router.include_router(crop_heat.router, prefix="/heat-risk", tags=["Crop Heat Risk"])
api_router.include_router(income.router, prefix="/income", tags=["Income Diversification"])
api_router.include_router(pmfby.router, prefix="/pmfby", tags=["PMFBY Crop Loss Evidence"])
api_router.include_router(assistant.router, prefix="/assistant", tags=["Text AI Assistant"])
