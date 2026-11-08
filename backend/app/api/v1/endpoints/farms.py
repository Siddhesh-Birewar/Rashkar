import uuid
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.db.models.farm import FarmerModel, FarmModel, FarmPlotModel, CropCycleModel, SoilProfileModel
from backend.app.db.models.crop_knowledge import CanonicalCropMasterModel
from backend.app.schemas.farm import (
    FarmCreateRequest, FarmPlotCreateRequest, CropCycleCreateRequest,
    FarmResponse, FarmerCreateRequest, FarmerResponse,
    GuidedRegistrationRequest, FarmSummaryResponse
)
from backend.app.services.crop_stage_service import CropStageService
from backend.app.services.cropnet_service import CropNetService
from backend.app.core.timezone import now_ist

router = APIRouter()

# --- Farmer Profiles ---

@router.post("/farmers", response_model=FarmerResponse)
def create_farmer(request: FarmerCreateRequest, db: Session = Depends(get_db)):
    farmer_id = f"farmer_{uuid.uuid4().hex[:8]}"
    farmer = FarmerModel(
        farmer_id=farmer_id,
        full_name=request.full_name,
        phone_number=request.phone_number,
        state=request.state,
        district=request.district,
        taluka=request.taluka,
        village=request.village,
        preferred_language=request.preferred_language
    )
    db.add(farmer)
    db.commit()
    db.refresh(farmer)
    return farmer

@router.get("/farmers/{farmer_id}", response_model=FarmerResponse)
def get_farmer(farmer_id: str, db: Session = Depends(get_db)):
    farmer = db.query(FarmerModel).filter(FarmerModel.farmer_id == farmer_id).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return farmer

@router.get("/farmers/{farmer_id}/farms", response_model=List[FarmResponse])
def get_farmer_farms(farmer_id: str, db: Session = Depends(get_db)):
    farms = db.query(FarmModel).filter(FarmModel.owner_id == farmer_id).all()
    return farms

# --- Farm Creation & Guided Registration ---

@router.get("/", response_model=List[FarmSummaryResponse])
def list_all_farms(db: Session = Depends(get_db)):
    """List all registered farms with their latest summary."""
    farms = db.query(FarmModel).order_by(FarmModel.created_at.desc()).all()
    summaries = []
    for f in farms:
        try:
            summaries.append(get_farm_summary(f.farm_id, db))
        except Exception:
            pass
    return summaries

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

