import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path

from backend.app.db.session import get_db
from backend.app.db.models.crop_knowledge import CanonicalCropMasterModel
from backend.app.core.config import settings

router = APIRouter()

CATALOG_PATH = settings.PROCESSED_DATA_DIR / "GEO" / "maharashtra_taluka_catalog.json"
DISTRICTS_GEOJSON = settings.PROCESSED_DATA_DIR / "GEO" / "maharashtra_districts_36.geojson"

class DistrictItem(BaseModel):
    district_name: str
    talukas_count: int
    is_pilot: bool

class TalukaItem(BaseModel):
    taluka_name: str
    district_name: str
    latitude: float
    longitude: float
    is_pune_pilot: bool
    census_id: Optional[int] = None

class CropItem(BaseModel):
    crop_code: str
    common_name_en: str
    common_name_mr: Optional[str] = None
    botanical_name: Optional[str] = None
    crop_category: str
    standard_season: str
    support_level: str

@router.get("/districts", response_model=List[DistrictItem])
def get_maharashtra_districts():
    """Returns all 36 recognized districts of Maharashtra with pilot status."""
    if DISTRICTS_GEOJSON.exists():
        with open(DISTRICTS_GEOJSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            districts = []
            for feat in data.get("features", []):
                p = feat["properties"]
                districts.append(DistrictItem(
                    district_name=p["district_name"],
                    talukas_count=p.get("talukas_count", 0),
                    is_pilot=p.get("is_pilot_district", False)
                ))
            districts.sort(key=lambda d: d.district_name)
            return districts

    # Fallback to catalog
    if CATALOG_PATH.exists():
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)
            counts = {}
            for item in catalog:
                d = item["district_name"]
                counts[d] = counts.get(d, 0) + 1
            return [
                DistrictItem(district_name=d, talukas_count=c, is_pilot=(d == "Pune"))
                for d, c in sorted(counts.items())
            ]

    raise HTTPException(status_code=500, detail="District dataset not found")

@router.get("/talukas", response_model=List[TalukaItem])
def get_maharashtra_talukas(
    district: Optional[str] = Query(None, description="Filter talukas by Maharashtra district")
):
    """Returns official talukas with true centroid coordinates across all 36 Maharashtra districts."""
    if not CATALOG_PATH.exists():
        raise HTTPException(status_code=500, detail="Taluka catalog not found")

    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    if district:
        d_lower = district.strip().lower()
        filtered = [item for item in catalog if item["district_name"].lower() == d_lower]
        return [TalukaItem(**item) for item in filtered]

    return [TalukaItem(**item) for item in catalog]

@router.get("/crops", response_model=List[CropItem])
def get_canonical_crops(db: Session = Depends(get_db)):
    """Returns all 38 canonical Maharashtra crops from the knowledge base."""
    crops = db.query(CanonicalCropMasterModel).order_by(
        CanonicalCropMasterModel.crop_category,
        CanonicalCropMasterModel.common_name_en
    ).all()

    return [
        CropItem(
            crop_code=c.crop_code,
            common_name_en=c.common_name_en,
            common_name_mr=c.common_name_mr,
            botanical_name=c.botanical_name,
            crop_category=c.crop_category,
            standard_season=c.standard_season,
            support_level=c.support_level or "data_limited"
        )
        for c in crops
    ]
