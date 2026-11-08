"""
CropNet AI — Master Farm Health Aggregation Service.

Orchestrates domain-specific collectors (Soil, Water, Satellite, Weather, Crop),
guarantees per-domain fault isolation, enforces strict governance against
universal health scores and synthetic data, and manages 5-minute TTL caching.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid
import logging
from sqlalchemy.orm import Session

from cropnet.services.api.app.schemas.farm_health import (
    DataAvailabilityState,
    OverallEvidenceOverview,
    SoilDomainSummary,
    SoilKeyIndicators,
    WaterDomainSummary,
    WaterKeyIndicators,
    SatelliteDomainSummary,
    SatelliteRasterUrls,
    WeatherDomainSummary,
    CurrentWeatherSummary,
    ForecastSummary,
    ClimateNormalsSummary,
    CropContextDomainSummary,
    FarmHealthSnapshotResponse,
)
from cropnet.services.api.app.services.farm_health.collectors import (
    SoilCollector,
    WaterCollector,
    SatelliteCollector,
    WeatherCollector,
    CropCollector,
)
from cropnet.services.api.app.services.farm_health.cache import (
    get_snapshot_cache,
    FarmHealthSnapshotCache,
)
from cropnet.services.api.app.services.farm_health.collectors.base import utc_now

logger = logging.getLogger(__name__)


class FarmHealthAggregator:
    """
    Master aggregator generating versioned FarmHealthSnapshotResponse payloads.
    """

    def __init__(self, cache: Optional[FarmHealthSnapshotCache] = None):
        self.cache = cache or get_snapshot_cache()
        self.soil_collector = SoilCollector()
        self.water_collector = WaterCollector()
        self.satellite_collector = SatelliteCollector()
        self.weather_collector = WeatherCollector()
        self.crop_collector = CropCollector()

    def get_snapshot(
        self,
        farm: Dict[str, Any],
        db: Session,
        force_refresh: bool = False,
        target_season: Optional[str] = None,
    ) -> FarmHealthSnapshotResponse:
        """
        Generate or retrieve cached unified health snapshot for a farm parcel.
        """
        farm_id = str(farm["id"])

        # 1. In-memory cache lookup
        if not force_refresh:
            cached = self.cache.get(farm_id)
            if cached is not None:
                logger.debug("Snapshot cache HIT for farm %s", farm_id)
                return cached
            logger.debug("Snapshot cache MISS for farm %s", farm_id)

        # 2. Collect domain summaries with strict fault isolation
        soil_summary = self._collect_soil_safe(farm, db)
        water_summary = self._collect_water_safe(farm, db)
        satellite_summary = self._collect_satellite_safe(farm, db)
        weather_summary = self._collect_weather_safe(farm, db, force_refresh=force_refresh)
        crop_summary = self._collect_crop_safe(farm, db, target_season=target_season)

        # 3. Compute categorical evidence completeness overview (NO health score)
        overall_overview = self._compute_evidence_overview(
            soil=soil_summary,
            water=water_summary,
            satellite=satellite_summary,
            weather=weather_summary,
            crop=crop_summary,
        )

        # 4. Resolve spatial & parcel area
        area_ha = float(farm.get("calculated_area_hectares") or 1.0)
        area_acres = float(farm.get("calculated_area_acres") or round(area_ha * 2.47105, 2))

        farm_uuid = uuid.UUID(farm_id) if not isinstance(farm["id"], uuid.UUID) else farm["id"]
        owner_id_val = farm["owner_id"]
        owner_uuid = uuid.UUID(str(owner_id_val)) if not isinstance(owner_id_val, uuid.UUID) else owner_id_val

        snapshot = FarmHealthSnapshotResponse(
            contract_version="1.0",
            farm_id=farm_uuid,
            farm_name=farm.get("farm_name") or farm.get("name", "Farm Parcel"),
            owner_id=owner_uuid,
            taluka=farm.get("taluka", "Indapur"),
            district=farm.get("district", "Pune"),
            state=farm.get("state", "Maharashtra"),
            calculated_area_hectares=area_ha,
            calculated_area_acres=area_acres,
            snapshot_timestamp=utc_now(),
            overall_evidence_overview=overall_overview,
            soil=soil_summary,
            water=water_summary,
            satellite=satellite_summary,
            weather=weather_summary,
            crop_context=crop_summary,
            governance_notice=(
                "CropNet AI provides independent, evidence-gated agricultural domain summaries. "
                "In accordance with institutional agricultural guidelines, no universal health score is computed."
            ),
        )

        # 5. Store assembled snapshot in TTL cache
        self.cache.set(farm_id, snapshot)
        return snapshot

    # -----------------------------------------------------------------------
    # Isolated Collector Invokers (Domain Fault Isolation)
    # -----------------------------------------------------------------------

    def _collect_soil_safe(self, farm: Dict[str, Any], db: Session) -> SoilDomainSummary:
        try:
            return self.soil_collector.collect(farm, db)
        except Exception as e:
            logger.error("SoilCollector failed for farm %s: %s", farm.get("id"), e, exc_info=True)
            return SoilDomainSummary(
                availability_state=DataAvailabilityState.NOT_AVAILABLE,
                last_updated=None,
                data_age_days=None,
                provenance=None,
                laboratory_name=None,
                sample_depth=None,
                key_indicators=SoilKeyIndicators(),
                missing_critical_parameters=["soil_ph", "organic_carbon", "nitrogen", "phosphorus", "potassium", "texture"],
                agronomic_notes=[f"Soil intelligence extraction encountered a technical error: {str(e)}"],
            )

    def _collect_water_safe(self, farm: Dict[str, Any], db: Session) -> WaterDomainSummary:
        try:
            return self.water_collector.collect(farm, db)
        except Exception as e:
            logger.error("WaterCollector failed for farm %s: %s", farm.get("id"), e, exc_info=True)
            return WaterDomainSummary(
                availability_state=DataAvailabilityState.NOT_AVAILABLE,
                last_updated=None,
                data_age_days=None,
                registered_sources_count=0,
                sources=[],
                laboratory_name=None,
                key_indicators=WaterKeyIndicators(
                    sar_status="UNAVAILABLE",
                    rsc_status="UNAVAILABLE",
                ),
                institutional_evaluations=[],
                missing_critical_parameters=["water_source", "electrical_conductivity", "sar", "rsc"],
            )

    def _collect_satellite_safe(self, farm: Dict[str, Any], db: Session) -> SatelliteDomainSummary:
        try:
            return self.satellite_collector.collect(farm, db)
        except Exception as e:
            logger.error("SatelliteCollector failed for farm %s: %s", farm.get("id"), e, exc_info=True)
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
                agronomic_interpretation=f"Satellite intelligence extraction encountered a technical error: {str(e)}",
            )

    def _collect_weather_safe(
        self, farm: Dict[str, Any], db: Session, force_refresh: bool = False
    ) -> WeatherDomainSummary:
        try:
            return self.weather_collector.collect(farm, db, force_refresh=force_refresh)
        except Exception as e:
            logger.error("WeatherCollector failed for farm %s: %s", farm.get("id"), e, exc_info=True)
            return WeatherDomainSummary(
                availability_state=DataAvailabilityState.NOT_AVAILABLE,
                last_updated=None,
                current_weather=CurrentWeatherSummary(),
                forecast=ForecastSummary(),
                climate_normals=ClimateNormalsSummary(),
            )

    def _collect_crop_safe(
        self, farm: Dict[str, Any], db: Session, target_season: Optional[str] = None
    ) -> CropContextDomainSummary:
        try:
            return self.crop_collector.collect(farm, db, target_season=target_season)
        except Exception as e:
            logger.error("CropCollector failed for farm %s: %s", farm.get("id"), e, exc_info=True)
            taluka = farm.get("taluka", "Indapur")
            return CropContextDomainSummary(
                availability_state=DataAvailabilityState.NOT_AVAILABLE,
                evaluated_at=None,
                target_season=None,
                taluka_resolved=taluka,
                evaluated_crops_count=0,
                suitable_crops=[],
                conditionally_suitable_crops=[],
                disqualified_crops=[],
                abstain_crops=[],
                top_limiting_factors=[f"Crop decision extraction encountered a technical error: {str(e)}"],
                pending_followup_questions_count=0,
            )

    # -----------------------------------------------------------------------
    # Evidence Overview & Categorical Synthesis (Zero Universal Health Score)
    # -----------------------------------------------------------------------

    def _compute_evidence_overview(
        self,
        soil: SoilDomainSummary,
        water: WaterDomainSummary,
        satellite: SatelliteDomainSummary,
        weather: WeatherDomainSummary,
        crop: CropContextDomainSummary,
    ) -> OverallEvidenceOverview:
        states = [
            soil.availability_state,
            water.availability_state,
            satellite.availability_state,
            weather.availability_state,
            crop.availability_state,
        ]

        avail_count = sum(1 for s in states if s == DataAvailabilityState.AVAILABLE)
        partial_count = sum(1 for s in states if s == DataAvailabilityState.PARTIALLY_AVAILABLE)
        stale_count = sum(1 for s in states if s == DataAvailabilityState.STALE)
        not_avail_count = sum(1 for s in states if s == DataAvailabilityState.NOT_AVAILABLE)
        insufficient_count = sum(1 for s in states if s == DataAvailabilityState.INSUFFICIENT_EVIDENCE)

        # Build actionable summary
        if not_avail_count == 5:
            actionable_summary = (
                "Zero evidence recorded for this farm. Immediate actions required: "
                "1) Run initial soil analysis or upload soil card, "
                "2) Register water source, "
                "3) Sync satellite vegetation."
            )
        elif stale_count == 5:
            actionable_summary = (
                "All recorded farm evidence is stale (>30 days for satellite, >2 hours for weather, "
                ">1 year for water, >3 years for soil, >180 days for crop evaluation). "
                "Re-synchronization and updated testing strongly recommended."
            )
        elif avail_count == 5:
            actionable_summary = "Complete actionable evidence available across all 5 domains. No blocking data gaps."
        else:
            parts: List[str] = []
            if not_avail_count > 0:
                missing_domains = []
                if soil.availability_state == DataAvailabilityState.NOT_AVAILABLE:
                    missing_domains.append("Soil")
                if water.availability_state == DataAvailabilityState.NOT_AVAILABLE:
                    missing_domains.append("Water")
                if satellite.availability_state == DataAvailabilityState.NOT_AVAILABLE:
                    missing_domains.append("Satellite")
                if weather.availability_state == DataAvailabilityState.NOT_AVAILABLE:
                    missing_domains.append("Weather")
                if crop.availability_state == DataAvailabilityState.NOT_AVAILABLE:
                    missing_domains.append("Crop context")
                parts.append(f"Missing evidence in: {', '.join(missing_domains)}")

            if stale_count > 0:
                stale_domains = []
                if soil.availability_state == DataAvailabilityState.STALE:
                    stale_domains.append("Soil")
                if water.availability_state == DataAvailabilityState.STALE:
                    stale_domains.append("Water")
                if satellite.availability_state == DataAvailabilityState.STALE:
                    stale_domains.append("Satellite")
                if weather.availability_state == DataAvailabilityState.STALE:
                    stale_domains.append("Weather")
                if crop.availability_state == DataAvailabilityState.STALE:
                    stale_domains.append("Crop context")
                parts.append(f"Stale records in: {', '.join(stale_domains)}")

            if partial_count > 0:
                parts.append(f"{partial_count} domain(s) have partial data pending verification")

            actionable_summary = f"{'; '.join(parts)}. Action required to complete farm health verification."

        return OverallEvidenceOverview(
            domains_available=avail_count,
            domains_partially_available=partial_count,
            domains_stale=stale_count,
            domains_not_available=not_avail_count,
            domains_insufficient_evidence=insufficient_count,
            total_domains=5,
            actionable_summary=actionable_summary,
        )