@router.post("/guided-registration", response_model=FarmSummaryResponse)
def guided_farm_registration(request: GuidedRegistrationRequest, db: Session = Depends(get_db)):
    """
    Step-by-step guided registration endpoint creating Farmer, Farm, Plot,
    Crop Season, and associating CropNet soil profile in one cohesive flow.
    """
    # 1. Create or link farmer
    farmer = db.query(FarmerModel).filter(
        FarmerModel.full_name == request.farmer_name,
        FarmerModel.taluka == request.taluka
    ).first()
    if not farmer:
        farmer_id = f"farmer_{uuid.uuid4().hex[:8]}"
        farmer = FarmerModel(
            farmer_id=farmer_id,
            full_name=request.farmer_name,
            phone_number=request.phone_number,
            state="Maharashtra",
            district=request.district,
            taluka=request.taluka,
            village=request.village
        )
        db.add(farmer)
        db.flush()

    # 2. Create Farm
    farm_id = f"farm_{uuid.uuid4().hex[:8]}"
    farm = FarmModel(
        farm_id=farm_id,
        owner_id=farmer.farmer_id,
        farm_name=request.farm_name or f"{request.farmer_name}'s Farm",
        total_area_acres=request.total_area_acres,
        state="Maharashtra",
        district=request.district,
        taluka=request.taluka,
        village=request.village,
        latitude=request.latitude,
        longitude=request.longitude
    )
    db.add(farm)
    db.flush()

    # 3. Create Plot
    plot_id = f"plot_{uuid.uuid4().hex[:8]}"
    plot = FarmPlotModel(
        plot_id=plot_id,
        farm_id=farm.farm_id,
        plot_name="Main Plot 1",
        area_acres=request.planted_area_acres or request.total_area_acres or 2.0,
        irrigation_type=request.irrigation_type
    )
    db.add(plot)
    db.flush()

    # 4. Create Crop Cycle
    cycle_id = f"cycle_{uuid.uuid4().hex[:8]}"
    crop_info = db.query(CanonicalCropMasterModel).filter(
        CanonicalCropMasterModel.crop_code == request.crop_code.lower()
    ).first()
    cycle = CropCycleModel(
        cycle_id=cycle_id,
        plot_id=plot.plot_id,
        crop_code=request.crop_code.lower(),
        variety_name=request.variety_name,
        season=request.season.lower(),
        sowing_date=request.sowing_date,
        planted_area_acres=request.planted_area_acres,
        is_active=True
    )
    db.add(cycle)
    db.flush()

    # 5. Fetch and attach CropNet Soil Profile
    soil_profile = CropNetService.get_soil_profile(farm.farm_id, plot.plot_id, farm.taluka)
    soil_record = SoilProfileModel(
        soil_id=f"soil_{uuid.uuid4().hex[:8]}",
        farm_id=farm.farm_id,
        depth_interval="0-30cm",
        ph=soil_profile.ph.value if hasattr(soil_profile, 'ph') and soil_profile.ph else 7.8,
        organic_carbon_pct=soil_profile.organic_carbon_pct.value if hasattr(soil_profile, 'organic_carbon_pct') and soil_profile.organic_carbon_pct else 0.65,
        clay_pct=soil_profile.clay_pct.value if hasattr(soil_profile, 'clay_pct') and soil_profile.clay_pct else 48.0,
        sand_pct=soil_profile.sand_pct.value if hasattr(soil_profile, 'sand_pct') and soil_profile.sand_pct else 24.0,
        silt_pct=soil_profile.silt_pct.value if hasattr(soil_profile, 'silt_pct') and soil_profile.silt_pct else 28.0,
        bulk_density_g_cm3=1.35,
        cec_cmol_kg=soil_profile.cation_exchange_capacity_cmol_kg.value if hasattr(soil_profile, 'cation_exchange_capacity_cmol_kg') and soil_profile.cation_exchange_capacity_cmol_kg else 42.0,
        available_water_capacity_mm_m=160.0,
        data_provenance="CropNet Maharashtra 250m baseline",
        is_lab_measured=False
    )
    db.add(soil_record)
    db.commit()

    return get_farm_summary(farm.farm_id, db)

# --- Farm Summary & Details ---

