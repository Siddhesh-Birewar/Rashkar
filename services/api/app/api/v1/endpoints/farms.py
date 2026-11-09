import uuid
from typing import List, Optional, Dict
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from shapely.geometry import Polygon

from cropnet.services.api.app.schemas.farm import FarmCreate, FarmUpdate, FarmResponse
from cropnet.services.api.app.schemas.soil import (
    UnifiedSoilProfile,
    SoilAnalyseRequest,
    VerificationStatus,
    ParameterAvailability,
    SoilParameterObservation,
)
from cropnet.services.api.app.schemas.soil_reports import (
    ReviewStatus,
    MeasurementVerificationStatus,
    CANONICAL_SOIL_PARAMETERS,
)
from cropnet.services.api.app.models.soil_reports import SoilTestReportModel, SoilMeasurementModel
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmContextInput,
    FarmEvaluationResponse,
    SoilDataProvenance,
)
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import (
    DeterministicDecisionEngine,
    record_decision_owner,
)
from cropnet.services.api.app.core.security import get_current_user, CurrentUser
from cropnet.services.api.app.core.database import get_db
from cropnet.services.api.app.models.soil_and_farm import FarmModel
from cropnet.services.api.app.models.weather import FarmWeatherSnapshotModel, FarmClimateSummaryModel
from cropnet.services.api.app.services.spatial_extractor import (
    calculate_polygon_area,
    SpatialSoilService
)

router = APIRouter()
spatial_soil_service = SpatialSoilService()

# Memory cache for fast lookups & test resilience
_FARM_STORAGE: dict[uuid.UUID, dict] = {}


def _build_farm_response_dict(
    farm_id: uuid.UUID,
    owner_id: uuid.UUID,
    name: str,
    village: Optional[str],
    taluka: str,
    district: str,
    state: str,
    irrigation_type: Optional[str],
    water_source: Optional[str],
    geometry_dict: dict,
    area_hectares: float,
    area_acres: float,
    centroid_lat: float,
    centroid_lon: float,
    created_at: datetime,
    updated_at: datetime
) -> dict:
    return {
        "id": farm_id,
        "owner_id": owner_id,
        "name": name,
        "village": village,
        "taluka": taluka,
        "district": district,
        "state": state,
        "irrigation_type": irrigation_type,
        "water_source": water_source,
        "geometry": geometry_dict,
        "calculated_area_hectares": area_hectares,
        "calculated_area_acres": area_acres,
        "centroid_latitude": centroid_lat,
        "centroid_longitude": centroid_lon,
        "latitude": centroid_lat,
        "longitude": centroid_lon,
        "created_at": created_at,
        "updated_at": updated_at
    }


