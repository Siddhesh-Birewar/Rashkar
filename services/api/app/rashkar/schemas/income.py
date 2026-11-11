"""Re-exports CropNet Extra Income Pydantic schemas under `app.rashkar.schemas`."""

try:
    from cropnet.services.api.app.schemas.income import (
        DiscoveredOpportunity,
        EnterpriseFinancialAnalysis,
        FarmerResourceProfile,
        FinancialScenarioItem,
        OpportunityCatalogItem,
        OpportunityComparisonItem,
        SavedIncomePlan,
        ScoredOpportunity,
    )
except ImportError:
    from app.schemas.income import (
        DiscoveredOpportunity,
        EnterpriseFinancialAnalysis,
        FarmerResourceProfile,
        FinancialScenarioItem,
        OpportunityCatalogItem,
        OpportunityComparisonItem,
        SavedIncomePlan,
        ScoredOpportunity,
    )

__all__ = [
    "FarmerResourceProfile",
    "OpportunityCatalogItem",
    "DiscoveredOpportunity",
    "ScoredOpportunity",
    "FinancialScenarioItem",
    "EnterpriseFinancialAnalysis",
    "OpportunityComparisonItem",
    "SavedIncomePlan",
]
