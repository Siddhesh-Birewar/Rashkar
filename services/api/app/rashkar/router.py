"""Root FastAPI router aggregating all strictly additive RASHKAR endpoints."""

from fastapi import APIRouter

from .endpoints import (
    context_router,
    crop_heat_router,
    income_router,
    worker_heat_router,
    yield_intelligence_router,
)


rashkar_router = APIRouter(prefix="/rashkar", tags=["RASHKAR"])
rashkar_router.include_router(context_router)
rashkar_router.include_router(worker_heat_router)
rashkar_router.include_router(crop_heat_router)
rashkar_router.include_router(yield_intelligence_router)
rashkar_router.include_router(income_router)

__all__ = ["rashkar_router"]
