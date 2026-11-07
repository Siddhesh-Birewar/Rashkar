"""
CropNet AI — Agriculture Intelligence Service Package.

Exposes deterministic evaluation engine, context validation, evidence gating,
and modular agronomic evaluators.
"""
from cropnet.services.api.app.services.agriculture_intelligence.evidence_gate import (
    EvidenceGate,
    SOURCE_TIER_MAPPING
)
from cropnet.services.api.app.services.agriculture_intelligence.context_validator import (
    FarmContextValidator,
    ValidationResult
)
from cropnet.services.api.app.services.agriculture_intelligence.knowledge_retriever import (
    KnowledgeRetriever
)
from cropnet.services.api.app.services.agriculture_intelligence.soil_evaluator import (
    SoilConstraintEvaluator,
    SoilEvaluationResult
)
from cropnet.services.api.app.services.agriculture_intelligence.climate_evaluator import (
    ClimateSuitabilityEvaluator,
    ClimateEvaluationResult
)
from cropnet.services.api.app.services.agriculture_intelligence.water_evaluator import (
    WaterAvailabilityEvaluator,
    WaterEvaluationResult
)
from cropnet.services.api.app.services.agriculture_intelligence.regional_evaluator import (
    RegionalSuitabilityEvaluator,
    RegionalEvaluationResult
)
from cropnet.services.api.app.services.agriculture_intelligence.decision_aggregator import (
    DecisionAggregator
)
from cropnet.services.api.app.services.agriculture_intelligence.followup_engine import (
    FollowUpQuestionEngine
)
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import (
    DeterministicDecisionEngine
)

__all__ = [
    "EvidenceGate",
    "SOURCE_TIER_MAPPING",
    "FarmContextValidator",
    "ValidationResult",
    "KnowledgeRetriever",
    "SoilConstraintEvaluator",
    "SoilEvaluationResult",
    "ClimateSuitabilityEvaluator",
    "ClimateEvaluationResult",
    "WaterAvailabilityEvaluator",
    "WaterEvaluationResult",
    "RegionalSuitabilityEvaluator",
    "RegionalEvaluationResult",
    "DecisionAggregator",
    "FollowUpQuestionEngine",
    "DeterministicDecisionEngine",
]
