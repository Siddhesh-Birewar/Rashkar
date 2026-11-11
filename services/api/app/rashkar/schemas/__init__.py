"""Pydantic schema package for the RASHKAR integration."""

from .context import (
    RashkarCanonicalCropItem,
    RashkarCropCycleCreate,
    RashkarCropCycleResponse,
    RashkarCropCycleUpdate,
    RashkarFarmContext,
    RashkarSoilContext,
)
from .crop_heat import (
    CropHeatAssessmentRequest,
    CropHeatAssessmentResponse,
    CropHeatIntervention,
    DailyCropHeatOutlook,
)
from .income import (
    DiscoveredOpportunity,
    EnterpriseFinancialAnalysis,
    FarmerResourceProfile,
    FinancialScenarioItem,
    OpportunityCatalogItem,
    OpportunityComparisonItem,
    SavedIncomePlan,
    ScoredOpportunity,
)
from .worker_heat import (
    HourlyHeatRiskProjection,
    WorkerHeatAssessmentRequest,
    WorkerHeatAssessmentResponse,
)
from .yield_risk import (
    ActionableRecommendation,
    HistoricalYieldBaseline,
    RiskItem,
    SoilSuitabilityAnalysis,
    YieldRiskResponse,
)

__all__ = [
    "RashkarFarmContext",
    "RashkarSoilContext",
    "RashkarCropCycleCreate",
    "RashkarCropCycleUpdate",
    "RashkarCropCycleResponse",
    "RashkarCanonicalCropItem",
    "WorkerHeatAssessmentRequest",
    "HourlyHeatRiskProjection",
    "WorkerHeatAssessmentResponse",
    "CropHeatAssessmentRequest",
    "CropHeatIntervention",
    "DailyCropHeatOutlook",
    "CropHeatAssessmentResponse",
    "RiskItem",
    "HistoricalYieldBaseline",
    "SoilSuitabilityAnalysis",
    "ActionableRecommendation",
    "YieldRiskResponse",
    "FarmerResourceProfile",
    "OpportunityCatalogItem",
    "DiscoveredOpportunity",
    "ScoredOpportunity",
    "FinancialScenarioItem",
    "EnterpriseFinancialAnalysis",
    "OpportunityComparisonItem",
    "SavedIncomePlan",
]
