"""
FastAPI REST Endpoints for Sentinel-2 Satellite-Based Vegetation Intelligence.

Prefix: /api/v1/farms/{farm_id}/satellite
Enforces:
- Supabase Bearer Authentication & Farm Ownership Verification
- Real Copernicus Sentinel-2 Level-2A surface reflectance data processing
- Real PostGIS farm polygon boundary intersection
- SCL cloud & shadow masking (classes 3, 8, 9, 10, 11)
- Deterministic NDVI (10m) and NDMI (resampled 10m) band math
- Small farm (<0.5 ha) spatial representativeness warnings
- Disclaimers that canopy reflectance is an indirect indicator, not direct yield/disease diagnosis
"""
import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

try:
    from cropnet.services.api.app.core.database import get_db
    from cropnet.services.api.app.core.security import get_current_user, CurrentUser
    from cropnet.services.api.app.api.v1.endpoints.farms import _get_farm_and_verify_owner
    from cropnet.services.api.app.models.satellite import SatelliteVegetationObservationModel
    from cropnet.services.api.app.schemas.satellite import (
        SatelliteObservationItem,
        SatelliteObservationQuality,
        SatelliteSyncRequest,
        SatelliteSyncResponse,
        VegetationTimeSeriesPoint,
        VegetationTimeSeriesResponse,
        SatelliteSpatialMetadataResponse,
    )
    from cropnet.services.api.app.services.satellite.copernicus_client import (
        copernicus_client,
        get_raster_map_path,
        get_spatial_metadata,
    )
except ImportError:
    from ...core.database import get_db
    from ...core.security import get_current_user, CurrentUser
    from .farms import _get_farm_and_verify_owner
    from ...models.satellite import SatelliteVegetationObservationModel
    from ...schemas.satellite import (
        SatelliteObservationItem,
        SatelliteObservationQuality,
        SatelliteSyncRequest,
        SatelliteSyncResponse,
        VegetationTimeSeriesPoint,
        VegetationTimeSeriesResponse,
        SatelliteSpatialMetadataResponse,
    )
    from ...services.satellite.copernicus_client import (
        copernicus_client,
        get_raster_map_path,
        get_spatial_metadata,
    )

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/farms/{farm_id}/satellite", tags=["Satellite Vegetation Intelligence"])

_ACTIVE_SYNCS = set()


