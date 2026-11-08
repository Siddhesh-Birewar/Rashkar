"""
Base Collector Interface & Common Utilities for Farm Health Aggregation.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(timezone.utc)


def compute_age_days(dt: Optional[datetime], now: Optional[datetime] = None) -> Optional[int]:
    """
    Compute age in full days between an observation timestamp and current UTC time.
    Handles both naive and timezone-aware datetimes safely.
    """
    if dt is None:
        return None
    now = now or utc_now()
    if dt.tzinfo is None:
        # Treat naive datetime as UTC
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    days = delta.days
    return max(0, days)


class BaseDomainCollector(ABC):
    """
    Abstract interface for isolated domain intelligence collectors.
    Guarantees domain isolation: any unhandled exception inside a collector
    must be caught by the aggregator so one domain's failure does not crash the snapshot.
    """

    @property
    @abstractmethod
    def domain_name(self) -> str:
        """Name of the intelligence domain."""
        pass

    @abstractmethod
    def collect(
        self,
        farm: Dict[str, Any],
        db: Session,
        **kwargs
    ) -> Any:
        """
        Collect domain summary for the given farm.
        Must return domain-specific Pydantic summary model.
        """
        pass
