"""
CropNet AI — Evidence Gate for Deterministic Agricultural Intelligence.

Classifies agricultural evidence into canonical tiers, ensures that unverified
or bibliographic sources do not trigger hard agronomic disqualifications,
and strictly prevents silent evidence upgrading.
"""
from typing import Optional, Dict, Any, Tuple
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    EvidenceTier,
    CitationMetadata,
    EnforcementLevel
)


# Canonical mapping of registered Supabase source IDs to evidence tiers
SOURCE_TIER_MAPPING: Dict[str, EvidenceTier] = {
    # Tier 1: Verified Authoritative Literature
    "mpkv_research_2023": EvidenceTier.VERIFIED,
    "mpkv_pop_2023": EvidenceTier.VERIFIED,
    "icrisat_chickpea_2010": EvidenceTier.VERIFIED,
    "icar_nrcp_manage_2022": EvidenceTier.VERIFIED,
    
    # Tier 2: Conditionally Supported Institutional Bulletins
    "icar_cicr_cotton_2022": EvidenceTier.CONDITIONALLY_SUPPORTED,
    "icar_iiwbr_wheat_2022": EvidenceTier.CONDITIONALLY_SUPPORTED,
    "icar_iisr_soybean_2022": EvidenceTier.CONDITIONALLY_SUPPORTED,
    "icar_iimr_millets_2022": EvidenceTier.CONDITIONALLY_SUPPORTED,
    
    # Tier 3: Unverified Bibliographic / General Brochures
    "iisr_brochure_glance": EvidenceTier.UNVERIFIED_BIBLIOGRAPHIC,
    "icar_iisr_sugarcane_2022": EvidenceTier.UNVERIFIED_BIBLIOGRAPHIC,
    "icar_iipr_pulses_2022": EvidenceTier.UNVERIFIED_BIBLIOGRAPHIC,
    
    # Tier 4: Superseded Historical Manuals
    "icar_nrcp_pomegranate_2021": EvidenceTier.UNVERIFIED_BIBLIOGRAPHIC
}


class EvidenceGate:
    """
    Evaluates evidence quality before allowing a rule to disqualify a crop
    or prescribe numerical dosages.
    """

    @staticmethod
    def get_tier(source_id: Optional[str]) -> EvidenceTier:
        """Resolve evidence tier for a given source ID."""
        if not source_id:
            return EvidenceTier.UNSUPPORTED
        return SOURCE_TIER_MAPPING.get(source_id, EvidenceTier.UNSUPPORTED)

    @staticmethod
    def can_enforce_hard_disqualification(tier: EvidenceTier, enforcement_level: Optional[EnforcementLevel] = None) -> bool:
        """
        Only VERIFIED and CONDITIONALLY_SUPPORTED evidence under explicit
        VERIFIED_HARD_CONSTRAINT enforcement level can enforce hard agronomic disqualifications.
        """
        if enforcement_level is not None:
            return enforcement_level == EnforcementLevel.VERIFIED_HARD_CONSTRAINT and tier in (EvidenceTier.VERIFIED, EvidenceTier.CONDITIONALLY_SUPPORTED)
        return tier in (EvidenceTier.VERIFIED, EvidenceTier.CONDITIONALLY_SUPPORTED)

    @staticmethod
    def can_prescribe_numerical_dosages(tier: EvidenceTier) -> bool:
        """
        Only VERIFIED evidence can prescribe hard numerical thresholds or quantitative inputs.
        """
        return tier == EvidenceTier.VERIFIED

    @staticmethod
    def format_citation(
        source_id: str,
        organization: str,
        publication_title: str,
        publication_year: Optional[int] = None,
        section_or_pages: Optional[str] = None
    ) -> CitationMetadata:
        """Create structured citation metadata with explicit evidence tier."""
        tier = EvidenceGate.get_tier(source_id)
        return CitationMetadata(
            source_id=source_id,
            organization=organization,
            publication_title=publication_title,
            publication_year=publication_year,
            section_or_pages=section_or_pages,
            evidence_tier=tier
        )