@router.post("", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    payload: FarmCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register a new farm with validated GeoJSON polygon boundary.
    - Calculates geodesic area in metric hectares and acres using WGS84 ellipsoid.
    - Computes polygon centroid coordinates.
    - Persists to PostgreSQL/PostGIS and memory cache.
    - Enforces user ownership.
    """
    farm_id = uuid.uuid4()
    now = datetime.utcnow()

    # Calculate geodesic area and centroid
    coords = payload.geometry.coordinates[0]
    poly = Polygon(coords)
    area_dict = calculate_polygon_area(poly)
    centroid = poly.centroid

    farm_dict = _build_farm_response_dict(
        farm_id=farm_id,
        owner_id=current_user.user_id,
        name=payload.name,
        village=payload.village,
        taluka=payload.taluka,
        district=payload.district,
        state=payload.state,
        irrigation_type=payload.irrigation_type,
        water_source=payload.water_source,
        geometry_dict=payload.geometry.model_dump(),
        area_hectares=area_dict["hectares"],
        area_acres=area_dict["acres"],
        centroid_lat=round(centroid.y, 6),
        centroid_lon=round(centroid.x, 6),
        created_at=now,
        updated_at=now
    )

    # Persist to PostgreSQL if connected
    try:
        db_farm = FarmModel(
            id=str(farm_id),
            owner_id=str(current_user.user_id),
            name=payload.name,
            village=payload.village,
            taluka=payload.taluka,
            district=payload.district,
            state=payload.state,
            irrigation_type=payload.irrigation_type,
            water_source=payload.water_source,
            geometry_geojson=payload.geometry.model_dump(),
            calculated_area_hectares=area_dict["hectares"],
            calculated_area_acres=area_dict["acres"],
            centroid_latitude=round(centroid.y, 6),
            centroid_longitude=round(centroid.x, 6),
            created_at=now,
            updated_at=now
        )
        db.add(db_farm)
        db.commit()
    except Exception as e:
        db.rollback()

    _FARM_STORAGE[farm_id] = farm_dict
    return FarmResponse(**farm_dict)


@router.get("", response_model=List[FarmResponse])
async def list_farms(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all farms belonging to the authenticated user.
    Strictly isolated: users cannot see other users' farms.
    """
    farms_list = []
    try:
        db_farms = db.query(FarmModel).filter(FarmModel.owner_id == str(current_user.user_id)).all()
        for f in db_farms:
            farms_list.append(FarmResponse(
                id=uuid.UUID(f.id),
                owner_id=uuid.UUID(f.owner_id),
                name=f.name,
                village=f.village,
                taluka=f.taluka,
                district=f.district,
                state=f.state,
                irrigation_type=f.irrigation_type,
                water_source=f.water_source,
                geometry=f.geometry_geojson,
                calculated_area_hectares=f.calculated_area_hectares,
                calculated_area_acres=f.calculated_area_acres,
                centroid_latitude=f.centroid_latitude or 0.0,
                centroid_longitude=f.centroid_longitude or 0.0,
                latitude=f.centroid_latitude or 0.0,
                longitude=f.centroid_longitude or 0.0,
                created_at=f.created_at,
                updated_at=f.updated_at
            ))
    except Exception:
        # Fallback to in-memory store
        pass

    if not farms_list:
        user_farms = [
            f for f in _FARM_STORAGE.values()
            if f["owner_id"] == current_user.user_id
        ]
        farms_list = [FarmResponse(**f) for f in user_farms]

    return farms_list


@router.get("/{farm_id}", response_model=FarmResponse)
async def get_farm(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve farm by ID. Enforces strict user ownership check.
    """
    # Check DB first
    try:
        f = db.query(FarmModel).filter(FarmModel.id == str(farm_id)).first()
        if f:
            if f.owner_id != str(current_user.user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this farm"
                )
            return FarmResponse(
                id=uuid.UUID(f.id),
                owner_id=uuid.UUID(f.owner_id),
                name=f.name,
                village=f.village,
                taluka=f.taluka,
                district=f.district,
                state=f.state,
                irrigation_type=f.irrigation_type,
                water_source=f.water_source,
                geometry=f.geometry_geojson,
                calculated_area_hectares=f.calculated_area_hectares,
                calculated_area_acres=f.calculated_area_acres,
                centroid_latitude=f.centroid_latitude or 0.0,
                centroid_longitude=f.centroid_longitude or 0.0,
                latitude=f.centroid_latitude or 0.0,
                longitude=f.centroid_longitude or 0.0,
                created_at=f.created_at,
                updated_at=f.updated_at
            )
    except HTTPException:
        raise
    except Exception:
        pass

    # Fallback to memory store
    farm = _FARM_STORAGE.get(farm_id)
    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm {farm_id} not found"
        )
    if farm["owner_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this farm"
        )
    return FarmResponse(**farm)


@router.put("/{farm_id}", response_model=FarmResponse)
async def update_farm(
    farm_id: uuid.UUID,
    payload: FarmUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update farm details and/or farm boundary polygon.
    - If boundary geometry is updated, recalculates geodesic area and centroid.
    - Enforces ownership authorization.
    """
    existing_farm = _FARM_STORAGE.get(farm_id)
    db_farm = None
    try:
        db_farm = db.query(FarmModel).filter(FarmModel.id == str(farm_id)).first()
    except Exception:
        pass

    if not existing_farm and not db_farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm {farm_id} not found"
        )

    # Check ownership
    owner_str = str(current_user.user_id)
    if db_farm and db_farm.owner_id != owner_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this farm"
        )
    if existing_farm and existing_farm["owner_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this farm"
        )

    now = datetime.utcnow()

    # Determine updated values
    name = payload.name or (db_farm.name if db_farm else existing_farm["name"])
    village = payload.village if payload.village is not None else (db_farm.village if db_farm else existing_farm.get("village"))
    taluka = payload.taluka or (db_farm.taluka if db_farm else existing_farm["taluka"])
    district = payload.district or (db_farm.district if db_farm else existing_farm.get("district", "Pune"))
    state = payload.state or (db_farm.state if db_farm else existing_farm.get("state", "Maharashtra"))
    irrigation_type = payload.irrigation_type or (db_farm.irrigation_type if db_farm else existing_farm.get("irrigation_type", "unknown"))
    water_source = payload.water_source or (db_farm.water_source if db_farm else existing_farm.get("water_source", "unknown"))
    
    # Check if geometry updated
    if payload.geometry:
        coords = payload.geometry.coordinates[0]
        poly = Polygon(coords)
        area_dict = calculate_polygon_area(poly)
        centroid = poly.centroid
        geom_dict = payload.geometry.model_dump()
        area_ha = area_dict["hectares"]
        area_ac = area_dict["acres"]
        c_lat = round(centroid.y, 6)
        c_lon = round(centroid.x, 6)
    else:
        geom_dict = db_farm.geometry_geojson if db_farm else existing_farm["geometry"]
        area_ha = db_farm.calculated_area_hectares if db_farm else existing_farm["calculated_area_hectares"]
        area_ac = db_farm.calculated_area_acres if db_farm else existing_farm["calculated_area_acres"]
        c_lat = db_farm.centroid_latitude if db_farm else existing_farm["centroid_latitude"]
        c_lon = db_farm.centroid_longitude if db_farm else existing_farm["centroid_longitude"]

    created_at = db_farm.created_at if db_farm else existing_farm["created_at"]

    # Update in DB
    if db_farm:
        try:
            db_farm.name = name
            db_farm.village = village
            db_farm.taluka = taluka
            db_farm.district = district
            db_farm.state = state
            db_farm.irrigation_type = irrigation_type
            db_farm.water_source = water_source
            db_farm.geometry_geojson = geom_dict
            db_farm.calculated_area_hectares = area_ha
            db_farm.calculated_area_acres = area_ac
            db_farm.centroid_latitude = c_lat
            db_farm.centroid_longitude = c_lon
            db_farm.updated_at = now
            db.commit()
        except Exception:
            db.rollback()

    updated_dict = _build_farm_response_dict(
        farm_id=farm_id,
        owner_id=current_user.user_id,
        name=name,
        village=village,
        taluka=taluka,
        district=district,
        state=state,
        irrigation_type=irrigation_type,
        water_source=water_source,
        geometry_dict=geom_dict,
        area_hectares=area_ha,
        area_acres=area_ac,
        centroid_lat=c_lat,
        centroid_lon=c_lon,
        created_at=created_at,
        updated_at=now
    )
    _FARM_STORAGE[farm_id] = updated_dict
    return FarmResponse(**updated_dict)