@router.post("/sync", response_model=SatelliteSyncResponse, status_code=status.HTTP_200_OK)
async def sync_satellite_observations(
    farm_id: uuid.UUID,
    payload: SatelliteSyncRequest = SatelliteSyncRequest(),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Sync and compute Sentinel-2 L2A vegetation indices for the farm's polygon boundary.
    Intersects the farm boundary with Copernicus Level-2A products, applies SCL cloud masking,
    and calculates NDVI and NDMI canopy indices.
    """
    farm = _get_farm_and_verify_owner(farm_id, current_user, db)

    poly_geojson = farm.get("geometry")
    area_ha = float(farm.get("calculated_area_hectares", 1.0))

    if not poly_geojson:
        raise HTTPException(status_code=400, detail="Farm polygon geometry is missing.")

    if str(farm_id) in _ACTIVE_SYNCS:
        raise HTTPException(
            status_code=409,
            detail="A satellite synchronization is already in progress for this farm."
        )

    _ACTIVE_SYNCS.add(str(farm_id))
    try:
        # Calculate observation (attempts live Sentinel-2 L2A raster streaming)
        indices = copernicus_client.compute_polygon_indices(
            polygon_geojson=poly_geojson,
            farm_area_ha=area_ha,
            observation_date=datetime.utcnow(),
            use_live_raster=True,
            farm_id=str(farm_id),
        )

        # Fail-closed handling: If live retrieval failed or no usable observation found,
        # DO NOT insert fabricated rows into the database. Preserve existing authentic observation.
        if indices.get("quality_status") == "NO_USABLE_OBSERVATION" or not indices.get("product_id"):
            existing_historical = (
                db.query(SatelliteVegetationObservationModel)
                .filter(
                    SatelliteVegetationObservationModel.farm_id == str(farm_id),
                    SatelliteVegetationObservationModel.quality_status != "SYNTHETIC_QA_ISOLATED",
                    SatelliteVegetationObservationModel.quality_status != "NO_USABLE_OBSERVATION",
                )
                .order_by(
                    SatelliteVegetationObservationModel.observation_date.desc(),
                    SatelliteVegetationObservationModel.created_at.desc(),
                )
                .first()
            )

            latest_item = None
            if existing_historical:
                latest_item = SatelliteObservationItem(
                    id=existing_historical.id,
                    farm_id=existing_historical.farm_id,
                    observation_date=existing_historical.observation_date,
                    product_id=existing_historical.product_id,
                    tile_id=existing_historical.tile_id,
                    sensor=existing_historical.sensor,
                    mean_ndvi=existing_historical.mean_ndvi,
                    median_ndvi=existing_historical.median_ndvi,
                    min_ndvi=existing_historical.min_ndvi,
                    max_ndvi=existing_historical.max_ndvi,
                    std_ndvi=existing_historical.std_ndvi,
                    mean_ndmi=existing_historical.mean_ndmi,
                    valid_pixel_count=existing_historical.valid_pixel_count,
                    total_pixel_count=existing_historical.total_pixel_count,
                    farm_coverage_percent=existing_historical.farm_coverage_percent,
                    cloud_masked_percent=existing_historical.cloud_masked_percent,
                    spatial_resolution_meters=existing_historical.spatial_resolution_meters,
                    quality_status=SatelliteObservationQuality(existing_historical.quality_status),
                    quality_notes=existing_historical.quality_notes,
                    is_small_farm_warning=existing_historical.is_small_farm_warning,
                    vegetation_pixel_count=existing_historical.vegetation_pixel_count,
                    bare_soil_pixel_count=existing_historical.bare_soil_pixel_count,
                    water_pixel_count=existing_historical.water_pixel_count,
                    vegetation_coverage_percent=existing_historical.vegetation_coverage_percent,
                    bare_soil_coverage_percent=existing_historical.bare_soil_coverage_percent,
                    water_coverage_percent=existing_historical.water_coverage_percent,
                    vegetation_mean_ndvi=existing_historical.vegetation_mean_ndvi,
                    vegetation_mean_ndmi=existing_historical.vegetation_mean_ndmi,
                    bare_soil_mean_ndvi=existing_historical.bare_soil_mean_ndvi,
                    polygon_area_hectares=existing_historical.polygon_area_hectares or farm.get("calculated_area_hectares"),
                    raster_discretized_area_hectares=existing_historical.raster_discretized_area_hectares,
                    radiometric_conversion_provenance=existing_historical.radiometric_conversion_provenance,
                    data_attribution=existing_historical.data_attribution,
                    created_at=existing_historical.created_at,
                )

            return SatelliteSyncResponse(
                success=False,
                farm_id=str(farm_id),
                synced_observations_count=0,
                latest_observation=latest_item,
                copernicus_provider_status=indices.get("copernicus_provider_status", "PROVIDER_UNAVAILABLE"),
                message=(
                    f"Live Sentinel-2 pass unavailable. Preserving latest historical observation ({existing_historical.observation_date.strftime('%Y-%m-%d')})."
                    if existing_historical else
                    "Live Sentinel-2 pass unavailable from Copernicus provider. No historical observation recorded."
                ),
            )

        # Duplicate checking: If an observation with the exact same product_id was recorded recently (<30m), reuse it
        existing = db.query(SatelliteVegetationObservationModel).filter(
            SatelliteVegetationObservationModel.farm_id == str(farm_id),
            SatelliteVegetationObservationModel.product_id == indices["product_id"],
        ).order_by(SatelliteVegetationObservationModel.created_at.desc()).first()

        if existing and (datetime.utcnow() - existing.created_at).total_seconds() < 1800:
            obs_model = existing
        else:
            obs_model = SatelliteVegetationObservationModel(
                id=str(uuid.uuid4()),
                farm_id=str(farm_id),
                observation_date=indices["observation_date"],
                product_id=indices["product_id"],
                tile_id=indices["tile_id"],
                sensor=indices["sensor"],
                processing_baseline=indices["processing_baseline"],
                mean_ndvi=indices["mean_ndvi"],
                median_ndvi=indices["median_ndvi"],
                min_ndvi=indices["min_ndvi"],
                max_ndvi=indices["max_ndvi"],
                std_ndvi=indices["std_ndvi"],
                mean_ndmi=indices["mean_ndmi"],
                valid_pixel_count=indices["valid_pixel_count"],
                total_pixel_count=indices["total_pixel_count"],
                farm_coverage_percent=indices["farm_coverage_percent"],
                cloud_masked_percent=indices["cloud_masked_percent"],
                spatial_resolution_meters=indices["spatial_resolution_meters"],
                quality_status=indices["quality_status"],
                quality_notes=indices["quality_notes"],
                is_small_farm_warning=indices["is_small_farm_warning"],
            )
            db.add(obs_model)
            db.commit()
            db.refresh(obs_model)
    finally:
        _ACTIVE_SYNCS.discard(str(farm_id))

    obs_item = SatelliteObservationItem(
        id=obs_model.id,
        farm_id=obs_model.farm_id,
        observation_date=obs_model.observation_date,
        product_id=obs_model.product_id,
        tile_id=obs_model.tile_id,
        sensor=obs_model.sensor,
        mean_ndvi=obs_model.mean_ndvi,
        median_ndvi=obs_model.median_ndvi,
        min_ndvi=obs_model.min_ndvi,
        max_ndvi=obs_model.max_ndvi,
        std_ndvi=obs_model.std_ndvi,
        mean_ndmi=obs_model.mean_ndmi,
        valid_pixel_count=obs_model.valid_pixel_count,
        total_pixel_count=obs_model.total_pixel_count,
        farm_coverage_percent=obs_model.farm_coverage_percent,
        cloud_masked_percent=obs_model.cloud_masked_percent,
        spatial_resolution_meters=obs_model.spatial_resolution_meters,
        quality_status=SatelliteObservationQuality(obs_model.quality_status),
        quality_notes=obs_model.quality_notes,
        is_small_farm_warning=obs_model.is_small_farm_warning,
        vegetation_pixel_count=indices.get("vegetation_pixel_count", obs_model.vegetation_pixel_count),
        bare_soil_pixel_count=indices.get("bare_soil_pixel_count", obs_model.bare_soil_pixel_count),
        water_pixel_count=indices.get("water_pixel_count", obs_model.water_pixel_count),
        vegetation_coverage_percent=indices.get("vegetation_coverage_percent", obs_model.vegetation_coverage_percent),
        bare_soil_coverage_percent=indices.get("bare_soil_coverage_percent", obs_model.bare_soil_coverage_percent),
        water_coverage_percent=indices.get("water_coverage_percent", obs_model.water_coverage_percent),
        vegetation_mean_ndvi=indices.get("vegetation_mean_ndvi", obs_model.vegetation_mean_ndvi),
        vegetation_mean_ndmi=indices.get("vegetation_mean_ndmi", obs_model.vegetation_mean_ndmi),
        bare_soil_mean_ndvi=indices.get("bare_soil_mean_ndvi", obs_model.bare_soil_mean_ndvi),
        polygon_area_hectares=indices.get("polygon_area_hectares", farm.get("calculated_area_hectares")),
        raster_discretized_area_hectares=indices.get("raster_discretized_area_hectares", obs_model.raster_discretized_area_hectares),
        radiometric_conversion_provenance=indices.get("radiometric_conversion_provenance", obs_model.radiometric_conversion_provenance),
        data_attribution=indices.get("data_attribution", "Copernicus Sentinel data [2026], processed by ESA, hosted on AWS by Element 84."),
        created_at=obs_model.created_at,
    )

    return SatelliteSyncResponse(
        success=True,
        farm_id=str(farm_id),
        synced_observations_count=1,
        latest_observation=obs_item,
        copernicus_provider_status=indices["copernicus_provider_status"],
        message="Sentinel-2 Level-2A canopy reflectance observation processed successfully.",
    )


@router.get("/observations", response_model=List[SatelliteObservationItem])
async def list_observations(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List historical satellite vegetation observations for the farm."""
    _get_farm_and_verify_owner(farm_id, current_user, db)

    observations = db.query(SatelliteVegetationObservationModel).filter(
        SatelliteVegetationObservationModel.farm_id == str(farm_id),
        SatelliteVegetationObservationModel.quality_status != "SYNTHETIC_QA_ISOLATED",
    ).order_by(
        SatelliteVegetationObservationModel.observation_date.desc(),
        SatelliteVegetationObservationModel.created_at.desc()
    ).all()

    return observations


@router.get("/latest", response_model=Optional[SatelliteObservationItem])
async def get_latest_observation(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the most recent valid satellite vegetation observation for the farm."""
    _get_farm_and_verify_owner(farm_id, current_user, db)

    obs = db.query(SatelliteVegetationObservationModel).filter(
        SatelliteVegetationObservationModel.farm_id == str(farm_id),
        SatelliteVegetationObservationModel.quality_status != "SYNTHETIC_QA_ISOLATED",
    ).order_by(
        SatelliteVegetationObservationModel.observation_date.desc(),
        SatelliteVegetationObservationModel.created_at.desc()
    ).first()

    if not obs:
        raise HTTPException(status_code=404, detail="No satellite observations found for this farm.")

    return obs


@router.get("/timeseries", response_model=VegetationTimeSeriesResponse)
async def get_vegetation_timeseries(
    farm_id: uuid.UUID,
    months: int = Query(6, ge=1, le=24),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve multi-month vegetation index time-series (NDVI & NDMI trends) with agronomic interpretation."""
    farm = _get_farm_and_verify_owner(farm_id, current_user, db)
    area_ha = float(farm.get("calculated_area_hectares", 1.0))
    poly_geojson = farm.get("geometry")

    cutoff_date = datetime.utcnow() - timedelta(days=months * 30)

    observations = db.query(SatelliteVegetationObservationModel).filter(
        SatelliteVegetationObservationModel.farm_id == str(farm_id),
        SatelliteVegetationObservationModel.observation_date >= cutoff_date,
        SatelliteVegetationObservationModel.quality_status != "SYNTHETIC_QA_ISOLATED",
    ).order_by(SatelliteVegetationObservationModel.observation_date.asc()).all()

    # Return genuine persisted database observations only (never interpolate or fabricate)
    series_points = []
    for o in observations:
        series_points.append(
            VegetationTimeSeriesPoint(
                date=o.observation_date,
                mean_ndvi=o.mean_ndvi,
                median_ndvi=o.median_ndvi,
                mean_ndmi=o.mean_ndmi,
                valid_pixels=o.valid_pixel_count,
                cloud_masked_percent=o.cloud_masked_percent,
                quality_status=o.quality_status,
                vegetation_pixel_count=o.vegetation_pixel_count,
                bare_soil_pixel_count=o.bare_soil_pixel_count,
                vegetation_coverage_percent=o.vegetation_coverage_percent,
                bare_soil_coverage_percent=o.bare_soil_coverage_percent,
                vegetation_mean_ndvi=o.vegetation_mean_ndvi,
                vegetation_mean_ndmi=o.vegetation_mean_ndmi,
            )
        )

    is_small_farm = area_ha < 0.5 or (series_points and series_points[-1].valid_pixels < 5)

    if not series_points:
        interpretation = "No satellite observations recorded yet for this parcel. Perform a sync to establish baseline."
    elif len(series_points) == 1:
        latest_ndvi = series_points[-1].mean_ndvi or 0.0
        if latest_ndvi >= 0.6:
            interpretation = "Initial baseline: Dense, actively photosynthesizing canopy cover with high biomass vigor."
        elif latest_ndvi >= 0.4:
            interpretation = "Initial baseline: Moderate canopy cover with healthy greenness."
        elif latest_ndvi >= 0.2:
            interpretation = "Initial baseline: Sparse vegetation or young crop emergence."
        else:
            interpretation = "Initial baseline: Bare soil, crop residue, or non-vegetated surface."
    else:
        latest_ndvi = series_points[-1].mean_ndvi or 0.0
        prev_ndvi = series_points[-2].mean_ndvi or 0.0
        delta = round(latest_ndvi - prev_ndvi, 3)
        if abs(delta) < 0.03:
            trend_str = "Canopy greenness is stable compared to previous observation."
        elif delta > 0:
            trend_str = f"Canopy vigor increased (+{delta}) compared to previous observation."
        else:
            trend_str = f"Canopy vigor decreased ({delta}) compared to previous observation."

        if latest_ndvi >= 0.6:
            interpretation = f"{trend_str} High biomass vigor."
        elif latest_ndvi >= 0.4:
            interpretation = f"{trend_str} Moderate canopy cover."
        else:
            interpretation = f"{trend_str} Sparse canopy or exposed soil paths."

    return VegetationTimeSeriesResponse(
        farm_id=str(farm_id),
        farm_area_hectares=area_ha,
        is_small_farm=is_small_farm,
        total_observations=len(series_points),
        series=series_points,
        vegetation_interpretation=interpretation,
        scientific_disclaimer=(
            "Sentinel-2 NDVI and NDMI reflect surface canopy spectral reflectance (10m resolution). "
            "They are indirect indicators of biomass and moisture vigor, and MUST NEVER be interpreted as "
            "direct diagnoses of specific plant pathogens, insect infestations, nutrient deficiencies, or final harvest yield."
        ),
    )


@router.get("/latest/raster-map")
async def get_latest_raster_map(
    farm_id: uuid.UUID,
    index_type: str = Query("ndvi", pattern="^(ndvi|ndmi|scl)$"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns actual clipped 2D raster map PNG for the farm polygon boundary.
    index_type: ndvi (10m canopy vigor), ndmi (20m resampled moisture), or scl (surface classification).
    """
    farm = _get_farm_and_verify_owner(farm_id, current_user, db)
    path = get_raster_map_path(str(farm_id), index_type)
    if not path or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Derived raster map not found for this farm.")

    meta = get_spatial_metadata(str(farm_id)) or {}
    bounds = meta.get("bounds", [])
    headers = {"X-Raster-Bounds": json.dumps(bounds)} if bounds else {}

    return FileResponse(path, media_type="image/png", headers=headers)


@router.get("/latest/spatial-metadata", response_model=SatelliteSpatialMetadataResponse)
async def get_latest_spatial_metadata(
    farm_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns spatial coordinate bounds, pixel dimensions, and band disclosures for the clipped farm raster.
    """
    farm = _get_farm_and_verify_owner(farm_id, current_user, db)
    meta = get_spatial_metadata(str(farm_id))
    if not meta:
        raise HTTPException(status_code=404, detail="Spatial metadata not available for this farm.")

    return SatelliteSpatialMetadataResponse(
        farm_id=str(farm_id),
        product_id=meta.get("product_id", "Sentinel-2 L2A"),
        observation_date=datetime.fromisoformat(meta.get("observation_date", datetime.utcnow().isoformat())),
        bounds=meta.get("bounds", [0.0, 0.0, 0.0, 0.0]),
        width=meta.get("width", 40),
        height=meta.get("height", 40),
        spatial_resolution_meters=10.0,
        b11_native_resolution_meters=20.0,
        vegetation_pixel_count=meta.get("vegetation_pixel_count", 0),
        bare_soil_pixel_count=meta.get("bare_soil_pixel_count", 0),
        water_pixel_count=meta.get("water_pixel_count", 0),
        cloud_masked_pixel_count=meta.get("cloud_masked_pixel_count", 0),
        boundary_masked_pixel_count=meta.get("boundary_masked_pixel_count", 0),
        total_pixel_count=meta.get("total_pixel_count", 0),
        ndvi_map_url=f"/api/v1/farms/{farm_id}/satellite/latest/raster-map?index_type=ndvi",
        ndmi_map_url=f"/api/v1/farms/{farm_id}/satellite/latest/raster-map?index_type=ndmi",
        scl_map_url=f"/api/v1/farms/{farm_id}/satellite/latest/raster-map?index_type=scl",
        legend={
            "ndvi": {
                "high_canopy": {"label": "High Canopy Vigor (NDVI > 0.60)", "color": "#2E7D32"},
                "moderate_canopy": {"label": "Moderate Canopy (NDVI 0.40 - 0.60)", "color": "#689F38"},
                "bare_soil": {"label": "Bare Soil Paths (NDVI 0.20 - 0.40)", "color": "#D7CCC8"},
                "masked": {"label": "Cloud / Shadow / Edge Masked", "color": "#BDBDBD"},
            },
            "ndmi": {
                "high_moisture": {"label": "High Canopy Moisture (NDMI > 0.20)", "color": "#0288D1"},
                "moderate_moisture": {"label": "Moderate Canopy Moisture (NDMI 0.10 - 0.20)", "color": "#26C6DA"},
                "low_moisture": {"label": "Dry / Exposed Soil", "color": "#D7CCC8"},
            },
            "scl": {
                "vegetation": {"label": "Vegetation Canopy (Class 4)", "color": "#2E7D32"},
                "bare_soil": {"label": "Bare Soil / Paths (Class 5)", "color": "#D7CCC8"},
                "water": {"label": "Water (Class 6)", "color": "#1976D2"},
                "cloud": {"label": "Cloud / Shadow (Classes 3,8,9,10,11)", "color": "#EEEEEE"},
            }
        },
        scientific_disclosure=(
            "Raster displays 10m Ground Sample Distance (GSD) pixels clipped to farm polygon boundary. "
            "NDMI incorporates 20m SWIR Band 11 bilinearly aligned to 10m NIR Band 8. "
            "Surface reflectance values represent canopy optical behavior and must not be used as standalone pathogen diagnoses."
        )
    )
