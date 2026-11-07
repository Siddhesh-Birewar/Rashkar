"""
CropNet AI — Agricultural Knowledge Retriever.

Executes parameterized queries against Phase 4 PostgreSQL knowledge tables
and retrieves verified crop requirements, decoupled irrigation statements,
Bahar daily tree water tables, and institutional source citations.
"""
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

from cropnet.services.api.app.services.crop_knowledge.crop_service import CropKnowledgeService
from cropnet.services.api.app.schemas.crop import CropFullProfileResponse, AgriculturalKnowledgeSourceResponse
from cropnet.services.api.app.schemas.agriculture_intelligence import CitationMetadata
from cropnet.services.api.app.services.agriculture_intelligence.evidence_gate import EvidenceGate, SOURCE_TIER_MAPPING


class KnowledgeRetriever:
    """
    Retrieves validated crop requirements and source metadata.
    """

    def __init__(self, crop_service: Optional[CropKnowledgeService] = None):
        self.crop_service = crop_service or CropKnowledgeService()

    def get_supported_crops(self, db: Optional[Session] = None) -> List[str]:
        """Returns the canonical 10 crop IDs."""
        summaries = self.crop_service.get_all_crops(db=db)
        return [s.id for s in summaries]

    def get_crop_profile(self, crop_id: str, db: Optional[Session] = None) -> Optional[CropFullProfileResponse]:
        """Retrieve full crop profile with all nested requirement modules."""
        return self.crop_service.get_crop_profile(crop_id=crop_id, db=db)

    def get_source_citation(self, source_id: Optional[str], db: Optional[Session] = None) -> Optional[CitationMetadata]:
        """Fetch granular citation metadata for a registered source ID."""
        if not source_id:
            return None
        src = self.crop_service.get_source(source_id=source_id, db=db)
        if not src:
            return None
        return EvidenceGate.format_citation(
            source_id=src.id,
            organization=src.organization,
            publication_title=src.publication_title,
            publication_year=src.publication_year,
            section_or_pages=src.section_or_pages
        )

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
