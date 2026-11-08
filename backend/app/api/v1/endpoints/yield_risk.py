from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models.farm import FarmModel, FarmPlotModel, CropCycleModel
from backend.app.schemas.yield_risk import YieldRiskResponse
from backend.app.services.yield_risk_engine import YieldRiskEngine

router = APIRouter()

@router.get("/{farm_id}/yield-risk", response_model=YieldRiskResponse)
def get_yield_risk(
    farm_id: str,
    plot_id: Optional[str] = Query(default=None),
    cycle_id: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail=f"Farm {farm_id} not found")

    # Locate plot and crop cycle
    plot = None
    if plot_id:
        plot = db.query(FarmPlotModel).filter(FarmPlotModel.plot_id == plot_id).first()
    elif farm.plots:
        plot = farm.plots[0]

    cycle = None
    if cycle_id:
        cycle = db.query(CropCycleModel).filter(CropCycleModel.cycle_id == cycle_id).first()
    elif plot and plot.crop_cycles:
        cycle = plot.crop_cycles[0]

    # Defaults if not yet populated in DB
    crop_code = cycle.crop_code if cycle else "soybean"
    sowing_date = cycle.sowing_date if cycle else date(2024, 6, 25)
    target_plot_id = plot.plot_id if plot else "plot_default_01"
    farmer_confirmed_stage = cycle.current_stage_code if cycle else None

    assessment = YieldRiskEngine.assess_yield_risk(
        db=db,
        farm_id=farm.farm_id,
        plot_id=target_plot_id,
        crop_code=crop_code,
        sowing_date=sowing_date,
        district=farm.district,
        taluka=farm.taluka,
        farmer_confirmed_stage=farmer_confirmed_stage
    )
    return assessment
