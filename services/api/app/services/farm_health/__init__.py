"""
CropNet AI — Phase 5.9A Unified Farm Health Backend Aggregation Package.
"""
from cropnet.services.api.app.schemas.farm_health import (
    DataAvailabilityState,
    FarmHealthSnapshotResponse,
    OverallEvidenceOverview,
    SoilDomainSummary,
    WaterDomainSummary,
    SatelliteDomainSummary,
    WeatherDomainSummary,
    CropContextDomainSummary,
)
from cropnet.services.api.app.services.farm_health.aggregator import FarmHealthAggregator
from cropnet.services.api.app.services.farm_health.cache import (
    invalidate_snapshot,
    get_snapshot_cache,
    FarmHealthSnapshotCache,
)

__all__ = [
    "FarmHealthAggregator",
    "DataAvailabilityState",
    "FarmHealthSnapshotResponse",
    "OverallEvidenceOverview",
    "SoilDomainSummary",
    "WaterDomainSummary",
    "SatelliteDomainSummary",
    "WeatherDomainSummary",
    "CropContextDomainSummary",
    "invalidate_snapshot",
    "get_snapshot_cache",
    "FarmHealthSnapshotCache",
]
