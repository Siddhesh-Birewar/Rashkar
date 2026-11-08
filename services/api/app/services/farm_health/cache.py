"""
In-Memory TTL Cache for Unified Farm Health Snapshots.

Maintains a 5-minute (300 seconds) cache of assembled FarmHealthSnapshotResponse objects
keyed by farm_id to eliminate redundant DB and external queries.
Supports farm-specific invalidation via invalidate_snapshot(farm_id).
"""
import threading
from typing import Dict, Optional, Tuple
from datetime import datetime, timezone
import logging

from cropnet.services.api.app.schemas.farm_health import FarmHealthSnapshotResponse

logger = logging.getLogger(__name__)

SNAPSHOT_CACHE_TTL_SECONDS = 300  # 5 minutes


class FarmHealthSnapshotCache:
    """
    Thread-safe in-memory cache for Farm Health Snapshots.
    """

    def __init__(self, ttl_seconds: int = SNAPSHOT_CACHE_TTL_SECONDS):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[FarmHealthSnapshotResponse, datetime]] = {}
        self._lock = threading.Lock()

    def get(self, farm_id: str) -> Optional[FarmHealthSnapshotResponse]:
        """
        Retrieve cached snapshot if present and younger than TTL.
        Returns None on cache miss or expiration.
        """
        farm_key = str(farm_id)
        with self._lock:
            if farm_key not in self._cache:
                return None
            snapshot, cached_at = self._cache[farm_key]
            now = datetime.now(timezone.utc)
            if cached_at.tzinfo is None:
                cached_at = cached_at.replace(tzinfo=timezone.utc)
            age = (now - cached_at).total_seconds()
            if age >= self.ttl_seconds:
                del self._cache[farm_key]
                return None
            return snapshot

    def set(self, farm_id: str, snapshot: FarmHealthSnapshotResponse) -> None:
        """Store snapshot in cache with current timestamp."""
        farm_key = str(farm_id)
        now = datetime.now(timezone.utc)
        with self._lock:
            self._cache[farm_key] = (snapshot, now)

    def invalidate(self, farm_id: str) -> bool:
        """
        Invalidate cached snapshot for a specific farm.
        Returns True if an entry was removed, False otherwise.
        """
        farm_key = str(farm_id)
        with self._lock:
            if farm_key in self._cache:
                del self._cache[farm_key]
                logger.info("Invalidated farm health snapshot cache for farm %s", farm_key)
                return True
            return False

    def clear(self) -> None:
        """Clear all entries in cache."""
        with self._lock:
            self._cache.clear()


# Global cache instance
_snapshot_cache = FarmHealthSnapshotCache()


def get_snapshot_cache() -> FarmHealthSnapshotCache:
    """Return the global snapshot cache singleton."""
    return _snapshot_cache


def invalidate_snapshot(farm_id: str) -> bool:
    """
    Public helper to invalidate a farm's cached snapshot.
    Call this from mutation endpoints (e.g. soil report confirmation, water source creation, satellite sync).
    """
    return _snapshot_cache.invalidate(farm_id)
