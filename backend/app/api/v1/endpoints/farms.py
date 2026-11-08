import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models.farm import FarmModel, FarmPlotModel, CropCycleModel
from backend.app.schemas.farm import FarmCreateRequest, FarmPlotCreateRequest, CropCycleCreateRequest, FarmResponse

router = APIRouter()

@router.post("/", response_model=FarmResponse)
def create_farm(request: FarmCreateRequest, db: Session = Depends(get_db)):
    farm_id = f"farm_{uuid.uuid4().hex[:8]}"
    farm = FarmModel(
        farm_id=farm_id,
        owner_id=request.owner_id,
        farm_name=request.farm_name,
        state=request.state,
        district=request.district,
        taluka=request.taluka,
        village=request.village,
        latitude=request.latitude,
        longitude=request.longitude
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm

@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(farm_id: str, db: Session = Depends(get_db)):
    farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm

@router.post("/{farm_id}/plots")
def add_plot(farm_id: str, request: FarmPlotCreateRequest, db: Session = Depends(get_db)):
    farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    plot_id = f"plot_{uuid.uuid4().hex[:8]}"
    plot = FarmPlotModel(
        plot_id=plot_id,
        farm_id=farm_id,
        plot_name=request.plot_name,
        area_acres=request.area_acres,
        irrigation_type=request.irrigation_type,
        polygon_geojson=request.polygon_geojson
    )
    db.add(plot)
    db.commit()
    db.refresh(plot)
    return {"plot_id": plot.plot_id, "plot_name": plot.plot_name, "area_acres": plot.area_acres}

@router.post("/{farm_id}/crop-cycles")
def create_crop_cycle(farm_id: str, plot_id: str, request: CropCycleCreateRequest, db: Session = Depends(get_db)):
    plot = db.query(FarmPlotModel).filter(FarmPlotModel.plot_id == plot_id).first()
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")
    cycle_id = f"cycle_{uuid.uuid4().hex[:8]}"
    cycle = CropCycleModel(
        cycle_id=cycle_id,
        plot_id=plot_id,
        crop_code=request.crop_code.lower(),
        variety_name=request.variety_name,
        season=request.season.lower(),
        sowing_date=request.sowing_date,
        current_stage_code=request.farmer_confirmed_stage
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return {
        "crop_cycle_id": cycle.cycle_id,
        "plot_id": cycle.plot_id,
        "crop_code": cycle.crop_code,
        "sowing_date": cycle.sowing_date.isoformat(),
        "status": "active"
    }
