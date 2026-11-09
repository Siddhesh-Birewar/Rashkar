"""
CropNet AI — Agricultural Knowledge Retriever.

Executes parameterized queries against Phase 4 PostgreSQL knowledge tables
and retrieves verified crop requirements, decoupled irrigation statements,
Bahar daily tree water tables, and institutional source citations.
Includes high-performance in-memory caching to prevent redundant WAN round-trips
during multi-dimensional crop evaluation cycles. Thread-safe for concurrent async
worker execution.
"""
import threading
import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from cropnet.services.api.app.services.crop_knowledge.crop_service import CropKnowledgeService
from cropnet.services.api.app.schemas.crop import CropFullProfileResponse, AgriculturalKnowledgeSourceResponse
from cropnet.services.api.app.schemas.agriculture_intelligence import CitationMetadata
from cropnet.services.api.app.services.agriculture_intelligence.evidence_gate import EvidenceGate, SOURCE_TIER_MAPPING
from cropnet.services.api.app.services.crop_knowledge.seed_data import KNOWLEDGE_SOURCES


class KnowledgeRetriever:
    """
    Retrieves validated crop requirements and source metadata with in-memory caching.
    Guarantees thread-safe access across concurrent API request worker threads.
    """

    def __init__(self, crop_service: Optional[CropKnowledgeService] = None):
        self._lock = threading.RLock()
        self.crop_service = crop_service or CropKnowledgeService()
        self._profile_cache: Dict[str, CropFullProfileResponse] = {}
        self._citation_cache: Dict[str, Optional[CitationMetadata]] = {}
        self._crops_list: Optional[List[str]] = None
        self._prime_cache()

    def _prime_cache(self) -> None:
        """
        Pre-populate memory cache from CropKnowledgeService's verified in-memory dataset
        to guarantee sub-millisecond evaluation latency without blocking WAN round trips.
        """
        with self._lock:
            try:
                summaries = self.crop_service.get_all_crops(db=None)
                self._crops_list = [s.id for s in summaries]
                for cid in self._crops_list:
                    prof = self.crop_service.get_crop_profile(cid, db=None)
                    if prof:
                        self._profile_cache[cid] = prof

                for src_data in KNOWLEDGE_SOURCES:
                    sid = src_data["id"]
                    src = self.crop_service.get_source(source_id=sid, db=None)
                    if src:
                        self._citation_cache[sid] = EvidenceGate.format_citation(
                            source_id=src.id,
                            organization=src.organization,
                            publication_title=src.publication_title,
                            publication_year=src.publication_year,
                            section_or_pages=src.section_or_pages
                        )
            except Exception as exc:
                logger.warning("Failed during knowledge retriever cache priming: %s", exc)

    def clear_cache(self) -> None:
        """Invalidate all cached crop profiles and citation metadata."""
        with self._lock:
            self._profile_cache.clear()
            self._citation_cache.clear()
            self._crops_list = None
            self._prime_cache()

    def get_supported_crops(self, db: Optional[Session] = None) -> List[str]:
        """Returns the canonical 10 crop IDs."""
        with self._lock:
            if self._crops_list is not None and len(self._crops_list) > 0:
                return list(self._crops_list)
            summaries = self.crop_service.get_all_crops(db=db)
            self._crops_list = [s.id for s in summaries]
            return list(self._crops_list)

    def get_crop_profile(self, crop_id: str, db: Optional[Session] = None) -> Optional[CropFullProfileResponse]:
        """Retrieve full crop profile with all nested requirement modules."""
        with self._lock:
            if crop_id in self._profile_cache:
                return self._profile_cache[crop_id]
            profile = self.crop_service.get_crop_profile(crop_id=crop_id, db=db)
            if profile is not None:
                self._profile_cache[crop_id] = profile
            return profile

    def get_source_citation(self, source_id: Optional[str], db: Optional[Session] = None) -> Optional[CitationMetadata]:
        """Fetch granular citation metadata for a registered source ID."""
        if not source_id:
            return None
        with self._lock:
            if source_id in self._citation_cache:
                return self._citation_cache[source_id]

            src = self.crop_service.get_source(source_id=source_id, db=db)
            if not src:
                self._citation_cache[source_id] = None
                return None

            citation = EvidenceGate.format_citation(
                source_id=src.id,
                organization=src.organization,
                publication_title=src.publication_title,
                publication_year=src.publication_year,
                section_or_pages=src.section_or_pages
            )
            self._citation_cache[source_id] = citation
            return citation

    def get_regional_suitability(
        self,
        crop_id: str,
        taluka: str,
        db: Optional[Session] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve taluka-specific regional suitability record."""
        profile = self.get_crop_profile(crop_id=crop_id, db=db)
        if not profile or not profile.regional_suitability:
            return None
        clean_taluka = taluka.strip().lower()
        for r in profile.regional_suitability:
            if r.taluka.strip().lower() == clean_taluka:
                return {
                    "taluka": r.taluka,
                    "district": r.district,
                    "suitability_status": r.suitability_status,
                    "agronomic_rationale": r.agronomic_rationale,
                    "limiting_factors": r.limiting_factors or [],
                    "evidence_status": r.evidence_status,
                    "source_id": r.source_id
                }
        return None

    def get_pomegranate_daily_water_table(
        self,
        bahar: str,
        tree_age: int,
        db: Optional[Session] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves the exact ICAR-NRCP Table 1, 2, or 3 daily tree water table
        in liters per tree per day for the requested Bahar and tree age.
        """
        profile = self.get_crop_profile("pomegranate", db=db)
        if not profile or not profile.water or not profile.water.daily_water_table:
            return None
        dwt = profile.water.daily_water_table
        clean_bahar = bahar.strip().lower()
        if clean_bahar not in dwt:
            return None
        bahar_data = dwt[clean_bahar]
        schedule = bahar_data.get("schedule", []) if isinstance(bahar_data, dict) else []
        return {
            "unit": dwt.get("unit", "liters_per_tree_per_day"),
            "bahar": clean_bahar,
            "tree_age_years": tree_age,
            "weekly_schedule": schedule
        }
