"""
Satellite Vegetation Intelligence Collector for Farm Health Snapshot.

Retrieves Copernicus Sentinel-2 Level-2A surface reflectance observations,
segregated pure Class 4 canopy indices (NDVI/NDMI), and spatial quality statuses.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from cropnet.services.api.app.schemas.farm_health import (
    DataAvailabilityState,
    SatelliteDomainSummary,
    SatelliteRasterUrls,
)
from cropnet.services.api.app.models.satellite import (
    SatelliteVegetationObservationModel,
)
from cropnet.services.api.app.services.farm_health.collectors.base import (
    BaseDomainCollector,
    compute_age_days,
    utc_now,
)

logger = logging.getLogger(__name__)

SATELLITE_FRESH_THRESHOLD_DAYS = 14
SATELLITE_STALE_THRESHOLD_DAYS = 30


class SatelliteCollector(BaseDomainCollector):
    """
    Collects Copernicus Sentinel-2 L2A observations for a farm boundary.
    """

    @property
    def domain_name(self) -> str:
        return "satellite"

    def collect(self, farm: Dict[str, Any], db: Session, **kwargs) -> SatelliteDomainSummary:
        farm_id = str(farm["id"])
        now = utc_now()

        # Query latest observation
        obs = (
            db.query(SatelliteVegetationObservationModel)
            .filter(SatelliteVegetationObservationModel.farm_id == farm_id)
            .order_by(SatelliteVegetationObservationModel.observation_date.desc())
            .first()
        )

        # Case A: ZERO satellite observations recorded
        if not obs:
            return SatelliteDomainSummary(
                availability_state=DataAvailabilityState.NOT_AVAILABLE,
                observation_date=None,
                observation_age_days=None,
                sensor="Sentinel-2 L2A",
                product_id=None,
                canopy_ndvi=None,
                canopy_ndmi=None,
                composite_mean_ndvi=None,
                bare_soil_mean_ndvi=None,
                vegetation_coverage_percent=None,
                bare_soil_coverage_percent=None,
                cloud_masked_percent=None,
                valid_pixel_count=0,
                quality_status=None,
                is_small_farm_warning=False,
                raster_maps=SatelliteRasterUrls(
                    ndvi_map_url=None,
                    ndmi_map_url=None,
                    scl_map_url=None,
                ),
                agronomic_interpretation=(
                    "No satellite synchronization has been performed for this farm boundary. "
                    "Trigger satellite sync to compute Sentinel-2 canopy vigor."
                ),
            )

        # Case B: Observation exists
        obs_date = obs.observation_date
        obs_age_days = compute_age_days(obs_date, now)

        # Relative raster map URLs
        raster_maps = SatelliteRasterUrls(
            ndvi_map_url=f"/api/v1/farms/{farm_id}/satellite/latest/raster-map?index_type=ndvi",
            ndmi_map_url=f"/api/v1/farms/{farm_id}/satellite/latest/raster-map?index_type=ndmi",
            scl_map_url=f"/api/v1/farms/{farm_id}/satellite/latest/raster-map?index_type=scl",
        )

        # Metrics
        canopy_ndvi = obs.vegetation_mean_ndvi if obs.vegetation_mean_ndvi is not None else obs.mean_ndvi
        canopy_ndmi = obs.vegetation_mean_ndmi if obs.vegetation_mean_ndmi is not None else obs.mean_ndmi
        composite_mean = obs.mean_ndvi
        bare_soil_ndvi = obs.bare_soil_mean_ndvi
        veg_cov = obs.vegetation_coverage_percent
        soil_cov = obs.bare_soil_coverage_percent
        cloud_pct = obs.cloud_masked_percent or 0.0
        valid_px = obs.valid_pixel_count or 0
        q_status = obs.quality_status
        is_small = bool(obs.is_small_farm_warning)

        # Freshness and Availability State evaluation
        if obs_age_days is not None and obs_age_days > SATELLITE_STALE_THRESHOLD_DAYS:
            availability_state = DataAvailabilityState.STALE
            interpretation = (
                f"Satellite observation is {obs_age_days} days old (>30 days). "
                "Historical canopy vigor may not reflect current vegetative stage. Trigger satellite sync."
            )
        elif cloud_pct >= 100.0 or valid_px == 0:
            availability_state = DataAvailabilityState.INSUFFICIENT_EVIDENCE
            interpretation = (
                "Observation is 100% obstructed by clouds/shadows or contains zero valid surface pixels. "
                "Data insufficient for agronomic evaluation."
            )
        elif cloud_pct > 50.0 or is_small:
            availability_state = DataAvailabilityState.PARTIALLY_AVAILABLE
            reason = "cloud cover > 50%" if cloud_pct > 50.0 else "small farm warning (<0.5 ha / <5 pixels)"
            interpretation = f"Observation partially available ({reason}). Canopy vigor metrics may carry spatial uncertainty."
        else:
            availability_state = DataAvailabilityState.AVAILABLE
            vig_level = "High" if (canopy_ndvi or 0) >= 0.6 else ("Moderate" if (canopy_ndvi or 0) >= 0.4 else "Sparse")
            cov_str = f"{veg_cov:.1f}%" if veg_cov is not None else "parcel"
            c_val = f"{canopy_ndvi:.2f}" if canopy_ndvi is not None else "N/A"
            interpretation = (
                f"Active photosynthetic canopy covering {cov_str} of parcel. "
                f"{vig_level} vegetative biomass vigor (canopy NDVI {c_val})."
            )

        return SatelliteDomainSummary(
            availability_state=availability_state,
            observation_date=obs_date,
            observation_age_days=obs_age_days,
            sensor=obs.sensor or "Sentinel-2 L2A",
            product_id=obs.product_id,
            canopy_ndvi=canopy_ndvi,
            canopy_ndmi=canopy_ndmi,
            composite_mean_ndvi=composite_mean,
            bare_soil_mean_ndvi=bare_soil_ndvi,
            vegetation_coverage_percent=veg_cov,
            bare_soil_coverage_percent=soil_cov,
            cloud_masked_percent=cloud_pct,
            valid_pixel_count=valid_px,
            quality_status=q_status,
            is_small_farm_warning=is_small,
            raster_maps=raster_maps,
            agronomic_interpretation=interpretation,
        )
