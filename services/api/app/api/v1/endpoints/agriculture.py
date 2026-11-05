from typing import List
from fastapi import APIRouter
from cropnet.services.api.app.schemas.crop import MaharashtraSeasonCalendarResponse
from cropnet.services.api.app.services.crop_knowledge.crop_service import CropKnowledgeService

router = APIRouter()
crop_service = CropKnowledgeService()


@router.get("/seasons", response_model=List[MaharashtraSeasonCalendarResponse])
async def list_agricultural_seasons():
    """
    Standard agricultural cropping seasons in Maharashtra:
    - Kharif (Monsoon)
    - Rabi (Winter)
    - Zaid / Summer (Hot season)
    Provides period months, primary crop types, and moisture characteristics.
    """
    return crop_service.get_maharashtra_seasons()