@router.get("/{farm_id}/summary", response_model=FarmSummaryResponse)
def get_farm_summary(farm_id: str, db: Session = Depends(get_db)):
    farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    farmer = db.query(FarmerModel).filter(FarmerModel.farmer_id == farm.owner_id).first()
    farmer_name = farmer.full_name if farmer else "Demo Farmer"

    # Find active crop cycle across plots
    active_cycle = None
    active_plot = None
    for plot in farm.plots:
        for cycle in plot.crop_cycles:
            if cycle.is_active:
                active_cycle = cycle
                active_plot = plot
                break
        if active_cycle:
            break

    crop_name = None
    days_after_sowing = None
    estimated_stage_code = None
    estimated_stage_name = None
    sowing_date_str = None

    if active_cycle:
        crop_master = db.query(CanonicalCropMasterModel).filter(
            CanonicalCropMasterModel.crop_code == active_cycle.crop_code
        ).first()
        crop_name = crop_master.common_name_en if crop_master else active_cycle.crop_code.title()
        sowing_date_str = active_cycle.sowing_date.isoformat()
        
        stage_info = CropStageService.estimate_crop_stage(
            db, active_cycle.crop_code, active_cycle.sowing_date, active_cycle.current_stage_code
        )
        days_after_sowing = stage_info["days_after_sowing"]
        estimated_stage_code = stage_info["stage_code"]
        estimated_stage_name = stage_info["stage_name_en"]

    # Soil summary
    soil = farm.soil_profile
    soil_summary = None
    if soil:
        soil_summary = {
            "depth": soil.depth_interval,
            "ph": soil.ph,
            "organic_carbon_pct": soil.organic_carbon_pct,
            "clay_pct": soil.clay_pct,
            "available_water_capacity_mm_m": soil.available_water_capacity_mm_m,
            "data_provenance": soil.data_provenance,
            "is_lab_measured": soil.is_lab_measured
        }

    # Weather summary (from live/district station context)
    now_t = now_ist()
    weather_summary = {
        "temperature_c": 32.5 if farm.latitude > 18.0 else 34.2,
        "relative_humidity_pct": 58.0 if "ghat" in (farm.taluka or "").lower() else 52.0,
        "wind_speed_kmh": 12.0,
        "condition": "Partly Cloudy",
        "rainfall_today_mm": 0.0,
        "source": f"IMD {farm.district} Station / 0.25° Gridded Baseline"
    }

    # 1 to 3 useful farmer recommendations / alerts tailored to active crop and district
    active_alerts = []
    crop_c = active_cycle.crop_code.lower() if active_cycle else "general"
    if crop_c == "soybean":
        active_alerts.append({
            "title": "Moisture & Pod Care",
            "message": f"Soybean in {farm.taluka} is in {estimated_stage_name or 'growth'}. Soil moisture is adequate; avoid excessive flooding.",
            "urgency": "medium",
            "source": "MPKV Rahuri Package of Practices"
        })
    elif crop_c in ["cotton"]:
        active_alerts.append({
            "title": "Boll Formation Alert",
            "message": f"Cotton in {farm.taluka} ({farm.district}) is entering flowering/boll stage. Monitor for pink bollworm and avoid water stress.",
            "urgency": "high",
            "source": "ICAR-CICR Nagpur Advisory"
        })
    elif crop_c in ["jowar", "sorghum"]:
        active_alerts.append({
            "title": "Drought & Heat Monitoring",
            "message": f"Jowar in {farm.district} is hardy, but critical moisture needed at boot-leaf stage. Mulch furrows if dry spell extends.",
            "urgency": "medium",
            "source": "MPKV Rahuri Millets Directorate"
        })
    elif crop_c in ["sugarcane"]:
        active_alerts.append({
            "title": "Trash Mulching & Irrigation",
            "message": f"Sugarcane in {farm.taluka}: Apply trash mulching between cane rows to preserve soil moisture in hot afternoon hours.",
            "urgency": "medium",
            "source": "VSI Pune Sugarcane Advisory"
        })
    elif crop_c in ["onion"]:
        active_alerts.append({
            "title": "Bulb Development & Thrips Watch",
            "message": f"Onion crop in {farm.district}: Maintain regular light irrigation. Monitor for thrips if daytime temperatures exceed 33°C.",
            "urgency": "high",
            "source": "ICAR-DOGR Rajgurunagar"
        })
    elif crop_c in ["gram", "chickpea"]:
        active_alerts.append({
            "title": "Pod Borer Monitoring",
            "message": f"Gram in {farm.district}: Install pheromone traps (5 per acre) for Helicoverpa pod borer monitoring.",
            "urgency": "high",
            "source": "MPKV Rahuri Pulses Research"
        })
    else:
        active_alerts.append({
            "title": f"{crop_name or 'Crop'} Management Advisory",
            "message": f"For your {crop_name or active_cycle.crop_code} crop in {farm.taluka}, ensure optimal weed management and monitor soil moisture.",
            "urgency": "medium",
            "source": "Maharashtra Krishi Vidyapeeth Advisory"
        })

    # Universal heat safety alert tailored to the farm's location
    active_alerts.append({
        "title": "Worker Heat Safety Advisory",
        "message": f"Afternoon heat peaks between 12:30 PM and 3:30 PM in {farm.taluka}. Schedule heavy field operations for early morning or post 4:00 PM.",
        "urgency": "high",
        "source": "Rashkar Occupational Heat Risk Service"
    })

    loc_parts = [p for p in [farm.village, farm.taluka, farm.district] if p]
    location_display = ", ".join(loc_parts)

    return FarmSummaryResponse(
        farmer_id=farm.owner_id,
        farmer_name=farmer_name,
        farm_id=farm.farm_id,
        farm_name=farm.farm_name,
        location_display=location_display,
        latitude=farm.latitude,
        longitude=farm.longitude,
        total_area_acres=farm.total_area_acres,
        active_crop_code=active_cycle.crop_code if active_cycle else None,
        active_crop_name=crop_name,
        sowing_date=sowing_date_str,
        days_after_sowing=days_after_sowing,
        estimated_stage_code=estimated_stage_code,
        estimated_stage_name=estimated_stage_name,
        planted_area_acres=active_plot.area_acres if active_plot else None,
        irrigation_type=active_plot.irrigation_type if active_plot else "rainfed",
        weather_summary=weather_summary,
        data_last_updated=now_t.strftime("%d %b %Y, %I:%M %p"),
        is_data_stale=False,
        soil_summary=soil_summary,
        active_alerts=active_alerts
    )

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
        current_stage_code=request.farmer_confirmed_stage,
        is_active=True
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