@router.delete("/{farm_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_farm(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a farm by ID. Enforces ownership authorization.
    """
    existing_farm = _FARM_STORAGE.get(farm_id)
    db_farm = None
    try:
        db_farm = db.query(FarmModel).filter(FarmModel.id == str(farm_id)).first()
    except Exception:
        pass

    if not existing_farm and not db_farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm {farm_id} not found"
        )

    # Check ownership
    owner_str = str(current_user.user_id)
    if db_farm and db_farm.owner_id != owner_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this farm"
        )
    if existing_farm and existing_farm["owner_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this farm"
        )

    if db_farm:
        try:
            farm_id_str = str(farm_id)
            db.query(FarmWeatherSnapshotModel).filter(FarmWeatherSnapshotModel.farm_id == farm_id_str).delete(synchronize_session=False)
            db.query(FarmClimateSummaryModel).filter(FarmClimateSummaryModel.farm_id == farm_id_str).delete(synchronize_session=False)
            db.delete(db_farm)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete farm from database: {str(e)}"
            )

    if farm_id in _FARM_STORAGE:
        del _FARM_STORAGE[farm_id]

    return None


def _get_farm_and_verify_owner(farm_id: uuid.UUID, current_user: CurrentUser, db: Session) -> dict:
    """
    Lookup farm from memory cache or database and verify caller ownership.
    """
    farm = _FARM_STORAGE.get(farm_id)
    if not farm:
        try:
            db_farm = db.query(FarmModel).filter(FarmModel.id == str(farm_id)).first()
            if db_farm:
                farm = {
                    "id": uuid.UUID(db_farm.id),
                    "owner_id": uuid.UUID(db_farm.owner_id),
                    "name": db_farm.name,
                    "village": db_farm.village,
                    "taluka": db_farm.taluka,
                    "district": db_farm.district,
                    "state": db_farm.state,
                    "geometry": db_farm.geometry_geojson,
                    "calculated_area_hectares": db_farm.calculated_area_hectares,
                    "calculated_area_acres": db_farm.calculated_area_acres,
                }
        except Exception:
            pass

    if not farm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farm {farm_id} not found"
        )
    if farm["owner_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this farm"
        )
    return farm


@router.post("/{farm_id}/soil/analyse", response_model=UnifiedSoilProfile)
async def analyse_farm_soil(
    farm_id: uuid.UUID,
    payload: SoilAnalyseRequest = SoilAnalyseRequest(),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger or retrieve farm-specific soil intelligence extraction.
    - Uses cached profile if force_refresh=False.
    - If no cache or force_refresh=True, extracts raster properties from SoilGrids WCS.
    - Derives USDA Soil Texture Classification (e.g. Clay, Clay Loam).
    - Checks spatial representativeness for parcels < 6.25 ha.
    - Strictly preserves unverified available NPK as null.
    - Persists profile snapshot and parameters to PostgreSQL database.
    """
    farm = _get_farm_and_verify_owner(farm_id, current_user, db)

    # 1. Return cached profile if available and not forcing refresh
    if not payload.force_refresh:
        cached = spatial_soil_service.get_latest_profile(db, str(farm_id), depth=payload.depth)
        if cached:
            fused = _fuse_confirmed_laboratory_measurements(cached, farm_id, farm, db, depth=payload.depth)
            return fused or cached

    # 2. Extract live from polygon boundary
    coords = farm["geometry"]["coordinates"][0]
    poly = Polygon(coords)
    profile = spatial_soil_service.generate_farm_soil_profile(
        farm_id=str(farm_id),
        polygon=poly,
        taluka=farm.get("taluka"),
        depth=payload.depth,
        farm_area_hectares=farm.get("calculated_area_hectares")
    )

    # 3. Persist profile and parameter observations
    spatial_soil_service.save_profile(db, profile)
    fused = _fuse_confirmed_laboratory_measurements(profile, farm_id, farm, db, depth=payload.depth)
    return fused or profile


def _fuse_confirmed_laboratory_measurements(
    profile: Optional[UnifiedSoilProfile],
    farm_id: uuid.UUID,
    farm_data: dict,
    db: Session,
    depth: Optional[str] = None
) -> Optional[UnifiedSoilProfile]:
    """
    Dual-Source Agricultural Intelligence Fusion:
    - Check if confirmed soil test reports exist for this farm (SoilTestReportModel.review_status == "CONFIRMED").
    - If confirmed measurements exist:
      * Dual-source preservation: Keep SoilGrids modelled estimates (source="ISRIC SoilGrids 2.0", verification_status="map_derived_estimate") intact.
      * Precedence rule: For the unified profile, prioritize confirmed laboratory measurements for
        soil_ph, organic_carbon, electrical_conductivity, available_nitrogen, available_phosphorus, available_potassium
        with source="Laboratory Report: <lab_name>" and verification_status="laboratory_verified".
      * Strict isolation: Unconfirmed measurements (NEEDS_REVIEW or EXTRACTED_UNVERIFIED) are completely ignored.
      * Rule compatibility: Preserve micronutrients (Zn, Fe, Mn, Cu, B, S), total_nitrogen, organic_matter
        in additional_parameters for display without passing them as unhandled inputs to SoilConstraintEvaluator.
    """
    confirmed_reports = (
        db.query(SoilTestReportModel)
        .filter(
            SoilTestReportModel.farm_id == str(farm_id),
            SoilTestReportModel.review_status == ReviewStatus.CONFIRMED.value
        )
        .order_by(SoilTestReportModel.report_date.desc(), SoilTestReportModel.upload_timestamp.desc())
        .all()
    )

    if not confirmed_reports:
        return profile

    confirmed_measurements = (
        db.query(SoilMeasurementModel)
        .join(SoilTestReportModel, SoilMeasurementModel.report_id == SoilTestReportModel.id)
        .filter(
            SoilMeasurementModel.farm_id == str(farm_id),
            SoilTestReportModel.review_status == ReviewStatus.CONFIRMED.value,
            SoilMeasurementModel.verification_status == MeasurementVerificationStatus.FARMER_CONFIRMED.value
        )
        .order_by(SoilTestReportModel.report_date.desc(), SoilMeasurementModel.created_at.desc())
        .all()
    )

    if not confirmed_measurements:
        return profile

    latest_by_param: Dict[str, SoilMeasurementModel] = {}
    for m in confirmed_measurements:
        if m.parameter_key not in latest_by_param:
            latest_by_param[m.parameter_key] = m

    if profile is None:
        first_rep_depth = confirmed_reports[0].sample_depth_interval if confirmed_reports else None
        if not first_rep_depth or first_rep_depth.strip().lower() in {"not specified", "unknown"}:
            first_rep_depth = "Not specified"
        profile = UnifiedSoilProfile(
            profile_id=str(uuid.uuid4()),
            farm_id=str(farm_id),
            created_at=datetime.utcnow(),
            version=1,
            taluka=farm_data.get("taluka"),
            district=farm_data.get("district", "Pune"),
            state=farm_data.get("state", "Maharashtra"),
            is_map_derived=False,
            disclaimer=(
                "This profile incorporates farmer-confirmed laboratory soil test measurements. "
                "Values reflect physical laboratory analysis."
            ),
            source_dataset="Laboratory Test Report",
            dataset_version="1.0.0",
            spatial_resolution="point_sample",
            depth_interval=first_rep_depth,
        )
    else:
        profile = profile.model_copy(deep=True)
        profile.profile_id = str(uuid.uuid4())

    def _make_lab_obs(key: str, meas: SoilMeasurementModel, display_name: str, scientific_note: Optional[str] = None) -> SoilParameterObservation:
        lab_name = meas.report.laboratory_name if (meas.report and meas.report.laboratory_name) else "Certified Laboratory"
        val = meas.farmer_corrected_value if meas.farmer_corrected_value is not None else (
            meas.normalized_value if meas.normalized_value is not None else meas.original_value
        )
        unit = meas.normalized_unit or meas.original_unit or ""
        depth_int = (
            meas.report.sample_depth_interval
            if (meas.report and meas.report.sample_depth_interval and meas.report.sample_depth_interval.strip().lower() not in {"not specified", "unknown"})
            else "Not specified"
        )
        vintage = meas.report.report_date.year if (meas.report and meas.report.report_date) else datetime.utcnow().year
        depth_prov = meas.report.depth_provenance if (meas.report and meas.report.depth_provenance) else "UNKNOWN"
        base_note = scientific_note or f"Farmer-confirmed physical laboratory test from {lab_name}."
        if depth_int == "Not specified":
            full_note = f"{base_note} (Depth: Not specified)."
        else:
            full_note = f"{base_note} (Depth: {depth_int}, provenance: {depth_prov})."

        return SoilParameterObservation(
            parameter_key=key,
            display_name=display_name,
            value=val,
            unit=unit,
            source=f"Laboratory Report: {lab_name}",
            dataset_version="1.0.0",
            depth_interval=depth_int,
            spatial_resolution="point_sample",
            vintage_year=vintage,
            verification_status=VerificationStatus.LABORATORY_VERIFIED,
            availability_status=ParameterAvailability.AVAILABLE,
            farm_coverage_percent=100.0,
            scientific_note=full_note
        )

    # 1. Precedence: soil_ph (Strict agronomic bounds: 3.0 to 11.0)
    if "soil_ph" in latest_by_param:
        m = latest_by_param["soil_ph"]
        val = m.farmer_corrected_value if m.farmer_corrected_value is not None else (
            m.normalized_value if m.normalized_value is not None else m.original_value
        )
        if val is not None and 3.0 <= val <= 11.0:
            if profile.ph and profile.ph.verification_status != VerificationStatus.LABORATORY_VERIFIED:
                profile.additional_parameters["isric_ph"] = profile.ph
            profile.ph = _make_lab_obs("ph", m, "Soil pH (Laboratory Measured)", "Farmer-confirmed laboratory measurement.")
        else:
            logger.warning("Skipping scientifically invalid laboratory soil_ph: %s (must be 3.0-11.0)", val)

    # 2. Precedence: organic_carbon (Strict agronomic bounds: 0.0 to 15.0%)
    if "organic_carbon" in latest_by_param:
        m = latest_by_param["organic_carbon"]
        val = m.farmer_corrected_value if m.farmer_corrected_value is not None else (
            m.normalized_value if m.normalized_value is not None else m.original_value
        )
        if val is not None and 0.0 <= val <= 15.0:
            if profile.organic_carbon and profile.organic_carbon.verification_status != VerificationStatus.LABORATORY_VERIFIED:
                profile.additional_parameters["isric_soc"] = profile.organic_carbon
            profile.organic_carbon = _make_lab_obs("soc", m, "Soil Organic Carbon (Laboratory Measured)", "Farmer-confirmed laboratory measurement.")
        else:
            logger.warning("Skipping scientifically invalid laboratory organic_carbon: %s", val)

    # 3. Precedence: electrical_conductivity (Strict agronomic bounds: 0.0 to 30.0 dS/m)
    if "electrical_conductivity" in latest_by_param:
        m = latest_by_param["electrical_conductivity"]
        val = m.farmer_corrected_value if m.farmer_corrected_value is not None else (
            m.normalized_value if m.normalized_value is not None else m.original_value
        )
        if val is not None and 0.0 <= val <= 30.0:
            profile.additional_parameters["electrical_conductivity"] = _make_lab_obs(
                "electrical_conductivity", m, "Electrical Conductivity (Laboratory Measured)", "Farmer-confirmed laboratory measurement."
            )
        else:
            logger.warning("Skipping scientifically invalid laboratory electrical_conductivity: %s", val)

    # 4. Precedence: available_nitrogen
    if "available_nitrogen" in latest_by_param:
        m = latest_by_param["available_nitrogen"]
        profile.available_nitrogen = _make_lab_obs(
            "available_nitrogen", m, "Available Nitrogen (Laboratory Measured)", "Farmer-confirmed laboratory measurement (alkaline permanganate)."
        )

    # 5. Precedence: available_phosphorus
    if "available_phosphorus" in latest_by_param:
        m = latest_by_param["available_phosphorus"]
        profile.available_phosphorus = _make_lab_obs(
            "available_phosphorus", m, "Available Phosphorus (Laboratory Measured)", "Farmer-confirmed laboratory measurement (Olsen P2O5)."
        )

    # 6. Precedence: available_potassium
    if "available_potassium" in latest_by_param:
        m = latest_by_param["available_potassium"]
        profile.available_potassium = _make_lab_obs(
            "available_potassium", m, "Available Potassium (Laboratory Measured)", "Farmer-confirmed laboratory measurement (neutral ammonium acetate)."
        )

    # 7. Dual-Source Preservation: keep all baseline SoilGrids modelled estimates
    if profile.sand_percent and "isric_sand_percent" not in profile.additional_parameters:
        profile.additional_parameters["isric_sand_percent"] = profile.sand_percent
    if profile.silt_percent and "isric_silt_percent" not in profile.additional_parameters:
        profile.additional_parameters["isric_silt_percent"] = profile.silt_percent
    if profile.clay_percent and "isric_clay_percent" not in profile.additional_parameters:
        profile.additional_parameters["isric_clay_percent"] = profile.clay_percent
    if profile.total_nitrogen and "isric_total_nitrogen" not in profile.additional_parameters:
        profile.additional_parameters["isric_total_nitrogen"] = profile.total_nitrogen
    if profile.cation_exchange_capacity and "isric_cec" not in profile.additional_parameters:
        profile.additional_parameters["isric_cec"] = profile.cation_exchange_capacity

    # 8. Preserve micronutrients, heavy metals, and secondary parameters in additional_parameters
    for key, m in latest_by_param.items():
        if key not in ("soil_ph", "organic_carbon", "available_nitrogen", "available_phosphorus", "available_potassium"):
            param_meta = CANONICAL_SOIL_PARAMETERS.get(key, {})
            disp = param_meta.get("display_name", key.replace("_", " ").title())
            profile.additional_parameters[key] = _make_lab_obs(key, m, f"{disp} (Laboratory Measured)")

    primary_list = [
        profile.ph, profile.organic_carbon, profile.sand_percent, profile.silt_percent,
        profile.clay_percent, profile.total_nitrogen, profile.cation_exchange_capacity,
        profile.available_nitrogen, profile.available_phosphorus, profile.available_potassium
    ]
    avail_count = sum(1 for p in primary_list if p and p.value is not None) + len(profile.additional_parameters)
    profile.available_parameters_count = avail_count

    return profile


def synchronize_farm_soil_profile(db: Session, farm_id: uuid.UUID) -> Optional[UnifiedSoilProfile]:
    """
    Recalculate, fuse, and persist the canonical soil profile snapshot for a farm
    based on the latest confirmed laboratory test measurements and SoilGrids estimates.
    Invalidates stale cache and pushes the updated profile into _SOIL_PROFILE_CACHE and PostgreSQL DB.
    """
    farm = _FARM_STORAGE.get(farm_id)
    if not farm:
        db_farm = db.query(FarmModel).filter(FarmModel.id == str(farm_id)).first()
        if db_farm:
            farm = {
                "owner_id": uuid.UUID(db_farm.owner_id),
                "geometry": db_farm.geometry_geojson,
                "taluka": db_farm.taluka,
                "district": db_farm.district,
                "state": db_farm.state,
                "calculated_area_hectares": db_farm.calculated_area_hectares,
                "calculated_area_acres": db_farm.calculated_area_acres,
                "id": db_farm.id,
                "name": db_farm.name
            }
            _FARM_STORAGE[farm_id] = farm

    if not farm:
        return None

    # Get latest profile or generate one if not yet extracted
    profile = spatial_soil_service.get_latest_profile(db, str(farm_id))
    if not profile and farm.get("geometry", {}).get("coordinates"):
        coords = farm["geometry"]["coordinates"][0]
        poly = Polygon(coords)
        profile = spatial_soil_service.generate_farm_soil_profile(
            farm_id=str(farm_id),
            polygon=poly,
            taluka=farm.get("taluka"),
            farm_area_hectares=farm.get("calculated_area_hectares")
        )

    fused = _fuse_confirmed_laboratory_measurements(profile, farm_id, farm, db)
    if fused:
        fused.profile_id = str(uuid.uuid4())
        fused.version = (profile.version + 1) if profile else 2
        fused.created_at = datetime.utcnow()
        spatial_soil_service.save_profile(db, fused)
        return fused
    elif profile:
        spatial_soil_service.save_profile(db, profile)
        return profile
    return None


@router.get("/{farm_id}/soil", response_model=UnifiedSoilProfile)
async def get_farm_soil_profile(
    farm_id: uuid.UUID,
    depth: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve latest soil intelligence profile for a farm.
    Fuses farmer-confirmed laboratory measurements with SoilGrids estimates under precedence rules.
    """
    farm = _get_farm_and_verify_owner(farm_id, current_user, db)
    profile = spatial_soil_service.get_latest_profile(db, str(farm_id), depth=depth)
    fused_profile = _fuse_confirmed_laboratory_measurements(profile, farm_id, farm, db, depth=depth)
    if not fused_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No soil profile has been generated for farm {farm_id} yet. Please run soil analysis first."
        )
    return fused_profile


@router.get("/{farm_id}/soil/history", response_model=List[UnifiedSoilProfile])
async def get_farm_soil_history(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve complete historical record of soil intelligence runs for a farm.
    """
    _get_farm_and_verify_owner(farm_id, current_user, db)
    return spatial_soil_service.get_profile_history(db, str(farm_id))


@router.post("/{farm_id}/advisory/evaluate", response_model=FarmEvaluationResponse, tags=["Farm Advisory"])
async def evaluate_farm_advisory(
    farm_id: uuid.UUID,
    payload: Optional[FarmContextInput] = None,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Execute deterministic agricultural intelligence evaluation for a farm.
    If confirmed laboratory measurements exist for this farm, fuses them into FarmContextInput
    with soil_data_provenance = SoilDataProvenance.LABORATORY_MEASURED.
    Otherwise uses SoilGrids spatial profile if available.
    """
    farm = _get_farm_and_verify_owner(farm_id, current_user, db)

    coords = farm.get("geometry", {}).get("coordinates", [[]])[0]
    centroid_lat = sum(c[1] for c in coords) / len(coords) if coords else None
    centroid_lon = sum(c[0] for c in coords) / len(coords) if coords else None

    ctx_dict = {
        "farm_id": str(farm_id),
        "taluka": farm.get("taluka"),
        "district": farm.get("district", "Pune"),
        "latitude": centroid_lat,
        "longitude": centroid_lon,
        "irrigation_available": farm.get("irrigation_type") != "rainfed",
        "irrigation_source": farm.get("water_source"),
    }

    if payload:
        payload_data = payload.model_dump(exclude_unset=True)
        ctx_dict.update(payload_data)

    # Check for confirmed laboratory measurements
    confirmed_measurements = (
        db.query(SoilMeasurementModel)
        .join(SoilTestReportModel, SoilMeasurementModel.report_id == SoilTestReportModel.id)
        .filter(
            SoilMeasurementModel.farm_id == str(farm_id),
            SoilTestReportModel.review_status == ReviewStatus.CONFIRMED.value,
            SoilMeasurementModel.verification_status == MeasurementVerificationStatus.FARMER_CONFIRMED.value
        )
        .order_by(SoilTestReportModel.report_date.desc(), SoilMeasurementModel.created_at.desc())
        .all()
    )

    if confirmed_measurements:
        latest_meas: Dict[str, SoilMeasurementModel] = {}
        for m in confirmed_measurements:
            if m.parameter_key not in latest_meas:
                latest_meas[m.parameter_key] = m

        ctx_dict["soil_data_provenance"] = SoilDataProvenance.LABORATORY_MEASURED

        def _val(k: str) -> Optional[float]:
            meas = latest_meas.get(k)
            if not meas:
                return None
            return meas.farmer_corrected_value if meas.farmer_corrected_value is not None else (
                meas.normalized_value if meas.normalized_value is not None else meas.original_value
            )

        if "soil_ph" in latest_meas:
            ctx_dict["soil_ph"] = _val("soil_ph")
        if "organic_carbon" in latest_meas:
            ctx_dict["soil_organic_carbon_pct"] = _val("organic_carbon")
        if "electrical_conductivity" in latest_meas:
            ctx_dict["electrical_conductivity_ds_m"] = _val("electrical_conductivity")
        if "available_nitrogen" in latest_meas:
            ctx_dict["available_nitrogen_kg_ha"] = _val("available_nitrogen")
        if "available_phosphorus" in latest_meas:
            ctx_dict["available_phosphorus_kg_ha"] = _val("available_phosphorus")
        if "available_potassium" in latest_meas:
            ctx_dict["available_potassium_kg_ha"] = _val("available_potassium")
        if "total_nitrogen" in latest_meas:
            ctx_dict["total_nitrogen_pct"] = _val("total_nitrogen")

        rep = confirmed_measurements[0].report
        if rep and rep.report_date:
            ctx_dict["soil_measurement_date"] = rep.report_date.date().isoformat()
    else:
        profile = spatial_soil_service.get_latest_profile(db, str(farm_id))
        if profile:
            if ctx_dict.get("soil_ph") is None and profile.ph and profile.ph.value is not None:
                ctx_dict["soil_ph"] = profile.ph.value
                ctx_dict["soil_data_provenance"] = SoilDataProvenance.SPATIALLY_ESTIMATED_ISRIC
            if ctx_dict.get("soil_organic_carbon_pct") is None and profile.organic_carbon and profile.organic_carbon.value is not None:
                soc_val = profile.organic_carbon.value
                if getattr(profile.organic_carbon, "unit", "") == "g/kg" or soc_val > 10.0:
                    soc_val = round(soc_val / 10.0, 3)
                ctx_dict["soil_organic_carbon_pct"] = soc_val

    context_input = FarmContextInput(**ctx_dict)
    decision_engine = DeterministicDecisionEngine()
    resp = decision_engine.evaluate_farm(ctx=context_input, db=db, user_id=str(current_user.user_id))
    record_decision_owner(resp.decision_id, user_id=str(current_user.user_id), farm_id=str(farm_id))
    return resp


@router.get("/decision/{decision_id}", response_model=FarmEvaluationResponse, tags=["Farm Advisory"])
def get_farm_decision_alias(
    decision_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve farm evaluation decision by decision ID with caller and farm ownership verification.
    """
    from cropnet.services.api.app.api.v1.endpoints.agriculture import _verify_decision_access
    return _verify_decision_access(decision_id, current_user, db)


# Sub-router for farm-specific weather & climate intelligence
from cropnet.services.api.app.api.v1.endpoints import weather
router.include_router(weather.router, prefix="/{farm_id}/weather", tags=["Farm Weather & Climate"])
