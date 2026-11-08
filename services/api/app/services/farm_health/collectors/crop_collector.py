"""
Crop Context Intelligence Collector for Farm Health Snapshot.

Retrieves evaluated crop outcomes, limiting factors, and active follow-up questions
from the DeterministicDecisionEngine without altering Phase 5.1 thresholds or rules.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from cropnet.services.api.app.schemas.farm_health import (
    DataAvailabilityState,
    CropContextDomainSummary,
    CropSuitabilityItem,
)
from cropnet.services.api.app.schemas.agriculture_intelligence import (
    FarmEvaluationResponse,
    CropEvaluationOutcome,
    DecisionState,
)
from cropnet.services.api.app.services.agriculture_intelligence.decision_engine import (
    _DECISION_STORE,
)
from cropnet.services.api.app.services.farm_health.collectors.base import (
    BaseDomainCollector,
    compute_age_days,
    utc_now,
)

logger = logging.getLogger(__name__)

CROP_DECISION_STALE_DAYS = 180  # Active cultivation season (~6 months)

# Module-level registry for latest evaluations by farm_id
_FARM_LATEST_EVALUATION: Dict[str, FarmEvaluationResponse] = {}


def record_farm_evaluation(farm_id: str, evaluation: FarmEvaluationResponse) -> None:
    """Register or update latest farm evaluation in memory."""
    _FARM_LATEST_EVALUATION[str(farm_id)] = evaluation


def clear_farm_evaluations() -> None:
    """Clear registered farm evaluations (for test teardown)."""
    _FARM_LATEST_EVALUATION.clear()


class CropCollector(BaseDomainCollector):
    """
    Collects deterministic crop suitability evaluation context for a farm.
    """

    @property
    def domain_name(self) -> str:
        return "crop_context"

    def _find_latest_evaluation(self, farm_id: str) -> Optional[FarmEvaluationResponse]:
        # 1. Direct registry lookup
        if farm_id in _FARM_LATEST_EVALUATION:
            return _FARM_LATEST_EVALUATION[farm_id]

        # 2. Search in _DECISION_STORE for evaluation matching farm_id
        matched = []
        for resp in _DECISION_STORE.values():
            if resp.farm_context and resp.farm_context.farm_id == farm_id:
                matched.append(resp)

        if matched:
            matched.sort(key=lambda r: r.evaluated_at, reverse=True)
            return matched[0]

        return None

    def collect(
        self,
        farm: Dict[str, Any],
        db: Session,
        target_season: Optional[str] = None,
        **kwargs
    ) -> CropContextDomainSummary:
        farm_id = str(farm["id"])
        taluka = farm.get("taluka", "Indapur")
        now = utc_now()

        eval_resp = self._find_latest_evaluation(farm_id)

        # Case A: ZERO evaluations ever executed for this farm
        if not eval_resp:
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
                top_limiting_factors=[
                    "No environmental or biological farm context available to evaluate crop suitability."
                ],
                pending_followup_questions_count=0,
            )

        # Case B: Evaluation exists
        eval_age_days = compute_age_days(eval_resp.evaluated_at, now)

        suitable: List[CropSuitabilityItem] = []
        conditionally_suitable: List[CropSuitabilityItem] = []
        disqualified: List[CropSuitabilityItem] = []
        abstained: List[CropSuitabilityItem] = []
        all_limiting_factors: List[str] = []

        for o in eval_resp.crop_outcomes:
            # Extract irrigation guidance if present
            irr_guidance: Optional[str] = None
            if isinstance(o.irrigation_guidance, dict):
                irr_guidance = o.irrigation_guidance.get("guidance") or o.irrigation_guidance.get("recommendation")
            elif isinstance(o.irrigation_guidance, str):
                irr_guidance = o.irrigation_guidance

            d_state = o.decision_state.value if hasattr(o.decision_state, "value") else str(o.decision_state)

            item = CropSuitabilityItem(
                crop_id=o.crop_id,
                common_name=o.common_name,
                marathi_name=o.marathi_name,
                decision_state=d_state,
                limiting_factors=o.limiting_factors or [],
                irrigation_guidance=irr_guidance,
            )

            # Categorize by state
            if o.decision_state == DecisionState.VERIFIED_SUITABLE:
                suitable.append(item)
            elif o.decision_state in (
                DecisionState.CONDITIONALLY_SUITABLE_PENDING_DATA,
                DecisionState.REQUIRES_REGIONAL_VALIDATION,
                DecisionState.REGIONAL_SCREENING_ONLY,
            ):
                conditionally_suitable.append(item)
            elif o.decision_state == DecisionState.UNSUITABLE_VERIFIED_CONSTRAINT or o.is_disqualified:
                disqualified.append(item)
            elif o.decision_state == DecisionState.ABSTAIN_INSUFFICIENT_EVIDENCE:
                abstained.append(item)
            else:
                abstained.append(item)

            for lf in (o.limiting_factors or []):
                if lf not in all_limiting_factors:
                    all_limiting_factors.append(lf)

        # Top limiting factors: limit to top 5
        top_factors = all_limiting_factors[:5]
        if not top_factors and disqualified:
            top_factors = ["Disqualifying agronomic constraints detected."]
        elif not top_factors and not suitable:
            top_factors = ["Missing critical parameters required to establish suitability."]

        # Freshness and Availability State evaluation
        total_crops = len(eval_resp.crop_outcomes)
        if eval_age_days is not None and eval_age_days > CROP_DECISION_STALE_DAYS:
            availability_state = DataAvailabilityState.STALE
            top_factors = [
                "Stale historical evaluation: Run updated crop suitability evaluation for current agricultural season."
            ]
        elif total_crops > 0 and len(abstained) > (total_crops / 2):
            availability_state = DataAvailabilityState.INSUFFICIENT_EVIDENCE
        elif len(conditionally_suitable) > 0 and len(suitable) == 0:
            availability_state = DataAvailabilityState.PARTIALLY_AVAILABLE
        else:
            availability_state = DataAvailabilityState.AVAILABLE

        pending_questions = len(eval_resp.follow_up_questions or [])

        return CropContextDomainSummary(
            availability_state=availability_state,
            evaluated_at=eval_resp.evaluated_at,
            target_season=target_season or eval_resp.target_season,
            taluka_resolved=eval_resp.taluka_resolved or taluka,
            evaluated_crops_count=total_crops,
            suitable_crops=suitable,
            conditionally_suitable_crops=conditionally_suitable,
            disqualified_crops=disqualified,
            abstain_crops=abstained,
            top_limiting_factors=top_factors,
            pending_followup_questions_count=pending_questions,
        )
